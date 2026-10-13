import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@/api/health'

const REFETCH_MS = 5_000

export function BackendStatusPill() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => fetchHealth(signal),
    refetchInterval: REFETCH_MS,
    retry: 0,
  })

  if (isLoading) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
        <span className="h-1.5 w-1.5 rounded-full bg-slate-400" aria-hidden />
        Backend …
      </span>
    )
  }

  if (isError || !data) {
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
