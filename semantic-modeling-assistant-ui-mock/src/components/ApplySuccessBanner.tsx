import { Link } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { syncProjectToDataspecer } from '@/api/projects'
import { actionButton } from '@/components/ActionButtons'
import {
  clearApplySuccessFeedback,
  readApplySuccessFeedback,
  saveApplySuccessFeedback,
  type ApplySuccessFeedback,
} from '@/utils/applySuccessFeedback'
import { saveDataspecerSyncFeedback } from '@/utils/dataspecerSyncFeedback'
import { dataspecerEditorUrl } from '@/utils/dataspecerLinks'

type ApplySuccessBannerProps = {
  projectId: string
  dataspecerPackageIri: string | null | undefined
}

/** Explicit confirmation shown after kept changes were applied, with links to the result. */
export function ApplySuccessBanner({ projectId, dataspecerPackageIri }: ApplySuccessBannerProps) {
  const queryClient = useQueryClient()
  const [feedback, setFeedback] = useState<ApplySuccessFeedback | null>(null)

  useEffect(() => {
    setFeedback(readApplySuccessFeedback(projectId))
  }, [projectId])

  const retrySync = useMutation({
    mutationFn: () => syncProjectToDataspecer(projectId),
    onSettled: (_data, error) => {
      if (!feedback) return
      const next: ApplySuccessFeedback = {
        ...feedback,
        dataspecerSynced: !error,
        dataspecerError: error ? toErrorMessage(error) : null,
      }
      saveApplySuccessFeedback(next)
      saveDataspecerSyncFeedback({
        projectId,
        synced: !error,
        error: next.dataspecerError,
        at: new Date().toISOString(),
      })
      setFeedback(next)
      void queryClient.invalidateQueries({ queryKey: ['project-activity', projectId] })
    },
  })

  if (!feedback) return null

  const syncFailed = feedback.dataspecerSynced === false
  const dismiss = () => {
    clearApplySuccessFeedback()
    setFeedback(null)
  }

  return (
    <section
      role="status"
      className={`rounded-2xl border p-4 text-sm shadow-sm ${
        syncFailed ? 'border-rose-200 bg-rose-50/80 text-rose-950' : 'border-emerald-300 bg-emerald-50 text-emerald-950'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-base font-semibold">
            {feedback.appliedCount} change{feedback.appliedCount === 1 ? '' : 's'} applied to the vocabulary
            {feedback.taskName ? <span className="font-normal"> · {feedback.taskName}</span> : null}
          </p>
          <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {feedback.dataspecerSynced === null ? null : (
              <li className={syncFailed ? 'font-semibold text-rose-800' : ''}>
                {syncFailed ? 'Dataspecer vocabulary was NOT updated' : 'Dataspecer vocabulary updated'}
              </li>
            )}
            {feedback.ofnSaved ? <li>OFN export updated</li> : null}
            {feedback.rejectedCount > 0 ? (
              <li>
                {feedback.rejectedCount} rejected change{feedback.rejectedCount === 1 ? '' : 's'} left out
              </li>
            ) : null}
          </ul>
          {syncFailed && feedback.dataspecerError ? (
            <p className="mt-2 break-words font-mono text-[11px] opacity-80">{feedback.dataspecerError}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          {syncFailed ? (
            <button
              type="button"
              onClick={() => retrySync.mutate()}
              disabled={retrySync.isPending}
              className={actionButton.primarySm}
            >
              {retrySync.isPending ? 'Syncing…' : 'Retry Dataspecer sync'}
            </button>
          ) : null}
          <Link
            to="/export-result"
            search={{
              projectId,
              domainId: undefined,
              iterationId: undefined,
              taskId: undefined,
              approved: undefined,
              pending: undefined,
              rejected: undefined,
              regenerated: undefined,
              guidanceUpdated: undefined,
            }}
            className={actionButton.primarySm}
          >
            View result
          </Link>
          {dataspecerPackageIri ? (
            <a
              href={dataspecerEditorUrl(dataspecerPackageIri)}
              target="_blank"
              rel="noreferrer"
              className={actionButton.secondarySm}
            >
              Open in Dataspecer
            </a>
          ) : null}
          <button type="button" onClick={dismiss} className={actionButton.secondarySm}>
            Dismiss
          </button>
        </div>
      </div>
    </section>
  )
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Dataspecer sync failed.'
}
