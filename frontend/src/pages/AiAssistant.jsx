import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, Send, Bot, User, RefreshCw } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function AiAssistant() {
  const [ragProjectId, setRagProjectId] = useState('PROJ-2609001');
  const messagesEndRef = useRef(null);
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: "Hello! I am Avira, your AI Project Assistant. Ask me any question about project risks, deadlines, blockers, or resource constraints based on ingested project documents.",
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages, chatLoading]);

  const handleSendChatMessage = async (textToSend) => {
    const messageText = (textToSend || chatInput).trim();
    if (!messageText || chatLoading) return;

    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text: messageText,
      time: timeStr
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: ragProjectId,
          question: messageText
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Q&A request failed.');
      }

      const data = await res.json();
      const botMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: data.answer,
        retrievedChunks: data.retrieved_chunks || [],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: `Error: ${err.message}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="page-transition max-w-4xl mx-auto space-y-4">
      
      {/* Assistant Header */}
      <div className="bg-gradient-to-r from-[#0F172A] via-[#1E293B] to-[#0F172A] p-5 rounded-2xl border border-[#1E293B] shadow-2xl text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2.5 font-heading">
            <Sparkles className="w-5 h-5 text-rose-400" />
            Avira AI Assistant
          </h1>
          <p className="text-xs text-slate-300 font-medium mt-0.5">
            Interactive project risk diagnosis and natural language assistant
          </p>
        </div>

        <div className="flex items-center gap-2 bg-[#070B14] border border-[#1E293B] px-3 py-1.5 rounded-xl shadow-inner">
          <span className="text-xs font-semibold text-rose-400 uppercase">Context ID:</span>
          <input
            type="text"
            value={ragProjectId}
            onChange={(e) => setRagProjectId(e.target.value)}
            className="font-mono font-bold text-xs text-cyan-400 bg-transparent outline-none w-28"
            placeholder="PROJ-ID"
          />
        </div>
      </div>

      {/* Main Chat Thread Container */}
      <div className="glass-card border border-[#1E293B] rounded-2xl shadow-2xl flex flex-col h-[530px] overflow-hidden border-l-4 border-l-rose-500">
        
        {/* Messages List Area */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4">
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-rose-500 to-purple-600 text-white shadow-[0_0_12px_rgba(244,63,94,0.4)]'
                    : 'bg-[#070B14] text-rose-400 border border-[#1E293B]'
                }`}
              >
                {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`space-y-1 ${msg.sender === 'user' ? 'text-right' : 'text-left'}`}>
                <div
                  className={`inline-block p-3.5 rounded-2xl text-xs leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-rose-500 via-purple-600 to-indigo-600 text-white rounded-tr-none shadow-lg font-medium'
                      : 'bg-[#070B14] text-slate-100 border border-[#1E293B] rounded-tl-none font-normal shadow-sm'
                  }`}
                >
                  {msg.text}

                  {msg.retrievedChunks && msg.retrievedChunks.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-[#1E293B] text-[11px] text-slate-300 space-y-1 text-left font-mono">
                      <span className="font-semibold text-rose-400 uppercase block">Context Snippet:</span>
                      <p className="bg-[#0F172A] p-2.5 rounded-lg border border-[#1E293B] text-cyan-300">
                        {msg.retrievedChunks[0].chunk_text}
                      </p>
                    </div>
                  )}
                </div>
                <span className="text-[10px] font-mono text-slate-400 block px-1">
                  {msg.time}
                </span>
              </div>
            </div>
          ))}

          {chatLoading && (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-xl bg-[#070B14] border border-[#1E293B] text-rose-400 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 animate-spin" />
              </div>
              <div className="bg-[#070B14] border border-[#1E293B] rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-300 flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-rose-400" />
                Avira is searching project knowledge...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendChatMessage();
          }}
          className="p-3 border-t border-[#1E293B] bg-[#070B14] flex items-center gap-2 rounded-b-2xl"
        >
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask Avira about project risks, deadlines, or blockers..."
            className="input-signal flex-1"
          />
          <button
            type="submit"
            disabled={!chatInput.trim() || chatLoading}
            className="btn-primary"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>

      </div>

    </div>
  );
}
