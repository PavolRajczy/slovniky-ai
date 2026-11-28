import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getDocumentProcessingJob } from '@/api/knowledgeBase'
import type { DocumentProcessingJob } from '@/api/types'

const POLL_INTERVAL_MS = 1000

export function isDocumentProcessingFinished(job: DocumentProcessingJob | undefined): boolean {
  return job?.stage === 'completed' || job?.stage === 'failed'
}

/**
 * Tracks one document processing job: polls it every second until it completes or fails
 * and calls onCompleted once when it completes.
 */
export function useTrackedDocumentProcessingJob(
  projectId: string,
  onCompleted: () => void | Promise<void>,
) {
  const [startedJob, setStartedJob] = useState<DocumentProcessingJob | null>(null)
  const handledJobIdRef = useRef<string | null>(null)

  const jobQuery = useQuery({
    queryKey: ['document-processing-job', projectId, startedJob?.id],
    queryFn: ({ signal }) => getDocumentProcessingJob(projectId, startedJob!.id, signal),
    enabled: startedJob !== null,
    retry: 1,
    refetchInterval: (query) =>
      query.state.status === 'error' || isDocumentProcessingFinished(query.state.data)
        ? false
        : POLL_INTERVAL_MS,
  })

  const job = startedJob ? (jobQuery.data ?? startedJob) : null

  useEffect(() => {
    if (job?.stage !== 'completed' || handledJobIdRef.current === job.id) return
    handledJobIdRef.current = job.id
    void onCompleted()
  }, [job, onCompleted])

  return {
    job,
    pollError: startedJob ? jobQuery.error : null,
    isRunning: job !== null && !isDocumentProcessingFinished(job) && !jobQuery.isError,
    track: setStartedJob,
    dismiss: () => setStartedJob(null),
  }
}
