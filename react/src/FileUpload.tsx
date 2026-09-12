import React, { useState } from 'react';

export default function FileUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setMessage('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('請先選擇檔案！');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setMessage('檔案上傳與向量化中，請稍候...');
      
      const response = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(`✅ 成功！${data.message} (新增 ${data.chunks_added} 個區塊)`);
      } else {
        setMessage(`❌ 上傳失敗：${data.detail || '未知錯誤'}`);
      }
    } catch (error: any) {
      setMessage(`⚠️ 連線錯誤，請確認後端伺服器已啟動：${error.message}`);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', maxWidth: '400px', margin: '20px auto', color: '#fff' }}>
      <h2>上傳知識庫檔案</h2>
      
      <input 
        type="file" 
        onChange={handleFileChange} 
        style={{ marginBottom: '15px', display: 'block' }}
      />
      
      <button 
        onClick={handleUpload} 
        disabled={!file}
        style={{ padding: '8px 16px', cursor: 'pointer' }}
      >
        開始上傳
      </button>

      {message && (
        <div style={{ marginTop: '15px', fontWeight: 'bold' }}>
          {message}
        </div>
      )}
    </div>
  );
}