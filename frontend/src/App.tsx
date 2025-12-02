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

interface DataInfo {
    text: string
    chunk_count: number
    has_index: boolean
}

interface Chunk {
    id: number
    page: number
    title: string
    content: string
    token_count?: number
}

function App() {
    const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'data'>('chat')
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    // Upload State
    const [uploadFiles, setUploadFiles] = useState<FileList | null>(null)
    const [textInput, setTextInput] = useState('')
    const [uploading, setUploading] = useState(false)
    const [uploadStatus, setUploadStatus] = useState<string>('')

    // Data View State
    const [dataInfo, setDataInfo] = useState<DataInfo | null>(null)
    const [chunks, setChunks] = useState<Chunk[]>([])

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const API_BASE_URL = 'http://localhost:8000'

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages, activeTab])

    // Fetch data info when switching to Data tab
    useEffect(() => {
        if (activeTab === 'data') {
            fetchDataInfo()
            fetchChunks()
        }
    }, [activeTab])

    const fetchDataInfo = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/data`)
            const data = await response.json()
            setDataInfo(data)
        } catch (err) {
            console.error("Failed to fetch data info", err)
        }
    }

    const fetchChunks = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/chunks`)
            const data = await response.json()
            if (data.success) {
                setChunks(data.chunks)
            }
        } catch (err) {
            console.error("Failed to fetch chunks", err)
        }
    }

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setUploadFiles(e.target.files)
        }
    }

    const handleUpload = async () => {
        if (!uploadFiles && !textInput.trim()) {
            setUploadStatus('파일 또는 텍스트를 입력해주세요.')
            return
        }
        setUploading(true)
        setUploadStatus('업로드 및 처리 중... (시간이 걸릴 수 있습니다)')
        const formData = new FormData()

        // Add all files
        if (uploadFiles) {
            for (let i = 0; i < uploadFiles.length; i++) {
                formData.append('files', uploadFiles[i])
            }
        }

        // Add text input
        if (textInput.trim()) {
            formData.append('text_input', textInput)
        }
        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            })
            const data = await response.json()
            if (data.success) {
                const fileInfo = data.file_count > 0 ? `${data.file_count}개 파일, ` : ''
                const textInfo = data.has_text_input ? '텍스트 입력, ' : ''
                setUploadStatus(`완료! ${fileInfo}${textInfo}${data.chunk_count}개의 청크가 생성되었습니다.`)
                setMessages([])
                setTextInput('') // Clear text input
            } else {
                setUploadStatus(`실패: ${data.error}`)
            }
        } catch (err) {
            setUploadStatus('업로드 중 서버 오류 발생')
            console.error(err)
        } finally {
            setUploading(false)
        }
    }

    const handleSearch = async (query: string) => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch(`${API_BASE_URL}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, k: 10 }),
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
                    <div className="tabs">
                        <button
                            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                            onClick={() => setActiveTab('chat')}
                        >
                            채팅
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
                            onClick={() => setActiveTab('upload')}
                        >
                            PDF 업로드
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'data' ? 'active' : ''}`}
                            onClick={() => setActiveTab('data')}
                        >
                            데이터 확인
                        </button>
                    </div>
                </div>

                <div className="content-area">
                    {activeTab === 'chat' && (
                        <>
                            <div className="chat-window">
                                {messages.length === 0 ? (
                                    <div className="welcome">
                                        <h2>안녕하세요!</h2>
                                        <p>PDF를 업로드하고 질문을 시작하세요.</p>
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
                                            <div className="loading"><span></span><span></span><span></span></div>
                                        </div>
                                    </div>
                                )}
                                {error && <div className="error-message"><p>⚠️ {error}</p></div>}
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
                                    전송
                                </button>
                            </form>
                        </>
                    )}

                    {activeTab === 'upload' && (
                        <div className="upload-container">
                            <h2>문서 업로드</h2>

                            {/* File Upload Section */}
                            <div className="upload-box">
                                <h3>파일 선택 (PDF, TXT)</h3>
                                <input
                                    type="file"
                                    accept=".pdf,.txt"
                                    multiple
                                    onChange={handleFileChange}
                                    className="file-input"
                                />
                                {uploadFiles && (
                                    <p className="file-count">
                                        {uploadFiles.length}개 파일 선택됨
                                    </p>
                                )}
                            </div>

                            {/* Text Input Section */}
                            <div className="text-input-box" style={{ marginTop: '20px' }}>
                                <h3>또는 텍스트 직접 입력</h3>
                                <textarea
                                    value={textInput}
                                    onChange={(e) => setTextInput(e.target.value)}
                                    placeholder="텍스트를 붙여넣으세요..."
                                    rows={10}
                                    className="text-input-area"
                                    style={{
                                        width: '100%',
                                        padding: '10px',
                                        fontSize: '14px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px'
                                    }}
                                />
                            </div>

                            {/* Upload Button */}
                            <button
                                onClick={handleUpload}
                                disabled={(!uploadFiles && !textInput.trim()) || uploading}
                                className="upload-button"
                                style={{ marginTop: '20px' }}
                            >
                                {uploading ? '처리 중...' : '업로드 및 분석 시작'}
                            </button>

                            {/* Status Display */}
                            {uploadStatus && (
                                <div className={`upload-status ${uploadStatus.includes('실패') ? 'error' : 'success'}`}>
                                    {uploadStatus}
                                </div>
                            )}

                            <div className="upload-info">
                                <p>⚠️ 주의: 새로운 파일을 업로드하면 이전 대화 내용과 데이터는 초기화됩니다.</p>
                                <p>💡 팁: 여러 파일을 동시에 선택하거나, 파일과 텍스트를 함께 입력할 수 있습니다.</p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'data' && (
                        <div className="data-view">
                            <h2>데이터 확인</h2>
                            {dataInfo ? (
                                <div className="data-info">
                                    <div className="info-card">
                                        <h3>인덱스 상태</h3>
                                        <p>상태: {dataInfo.has_index ? '✅ 생성됨' : '❌ 없음'}</p>
                                        <p>청크 개수: {dataInfo.chunk_count}개</p>
                                    </div>

                                    <div className="chunk-list-section" style={{ marginTop: '20px' }}>
                                        <h3>인덱스 상세 (청크 목록)</h3>
                                        <div className="chunk-list" style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid #eee', padding: '10px' }}>
                                            {chunks.map(chunk => (
                                                <div key={chunk.id} className="chunk-item" style={{ marginBottom: '15px', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '5px' }}>
                                                    <div className="chunk-header" style={{ display: 'flex', gap: '10px', marginBottom: '5px', fontWeight: 'bold', color: '#555' }}>
                                                        <span className="chunk-id">#{chunk.id}</span>
                                                        <span className="chunk-page">p.{chunk.page}</span>
                                                        <span className="chunk-title">{chunk.title}</span>
                                                    </div>
                                                    <div className="chunk-content" style={{ fontSize: '0.9em', whiteSpace: 'pre-wrap' }}>
                                                        {chunk.content}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="text-preview" style={{ marginTop: '20px' }}>
                                        <h3>전체 텍스트 미리보기</h3>
                                        <pre>{dataInfo.text || "데이터가 없습니다."}</pre>
                                    </div>
                                </div>
                            ) : (
                                <p>데이터를 불러오는 중...</p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default App