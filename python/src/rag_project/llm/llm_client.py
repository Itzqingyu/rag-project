import os
from litellm import completion

def generate_answer(user_query: str, retrieved_chunks: list[str], system_prompt: str = None) -> str:
    """
    負責接收前端的問題、系統設定，以及 RAG 找出的歷史片段，並交給 LLM 回答。
    支援動態切換多種模型 (OpenAI, Gemini, DeepSeek) 以及本地 llama.cpp。
    """
    
    # 0. 設定預設的 System Prompt
    if system_prompt is None:
        system_prompt = (
            "你是一個專業的 AI 助理。請根據使用者提供的【參考資料】來回答問題。"
            "如果參考資料中沒有答案，請直接說「我不知道」，不要自行編造。"
        )

    # 1. 將 RAG 找出的多個文字分片串接成一整段參考資料
    context_text = "\n\n---\n\n".join(retrieved_chunks)
    
    # 2. 將參考資料與用戶問題組合成最終要給 AI 的 User Prompt
    final_user_prompt = f"【參考資料】\n{context_text}\n\n【使用者問題】\n{user_query}"

    # 3. 讀取環境變數設定 (預設 fallback 為 local/my-model)
    model_name = os.getenv("ACTIVE_MODEL", "local/my-model")
    api_base = None
    api_key = None

    # 針對本地端 (llama.cpp) 的特殊處理
    # 如果 ACTIVE_MODEL 以 local/ 開頭，轉換為 openai/ 並帶入本地端 api_base
    if model_name.startswith("local/"):
        model_name = "openai/" + model_name[6:]
        api_base = os.getenv("LLAMACPP_API_BASE", "http://localhost:8080/v1")
        # 本地伺服器雖然不驗證金鑰，但底層 OpenAI Client 強制要求此欄位不能為空
        api_key = "sk-no-key-required"

    try:
        # 4. 透過 litellm 呼叫模型
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
        # 回傳明顯的錯誤訊息，方便 CLI 測試時追蹤
        return f"❌ LLM 呼叫失敗: {str(e)}"