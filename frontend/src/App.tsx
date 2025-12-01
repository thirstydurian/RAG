import { useState, useRef, useEffect } from 'react'
import './App.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  sources?: Array<{ page: number; title: string }>
  timestamp: Date
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const API_BASE_URL = 'http://localhost:8000'

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
      })

      const data = await response.json()

      if (data.success) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.answer,
          sources: data.sources,
          timestamp: new Date(),
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        setError(data.error || '응답을 받을 수 없습니다.')
      }
    } catch (err) {
      setError('서버와 연결할 수 없습니다. 백엔드가 실행 중인지 확인하세요.')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>🤖 세탁기 챗봇</h1>
          <p className="subtitle">삼성 세탁기 매뉴얼 전문가</p>
        </div>

        <div className="chat-window">
          {messages.length === 0 ? (
            <div className="welcome">
              <h2>안녕하세요!</h2>
              <p>세탁기에 대한 궁금한 점을 물어봐주세요.</p>
              <div className="sample-questions">
                <p className="sample-label">예시 질문:</p>
                <ul>
                  <li>세탁기 사용 방법이 뭐예요?</li>
                  <li>에러 코드 E1은 뭐예요?</li>
                  <li>섬세한 세탁은 어떻게 하나요?</li>
                </ul>
              </div>
            </div>
          ) : (
            messages.map(message => (
              <div key={message.id} className={`message ${message.type}`}>
                <div className="message-content">
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                  {message.sources && message.sources.length > 0 && (
                    <div className="sources">
                      <p className="sources-label">📄 참고 페이지:</p>
                      {message.sources.map((source, idx) => (
                        <span key={idx} className="source-tag">
                          {source.title} ({source.page}p)
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="error-message">
              <p>⚠️ {error}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={sendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="질문을 입력하세요..."
            disabled={loading}
            className="input-field"
          />
          <button type="submit" disabled={loading || !input.trim()} className="send-button">
            {loading ? '전송 중...' : '전송'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default App
