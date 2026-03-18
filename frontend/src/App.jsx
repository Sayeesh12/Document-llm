import { useState, useEffect } from 'react'
import UploadForm from './components/UploadForm'
import ResultCard from './components/ResultCard'
import DocumentHistory from './components/DocumentHistory'
import { checkHealth, getDocuments } from './api'

function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [result, setResult] = useState(null)
  const [documents, setDocuments] = useState([])

  useEffect(() => {
    const checkApi = async () => {
      const healthy = await checkHealth()
      setApiStatus(healthy ? 'online' : 'offline')
    }
    checkApi()
    const interval = setInterval(checkApi, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    try {
      const data = await getDocuments(10)
      setDocuments(data.documents || [])
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const handleProcessed = (newResult) => {
    setResult(newResult)
    loadDocuments()
  }

  const handleSelectDocument = (doc) => {
    setResult(doc)
  }

  return (
    <div className="min-h-screen bg-dark-bg">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 bg-card-bg border-b border-slate-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔍</span>
            <span className="text-lg font-semibold text-white">Document Intelligence API</span>
          </div>
          <div className="text-sm text-slate-400 hidden sm:block">
            Gemini AI • FastAPI • GCP Ready
          </div>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-green-400' : apiStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-400'}`}></span>
            <span className="text-sm text-slate-300">
              {apiStatus === 'online' ? 'API Ready' : apiStatus === 'offline' ? 'API Offline' : 'Checking...'}
            </span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Upload Form - Left Column */}
          <div className="lg:col-span-2">
            <UploadForm onProcessed={handleProcessed} />
          </div>

          {/* Result Card - Right Column */}
          <div className="lg:col-span-3">
            {result ? (
              <ResultCard result={result} onReset={() => setResult(null)} />
            ) : (
              <div className="bg-card-bg rounded-lg border border-slate-700 p-8 h-full flex items-center justify-center">
                <div className="text-center text-slate-400">
                  <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-lg">Upload a document to see extracted data</p>
                  <p className="text-sm mt-2">Supports invoices, bank statements, and KYC documents</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Document History - Full Width */}
        <div className="mt-8">
          <DocumentHistory 
            documents={documents} 
            onSelect={handleSelectDocument}
            onRefresh={loadDocuments}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-slate-400 text-sm">
          Powered by Google Gemini 1.5 Flash • Built for financial document processing
        </div>
      </footer>
    </div>
  )
}

export default App
