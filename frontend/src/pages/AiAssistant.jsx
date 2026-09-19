import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, Send, Layers, ChevronDown } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function AiAssistant() {
  const [ragProjectId, setRagProjectId] = useState('PROJ-101');
  const messagesEndRef = useRef(null);
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: "Hello! I am Avira, your AI Project Assistant. Ask me any question about project risks, deadlines, blockers, or resource constraints based on ingested ChromaDB documents.",
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
    <div className="page-transition max-w-4xl mx-auto space-y-6">
      <div className="card-content space-y-4">
        {/* Header bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[#232E47] pb-3 gap-2">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[6px] bg-[#131B2E] border border-[#232E47] flex items-center justify-center text-[#FF8A3D]">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="page-title text-[22px]">Avira — AI Assistant</h1>
              <p className="small-label mt-0.5">Powered by Local RAG & Flan-T5 Synthesis</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="small-label">Project ID Context:</label>
            <input
              type="text"
              value={ragProjectId}
              onChange={(e) => setRagProjectId(e.target.value)}
              className="input-signal font-mono text-xs py-1 px-3 w-28 text-[#FF8A3D] font-bold"
              placeholder="PROJ-101"
            />
          </div>
        </div>

        {/* Scrollable Chat Window */}
        <div className="chat-window-signal min-h-[380px] max-h-[500px]">
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={
                  msg.sender === 'user'
                    ? 'chat-bubble-user-signal max-w-[80%]'
                    : 'chat-bubble-assistant-signal max-w-[88%] space-y-2'
                }
              >
                {msg.sender === 'assistant' && (
                  <div className="flex items-center gap-2 mb-1.5 pb-1 border-b border-[#232E47]">
                    <Sparkles className="w-4 h-4 text-[#FF8A3D]" />
                    <span className="font-heading text-[13px] font-semibold text-[#FF8A3D]">Avira</span>
                  </div>
                )}

                {/* Main Answer Message Text */}
                <div className="body-text whitespace-pre-wrap leading-relaxed">
                  {msg.text}
                </div>

                {/* Collapsible Sources & Evidence Chunks Section */}
                {msg.retrievedChunks && msg.retrievedChunks.length > 0 && (
                  <details className="mt-3 pt-2 border-t border-[#232E47] group">
                    <summary className="cursor-pointer font-sans text-[12px] font-medium text-[#FF8A3D] hover:underline flex items-center justify-between py-1 select-none">
                      <span className="flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5" />
                        <span>View Sources ({msg.retrievedChunks.length} Chunks)</span>
                      </span>
                      <ChevronDown className="w-3.5 h-3.5 group-open:rotate-180 transition-transform" />
                    </summary>

                    <div className="mt-2 space-y-2">
                      {msg.retrievedChunks.map((chunk, cIdx) => (
                        <div
                          key={cIdx}
                          className="p-2.5 bg-[#0B1220] border border-[#232E47] rounded-[6px] space-y-1 font-mono text-xs"
                        >
                          <div className="flex justify-between items-center text-[10px] text-[#8B95AC]">
                            <span>Source: {chunk.document_name}</span>
                            <span className="text-[#FF8A3D]">Similarity: {chunk.similarity_score}</span>
                          </div>
                          <p className="m-0 text-[#E8ECF4] italic leading-normal">"{chunk.chunk_text}"</p>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                <span className="small-label block mt-1 text-[10px] text-right">{msg.time}</span>
              </div>
            </div>
          ))}

          {/* Typing Indicator with 3 Pulsing Dots */}
          {chatLoading && (
            <div className="flex items-center gap-2 chat-bubble-assistant-signal w-fit">
              <Sparkles className="w-4 h-4 text-[#FF8A3D] animate-spin" />
              <span className="small-label text-[#E8ECF4]">Avira is synthesizing answer</span>
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A3D] animate-bounce"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A3D] animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#FF8A3D] animate-bounce [animation-delay:0.4s]"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Question Prompts */}
        <div className="flex flex-wrap gap-2 pt-1">
          <span className="small-label self-center">Suggested Prompts:</span>
          {[
            "What is currently blocking this project?",
            "When is milestone 3 scheduled?",
            "Are there defect density concerns?"
          ].map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSendChatMessage(q)}
              className="btn-secondary text-xs py-1 px-3"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Pill-Shaped Chat Input Bar with Send Icon Button */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendChatMessage(chatInput);
          }}
          className="flex items-center gap-2 pt-2"
        >
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendChatMessage(chatInput);
              }
            }}
            placeholder={`Ask Avira a question about project '${ragProjectId}'...`}
            disabled={chatLoading}
            className="input-signal rounded-full px-4 py-2.5 flex-1"
          />
          <button
            type="submit"
            disabled={chatLoading || !chatInput.trim()}
            className="w-10 h-10 rounded-full bg-[#FF8A3D] text-[#0B1220] hover:bg-[#e07730] flex items-center justify-center flex-shrink-0 disabled:opacity-50 transition-colors cursor-pointer"
            title="Send Message"
          >
            <Send className="w-4 h-4 font-bold" />
          </button>
        </form>
      </div>
    </div>
  );
}
