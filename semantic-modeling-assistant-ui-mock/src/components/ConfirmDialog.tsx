import type { ReactNode } from 'react'

type ConfirmDialogProps = {
  title: string
  description?: string
  detail?: ReactNode
  headerLabel?: string
  confirmLabel?: string
  confirmPendingLabel?: string
  cancelLabel?: string
  tone?: 'danger' | 'default' | 'primary'
  isConfirmPending?: boolean
  onConfirm: () => void | Promise<void>
  onCancel: () => void
}

const toneStyles = {
  danger: {
    header: 'Confirm deletion',
    confirmButton: 'bg-rose-700 hover:bg-rose-800',
    pendingLabel: 'Deleting…',
  },
  default: {
    header: 'Confirm action',
    confirmButton: 'bg-slate-900 hover:bg-slate-800',
    pendingLabel: 'Confirming…',
  },
  primary: {
    header: 'Confirm finalization',
    confirmButton: 'bg-emerald-600 hover:bg-emerald-700',
    pendingLabel: 'Finalizing…',
  },
} as const

export function ConfirmDialog({
  title,
  description,
  detail,
  headerLabel,
  confirmLabel = 'Confirm',
  confirmPendingLabel,
  cancelLabel = 'Cancel',
  tone = 'danger',
  isConfirmPending = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const toneStyle = toneStyles[tone]
  const resolvedHeader = headerLabel ?? toneStyle.header
  const resolvedPendingLabel = confirmPendingLabel ?? toneStyle.pendingLabel

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40"
        aria-label="Close confirmation dialog"
        onClick={onCancel}
        disabled={isConfirmPending}
      />
      <div className="relative z-10 m-4 w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
        <div>
          <p
            className={`text-xs font-semibold uppercase tracking-wide ${
              tone === 'danger'
                ? 'text-rose-700'
                : tone === 'primary'
                  ? 'text-emerald-800'
                  : 'text-slate-600'
            }`}
          >
            {resolvedHeader}
          </p>
          <p id="confirm-dialog-title" className="mt-2 text-sm font-medium text-slate-900">
            {title}
          </p>
          {description ? (
            <p className="mt-2 text-xs leading-5 text-slate-600">{description}</p>
          ) : null}
          {detail ? <div className="mt-2">{detail}</div> : null}
        </div>

        <div className="mt-5 flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            onClick={onCancel}
            disabled={isConfirmPending}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className={`rounded-lg px-3 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60 ${toneStyle.confirmButton}`}
            onClick={() => void onConfirm()}
            disabled={isConfirmPending}
          >
            {isConfirmPending ? resolvedPendingLabel : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
