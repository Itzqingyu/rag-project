import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_project.converter import convert_to_markdown
from rag_project.database import get_doc_by_id, get_doc_by_path, get_all_docs
from rag_project.rag_engine import add_document, search, list_documents, delete_document
from rag_project.llm_client import generate_answer, extract_structured_meeting_data
from rag_project.activity import (
    create_activity,
    get_activity,
    list_activities,
    update_activity,
    delete_activity,
)
from rag_project.meeting_task import (
    add_meeting,
    get_meetings,
    get_meeting_by_id,
    update_meeting,
    delete_meeting,
    add_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task,
)
from rag_project.decision import (
    create_decision,
    get_decision,
    list_decisions,
    update_decision,
    delete_decision,
)
from rag_project.schedule import (
    create_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
    delete_schedule,
)
from rag_project.incident import (
    create_incident,
    get_incident,
    list_incidents,
    update_incident,
    delete_incident,
)

app = FastAPI(
    title="RAG Project Backend API",
    description="智能客製化意見助手 - RAG 檢索、轉檔與 AI 結構化會議解析 REST API",
    version="1.1.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Pydantic Schemas (資料模型的請求與回應)
# ==========================================

class PingResponse(BaseModel):
    status: str
    message: str

# RAG & LLM
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    generate_answer: bool = False

class DocumentChunk(BaseModel):
    content: str
    metadata: Dict[str, Any]

class QueryResponse(BaseModel):
    results: List[DocumentChunk]
    answer: Optional[str] = None

# AI 結構化萃取與 Preview-Commit 流程模型
class ExtractSummaryRequest(BaseModel):
    doc_id: Optional[int] = None
    file_path: Optional[str] = None

class MeetingCreate(BaseModel):
    activity_id: int
    name: str
    start_time: str = ""
    end_time: str = ""
    location: str = ""
    participants: str = ""
    content: str = ""
    date: str = ""

class TaskCreate(BaseModel):
    activity_id: int
    content: str
    assignee: str = ""
    due_date: str = ""
    priority: str = "中"
    status: str = "pending"
    meeting_id: Optional[int] = None

class DecisionCreate(BaseModel):
    activity_id: int
    problem: str
    options: str  # JSON array string如 '["解方A", "解方B"]'
    final_decision: str
    reason: str
    source: str
    confirmation_status: str = "pending"
    meeting_id: Optional[int] = None

class CommitSummaryRequest(BaseModel):
    activity_id: int
    meeting: MeetingCreate
    decisions: List[DecisionCreate] = []
    tasks: List[TaskCreate] = []

# Activity
class ActivityCreate(BaseModel):
    name: str
    year: int
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    venue: Optional[str] = None
    activity_type: Optional[str] = None
    coordinator: Optional[str] = None
    expected_attendees: Optional[int] = None
    budget: Optional[int] = None

class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    venue: Optional[str] = None
    activity_type: Optional[str] = None
    coordinator: Optional[str] = None
    expected_attendees: Optional[int] = None
    budget: Optional[int] = None

class MeetingUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[str] = None
    content: Optional[str] = None
    activity_id: Optional[int] = None
    date: Optional[str] = None

class TaskUpdate(BaseModel):
    content: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    activity_id: Optional[int] = None
    meeting_id: Optional[int] = None

class DecisionUpdate(BaseModel):
    activity_id: Optional[int] = None
    meeting_id: Optional[int] = None
    problem: Optional[str] = None
    options: Optional[str] = None
    final_decision: Optional[str] = None
    reason: Optional[str] = None
    source: Optional[str] = None
    confirmation_status: Optional[str] = None

# Schedule
class ScheduleCreate(BaseModel):
    activity_id: int
    name: str
    start_time: str
    location: str
    owner: str
    notes: str
    category: str
    end_time: Optional[str] = None
    meeting_id: Optional[int] = None

class ScheduleUpdate(BaseModel):
    activity_id: Optional[int] = None
    meeting_id: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    owner: Optional[str] = None
    notes: Optional[str] = None
    category: Optional[str] = None

# Incident
class IncidentCreate(BaseModel):
    activity_id: int
    content: str
    occurred_at: str
    schedule_id: Optional[int] = None
    cause: Optional[str] = None
    suggestion: Optional[str] = None

class IncidentUpdate(BaseModel):
    activity_id: Optional[int] = None
    schedule_id: Optional[int] = None
    content: Optional[str] = None
    occurred_at: Optional[str] = None
    cause: Optional[str] = None
    suggestion: Optional[str] = None


# ==========================================
# 系統與 RAG/轉檔 端點
# ==========================================

@app.get("/ping", response_model=PingResponse, tags=["System"])
def ping():
    return {"status": "ok", "message": "Backend is running!"}


@app.get("/documents", tags=["RAG Document"])
def get_documents():
    return list_documents()


@app.post("/upload", tags=["RAG Document"])
def upload_document(file: UploadFile = File(...)):
    """接受 MD, TXT, PDF, DOCX 上傳，由 converter 統一轉成 Markdown 並託管於 python/data/markdown/。"""
    temp_dir = tempfile.mkdtemp()
    try:
        raw_file_path = os.path.join(temp_dir, file.filename)
        with open(raw_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 呼叫多格式轉檔器將檔案轉換為標準 Markdown
        target_md_path = convert_to_markdown(raw_file_path)
        
        # 將轉換後的 Markdown 送入 RAG 引擎
        chunks_added = add_document(
            file_path=target_md_path, 
            force=True,
            raw_file_path=file.filename
        )
        
        doc_record = get_doc_by_path(target_md_path)
        
        return {
            "status": "success", 
            "message": f"成功轉檔並向量化 {file.filename}！",
            "doc_id": doc_record["id"] if doc_record else None,
            "file_path": target_md_path,
            "chunks_added": chunks_added
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@app.delete("/documents/{identifier:path}", tags=["RAG Document"])
def remove_document(identifier: str):
    success = delete_document(identifier)
    if not success:
        raise HTTPException(status_code=404, detail="找不到該檔案紀錄")
    return {"status": "success", "message": f"已成功刪除 {identifier}"}


@app.post("/query", response_model=QueryResponse, tags=["RAG Document"])
def query_docs(req: QueryRequest):
    try:
        docs = search(req.query, top_k=req.top_k)
        results = [
            DocumentChunk(
                content=doc.page_content,
                metadata=doc.metadata
            ) for doc in docs
        ]
        
        answer = None
        if req.generate_answer and docs:
            chunks = [doc.page_content for doc in docs]
            answer = generate_answer(req.query, chunks)

        return QueryResponse(results=results, answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# AI 結構化會議解析與 Preview-Commit 端點
# ==========================================

@app.post("/extract_summary", tags=["AI Structured Extraction"])
def extract_summary(req: ExtractSummaryRequest):
    """階段 1：傳入 doc_id 或 file_path，LLM 從全文萃取會議日期/解方/決策/待辦，回傳預覽 JSON。"""
    record = None
    if req.doc_id is not None:
        record = get_doc_by_id(req.doc_id)
    elif req.file_path is not None:
        record = get_doc_by_path(req.file_path)
        
    if not record:
        raise HTTPException(status_code=404, detail="找不到指定的文件紀錄")
        
    markdown_content = record.get("markdown_content", "")
    if not markdown_content.strip():
        raise HTTPException(status_code=400, detail="文件內文為空，無法進行 AI 萃取")
        
    try:
        # 直接帶入整份 Markdown 內文進行 1-shot 結構化萃取
        extracted_data = extract_structured_meeting_data(markdown_content)
        return {
            "status": "success",
            "doc_id": record["id"],
            "preview_data": extracted_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 結構化萃取失敗: {e}")


@app.post("/commit_summary", tags=["AI Structured Extraction"])
def commit_summary(req: CommitSummaryRequest):
    """階段 2：接收使用者確認/編修後的結構化資料，一次性事務寫入 SQLite 業務表。"""
    try:
        # 1. 寫入 Meeting
        meeting_dict = req.meeting.model_dump()
        meeting_dict["activity_id"] = req.activity_id
        created_meeting = add_meeting(**meeting_dict)
        meeting_id = created_meeting["id"]

        # 2. 寫入 Decisions
        created_decisions = []
        for d in req.decisions:
            d_dict = d.model_dump()
            d_dict["activity_id"] = req.activity_id
            d_dict["meeting_id"] = meeting_id
            created_d = create_decision(**d_dict)
            created_decisions.append(created_d)

        # 3. 寫入 Tasks
        created_tasks = []
        for t in req.tasks:
            t_dict = t.model_dump()
            t_dict["activity_id"] = req.activity_id
            t_dict["meeting_id"] = meeting_id
            created_t = add_task(**t_dict)
            created_tasks.append(created_t)

        return {
            "status": "success",
            "message": "成功將 AI 結構化會議紀錄寫入資料庫！",
            "meeting": created_meeting,
            "decisions": created_decisions,
            "tasks": created_tasks
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"寫入資料庫失敗: {e}")


# ==========================================
# 活動管理 (Activity Endpoints)
# ==========================================

@app.get("/activities", tags=["Activity"])
def api_list_activities():
    return list_activities()

@app.get("/activities/{activity_id}", tags=["Activity"])
def api_get_activity(activity_id: int):
    act = get_activity(activity_id)
    if not act:
        raise HTTPException(status_code=404, detail="找不到活動")
    return act

@app.post("/activities", tags=["Activity"])
def api_create_activity(payload: ActivityCreate):
    try:
        return create_activity(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.put("/activities/{activity_id}", tags=["Activity"])
def api_update_activity(activity_id: int, payload: ActivityUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        updated = update_activity(activity_id, **changes)
        if not updated:
            raise HTTPException(status_code=404, detail="找不到活動")
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/activities/{activity_id}", tags=["Activity"])
def api_delete_activity(activity_id: int):
    try:
        deleted = delete_activity(activity_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="找不到活動")
        return {"status": "success", "deleted": deleted}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ==========================================
# 會議管理 (Meeting Endpoints)
# ==========================================

@app.get("/meetings", tags=["Meeting"])
def api_get_meetings(activity_id: Optional[int] = Query(None)):
    return get_meetings(activity_id=activity_id)

@app.get("/meetings/{meeting_id}", tags=["Meeting"])
def api_get_meeting(meeting_id: int):
    m = get_meeting_by_id(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="找不到會議紀錄")
    return m

@app.post("/meetings", tags=["Meeting"])
def api_create_meeting(payload: MeetingCreate):
    try:
        return add_meeting(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.put("/meetings/{meeting_id}", tags=["Meeting"])
def api_update_meeting(meeting_id: int, payload: MeetingUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        ok = update_meeting(meeting_id, **changes)
        if not ok:
            raise HTTPException(status_code=404, detail="找不到會議或無更新")
        return get_meeting_by_id(meeting_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/meetings/{meeting_id}", tags=["Meeting"])
def api_delete_meeting(meeting_id: int):
    ok = delete_meeting(meeting_id)
    if not ok:
        raise HTTPException(status_code=404, detail="找不到會議紀錄")
    return {"status": "success", "deleted_id": meeting_id}


# ==========================================
# 待辦事項 (Task Endpoints)
# ==========================================

@app.get("/tasks", tags=["Task"])
def api_get_tasks(activity_id: Optional[int] = Query(None), meeting_id: Optional[int] = Query(None)):
    return get_tasks(activity_id=activity_id, meeting_id=meeting_id)

@app.get("/tasks/{task_id}", tags=["Task"])
def api_get_task(task_id: int):
    t = get_task_by_id(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="找不到待辦事項")
    return t

@app.post("/tasks", tags=["Task"])
def api_create_task(payload: TaskCreate):
    try:
        return add_task(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.put("/tasks/{task_id}", tags=["Task"])
def api_update_task(task_id: int, payload: TaskUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        ok = update_task(task_id, **changes)
        if not ok:
            raise HTTPException(status_code=404, detail="找不到待辦事項或無更新")
        return get_task_by_id(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/tasks/{task_id}", tags=["Task"])
def api_delete_task(task_id: int):
    ok = delete_task(task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="找不到待辦事項")
    return {"status": "success", "deleted_id": task_id}


# ==========================================
# 決策紀錄 (Decision Endpoints)
# ==========================================

@app.get("/decisions", tags=["Decision"])
def api_list_decisions(activity_id: Optional[int] = Query(None)):
    return list_decisions(activity_id=activity_id)

@app.get("/decisions/{decision_id}", tags=["Decision"])
def api_get_decision(decision_id: int):
    d = get_decision(decision_id)
    if not d:
        raise HTTPException(status_code=404, detail="找不到決策紀錄")
    return d

@app.post("/decisions", tags=["Decision"])
def api_create_decision(payload: DecisionCreate):
    try:
        return create_decision(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.put("/decisions/{decision_id}", tags=["Decision"])
def api_update_decision(decision_id: int, payload: DecisionUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        updated = update_decision(decision_id, **changes)
        if not updated:
            raise HTTPException(status_code=404, detail="找不到決策紀錄")
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/decisions/{decision_id}", tags=["Decision"])
def api_delete_decision(decision_id: int):
    deleted = delete_decision(decision_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="找不到決策紀錄")
    return {"status": "success", "deleted": deleted}


# ==========================================
# 流程日程 (Schedule Endpoints)
# ==========================================

@app.get("/schedules", tags=["Schedule"])
def api_list_schedules(activity_id: Optional[int] = Query(None)):
    return list_schedules(activity_id=activity_id)

@app.get("/schedules/{schedule_id}", tags=["Schedule"])
def api_get_schedule(schedule_id: int):
    s = get_schedule(schedule_id)
    if not s:
        raise HTTPException(status_code=404, detail="找不到流程日程")
    return s

@app.post("/schedules", tags=["Schedule"])
def api_create_schedule(payload: ScheduleCreate):
    try:
        return create_schedule(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.put("/schedules/{schedule_id}", tags=["Schedule"])
def api_update_schedule(schedule_id: int, payload: ScheduleUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        updated = update_schedule(schedule_id, **changes)
        if not updated:
            raise HTTPException(status_code=404, detail="找不到流程日程")
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/schedules/{schedule_id}", tags=["Schedule"])
def api_delete_schedule(schedule_id: int):
    deleted = delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="找不到流程日程")
    return {"status": "success", "deleted": deleted}


# ==========================================
# 突發事件 (Incident Endpoints)
# ==========================================

@app.get("/incidents", tags=["Incident"])
def api_list_incidents(activity_id: Optional[int] = Query(None)):
    return list_incidents(activity_id=activity_id)

@app.get("/incidents/{incident_id}", tags=["Incident"])
def api_get_incident(incident_id: int):
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="找不到突發事件紀錄")
    return inc

@app.post("/incidents", tags=["Incident"])
def api_create_incident(payload: IncidentCreate):
    try:
        return create_incident(**payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.put("/incidents/{incident_id}", tags=["Incident"])
def api_update_incident(incident_id: int, payload: IncidentUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        updated = update_incident(incident_id, **changes)
        if not updated:
            raise HTTPException(status_code=404, detail="找不到突發事件紀錄")
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.delete("/incidents/{incident_id}", tags=["Incident"])
def api_delete_incident(incident_id: int):
    deleted = delete_incident(incident_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="找不到突發事件紀錄")
    return {"status": "success", "deleted": deleted}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)