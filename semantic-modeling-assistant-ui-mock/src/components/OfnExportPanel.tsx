import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import {
  getProjectOfn,
  regenerateProjectOfn,
  type ProjectOfnDocument,
} from '@/api/projects'
import type { OfnDocument, OfnPojem } from '@/api/types'
import {
  clearOfnSaveFeedback,
  readOfnSaveFeedback,
  type OfnSaveFeedback,
} from '@/utils/ofnSaveFeedback'

type PojemKind = 'all' | 'Třída' | 'Vztah' | 'Vlastnost'

const KIND_FILTERS: { id: PojemKind; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'Třída', label: 'Classes' },
  { id: 'Vztah', label: 'Relations' },
  { id: 'Vlastnost', label: 'Properties' },
]

function textCs(value?: { cs?: string; en?: string } | null): string {
  if (!value) return ''
  return value.cs || value.en || ''
}

function shortIri(iri: string): string {
  if (!iri) return ''
  const parts = iri.split('/')
  return parts[parts.length - 1] || iri
}

function primaryKind(pojem: OfnPojem): 'Třída' | 'Vztah' | 'Vlastnost' | 'Pojem' {
  if (pojem.typ.includes('Třída')) return 'Třída'
  if (pojem.typ.includes('Vztah')) return 'Vztah'
  if (pojem.typ.includes('Vlastnost')) return 'Vlastnost'
  return 'Pojem'
}

function kindBadgeClass(kind: string): string {
  switch (kind) {
    case 'Třída':
      return 'bg-sky-100 text-sky-900'
    case 'Vztah':
      return 'bg-violet-100 text-violet-900'
    case 'Vlastnost':
      return 'bg-amber-100 text-amber-900'
    case 'Typ subjektu práva':
      return 'bg-emerald-100 text-emerald-900'
    case 'Typ objektu práva':
      return 'bg-teal-100 text-teal-900'
    default:
      return 'bg-slate-100 text-slate-700'
  }
}

function stripMeta(document: ProjectOfnDocument): OfnDocument {
  const { _meta: _ignored, ...rest } = document
  return rest as OfnDocument
}

type OfnExportPanelProps = {
  projectId?: string | null
  projectName?: string
}

export function OfnExportPanel({ projectId, projectName }: OfnExportPanelProps) {
  const queryClient = useQueryClient()
  const [filter, setFilter] = useState<PojemKind>('all')
  const [query, setQuery] = useState('')
  const [selectedIri, setSelectedIri] = useState<string | null>(null)
  const [showRaw, setShowRaw] = useState(false)
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')
  const [saveFeedback, setSaveFeedback] = useState<OfnSaveFeedback | null>(null)

  useEffect(() => {
    if (!projectId) {
      setSaveFeedback(null)
      return
    }
    setSaveFeedback(readOfnSaveFeedback(projectId))
  }, [projectId])

  const ofnQuery = useQuery({
    queryKey: ['project-ofn', projectId],
    queryFn: ({ signal }) => getProjectOfn(projectId!, signal),
    enabled: Boolean(projectId),
    retry: false,
  })

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateProjectOfn(projectId!),
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ['project-ofn', projectId] })
      if (projectId) {
        const feedback: OfnSaveFeedback = {
          projectId,
          path: result.ofn_path,
          absolutePath: result.ofn_absolute_path,
          pojmyCount: result.ofn_pojmy_count,
          overwroteExisting: result.ofn_overwrote_existing,
          savedAt: new Date().toISOString(),
        }
        setSaveFeedback(feedback)
      }
    },
  })

  const storedDocument = ofnQuery.data
  const document = storedDocument ? stripMeta(storedDocument) : undefined
  const pojmy = document?.pojmy ?? []
  const missingOfn = ofnQuery.isError && (ofnQuery.error as ApiError)?.status === 404

  const counts = useMemo(() => {
    return {
      total: pojmy.length,
      classes: pojmy.filter((p) => p.typ.includes('Třída')).length,
      relations: pojmy.filter((p) => p.typ.includes('Vztah')).length,
      properties: pojmy.filter((p) => p.typ.includes('Vlastnost')).length,
    }
  }, [pojmy])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return pojmy.filter((pojem) => {
      if (filter !== 'all' && !pojem.typ.includes(filter)) return false
      if (!q) return true
      const haystack = [
        textCs(pojem.název),
        textCs(pojem.definice),
        textCs(pojem.popis),
        pojem.iri,
        ...(pojem.typ ?? []),
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [pojmy, filter, query])

  useEffect(() => {
    if (filtered.length === 0) {
      setSelectedIri(null)
      return
    }
    if (!selectedIri || !filtered.some((p) => p.iri === selectedIri)) {
      setSelectedIri(filtered[0].iri)
    }
  }, [filtered, selectedIri])

  const selected = filtered.find((p) => p.iri === selectedIri) ?? null

  const jsonText = useMemo(
    () => (document ? JSON.stringify(document, null, 2) : ''),
    [document],
  )

  const downloadJson = () => {
    if (!jsonText) return
    const blob = new Blob([jsonText], { type: 'application/ld+json;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const anchor = window.document.createElement('a')
    const slug = shortIri(document?.iri || 'slovnik') || 'ofn-slovnik'
    anchor.href = url
    anchor.download = `${slug}.ofn.json`
    anchor.click()
    URL.revokeObjectURL(url)
  }

  const copyJson = async () => {
    if (!jsonText) return
    try {
      await navigator.clipboard.writeText(jsonText)
      setCopyState('copied')
      window.setTimeout(() => setCopyState('idle'), 1800)
    } catch {
      setCopyState('failed')
      window.setTimeout(() => setCopyState('idle'), 1800)
    }
  }

  const loadError =
    ofnQuery.error instanceof ApiError && ofnQuery.error.status !== 404
      ? ofnQuery.error.message
      : ofnQuery.error instanceof Error && !missingOfn
        ? ofnQuery.error.message
        : null

  const regenerateError =
    regenerateMutation.error instanceof ApiError
      ? regenerateMutation.error.message
      : regenerateMutation.error instanceof Error
        ? regenerateMutation.error.message
        : regenerateMutation.isError
          ? 'Failed to regenerate OFN.'
          : null

  const storageHint = projectId
    ? `semantic-modeling-assistant-agentic-backend/data/projects/${projectId}/ofn.json`
    : null

  return (
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-sky-50/60 px-6 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">
              OFN Slovníky · project file
            </p>
            <h3 className="mt-1 text-xl font-semibold tracking-tight text-slate-900">
              {document ? textCs(document.název) || 'Project OFN' : 'Project OFN'}
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-slate-600">
              Finalize writes approved changes into the ontology and regenerates this OFN file
              (overwrite). Path is fixed per project for now.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => projectId && regenerateMutation.mutate()}
              disabled={!projectId || regenerateMutation.isPending}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            >
              {regenerateMutation.isPending ? 'Saving…' : document ? 'Regenerate & overwrite' : 'Generate OFN'}
            </button>
            <button
              type="button"
              onClick={() => void copyJson()}
              disabled={!jsonText}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            >
              {copyState === 'copied' ? 'Copied' : copyState === 'failed' ? 'Copy failed' : 'Copy JSON'}
            </button>
            <button
              type="button"
              onClick={downloadJson}
              disabled={!jsonText}
              className="rounded-lg bg-sky-700 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-800 disabled:opacity-60"
            >
              Download copy
            </button>
          </div>
        </div>

        {storageHint ? (
          <div className="mt-4 rounded-xl border border-sky-200 bg-white/80 px-3 py-2 text-xs text-sky-950">
            <p className="font-semibold uppercase tracking-wide text-sky-800">Saved location</p>
            <p className="mt-1 break-all font-mono text-[11px]">{storageHint}</p>
            {storedDocument?._meta?.saved_at ? (
              <p className="mt-1 text-sky-900/80">
                Last saved: {storedDocument._meta.saved_at}
                {storedDocument._meta.overwrote_existing ? ' · overwritten' : ' · created'}
              </p>
            ) : null}
            {saveFeedback ? (
              <p className="mt-1 text-sky-900/80">
                Latest finalize wrote {saveFeedback.pojmyCount} concepts
                {saveFeedback.overwroteExisting ? ' (overwrite)' : ''}.
                <button
                  type="button"
                  className="ml-2 underline"
                  onClick={() => {
                    clearOfnSaveFeedback()
                    setSaveFeedback(null)
                  }}
                >
                  Dismiss
                </button>
              </p>
            ) : null}
          </div>
        ) : null}

        {document ? (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {(document.typ ?? []).map((typ) => (
              <span
                key={typ}
                className="rounded-md bg-white/80 px-2 py-1 text-[11px] font-medium text-slate-700 ring-1 ring-slate-200"
              >
                {typ}
              </span>
            ))}
            <span className="ml-1 truncate font-mono text-[11px] text-slate-500" title={document.iri}>
              {document.iri}
            </span>
          </div>
        ) : null}

        <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            { label: 'Concepts', value: counts.total },
            { label: 'Classes', value: counts.classes },
            { label: 'Relations', value: counts.relations },
            { label: 'Properties', value: counts.properties },
          ].map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-200/80 bg-white/70 px-3 py-2"
            >
              <p className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
                {stat.label}
              </p>
              <p className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">{stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="px-6 py-5">
        {!projectId ? (
          <p className="text-sm text-slate-600">Select a project to manage its OFN file.</p>
        ) : loadError || regenerateError ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
            {loadError || regenerateError}
          </div>
        ) : ofnQuery.isLoading ? (
          <p className="text-sm text-slate-600">Loading saved OFN…</p>
        ) : missingOfn ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            <p className="font-medium">No OFN file for this project yet.</p>
            <p className="mt-1 text-amber-900/90">
              Finalize approved changes, or click <span className="font-semibold">Generate OFN</span>{' '}
              to create{' '}
              <span className="font-mono text-[11px]">data/projects/{projectId}/ofn.json</span>.
            </p>
          </div>
        ) : document ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              {KIND_FILTERS.map((item) => {
                const active = filter === item.id
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setFilter(item.id)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                      active
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {item.label}
                  </button>
                )
              })}
              <input
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search pojmy…"
                className="ml-auto min-w-48 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-800 shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30"
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
              <ul className="max-h-112 space-y-1 overflow-y-auto rounded-xl border border-slate-200 bg-slate-50/60 p-2">
                {filtered.length === 0 ? (
                  <li className="px-3 py-6 text-center text-sm text-slate-500">No matching concepts.</li>
                ) : (
                  filtered.map((pojem) => {
                    const kind = primaryKind(pojem)
                    const active = pojem.iri === selectedIri
                    return (
                      <li key={pojem.iri}>
                        <button
                          type="button"
                          onClick={() => setSelectedIri(pojem.iri)}
                          className={`w-full rounded-lg px-3 py-2 text-left transition ${
                            active
                              ? 'bg-white shadow-sm ring-1 ring-sky-300'
                              : 'hover:bg-white/80'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="truncate text-sm font-medium text-slate-900">
                              {textCs(pojem.název) || shortIri(pojem.iri)}
                            </span>
                            <span
                              className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold ${kindBadgeClass(kind)}`}
                            >
                              {kind}
                            </span>
                          </div>
                          <p className="mt-0.5 truncate font-mono text-[10px] text-slate-500">
                            {shortIri(pojem.iri)}
                          </p>
                        </button>
                      </li>
                    )
                  })
                )}
              </ul>

              <div className="rounded-xl border border-slate-200 bg-white p-4">
                {selected ? (
                  <OfnPojemDetail pojem={selected} />
                ) : (
                  <p className="text-sm text-slate-500">Select a concept to inspect details.</p>
                )}
              </div>
            </div>

            <div>
              <button
                type="button"
                onClick={() => setShowRaw((value) => !value)}
                className="text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-800"
              >
                {showRaw ? 'Hide raw JSON' : 'Show raw JSON'}
              </button>
              {showRaw ? (
                <pre className="mt-2 max-h-80 overflow-auto rounded-xl border border-slate-200 bg-slate-950 p-4 text-[11px] leading-relaxed text-slate-100">
                  {jsonText}
                </pre>
              ) : null}
            </div>

            {projectName ? (
              <p className="text-[11px] text-slate-500">
                Source project: <span className="font-medium text-slate-700">{projectName}</span>
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </section>
  )
}

function OfnPojemDetail({ pojem }: { pojem: OfnPojem }) {
  const defining = pojem['definující-ustanovení-právního-předpisu'] ?? []
  const related = pojem['související-ustanovení-právního-předpisu'] ?? []
  const parents = pojem['nadřazená-třída'] ?? []

  return (
    <div className="space-y-3">
      <div>
        <div className="flex flex-wrap gap-1.5">
          {pojem.typ.map((typ) => (
            <span
              key={typ}
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold ${kindBadgeClass(typ)}`}
            >
              {typ}
            </span>
          ))}
        </div>
        <h4 className="mt-2 text-lg font-semibold text-slate-900">
          {textCs(pojem.název) || shortIri(pojem.iri)}
        </h4>
        <p className="mt-1 break-all font-mono text-[11px] text-slate-500">{pojem.iri}</p>
      </div>

      {textCs(pojem.definice) ? (
        <DetailBlock label="Definition">{textCs(pojem.definice)}</DetailBlock>
      ) : null}
      {textCs(pojem.popis) ? (
        <DetailBlock label="Description">{textCs(pojem.popis)}</DetailBlock>
      ) : null}

      {pojem['definiční-obor'] ? (
        <DetailBlock label="Domain">
          <span className="font-mono text-xs">{pojem['definiční-obor']}</span>
        </DetailBlock>
      ) : null}
      {pojem['obor-hodnot'] ? (
        <DetailBlock label="Range">
          <span className="font-mono text-xs">{pojem['obor-hodnot']}</span>
        </DetailBlock>
      ) : null}

      {parents.length > 0 ? (
        <DetailBlock label="Broader classes">
          <ul className="space-y-1">
            {parents.map((iri) => (
              <li key={iri} className="break-all font-mono text-xs text-slate-700">
                {iri}
              </li>
            ))}
          </ul>
        </DetailBlock>
      ) : null}

      {defining.length > 0 ? (
        <DetailBlock label="Defining provisions">
          <ul className="space-y-1">
            {defining.map((iri) => (
              <li key={iri}>
                <a
                  href={iri}
                  target="_blank"
                  rel="noreferrer"
                  className="break-all font-mono text-xs text-sky-800 underline"
                >
                  {iri}
                </a>
              </li>
            ))}
          </ul>
        </DetailBlock>
      ) : null}

      {related.length > 0 ? (
        <DetailBlock label="Related provisions">
          <ul className="space-y-1">
            {related.map((iri) => (
              <li key={iri}>
                <a
                  href={iri}
                  target="_blank"
                  rel="noreferrer"
                  className="break-all font-mono text-xs text-sky-800 underline"
                >
                  {iri}
                </a>
              </li>
            ))}
          </ul>
        </DetailBlock>
      ) : null}
    </div>
  )
}

function DetailBlock({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <div className="mt-1 text-sm text-slate-800">{children}</div>
    </div>
  )
}
