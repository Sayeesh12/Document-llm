import ConfidenceBar from './ConfidenceBar'
import StatusBadge from './StatusBadge'

function DocumentHistory({ documents, onSelect, onRefresh }) {
  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now - date) / 1000)
    
    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  const getDocTypeBadge = (type) => {
    const badges = {
      'INVOICE': 'bg-purple-500/20 text-purple-400',
      'BANK_STATEMENT': 'bg-blue-500/20 text-blue-400',
      'KYC_DOCUMENT': 'bg-orange-500/20 text-orange-400'
    }
    return badges[type] || 'bg-slate-500/20 text-slate-400'
  }

  if (documents.length === 0) {
    return (
      <div className="bg-card-bg rounded-lg border border-slate-700 p-8">
        <div className="text-center text-slate-400">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <p>No documents processed yet</p>
          <p className="text-sm mt-1">Upload a document to get started</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card-bg rounded-lg border border-slate-700">
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
        <h3 className="text-white font-medium">Recent Documents</h3>
        <button
          onClick={onRefresh}
          className="text-slate-400 hover:text-white transition-colors"
          title="Refresh"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>
      <div className="divide-y divide-slate-700/50">
        {documents.map((doc) => (
          <div
            key={doc.document_id}
            onClick={() => onSelect(doc)}
            className="px-6 py-4 hover:bg-slate-800/50 cursor-pointer transition-colors"
          >
            <div className="flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-white font-medium truncate">{doc.filename}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${getDocTypeBadge(doc.document_type)}`}>
                    {doc.document_type?.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div className="w-32">
                    <ConfidenceBar score={doc.confidence_score} size="sm" />
                  </div>
                  <span className="text-slate-400">{formatTimeAgo(doc.created_at)}</span>
                </div>
              </div>
              <StatusBadge status={doc.status} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default DocumentHistory
