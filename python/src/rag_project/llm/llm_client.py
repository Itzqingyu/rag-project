from litellm import completion

def generate_answer(user_query: str, system_prompt: str, retrieved_chunks: list[str]) -> str:
    """
    這就是你負責的 LLM 接口模組。
    負責接收前端的問題、系統設定，以及 RAG 找出的歷史片段，並交給 LLM 回答。
    """
    
    # 1. 將 RAG 找出的多個文字分片串接成一整段參考資料
    context_text = "\n\n---\n\n".join(retrieved_chunks)
    
    # 2. 將參考資料與用戶問題組合成最終要給 AI 的 User Prompt
    final_user_prompt = f"【參考資料】\n{context_text}\n\n【使用者問題】\n{user_query}"

    try:
        # 3. 透過 litellm 呼叫模型
        # 注意：這裡的 model 名稱先暫寫一個標準格式，等整合時隊友只要改這行就能對接他本地的 qwen3.5
        response = completion(
            model="ollama/qwen", # 假設隊友是用 ollama 跑地端模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_user_prompt}
            ],
            temperature=0.2 
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"LLM 接口發生錯誤: {str(e)}"