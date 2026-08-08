type NextActionBannerProps = {
  variant: 'iterations' | 'tasks' | 'operations'
  operationsHasRejected?: boolean
}

export function NextActionBanner({ variant, operationsHasRejected }: NextActionBannerProps) {
  let message: string
  switch (variant) {
    case 'iterations':
      message =
        'Set goal and subarea, then generate a new iteration from this scope; open tasks from a specific iteration card when you are ready.'
      break
    case 'tasks':
      message =
        "Run tasks as needed; open the change review from a task card to approve or reject that task's proposed changes only."
      break
    case 'operations':
      message = operationsHasRejected
        ? 'Rejected changes can be regenerated in place. Update guidance if needed, then approve remaining changes and export.'
        : 'Approve or reject each proposed change, then apply selected changes and continue to export.'
      break
    default:
      message = ''
  }

  return (
    <div className="rounded-lg border border-sky-200 bg-sky-50/90 px-3 py-2 text-sm text-sky-950">
      <span className="font-semibold text-sky-900">Next:</span> <span className="text-sky-950/95">{message}</span>
    </div>
  )
}
