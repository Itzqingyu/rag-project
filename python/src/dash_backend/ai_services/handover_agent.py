import os
from litellm import completion
from typing import List, Dict, Any

# 💡 動態定位 prompts 資料夾路徑，不管你在哪裡執行程式都不會出錯
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # 目前在 ai_services/
PROMPTS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "prompts") # 往上一層找 prompts/
PROMPT_FILE_PATH = os.path.join(PROMPTS_DIR, "handover_summary.md")

def generate_handover_summary(schedules: List[Dict[str, Any]], decisions: List[Dict[str, Any]]) -> str:
    # 1. 將陣列資料整理成字串
    schedules_text = ""
    for s in schedules:
        if s.get('outcome_note'):
            schedules_text += f"- {s.get('name')}: {s.get('outcome_note')}\n"
            
    decisions_text = ""
    for d in decisions:
        if d.get('outcome_note'):
            decisions_text += f"- 問題：{d.get('problem')} / 決策：{d.get('title')} / 結果：{d.get('outcome_note')}\n"

    # 若沒有資料，給予預設文字避免空白
    if not schedules_text: schedules_text = "無相關紀錄\n"
    if not decisions_text: decisions_text = "無相關紀錄\n"

    # 2. 讀取 Markdown Prompt 模板
    try:
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到 Prompt 模板檔案：{PROMPT_FILE_PATH}")

    # 3. 將資料填入模板中的佔位符 (使用 replace 避免花括號格式衝突)
    final_prompt = prompt_template.replace("{{schedules_data}}", schedules_text)\
                                  .replace("{{decisions_data}}", decisions_text)

    # 4. 呼叫 AI 模型
    response = completion(
        model="gemini/gemini-1.5-flash", # 請確認 .env 裡有正確配置金鑰
        messages=[
            # 這裡我們將 system 角色與資料合併，直接作為 user 訊息發送，能達到一樣好的效果
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content