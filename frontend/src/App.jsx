import React, { useState } from 'react'
import './App.css'

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Namaste! I am BIS Setu, your AI assistant for Indian Standards, certification schemes, and hallmarking. How may I assist you today?',
      sources: []
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: input.trim(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage.text })
      })

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`)
      }

      const data = await res.json()
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: data.answer,
          sources: data.sources || []
        }
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: 'assistant',
          text: 'Sorry, I encountered an error connecting to the service. Please make sure the backend server is running.',
          sources: []
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <div className="header-badge">SIH 2026 | PS 26107</div>
        <h1>BIS Setu</h1>
        <p>AI Assistant for Indian Standards & BIS Services — Source-Verified Answers</p>
      </header>

      <main className="chat-messages">
        {messages.map((m) => (
          <div key={m.id} className={`message-row ${m.sender}`}>
            <div className="message-bubble">
              <div className="message-content">{m.text}</div>
              {m.sources && m.sources.length > 0 && (
                <div className="sources-container">
                  <span className="sources-label">Sources & Citations:</span>
                  <ul className="sources-list">
                    {m.sources.map((src, i) => (
                      <li key={i} className="source-item">
                        <strong>{src.document_name}</strong>
                        {src.section ? ` — ${src.section}` : ''}
                        {src.clause ? ` (${src.clause})` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-row assistant">
            <div className="message-bubble loading">
              <span>Thinking & verifying against BIS standards...</span>
            </div>
          </div>
        )}
      </main>

      <footer className="chat-input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="query-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about BIS certification, ISI mark, CRS, or hallmarking..."
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </footer>
    </div>
  )
}
