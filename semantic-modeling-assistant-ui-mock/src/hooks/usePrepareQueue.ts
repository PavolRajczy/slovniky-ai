import { useCallback, useEffect, useRef, useState } from 'react'
import { prepareTask } from '@/api/tasks'

export type PrepareQueueEntry = {
  taskId: string
  taskName: string
  iterationId: string
}

export type PreparedTaskResult = PrepareQueueEntry & {
  operationsCount: number
}

type Options = {
  projectId: string | undefined
  onPrepared: (result: PreparedTaskResult) => void | Promise<void>
  onFailed: (entry: PrepareQueueEntry, error: unknown) => void | Promise<void>
}

/**
 * Prepares work items one after another. The backend locks the direction while one work item
 * is being prepared, so further clicks are queued instead of being sent in parallel.
 */
export function usePrepareQueue({ projectId, onPrepared, onFailed }: Options) {
  const [queue, setQueue] = useState<PrepareQueueEntry[]>([])
  const [running, setRunning] = useState<PrepareQueueEntry | null>(null)
  const runningRef = useRef(false)
  const callbacksRef = useRef({ onPrepared, onFailed })

  useEffect(() => {
    callbacksRef.current = { onPrepared, onFailed }
  }, [onPrepared, onFailed])

  useEffect(() => {
    if (!projectId || runningRef.current || queue.length === 0) return
    const [next, ...rest] = queue
    runningRef.current = true
    setRunning(next)
    setQueue(rest)
    prepareTask(projectId, next.iterationId, next.taskId)
      .then((data) => callbacksRef.current.onPrepared({ ...next, operationsCount: data.operations.length }))
      .catch((error: unknown) => callbacksRef.current.onFailed(next, error))
      .finally(() => {
        runningRef.current = false
        setRunning(null)
      })
  }, [projectId, queue, running])

  const enqueue = useCallback(
    (entries: PrepareQueueEntry[]) => {
      setQueue((current) => {
        const known = new Set([...current.map((e) => e.taskId), running?.taskId])
        return [...current, ...entries.filter((entry) => !known.has(entry.taskId))]
      })
    },
    [running],
  )

  const statusOf = useCallback(
    (taskId: string): 'preparing' | 'queued' | null => {
      if (running?.taskId === taskId) return 'preparing'
      if (queue.some((entry) => entry.taskId === taskId)) return 'queued'
      return null
    },
    [queue, running],
  )

  return {
    enqueue,
    statusOf,
    isBusy: running !== null || queue.length > 0,
    pendingCount: queue.length + (running ? 1 : 0),
  }
}
