function ConfidenceBar({ score, size = 'md' }) {
  const getColor = (score) => {
    if (score >= 0.8) return 'bg-green-400'
    if (score >= 0.6) return 'bg-yellow-400'
    return 'bg-red-500'
  }

  const getTextColor = (score) => {
    if (score >= 0.8) return 'text-green-400'
    if (score >= 0.6) return 'text-yellow-400'
    return 'text-red-500'
  }

  const percentage = Math.round(score * 100)
  const heightClass = size === 'sm' ? 'h-1.5' : 'h-2'
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-slate-700 rounded-full overflow-hidden" style={{ height: size === 'sm' ? '6px' : '8px' }}>
        <div
          className={`${getColor(score)} h-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={`${textSize} ${getTextColor(score)} font-medium min-w-[3rem] text-right`}>
        {percentage}%
      </span>
    </div>
  )
}

export default ConfidenceBar
