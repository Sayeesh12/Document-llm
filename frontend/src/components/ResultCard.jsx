import ConfidenceBar from './ConfidenceBar'
import StatusBadge from './StatusBadge'

function ResultCard({ result, onReset }) {
  const getDocTypeBadge = (type) => {
    const badges = {
      'INVOICE': { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/30' },
      'BANK_STATEMENT': { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' },
      'KYC_DOCUMENT': { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' }
    }
    const style = badges[type] || badges['INVOICE']
    return `${style.bg} ${style.text} ${style.border}`
  }

  const formatCurrency = (amount, currency) => {
    if (amount == null) return null
    const symbols = { 'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£' }
    const symbol = symbols[currency] || currency || ''
    return `${symbol}${amount.toLocaleString()}`
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(result.extracted_data, null, 2))
  }

  const renderValue = (value, key) => {
    if (value === null || value === undefined) {
      return <span className="text-slate-500 italic">Not found</span>
    }
    if (key.includes('number') && typeof value === 'string' && value.includes('XXXX')) {
      return <span className="flex items-center gap-1">🔒 {value}</span>
    }
    if (typeof value === 'number') {
      return value.toLocaleString()
    }
    return String(value)
  }

  const renderExtractedData = () => {
    const data = result.extracted_data
    const entries = Object.entries(data).filter(([key]) => 
      !['line_items', 'transactions'].includes(key)
    )

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {entries.map(([key, value]) => (
          <div key={key} className="bg-slate-800/50 rounded p-3">
            <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">
              {key.replace(/_/g, ' ')}
            </div>
            <div className="text-white">
              {renderValue(value, key)}
            </div>
          </div>
        ))}
      </div>
    )
  }

  const renderLineItems = () => {
    const items = result.extracted_data.line_items
    if (!items || items.length === 0) return null

    return (
      <div className="mt-4">
        <h4 className="text-sm text-slate-400 uppercase tracking-wide mb-2">Line Items</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="py-2 pr-4">Description</th>
                <th className="py-2 pr-4">Qty</th>
                <th className="py-2 pr-4">Unit Price</th>
                <th className="py-2">Total</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => (
                <tr key={idx} className="border-b border-slate-700/50">
                  <td className="py-2 pr-4 text-white">{item.description || '-'}</td>
                  <td className="py-2 pr-4 text-slate-300">{item.quantity || '-'}</td>
                  <td className="py-2 pr-4 text-slate-300">{item.unit_price || '-'}</td>
                  <td className="py-2 text-white">{item.total || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const renderTransactions = () => {
    const txns = result.extracted_data.transactions
    if (!txns || txns.length === 0) return null

    return (
      <div className="mt-4">
        <h4 className="text-sm text-slate-400 uppercase tracking-wide mb-2">
          Transactions ({txns.length})
        </h4>
        <div className="overflow-x-auto max-h-64 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-card-bg">
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Description</th>
                <th className="py-2 pr-4 text-right text-green-400">Credit</th>
                <th className="py-2 pr-4 text-right text-red-400">Debit</th>
                <th className="py-2 text-right">Balance</th>
              </tr>
            </thead>
            <tbody>
              {txns.map((txn, idx) => (
                <tr key={idx} className="border-b border-slate-700/50">
                  <td className="py-2 pr-4 text-slate-300">{txn.date || '-'}</td>
                  <td className="py-2 pr-4 text-white">{txn.description || '-'}</td>
                  <td className="py-2 pr-4 text-right text-green-400">{txn.credit || '-'}</td>
                  <td className="py-2 pr-4 text-right text-red-400">{txn.debit || '-'}</td>
                  <td className="py-2 text-right text-white">{txn.balance || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card-bg rounded-lg border border-slate-700 p-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getDocTypeBadge(result.document_type)}`}>
          {result.document_type?.replace(/_/g, ' ')}
        </span>
        <StatusBadge status={result.status} />
        <span className="text-sm text-slate-400">
          {result.processing_time_ms}ms
        </span>
        <span className="text-sm text-slate-400">
          {result.page_count} page{result.page_count !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Confidence */}
      <div className="mb-6">
        <div className="text-sm text-slate-400 mb-2">Confidence Score</div>
        <ConfidenceBar score={result.confidence_score} size="lg" />
      </div>

      {/* Error Message */}
      {result.error_message && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded text-red-400">
          {result.error_message}
        </div>
      )}

      {/* Extracted Data */}
      {Object.keys(result.extracted_data).length > 0 && (
        <>
          <h3 className="text-white font-medium mb-3">Extracted Data</h3>
          {renderExtractedData()}
          {renderLineItems()}
          {renderTransactions()}
        </>
      )}

      {/* Actions */}
      <div className="mt-6 flex gap-3">
        <button
          onClick={copyToClipboard}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-white text-sm transition-colors"
        >
          Copy JSON
        </button>
        <button
          onClick={onReset}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded text-white text-sm transition-colors"
        >
          Process Another
        </button>
      </div>
    </div>
  )
}

export default ResultCard
