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
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!destination.trim()) return;

        setLoading(true);
        setError(null);
        setReport(null);

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

            {report && (
                <div className="report-result">
                    <h3>📄 생성된 보고서</h3>
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
                    max-width: 800px;
                    margin: 0 auto;
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
                .report-result {
                    margin-top: 30px;
                    border-top: 2px solid #eee;
                    padding-top: 20px;
                }
                .report-content {
                    background: white;
                    padding: 30px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    line-height: 1.6;
                }
                .report-content h1, .report-content h2, .report-content h3 {
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                    color: #333;
                }
                .report-content ul, .report-content ol {
                    padding-left: 20px;
                }
            `}</style>
        </div>
    );
};

export default TripPrep;
