import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Loader2, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello! Please upload a markdown document to start asking questions.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ----------------------------------------------------
  // 修改這裡：改用標準 HTML input(type="file") 配合 fetch 呼叫 FastAPI
  // ----------------------------------------------------
  const handleUpload = () => {
    // 建立一個隱藏的檔案選擇視窗
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.md,.txt'; // 可依需求調整

    fileInput.onchange = async (e: Event) => {
      const target = e.target as HTMLInputElement;
      if (!target.files || target.files.length === 0) return;

      const file = target.files[0];
      const formData = new FormData();
      formData.append('file', file);

      setUploading(true);
      try {
        // 直接對接你的 FastAPI 後端上傳介面
        const response = await fetch('http://127.0.0.1:8000/upload', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: `✅ Successfully uploaded **${file.name}**. ${data.message} (Added ${data.chunks_added} chunks)`
          }]);
        } else {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: `❌ Failed to upload document: ${data.detail || 'Unknown error'}`
          }]);
        }
      } catch (error: any) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `⚠️ Connection error: Make sure the FastAPI backend is running. (${error.message})`
        }]);
      } finally {
        setUploading(false);
      }
    };

    // 觸發檔案選擇視窗
    fileInput.click();
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      // 這裡保留你原本預計串接查詢的邏輯（未來可對接後端的 query API）
      // const res = await window.electronAPI.queryDoc(userMessage.content);
      
      // 目前先做個假回覆防呆，等查詢 API 寫好可直接替換
      setTimeout(() => {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Echo: You asked "${userMessage.content}". (Query API pending connection)`
        }]);
        setLoading(false);
      }, 1000);

    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Query failed: ${error.message}`
      }]);
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>RAG Assistant</h1>
        <span className="badge">Beta</span>
      </header>

      <main className="chat-area">
        <div className="messages-container">
          {messages.map(msg => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`}>
              <div className="avatar">
                {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className="message-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-wrapper assistant">
              <div className="avatar"><Bot size={20} /></div>
              <div className="message-content loading">
                <Loader2 className="spinner" size={20} />
                <span>Searching documents...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="input-area">
        <div className="input-box">
          <button 
            className="action-btn upload-btn" 
            onClick={handleUpload} 
            disabled={uploading}
            title="Upload Markdown File"
          >
            {uploading ? <Loader2 className="spinner" size={20} /> : <Paperclip size={20} />}
          </button>
          
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            rows={1}
            disabled={loading}
          />
          
          <button 
            className="action-btn send-btn" 
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            <Send size={20} />
          </button>
        </div>
        <div className="footer-text">
          Powered by local RAG engine & fastembed
        </div>
      </footer>
    </div>
  );
}