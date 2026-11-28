import { Link } from '@tanstack/react-router'

type PageBackLinkProps = {
  to: string
  label: string
  search?: Record<string, unknown>
}

export function PageBackLink({ to, label, search }: PageBackLinkProps) {
  return (
    <Link
      to={to}
      search={search as never}
      className="inline-flex rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
    >
      Back to {label}
    </Link>
  )
}
