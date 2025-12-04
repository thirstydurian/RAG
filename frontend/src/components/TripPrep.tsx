import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface TripPrepProps {
    apiBaseUrl: string;
}

const TripPrep: React.FC<TripPrepProps> = ({ apiBaseUrl }) => {
    const [destination, setDestination] = useState('');
    const [keywords, setKeywords] = useState('');
    const [report, setReport] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [notionLoading, setNotionLoading] = useState(false);
    const [checklistLoading, setChecklistLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [notionMessage, setNotionMessage] = useState<string | null>(null);

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!destination.trim()) return;

        setLoading(true);
        setError(null);
        setReport(null);
        setNotionMessage(null);

        try {
            const keywordList = keywords.split(',').map(k => k.trim()).filter(k => k);

            const response = await fetch(`${apiBaseUrl}/api/tripprep/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    destination,
                    keywords: keywordList
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setReport(data.report);
            } else {
                setError(data.detail || '보고서 생성 실패');
            }
        } catch (err) {
            setError('서버 연결 실패');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadTxt = () => {
        if (!report) return;

        const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `TripPrep_${destination}_${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleSendToNotion = async () => {
        if (!report) return;

        setNotionLoading(true);
        setNotionMessage(null);

        try {
            const response = await fetch(`${apiBaseUrl}/api/tripprep/notion/send-report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report, destination }),
            });

            const data = await response.json();

            if (response.ok) {
                setNotionMessage('✅ ' + data.message);
            } else {
                setNotionMessage('❌ ' + (data.detail || 'Notion 전송 실패'));
            }
        } catch (err) {
            setNotionMessage('❌ 서버 연결 실패');
            console.error(err);
        } finally {
            setNotionLoading(false);
        }
    };

    const handleCreateChecklist = async () => {
        if (!report) return;

        setChecklistLoading(true);
        setNotionMessage(null);

        try {
            const response = await fetch(`${apiBaseUrl}/api/tripprep/notion/create-checklist`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ report, destination }),
            });

            const data = await response.json();

            if (response.ok) {
                setNotionMessage('✅ ' + data.message);
            } else {
                setNotionMessage('❌ ' + (data.detail || '체크리스트 생성 실패'));
            }
        } catch (err) {
            setNotionMessage('❌ 서버 연결 실패');
            console.error(err);
        } finally {
            setChecklistLoading(false);
        }
    };

    return (
        <div className="tripprep-container">
            <h2>✈️ TripPrep: 여행 보고서 생성기</h2>

            <div className="input-section">
                <form onSubmit={handleGenerate} className="tripprep-form">
                    <div className="form-group">
                        <label>여행지:</label>
                        <input
                            type="text"
                            value={destination}
                            onChange={(e) => setDestination(e.target.value)}
                            placeholder="예: 일본 오사카, 프랑스 파리"
                            disabled={loading}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>관심 키워드 (콤마 구분):</label>
                        <input
                            type="text"
                            value={keywords}
                            onChange={(e) => setKeywords(e.target.value)}
                            placeholder="예: 맛집, 쇼핑, 역사"
                            disabled={loading}
                        />
                    </div>

                    <button type="submit" disabled={loading || !destination.trim()} className="generate-btn">
                        {loading ? '보고서 생성 중... (약 1-2분 소요)' : '보고서 생성 시작'}
                    </button>
                </form>
            </div>

            {error && <div className="error-message">⚠️ {error}</div>}
            {notionMessage && <div className="notion-message">{notionMessage}</div>}

            {report && (
                <div className="report-result">
                    <div className="report-header">
                        <h3>📄 생성된 보고서</h3>
                        <div className="action-buttons">
                            <button onClick={handleDownloadTxt} className="action-btn download-btn">
                                💾 TXT 다운로드
                            </button>
                            <button
                                onClick={handleSendToNotion}
                                disabled={notionLoading}
                                className="action-btn notion-btn"
                            >
                                {notionLoading ? '전송 중...' : '📤 Notion으로 보고서 전송'}
                            </button>
                            <button
                                onClick={handleCreateChecklist}
                                disabled={checklistLoading}
                                className="action-btn checklist-btn"
                            >
                                {checklistLoading ? '생성 중...' : '✅ Notion에 체크리스트 생성'}
                            </button>
                        </div>
                    </div>
                    <div className="markdown-content report-content">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {report}
                        </ReactMarkdown>
                    </div>
                </div>
            )}

            <style>{`
                .tripprep-container {
                    padding: 20px;
                    max-width: 900px;
                    margin: 0 auto;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                }
                .tripprep-form {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 8px;
                }
                .form-group {
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                }
                .form-group input {
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 16px;
                }
                .generate-btn {
                    padding: 12px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background-color 0.3s;
                }
                .generate-btn:disabled {
                    background-color: #cccccc;
                    cursor: not-allowed;
                }
                .generate-btn:hover:not(:disabled) {
                    background-color: #45a049;
                }
                .error-message {
                    margin-top: 15px;
                    padding: 12px;
                    background-color: #ffebee;
                    color: #c62828;
                    border-radius: 4px;
                    border-left: 4px solid #c62828;
                }
                .notion-message {
                    margin-top: 15px;
                    padding: 12px;
                    background-color: #e8f5e9;
                    color: #2e7d32;
                    border-radius: 4px;
                    border-left: 4px solid #2e7d32;
                }
                .report-result {
                    margin-top: 30px;
                    border-top: 2px solid #eee;
                    padding-top: 20px;
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    min-height: 0;
                }
                .report-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    flex-wrap: wrap;
                    gap: 10px;
                }
                .action-buttons {
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                .action-btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .action-btn:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                .download-btn {
                    background-color: #2196F3;
                    color: white;
                }
                .download-btn:hover:not(:disabled) {
                    background-color: #1976D2;
                }
                .notion-btn {
                    background-color: #000000;
                    color: white;
                }
                .notion-btn:hover:not(:disabled) {
                    background-color: #333333;
                }
                .checklist-btn {
                    background-color: #FF9800;
                    color: white;
                }
                .checklist-btn:hover:not(:disabled) {
                    background-color: #F57C00;
                }
                .report-content {
                    background: white;
                    padding: 30px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    line-height: 1.6;
                    overflow-y: auto;
                    max-height: 600px;
                    flex: 1;
                }
                .report-content h1, .report-content h2, .report-content h3 {
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                    color: #333;
                }
                .report-content ul, .report-content ol {
                    padding-left: 20px;
                }
                .report-content a {
                    color: #2196F3;
                    text-decoration: none;
                }
                .report-content a:hover {
                    text-decoration: underline;
                }
            `}</style>
        </div>
    );
};

export default TripPrep;
