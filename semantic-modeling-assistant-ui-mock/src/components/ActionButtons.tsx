import type { ReactNode } from 'react'

/** Shared card/list action buttons: primary (emerald) → secondary (slate) → danger (rose). */
export const actionButton = {
  primary:
    'inline-flex items-center justify-center whitespace-nowrap rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-60',
  primarySm:
    'inline-flex items-center justify-center whitespace-nowrap rounded-md bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-60',
  secondary:
    'inline-flex items-center justify-center whitespace-nowrap rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60',
  secondarySm:
    'inline-flex items-center justify-center whitespace-nowrap rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60',
  danger:
    'inline-flex items-center justify-center whitespace-nowrap rounded-md border border-rose-200 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-60',
  dangerSm:
    'inline-flex items-center justify-center whitespace-nowrap rounded-md border border-rose-200 bg-white px-2.5 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-60',
} as const

type CardActionsProps = {
  children: ReactNode
  className?: string
}

export function CardActions({ children, className }: CardActionsProps) {
  return <div className={className ? `flex flex-wrap gap-2 ${className}` : 'flex flex-wrap gap-2'}>{children}</div>
}

type TableActionsProps = {
  children: ReactNode
}

/** Vertical action stack for narrow table cells — keeps buttons the same width. */
export function TableActions({ children }: TableActionsProps) {
  return <div className="ml-auto flex w-28 flex-col gap-1.5">{children}</div>
}
