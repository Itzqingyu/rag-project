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

  const handleUpload = async () => {
    try {
      const filePath = await window.electronAPI.openFile();
      if (!filePath) return;

      setUploading(true);
      const res = await window.electronAPI.uploadFile(filePath);
      
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `✅ Successfully uploaded document. Added ${res.chunks_added} chunks to the database. You can now ask questions about it!`
      }]);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Failed to upload document: ${error.message}`
      }]);
    } finally {
      setUploading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const res = await window.electronAPI.queryDoc(userMessage.content);
      
      // We are just returning the retrieved chunks since LLM summarization is deferred.
      const resultsText = res.results.length > 0 
        ? res.results.map((r, i) => `**Result ${i + 1}**:\n${r.content}`).join('\n\n---\n\n')
        : 'No relevant information found.';

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: resultsText
      }]);
    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `❌ Query failed: ${error.message}`
      }]);
    } finally {
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
