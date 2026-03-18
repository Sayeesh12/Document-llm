function StatusBadge({ status }) {
  const styles = {
    COMPLETED: 'bg-green-500/20 text-green-400 border-green-500/30',
    PROCESSING: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    PENDING: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    FAILED: 'bg-red-500/20 text-red-400 border-red-500/30',
  }

  const labels = {
    COMPLETED: 'Completed',
    PROCESSING: 'Processing',
    PENDING: 'Pending',
    FAILED: 'Failed',
  }

  return (
    <span className={`px-2 py-1 rounded text-xs border ${styles[status] || styles.PENDING}`}>
      {labels[status] || status}
    </span>
  )
}

export default StatusBadge
