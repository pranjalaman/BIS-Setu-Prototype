import React, { useState, useRef, useEffect } from 'react'
import './App.css'

const SUGGESTIONS = [
  "What are the three marks on BIS hallmarked gold jewellery?",
  "Can a trader or importer get an ISI mark licence under Scheme-I?",
  "What is the penalty for unauthorized use of ISI mark under the BIS Act 2016?",
  "Are laptops and mobile phones covered under the Compulsory Registration Scheme?",
  "What compensation is a consumer entitled to if hallmarked gold has lower purity?"
]

export default function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Namaste! I am BIS Setu, your AI assistant for Indian Standards, BIS certification schemes (ISI, CRS, FMCS), and Hallmarking.\n\nAsk any question about standard conformity, registration procedures, or consumer rights to get accurate, source-verified answers.',
      sources: []
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const sendQuestion = async (questionText) => {
    const trimmed = questionText.trim()
    if (!trimmed || isLoading) return

    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: trimmed,
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      let res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: trimmed })
      }).catch(() => null)

      // Direct fallback to localhost:8000 if proxy isn't reached
      if (!res || !res.ok) {
        res = await fetch('http://127.0.0.1:8000/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: trimmed })
        })
      }

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`)
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
          text: 'Unable to connect to BIS Setu backend server. Please verify that the FastAPI backend is running on http://127.0.0.1:8000.',
          sources: []
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendQuestion(input)
  }

  const formatMessageText = (text) => {
    // Simple helper to render bold text and bullet points cleanly
    return text.split('\n').map((line, idx) => {
      const isBullet = line.trim().startsWith('*') || line.trim().startsWith('•') || line.trim().startsWith('-')
      const cleanLine = isBullet ? line.replace(/^[\*\•\-]\s*/, '') : line

      // Handle bold **text**
      const parts = cleanLine.split(/(\*\*.*?\*\*)/g).map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>
        }
        return part
      })

      if (isBullet) {
        return (
          <div key={idx} className="bullet-point">
            <span className="bullet-dot">•</span>
            <span className="bullet-content">{parts}</span>
          </div>
        )
      }
      return <div key={idx} className="text-line">{parts}</div>
    })
  }

  return (
    <div className="chat-layout">
      <header className="chat-header">
        <div className="header-badge">SIH 2026 | PS 26107 | Team ByteKode</div>
        <div className="header-title-row">
          <div className="logo-emblem">🇮🇳</div>
          <div>
            <h1>BIS Setu — AI Assistant</h1>
            <p>Direct, Source-Verified Answers from Official Bureau of Indian Standards Documentation</p>
          </div>
        </div>
      </header>

      <main className="chat-messages">
        {messages.map((m) => (
          <div key={m.id} className={`message-row ${m.sender}`}>
            <div className="message-bubble">
              <div className="sender-tag">{m.sender === 'assistant' ? 'BIS Setu AI' : 'You'}</div>
              <div className="message-content">{formatMessageText(m.text)}</div>

              {m.sources && m.sources.length > 0 && (
                <div className="sources-container">
                  <div className="sources-label">
                    <span className="source-icon">📚</span> Verified Source Citations:
                  </div>
                  <ul className="sources-list">
                    {m.sources.map((src, i) => (
                      <li key={i} className="source-item">
                        <span className="source-doc">{src.document_name}</span>
                        {src.section && <span className="source-sec"> — {src.section}</span>}
                        {src.clause && <span className="source-clause"> ({src.clause})</span>}
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
              <div className="sender-tag">BIS Setu AI</div>
              <div className="loading-state">
                <div className="spinner"></div>
                <span>Retrieving relevant BIS standards & generating source-verified response...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <div className="suggestions-container">
        <div className="suggestions-label">Try asking:</div>
        <div className="suggestions-chips">
          {SUGGESTIONS.map((s, idx) => (
            <button
              key={idx}
              className="suggestion-chip"
              onClick={() => sendQuestion(s)}
              disabled={isLoading}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <footer className="chat-input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="query-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about ISI Mark, CRS, Hallmarking HUID, FMCS, or BIS regulations..."
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading || !input.trim()}>
            Send Question
          </button>
        </form>
      </footer>
    </div>
  )
}
