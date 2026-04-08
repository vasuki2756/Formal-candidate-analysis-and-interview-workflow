import { useMemo, useState } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8001/api/v1'

interface Analysis {
  candidate_skills: string[]
  required_skills: string[]
  matched_skills: string[]
  partial_skills: string[]
  missing_skills: string[]
  readiness_score: string
  top_gaps: string[]
  recommendations: string[]
}

interface Question {
  question: string
  type: string
  skill_related: string
}

interface Evaluation {
  score: string
  strengths: string[]
  weaknesses: string[]
  follow_up: string
  improvement: string
}

interface RAGStatus {
  has_data: boolean
  num_chunks: number
  chunks: string[]
  sample_embedding_size: number
}

function scoreToNumber(score: string): number {
  const parsed = Number.parseInt(score.replace(/[^0-9]/g, ''), 10)
  if (Number.isNaN(parsed)) {
    return 0
  }
  return Math.max(0, Math.min(parsed, 100))
}

function App() {
  const [activeTab, setActiveTab] = useState<'analyze' | 'results' | 'interview'>('analyze')
  const [resume, setResume] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [companyData, setCompanyData] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null)
  const [answer, setAnswer] = useState('')
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [ragStatus, setRagStatus] = useState<RAGStatus | null>(null)

  const readinessNumber = useMemo(() => scoreToNumber(analysis?.readiness_score ?? '0%'), [analysis])

  const analyzeWithText = async () => {
    if (!resume || !jobDescription) {
      setError('Please provide resume and job description')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await axios.post<Analysis>(`${API_URL}/analyze`, {
        resume,
        job_description: jobDescription,
        company_data: companyData
      })
      setAnalysis(res.data)
      setActiveTab('results')

      const ragRes = await axios.get<RAGStatus>(`${API_URL}/rag/status`)
      setRagStatus(ragRes.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    }

    setLoading(false)
  }

  const analyzeWithFile = async () => {
    if (!file || !jobDescription) {
      setError('Please upload a resume file and provide job description')
      return
    }

    setLoading(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('resume', file)
      formData.append('job_description', jobDescription)
      if (companyData) {
        formData.append('company_data', companyData)
      }

      const res = await axios.post<Analysis>(`${API_URL}/analyze/file`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setAnalysis(res.data)
      setActiveTab('results')

      const ragRes = await axios.get<RAGStatus>(`${API_URL}/rag/status`)
      setRagStatus(ragRes.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    }

    setLoading(false)
  }

  const generateQuestions = async () => {
    if (!analysis) {
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await axios.post<{ questions: Question[] }>(`${API_URL}/generate-questions`, {
        missing_skills: analysis.missing_skills,
        partial_skills: analysis.partial_skills,
        role: jobDescription,
        company_context: companyData
      })
      setQuestions(res.data.questions)
      setSelectedQuestion(null)
      setEvaluation(null)
      setAnswer('')
      setActiveTab('interview')
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    }

    setLoading(false)
  }

  const evaluateAnswer = async () => {
    if (!selectedQuestion || !answer) {
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await axios.post<Evaluation>(`${API_URL}/evaluate-answer`, {
        question: selectedQuestion.question,
        answer
      })
      setEvaluation(res.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    }

    setLoading(false)
  }

  return (
    <div className="app-shell">
      <div className="ambient ambient-a" aria-hidden="true" />
      <div className="ambient ambient-b" aria-hidden="true" />

      <header className="topbar">
        <div>
          <p className="eyebrow">AI Hiring Simulator</p>
          <h1>Formal candidate analysis and interview workflow</h1>
        </div>
      </header>

      <main className="layout-grid">
        <aside className="side-panel glass-panel animate-fade-up">
          <section className="intro-block">
            <p className="eyebrow">Workflow</p>
            <h2>Analyze, review, and simulate interviews in one sequence.</h2>
            <p>
              Structured interface with clear hierarchy and subtle motion to keep the experience professional.
            </p>
          </section>

          <nav className="stepper" aria-label="Workflow steps">
            <button className={`step ${activeTab === 'analyze' ? 'active' : ''}`} onClick={() => setActiveTab('analyze')}>1. Analyze</button>
            <button className={`step ${activeTab === 'results' ? 'active' : ''}`} onClick={() => analysis && setActiveTab('results')} disabled={!analysis}>2. Results</button>
            <button className={`step ${activeTab === 'interview' ? 'active' : ''}`} onClick={() => analysis && setActiveTab('interview')} disabled={!analysis}>3. Interview</button>
          </nav>

          <div className="stats-grid">
            <article className="metric-card">
              <p>Readiness</p>
              <strong>{analysis?.readiness_score ?? '0%'}</strong>
              <span>Latest assessment score</span>
            </article>
            <article className="metric-card">
              <p>Missing skills</p>
              <strong>{analysis?.missing_skills.length ?? 0}</strong>
              <span>Priority focus areas</span>
            </article>
          </div>

          <div className="notice-panel">
            <p className="eyebrow">Status</p>
            <strong>{error ? 'Action required' : loading ? 'Processing request' : 'Ready'}</strong>
            <p>{error || 'Submit resume and job details to start analysis.'}</p>
          </div>
        </aside>

        <section className="content-panel">
          <div className={`flow-indicator ${activeTab === 'analyze' ? 'progress-analyze' : activeTab === 'results' ? 'progress-results' : 'progress-interview'}`} />

          {loading ? <div className="loading-panel animate-fade-up">Processing request</div> : null}
          {error ? <div className="error animate-fade-up">{error}</div> : null}

          {activeTab === 'analyze' && !loading && (
            <div className="stage-card animate-fade-up">
              <div className="card-header">
                <div>
                  <p className="eyebrow">Stage 1</p>
                  <h2>Analyze resume against target role</h2>
                </div>
              </div>

              <div className="form-grid">
                <label className="field">
                  <span>Resume file (PDF, DOCX, TXT)</span>
                  <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                </label>

                <label className="field field-full">
                  <span>Job description</span>
                  <textarea value={jobDescription} onChange={(e) => setJobDescription(e.target.value)} placeholder="Add the target role description" />
                </label>

                <label className="field field-full">
                  <span>Company URL or context</span>
                  <textarea value={companyData} onChange={(e) => setCompanyData(e.target.value)} placeholder="Provide company URL or context" />
                </label>

                <label className="field field-full">
                  <span>Resume text (optional if file is uploaded)</span>
                  <textarea value={resume} onChange={(e) => setResume(e.target.value)} placeholder="Paste resume content" />
                </label>
              </div>

              <div className="action-row">
                <button className="secondary-button" onClick={analyzeWithFile}>Analyze with file</button>
                <button className="primary-button" onClick={analyzeWithText}>Analyze with text</button>
              </div>
            </div>
          )}

          {activeTab === 'results' && analysis && !loading && (
            <div className="results-grid animate-fade-up">
              <section className="stage-card hero-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Stage 2</p>
                    <h2>Analysis results</h2>
                  </div>
                </div>

                <div className="score-ring" style={{ ['--score' as never]: `${readinessNumber}%` }}>
                  <div>
                    <span>{analysis.readiness_score}</span>
                    <p>Readiness score</p>
                  </div>
                </div>

                <div className="tag-block">
                  <div>
                    <h3>Matched</h3>
                    <div className="tag-row">
                      {analysis.matched_skills.length ? analysis.matched_skills.map((skill) => <span className="skill-tag skill-tag-success" key={skill}>{skill}</span>) : <span className="muted-text">No matched skills</span>}
                    </div>
                  </div>
                  <div>
                    <h3>Partial</h3>
                    <div className="tag-row">
                      {analysis.partial_skills.length ? analysis.partial_skills.map((skill) => <span className="skill-tag skill-tag-warning" key={skill}>{skill}</span>) : <span className="muted-text">No partial skills</span>}
                    </div>
                  </div>
                  <div>
                    <h3>Missing</h3>
                    <div className="tag-row">
                      {analysis.missing_skills.length ? analysis.missing_skills.map((skill) => <span className="skill-tag skill-tag-danger" key={skill}>{skill}</span>) : <span className="muted-text">No missing skills</span>}
                    </div>
                  </div>
                </div>
              </section>

              <section className="stack-card">
                <article className="stage-card">
                  <div className="card-header">
                    <div>
                      <p className="eyebrow">RAG</p>
                      <h3>Stored context</h3>
                    </div>
                  </div>

                  {ragStatus ? (
                    <div className="rag-grid">
                      <article className="metric-card"><p>Chunks</p><strong>{ragStatus.num_chunks}</strong><span>Stored segments</span></article>
                      <article className="metric-card"><p>Embedding size</p><strong>{ragStatus.sample_embedding_size}</strong><span>Vector dimensions</span></article>
                      <div className="rag-sample">
                        <p>Sample chunk</p>
                        <strong>{ragStatus.chunks[0] ? ragStatus.chunks[0].slice(0, 180) : 'No chunk content available.'}</strong>
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state"><p>RAG status not available.</p></div>
                  )}
                </article>

                <article className="stage-card">
                  <div className="card-header">
                    <div>
                      <p className="eyebrow">Insights</p>
                      <h3>Top gaps and recommendations</h3>
                    </div>
                  </div>

                  <div className="list-columns">
                    <div>
                      <h4>Top gaps</h4>
                      <ol className="clean-list">
                        {analysis.top_gaps.length ? analysis.top_gaps.map((gap) => <li key={gap}>{gap}</li>) : <li>No top gaps provided</li>}
                      </ol>
                    </div>
                    <div>
                      <h4>Recommendations</h4>
                      <ul className="clean-list">
                        {analysis.recommendations.length ? analysis.recommendations.map((item) => <li key={item}>{item}</li>) : <li>No recommendations provided</li>}
                      </ul>
                    </div>
                  </div>
                </article>

                <div className="action-row action-row-space">
                  <button className="secondary-button" onClick={() => setActiveTab('analyze')}>Edit inputs</button>
                  <button className="primary-button" onClick={generateQuestions}>Generate interview questions</button>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'interview' && !loading && (
            <div className="interview-grid animate-fade-up">
              <section className="stage-card question-column">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Stage 3</p>
                    <h2>Interview questions</h2>
                  </div>
                </div>

                <div className="question-list">
                  {questions.length ? questions.map((item, index) => (
                    <button className={`question-card ${selectedQuestion?.question === item.question ? 'active' : ''}`} key={`${item.question}-${index}`} onClick={() => { setSelectedQuestion(item); setEvaluation(null); setAnswer('') }}>
                      <div className="question-card-head"><span className="badge badge-info">{item.type}</span><span>{item.skill_related}</span></div>
                      <p>{item.question}</p>
                    </button>
                  )) : (
                    <div className="empty-state"><p>No questions generated yet.</p></div>
                  )}
                </div>
              </section>

              <section className="stack-card">
                <article className="stage-card">
                  <div className="card-header">
                    <div>
                      <p className="eyebrow">Selected question</p>
                      <h3>{selectedQuestion?.skill_related ?? 'Question preview'}</h3>
                    </div>
                  </div>

                  <p className="question-preview">{selectedQuestion?.question ?? 'Select a question to evaluate.'}</p>

                  <label className="field">
                    <span>Candidate answer</span>
                    <textarea rows={9} value={answer} onChange={(e) => setAnswer(e.target.value)} placeholder="Type the candidate answer" />
                  </label>

                  <div className="action-row">
                    <button className="secondary-button" onClick={() => setActiveTab('results')}>Back to results</button>
                    <button className="primary-button" onClick={evaluateAnswer} disabled={!selectedQuestion || !answer.trim()}>Submit answer</button>
                  </div>
                </article>

                <article className="stage-card evaluation-card">
                  <div className="card-header">
                    <div>
                      <p className="eyebrow">Evaluation</p>
                      <h3>Answer review</h3>
                    </div>
                    <span className="badge badge-neutral">{evaluation?.score ?? 'Pending'}</span>
                  </div>

                  {evaluation ? (
                    <div className="evaluation-layout">
                      <div>
                        <h4>Strengths</h4>
                        <ul className="clean-list">{evaluation.strengths.length ? evaluation.strengths.map((item) => <li key={item}>{item}</li>) : <li>No strengths returned</li>}</ul>
                      </div>
                      <div>
                        <h4>Weaknesses</h4>
                        <ul className="clean-list">{evaluation.weaknesses.length ? evaluation.weaknesses.map((item) => <li key={item}>{item}</li>) : <li>No weaknesses returned</li>}</ul>
                      </div>
                      <div>
                        <h4>Follow-up</h4>
                        <p>{evaluation.follow_up || 'No follow-up question returned'}</p>
                      </div>
                      <div>
                        <h4>Improvement</h4>
                        <p>{evaluation.improvement || 'No improvement note returned'}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state"><p>Submit an answer to receive structured evaluation.</p></div>
                  )}
                </article>
              </section>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
