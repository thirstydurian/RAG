import { useState, useRef, useEffect } from 'react'
import './App.css'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface SearchResult {
    index: number
    page: number
    title: string
    content: string
    score: number
    selected?: boolean
}

interface Message {
    id: string
    type: 'user' | 'assistant' | 'system'
    content: string
    sources?: Array<{ page: number; title: string }>
    searchResults?: SearchResult[]
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

    const handleSearch = async (query: string) => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch(`${API_BASE_URL}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, k: 5 }),
            })
            const data = await response.json()

            if (data.success) {
                const systemMessage: Message = {
                    id: Date.now().toString(),
                    type: 'system',
                    content: '답변에 참고할 문서를 선택해주세요.',
                    searchResults: data.results.map((r: SearchResult) => ({ ...r, selected: true })),
                    timestamp: new Date(),
                }
                setMessages(prev => [...prev, systemMessage])
            } else {
                setError(data.error || '검색 실패')
            }
        } catch (err) {
            setError('서버 연결 실패')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleGenerate = async (query: string, selectedIndices: number[]) => {
        setLoading(true)
        setError(null)

        // 시스템 메시지(선택창) 제거 또는 완료 상태로 변경하는 로직이 필요할 수 있음
        // 여기서는 간단히 답변 생성 요청만 보냄

        try {
            const response = await fetch(`${API_BASE_URL}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, selected_indices: selectedIndices }),
            })
            const data = await response.json()

            if (data.success) {
                const assistantMessage: Message = {
                    id: Date.now().toString(),
                    type: 'assistant',
                    content: data.answer,
                    sources: data.sources,
                    timestamp: new Date(),
                }
                setMessages(prev => [...prev, assistantMessage])
            } else {
                setError(data.error || '생성 실패')
            }
        } catch (err) {
            setError('서버 연결 실패')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

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
        const currentInput = input
        setInput('')

        // 1. 검색 요청
        await handleSearch(currentInput)
    }

    const toggleSelection = (messageId: string, resultIndex: number) => {
        setMessages(prev => prev.map(msg => {
            if (msg.id === messageId && msg.searchResults) {
                const newResults = [...msg.searchResults]
                newResults[resultIndex] = {
                    ...newResults[resultIndex],
                    selected: !newResults[resultIndex].selected
                }
                return { ...msg, searchResults: newResults }
            }
            return msg
        }))
    }

    const submitSelection = (messageId: string) => {
        const message = messages.find(m => m.id === messageId)
        if (!message || !message.searchResults) return

        // 해당 시스템 메시지 이전의 사용자 메시지 찾기
        const msgIndex = messages.findIndex(m => m.id === messageId)
        const userMessage = messages[msgIndex - 1]

        if (!userMessage) return

        const selectedIndices = message.searchResults
            .filter(r => r.selected)
            .map(r => r.index)

        handleGenerate(userMessage.content, selectedIndices)
    }

    return (
        <div className="app">
            <div className="container">
                <div className="header">
                    <h1>RAG 챗봇</h1>
                    <p className="subtitle">당신의 문서 전문가</p>
                </div>

                <div className="chat-window">
                    {messages.length === 0 ? (
                        <div className="welcome">
                            <h2>안녕하세요!</h2>
                            <p>첨부한 문서에 대해 궁금한 점을 물어봐주세요.</p>
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
                                    {message.type === 'system' && message.searchResults ? (
                                        <div className="search-results">
                                            <p className="system-instruction">🔍 답변에 참고할 문서를 선택하세요:</p>
                                            <div className="results-list">
                                                {message.searchResults.map((result, idx) => (
                                                    <div key={idx} className={`result-item ${result.selected ? 'selected' : ''}`}
                                                        onClick={() => toggleSelection(message.id, idx)}>
                                                        <div className="checkbox">
                                                            {result.selected ? '✅' : '⬜'}
                                                        </div>
                                                        <div className="result-info">
                                                            <span className="result-title">{result.title} (p.{result.page})</span>
                                                            <p className="result-preview">{result.content.substring(0, 100)}...</p>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                            <button
                                                className="generate-button"
                                                onClick={() => submitSelection(message.id)}
                                                disabled={loading}
                                            >
                                                {loading ? '답변 생성 중...' : '선택한 문서로 답변 생성'}
                                            </button>
                                        </div>
                                    ) : (
                                        <>
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
                                        </>
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