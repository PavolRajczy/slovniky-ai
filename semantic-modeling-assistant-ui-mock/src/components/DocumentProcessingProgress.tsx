import type { DocumentProcessingJob, DocumentProcessingStage } from '@/api/types'

type WorkStage = Extract<DocumentProcessingStage, 'loading' | 'summarizing' | 'indexing' | 'saving'>

type StepDefinition = {
  stage: WorkStage
  label: string
  /** Share of the overall bar where this step starts and ends, in percent. */
  from: number
  to: number
}

const STEPS: StepDefinition[] = [
  { stage: 'loading', label: 'Load', from: 0, to: 15 },
  { stage: 'summarizing', label: 'Summarize sections', from: 15, to: 80 },
  { stage: 'indexing', label: 'Index for search', from: 80, to: 97 },
  { stage: 'saving', label: 'Save', from: 97, to: 100 },
]

type StepState = 'done' | 'current' | 'failed' | 'pending'

type Props = {
  job: DocumentProcessingJob
  /** Shown as a close link once the job has completed or failed. */
  onDismiss?: () => void
}

export function DocumentProcessingProgress({ job, onDismiss }: Props) {
  const currentIndex = currentStepIndex(job)
  const percent = overallPercent(job, currentIndex)
  const isFailed = job.stage === 'failed'
  const isFinished = isFailed || job.stage === 'completed'
  const isIndeterminate = !isFinished && job.total === null

  return (
    <div
      className={`space-y-2 rounded-lg border p-3 ${
        isFailed ? 'border-rose-200 bg-rose-50/60' : 'border-emerald-200 bg-emerald-50/40'
      }`}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="min-w-0 truncate font-medium text-slate-800" title={job.document_label}>
          {headline(job)}
        </span>
        <span className="shrink-0 font-semibold tabular-nums text-slate-700">{percent} %</span>
      </div>

      <div
        className="h-2 overflow-hidden rounded-full bg-white ring-1 ring-inset ring-slate-200"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-label="Document processing progress"
      >
        <div
          className={`h-full rounded-full transition-[width] duration-700 ease-out ${
            isFailed ? 'bg-rose-500' : 'bg-emerald-500'
          } ${isIndeterminate ? 'animate-pulse' : ''}`}
          style={{ width: `${Math.max(percent, 2)}%` }}
        />
      </div>

      <ol className="grid grid-cols-4 gap-1">
        {STEPS.map((step, index) => (
          <StepItem key={step.stage} label={step.label} state={stepState(job, index, currentIndex)} />
        ))}
      </ol>

      <div className="flex items-start justify-between gap-2">
        <p className={`text-[11px] ${isFailed ? 'text-rose-800' : 'text-slate-600'}`}>{detail(job)}</p>
        {isFinished && onDismiss ? (
          <button
            type="button"
            onClick={onDismiss}
            className="shrink-0 text-[11px] font-medium text-slate-500 hover:text-slate-800 hover:underline"
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </div>
  )
}

function StepItem({ label, state }: { label: string; state: StepState }) {
  const marker = {
    done: 'bg-emerald-500 text-white',
    current: 'bg-white text-emerald-700 ring-2 ring-emerald-500',
    failed: 'bg-rose-500 text-white',
    pending: 'bg-white text-slate-400 ring-1 ring-slate-300',
  }[state]
  const symbol = { done: '✓', current: '•', failed: '✕', pending: '' }[state]
  return (
    <li className="flex items-center gap-1.5 text-[11px]">
      <span
        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px] font-bold ${marker}`}
        aria-hidden="true"
      >
        {symbol}
      </span>
      <span className={state === 'pending' ? 'text-slate-400' : 'font-medium text-slate-700'}>
        {label}
      </span>
    </li>
  )
}

function activeStage(job: DocumentProcessingJob): DocumentProcessingStage {
  return job.stage === 'failed' ? (job.failed_stage ?? 'queued') : job.stage
}

function currentStepIndex(job: DocumentProcessingJob): number {
  if (job.stage === 'completed') return STEPS.length
  const stage = activeStage(job)
  const index = STEPS.findIndex((step) => step.stage === stage)
  return index === -1 ? 0 : index
}

function stepState(job: DocumentProcessingJob, index: number, currentIndex: number): StepState {
  if (index < currentIndex) return 'done'
  if (index > currentIndex) return 'pending'
  return job.stage === 'failed' ? 'failed' : 'current'
}

function overallPercent(job: DocumentProcessingJob, currentIndex: number): number {
  if (job.stage === 'completed') return 100
  const step = STEPS[currentIndex]
  if (!step || activeStage(job) === 'queued') return 0
  const fraction = job.total ? job.completed / job.total : 0
  return Math.round(step.from + (step.to - step.from) * fraction)
}

function headline(job: DocumentProcessingJob): string {
  if (job.stage === 'completed') return `Done: ${job.document_label}`
  if (job.stage === 'failed') return `Failed: ${job.document_label}`
  return `Processing ${job.document_label}`
}

function detail(job: DocumentProcessingJob): string {
  switch (job.stage) {
    case 'queued':
      return 'Waiting to start…'
    case 'loading':
      return job.document_kind === 'legal'
        ? 'Downloading the act from e-Sbírka…'
        : 'Reading the file and detecting its sections…'
    case 'summarizing':
      return job.total === null
        ? 'Summarizing sections…'
        : `Summarizing sections: ${job.completed} of ${job.total} done`
    case 'indexing':
      return job.total === null
        ? 'Preparing the search index…'
        : `Creating search embeddings: batch ${job.completed} of ${job.total}`
    case 'saving':
      return 'Saving the project…'
    case 'completed':
      return job.message ?? 'The document is ready.'
    case 'failed':
      return job.error ?? 'Processing failed.'
  }
}
