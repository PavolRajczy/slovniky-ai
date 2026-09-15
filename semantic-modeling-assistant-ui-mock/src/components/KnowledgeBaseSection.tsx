import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import {
  addExpertDocuments,
  addLegalDocuments,
  getProjectKnowledgeBase,
  removeExpertDocument,
  removeLegalDocument,
  setKeyDocument,
} from '@/api/knowledgeBase'
import { getProject } from '@/api/projects'
import type { KnowledgeDocumentSummary } from '@/api/types'

const EXAMPLE_LEGAL_URL =
  'https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01'

type Props = {
  projectId: string
}

export function KnowledgeBaseSection({ projectId }: Props) {
  const queryClient = useQueryClient()

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId, signal),
  })

  const kbQuery = useQuery({
    queryKey: ['project-kb', projectId],
    queryFn: ({ signal }) => getProjectKnowledgeBase(projectId, signal),
  })

  const keyDocumentId = projectQuery.data?.key_knowledge_document_id ?? null

  const invalidateKb = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['project-kb', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
    ])
  }

  const [legalUrl, setLegalUrl] = useState('')
  const [expertId, setExpertId] = useState('')
  const [legalError, setLegalError] = useState<string | null>(null)
  const [expertError, setExpertError] = useState<string | null>(null)
  const [keyError, setKeyError] = useState<string | null>(null)

  const addLegalMutation = useMutation({
    mutationFn: (documentId: string) =>
      addLegalDocuments(projectId, { document_ids: [documentId] }),
    onSuccess: async () => {
      setLegalError(null)
      setLegalUrl('')
      await invalidateKb()
    },
    onError: (error: unknown) => setLegalError(toErrorMessage(error)),
  })

  const removeLegalMutation = useMutation({
    mutationFn: (documentId: string) => removeLegalDocument(projectId, documentId),
    onSuccess: invalidateKb,
    onError: (error: unknown) => setLegalError(toErrorMessage(error)),
  })

  const addExpertMutation = useMutation({
    mutationFn: (documentId: string) =>
      addExpertDocuments(projectId, { document_ids: [documentId] }),
    onSuccess: async () => {
      setExpertError(null)
      setExpertId('')
      await invalidateKb()
    },
    onError: (error: unknown) => setExpertError(toErrorMessage(error)),
  })

  const removeExpertMutation = useMutation({
    mutationFn: (documentId: string) => removeExpertDocument(projectId, documentId),
    onSuccess: invalidateKb,
    onError: (error: unknown) => setExpertError(toErrorMessage(error)),
  })

  const setKeyMutation = useMutation({
    mutationFn: (documentId: string) =>
      setKeyDocument(projectId, { document_id: documentId }),
    onSuccess: async () => {
      setKeyError(null)
      await invalidateKb()
    },
    onError: (error: unknown) => setKeyError(toErrorMessage(error)),
  })

  const handleAddLegal = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const value = legalUrl.trim()
    if (!value) {
      setLegalError('Document URL is required.')
      return
    }
    addLegalMutation.mutate(value)
  }

  const handleAddExpert = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const value = expertId.trim()
    if (!value) {
      setExpertError('Document ID is required.')
      return
    }
    addExpertMutation.mutate(value)
  }

  const legalDocuments = kbQuery.data?.legal_documents ?? []
  const expertDocuments = kbQuery.data?.expert_documents ?? []

  const keyDocumentSummary = useMemo(() => {
    if (!keyDocumentId) return null
    return (
      legalDocuments.find((doc) => doc.id === keyDocumentId) ??
      expertDocuments.find((doc) => doc.id === keyDocumentId) ??
      null
    )
  }, [keyDocumentId, legalDocuments, expertDocuments])

  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Knowledge base
        </h3>
        {kbQuery.isFetching ? <span className="text-xs text-slate-500">refreshing…</span> : null}
      </div>
      <p className="mt-1 text-sm text-slate-600">
        Attach the legal act that defines the domain and supplementary expert documents. Each document is
        loaded, summarized and indexed by the backend; pick one legal act as the <strong>key document</strong>{' '}
        used for domain-area analysis.
      </p>

      {kbQuery.isError ? (
        <p className="mt-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
          {(kbQuery.error as Error).message}
        </p>
      ) : null}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Legal documents</h4>
              <p className="mt-1 text-xs text-slate-600">
                Czech legal acts loaded from{' '}
                <a
                  href="https://e-sbirka.gov.cz"
                  target="_blank"
                  rel="noreferrer"
                  className="font-medium text-emerald-700 underline-offset-2 hover:underline"
                >
                  e-sbirka.gov.cz
                </a>{' '}
                via ESEL SPARQL. Paste an ELI URL using format{' '}
                <code className="rounded bg-white px-1 py-0.5 text-[11px] text-slate-700">
                  …/eli/cz/sb/YEAR/NUMBER/EFFECTIVE-DATE
                </code>
                .
              </p>
            </div>
          </div>

          <form onSubmit={handleAddLegal} className="mt-3 space-y-2 rounded-lg border border-slate-200 bg-white p-3">
            <label className="text-xs font-medium text-slate-700" htmlFor="legal-doc-url">
              ESEL ELI URL
            </label>
            <input
              id="legal-doc-url"
              value={legalUrl}
              onChange={(event) => setLegalUrl(event.target.value)}
              placeholder={EXAMPLE_LEGAL_URL}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-xs text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <div className="flex flex-wrap items-center justify-between gap-2">
              <button
                type="button"
                onClick={() => setLegalUrl(EXAMPLE_LEGAL_URL)}
                className="text-[11px] font-medium text-emerald-700 hover:underline"
              >
                Use example (Act 56/2001 - traffic)
              </button>
              <button
                type="submit"
                disabled={addLegalMutation.isPending}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm disabled:opacity-60"
              >
                {addLegalMutation.isPending ? 'Loading + indexing…' : 'Add legal document'}
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              Adding a new act may take several minutes the first time (load → summarize → index).
            </p>
          </form>

          {legalError ? (
            <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
              {legalError}
            </p>
          ) : null}

          <ul className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
            {kbQuery.isLoading ? (
              <li className="px-3 py-2 text-xs text-slate-500">Loading documents…</li>
            ) : legalDocuments.length === 0 ? (
              <li className="px-3 py-2 text-xs text-slate-500">No legal documents yet.</li>
            ) : (
              legalDocuments.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  isKey={doc.id === keyDocumentId}
                  onSetKey={() => setKeyMutation.mutate(doc.id)}
                  onRemove={() => removeLegalMutation.mutate(doc.id)}
                  isBusy={
                    (setKeyMutation.isPending && setKeyMutation.variables === doc.id) ||
                    (removeLegalMutation.isPending && removeLegalMutation.variables === doc.id)
                  }
                />
              ))
            )}
          </ul>
        </section>

        <section className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h4 className="text-sm font-semibold text-slate-900">Domain-expert documents</h4>
              <p className="mt-1 text-xs text-slate-600">
                Optional supplementary references for retrieval and task context. Provide a stable document ID
                (URL or identifier known to the backend expert loader).
              </p>
            </div>
          </div>

          <form onSubmit={handleAddExpert} className="mt-3 space-y-2 rounded-lg border border-slate-200 bg-white p-3">
            <label className="text-xs font-medium text-slate-700" htmlFor="expert-doc-id">
              Expert document ID
            </label>
            <input
              id="expert-doc-id"
              value={expertId}
              onChange={(event) => setExpertId(event.target.value)}
              placeholder="e.g. https://example.org/handbook/v1"
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-xs text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={addExpertMutation.isPending}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-60"
              >
                {addExpertMutation.isPending ? 'Adding…' : 'Add expert document'}
              </button>
            </div>
          </form>

          {expertError ? (
            <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
              {expertError}
            </p>
          ) : null}

          <ul className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
            {kbQuery.isLoading ? (
              <li className="px-3 py-2 text-xs text-slate-500">Loading documents…</li>
            ) : expertDocuments.length === 0 ? (
              <li className="px-3 py-2 text-xs text-slate-500">No expert documents yet.</li>
            ) : (
              expertDocuments.map((doc) => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  isKey={doc.id === keyDocumentId}
                  onSetKey={() => setKeyMutation.mutate(doc.id)}
                  onRemove={() => removeExpertMutation.mutate(doc.id)}
                  isBusy={
                    (setKeyMutation.isPending && setKeyMutation.variables === doc.id) ||
                    (removeExpertMutation.isPending && removeExpertMutation.variables === doc.id)
                  }
                />
              ))
            )}
          </ul>
        </section>
      </div>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50/80 p-4">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h4 className="text-sm font-semibold text-slate-900">Key document</h4>
          {keyError ? (
            <span className="text-xs font-medium text-rose-700">{keyError}</span>
          ) : null}
        </div>
        {keyDocumentId ? (
          <div className="mt-2 rounded-lg border border-emerald-200 bg-white px-3 py-2 text-sm">
            <div className="font-medium text-slate-900">
              {keyDocumentSummary?.title || keyDocumentId}
            </div>
            <div className="mt-0.5 break-all font-mono text-[11px] text-slate-500">{keyDocumentId}</div>
            {keyDocumentSummary?.content_summary ? (
              <p className="mt-1 text-xs text-slate-600">{keyDocumentSummary.content_summary}</p>
            ) : null}
          </div>
        ) : (
          <p className="mt-2 text-xs text-slate-600">
            No key document set. Use the <em>Set as key</em> button next to a legal or expert document to pick
            one — it becomes the primary source for domain-area analysis.
          </p>
        )}
      </div>
    </section>
  )
}

type DocumentRowProps = {
  doc: KnowledgeDocumentSummary
  isKey: boolean
  isBusy: boolean
  onSetKey: () => void
  onRemove: () => void
}

function DocumentRow({ doc, isKey, isBusy, onSetKey, onRemove }: DocumentRowProps) {
  return (
    <li className="space-y-1 px-3 py-2 text-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium text-slate-800">{doc.title || doc.id}</span>
            <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800">
              indexed
            </span>
            {isKey ? (
              <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-900">
                key document
              </span>
            ) : null}
            {doc.element_type ? (
              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
                {doc.element_type}
              </span>
            ) : null}
          </div>
          <div className="mt-0.5 truncate font-mono text-[11px] text-slate-500" title={doc.id}>
            {doc.id}
          </div>
          {doc.content_summary ? (
            <p className="mt-1 text-xs text-slate-600 line-clamp-2">{doc.content_summary}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          {!isKey ? (
            <button
              type="button"
              onClick={onSetKey}
              disabled={isBusy}
              className="rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
            >
              Set as key
            </button>
          ) : null}
          <button
            type="button"
            onClick={onRemove}
            disabled={isBusy}
            className="rounded-md border border-rose-200 bg-white px-2 py-1 text-[11px] font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-60"
          >
            Remove
          </button>
        </div>
      </div>
    </li>
  )
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
