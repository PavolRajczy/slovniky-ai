import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@/api/health'

const REFETCH_MS = 5_000
const SLOW_CHECK_MS = 3_000

export function BackendStatusPill() {
  const { data, isError, isLoading, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
    refetchInterval: REFETCH_MS,
    // A single missed check while the backend is busy should not show "down".
    retry: 1,
    retryDelay: 2_000,
  })
  const isSlow = useIsSlow(isFetching)

  if (isLoading && !isSlow) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-400" aria-hidden />
        Backend …
      </span>
    )
  }

  if (isError) {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-1 text-[11px] font-medium text-rose-900"
        title="Backend not reachable. Is the FastAPI server running at the configured base URL?"
      >
        <span className="h-1.5 w-1.5 rounded-full bg-rose-500" aria-hidden />
        Backend down
      </span>
    )
  }

  if (isSlow || !data) {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-900"
        title="The backend is responding slowly, usually while the AI prepares changes or Dataspecer is being updated."
      >
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" aria-hidden />
        Backend busy
      </span>
    )
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-medium text-emerald-900"
      title={`Backend OK · v${data.version}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden />
      Backend OK
    </span>
  )
}

function useIsSlow(isFetching: boolean): boolean {
  const [isSlow, setIsSlow] = useState(false)
  useEffect(() => {
    if (!isFetching) {
      setIsSlow(false)
      return
    }
    const timer = window.setTimeout(() => setIsSlow(true), SLOW_CHECK_MS)
    return () => window.clearTimeout(timer)
  }, [isFetching])
  return isSlow
}
