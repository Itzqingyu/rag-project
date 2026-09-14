"""LLM 大語言模型介面模組。

提供讀取 prompts/ 目錄下提示詞範本的能力，
並透過 litellm 支援雲端與本地端 LLM 的通用問答與 1-shot 結構化萃取。
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
from litellm import completion

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")


def load_prompt_template(template_name: str) -> str:
    """從 prompts/ 目錄讀取指定的 Markdown 提示詞範本檔案內容。
    
    :param template_name: 範本名稱 (例如 'meeting_extraction' 或 'rag_qa')
    """
    if not template_name.endswith(".md"):
        template_name += ".md"
        
    prompt_path = os.path.join(PROMPTS_DIR, template_name)
    if not os.path.exists(prompt_path):
        raise FileNotFoundError(f"找不到 Prompt 範本檔案: {prompt_path}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_answer(user_query: str, retrieved_chunks: List[str], system_prompt: Optional[str] = None) -> str:
    """負責接收問題與 RAG 召回的文本片段，結合 Prompt 範本呼叫 LLM 進行問答生成。"""
    if system_prompt is None:
        try:
            system_prompt = load_prompt_template("rag_qa")
        except Exception:
            system_prompt = (
                "你是一個專業的 AI 助理。請根據使用者提供的【參考資料】來回答問題。"
                "如果參考資料中沒有答案，請直接說「我不知道」，不要自行編造。"
            )

    context_text = "\n\n---\n\n".join(retrieved_chunks)
    final_user_prompt = f"【參考資料】\n{context_text}\n\n【使用者問題】\n{user_query}"

    model_name = os.getenv("ACTIVE_MODEL", "local/my-model")
    api_base = None
    api_key = None

    if model_name.startswith("local/"):
        model_name = "openai/" + model_name[6:]
        api_base = os.getenv("LLAMACPP_API_BASE", "http://localhost:8080/v1")
        api_key = "sk-no-key-required"

    try:
        response = completion(
            model=model_name,
            api_base=api_base,
            api_key=api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_user_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ LLM 呼叫失敗: {str(e)}"


def extract_structured_meeting_data(full_text: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
    """傳入完整會議紀錄 Markdown 全文，呼叫 LLM 進行 1-shot 結構化萃取並解析為 Python 字典。
    
    回傳字典結構包含：
    {
      "meeting": {...},
      "decisions": [...],
      "tasks": [...]
    }
    """
    if system_prompt is None:
        system_prompt = load_prompt_template("meeting_extraction")

    user_prompt = f"請閱讀以下會議紀錄內文，並按照規定萃取為單一 JSON 物件：\n\n{full_text}"

    model_name = os.getenv("ACTIVE_MODEL", "local/my-model")
    api_base = None
    api_key = None

    if model_name.startswith("local/"):
        model_name = "openai/" + model_name[6:]
        api_base = os.getenv("LLAMACPP_API_BASE", "http://localhost:8080/v1")
        api_key = "sk-no-key-required"

    try:
        response = completion(
            model=model_name,
            api_base=api_base,
            api_key=api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1
        )
        raw_output = response.choices[0].message.content.strip()
        
        # 清理可能包含的 Markdown ```json ... ``` 包裹標籤
        clean_json_str = re.sub(r"^```(?:json)?\s*", "", raw_output, flags=re.MULTILINE)
        clean_json_str = re.sub(r"\s*```$", "", clean_json_str, flags=re.MULTILINE).strip()
        
        parsed_data = json.loads(clean_json_str)
        return parsed_data
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM 輸出的文字無法被解析為合法 JSON: {exc}\n原始輸出內容:\n{raw_output}") from exc
    except Exception as e:
        raise RuntimeError(f"LLM 結構化萃取呼叫失敗: {e}") from e
