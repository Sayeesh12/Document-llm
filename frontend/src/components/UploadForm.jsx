import { useState, useRef } from 'react'
import { processDocument } from '../api'

function UploadForm({ onProcessed }) {
  const [file, setFile] = useState(null)
  const [documentType, setDocumentType] = useState('auto')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFile = (f) => {
    const validTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
    if (!validTypes.includes(f.type)) {
      setError('Please upload a PDF, PNG, or JPG file')
      return
    }
    if (f.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }
    setFile(f)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const result = await processDocument(file, documentType)
      onProcessed(result)
      setFile(null)
    } catch (err) {
      setError(err.message || 'Failed to process document')
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="bg-card-bg rounded-lg border border-slate-700 p-6">
      <h2 className="text-lg font-semibold text-white mb-4">Upload Document</h2>
      
      <form onSubmit={handleSubmit}>
        {/* Drop Zone */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            dragActive 
              ? 'border-blue-400 bg-blue-500/10' 
              : error 
              ? 'border-red-500 bg-red-500/10' 
              : 'border-slate-600 hover:border-slate-500'
          }`}
          onClick={() => inputRef.current?.click()}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          
          {file ? (
            <div className="text-slate-300">
              <svg className="w-10 h-10 mx-auto mb-2 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="font-medium">{file.name}</p>
              <p className="text-sm text-slate-400 mt-1">{formatFileSize(file.size)}</p>
            </div>
          ) : (
            <div className="text-slate-400">
              <svg className="w-10 h-10 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="font-medium">Drop invoice, bank statement, or KYC document</p>
              <p className="text-sm mt-1">PDF, PNG, JPG up to 10MB</p>
            </div>
          )}
        </div>

        {/* Document Type Selector */}
        <div className="mt-4">
          <label className="block text-sm text-slate-300 mb-2">Document Type</label>
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value)}
            className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-400"
          >
            <option value="auto">Auto-detect</option>
            <option value="INVOICE">Invoice</option>
            <option value="BANK_STATEMENT">Bank Statement</option>
            <option value="KYC_DOCUMENT">KYC Document</option>
          </select>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-500/20 border border-red-500/30 rounded text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!file || loading}
          className={`mt-4 w-full py-3 rounded font-medium transition-colors ${
            !file || loading
              ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Analyzing with Gemini AI...
            </span>
          ) : (
            '🔍 Analyze Document'
          )}
        </button>
      </form>
    </div>
  )
}

export default UploadForm
