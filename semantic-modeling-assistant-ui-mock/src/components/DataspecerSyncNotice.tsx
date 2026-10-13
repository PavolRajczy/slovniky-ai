import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { syncProjectToDataspecer } from '@/api/projects'
import { actionButton } from '@/components/ActionButtons'
import {
  readDataspecerSyncFeedback,
  saveDataspecerSyncFeedback,
  type DataspecerSyncFeedback,
} from '@/utils/dataspecerSyncFeedback'

type DataspecerSyncNoticeProps = {
  projectId: string
  /** Whether the project is linked to a Dataspecer vocabulary. Unlinked projects render nothing. */
  linked: boolean
  /** Render even before any finalize has reported a sync result. */
  showWithoutFeedback?: boolean
}

export function DataspecerSyncNotice({ projectId, linked, showWithoutFeedback = false }: DataspecerSyncNoticeProps) {
  const queryClient = useQueryClient()
  const [feedback, setFeedback] = useState<DataspecerSyncFeedback | null>(null)

  useEffect(() => {
    setFeedback(readDataspecerSyncFeedback(projectId))
  }, [projectId])

  const record = (next: DataspecerSyncFeedback) => {
    saveDataspecerSyncFeedback(next)
    setFeedback(next)
    void queryClient.invalidateQueries({ queryKey: ['project-activity', projectId] })
  }

  const syncMutation = useMutation({
    mutationFn: () => syncProjectToDataspecer(projectId),
    onSuccess: () => record({ projectId, synced: true, error: null, at: new Date().toISOString() }),
    onError: (error: unknown) =>
      record({ projectId, synced: false, error: toErrorMessage(error), at: new Date().toISOString() }),
  })

  if (!linked || (!feedback && !showWithoutFeedback)) {
    return null
  }

  const failed = feedback ? !feedback.synced : false
  const tone = failed
    ? 'border-rose-200 bg-rose-50/80 text-rose-950'
    : 'border-emerald-200 bg-emerald-50/70 text-emerald-950'

  return (
    <section className={`rounded-2xl border p-4 text-sm shadow-sm ${tone}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-80">Dataspecer sync</p>
          <p className="mt-1">{describe(feedback, syncMutation.isPending)}</p>
          {failed && feedback?.error ? (
            <p className="mt-1 break-words font-mono text-[11px] opacity-80">{feedback.error}</p>
          ) : null}
          {feedback ? (
            <p className="mt-1 text-[11px] opacity-70">Last attempt: {new Date(feedback.at).toLocaleString()}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          className={failed ? actionButton.primarySm : actionButton.secondarySm}
        >
          {syncMutation.isPending ? 'Syncing…' : failed ? 'Retry sync' : 'Sync again'}
        </button>
      </div>
    </section>
  )
}

function describe(feedback: DataspecerSyncFeedback | null, pending: boolean): string {
  if (pending) return 'Sending the current ontology to Dataspecer…'
  if (!feedback) return 'Each finalize updates the linked Dataspecer vocabulary with the current ontology.'
  if (feedback.synced) return 'The linked Dataspecer vocabulary is up to date with the current ontology.'
  return 'The ontology changes were saved, but the linked Dataspecer vocabulary could not be updated.'
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Dataspecer sync failed.'
}
