---

## #6更新與新增功能

1. **`run.py` 伺服器啟動腳本**
   - 簡化 Uvicorn 服務的啟動流程，支援開發時的自動重載（Hot Reload），確保後端能快速掛載。

2. **後端原始資料儲存機制**
   - 建立標準化檔案儲存路徑（`python/uploads/raw/`），完整保存使用者上傳的原始檔案。

3. **檔案上傳與切塊處理 API (`/upload`)**
   - 支援 `multipart/form-data` 格式，接收檔案後自動進行文字切塊（Chunking）並寫入向量資料庫。

4. **前後端端對端整合**
   - 前端介面成功對接後端上傳 API，實現檔案選取、非同步傳輸與即時成功狀態回饋。

---

## 快速開始指南

1.功能需求：接收前端傳來的「實體原始檔案」並存進 uploads/raw/。

2.改動：為了接住前端的檔案，我們不能再依賴原本只能讀取本機路徑的終端機測試工具（test_main.py），必須去改寫並啟動 main.py 裡面的 FastAPI 上傳介面 (@app.post("/upload"))。

3.觸發地雷：為了測試這支剛寫好的 API，我們必須把系統從「測試模式」切換到「伺服器模式」，因此我們第一次使用了 Uvicorn 這個外部工具來啟動系統。

4.問題 (和 test_main.py 裡針對 src 路徑初始化衝突)：Uvicorn 身上沒有你寫在 test_main.py 裡面的那段 sys.path 導航作弊代碼，它看不懂 src 資料夾架構，於是報錯 ModuleNotFoundError。

### 解決方案 : 優先啟動後端(伺服器)
優先進入後端目錄並執行啟動腳本(開啟後端伺服器)：
```powershell
cd python
python run.py
