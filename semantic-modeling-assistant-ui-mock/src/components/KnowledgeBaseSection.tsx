import { useMemo, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import {
  addExpertDocuments,
  getProjectKnowledgeBase,
  removeExpertDocument,
  removeLegalDocument,
  setKeyDocument,
  startExpertUploadJob,
  startLegalDocumentJob,
} from '@/api/knowledgeBase'
import { getProject } from '@/api/projects'
import type { KnowledgeBaseResponse, KnowledgeDocumentSummary, ProjectModel } from '@/api/types'
import { DocumentProcessingProgress } from '@/components/DocumentProcessingProgress'
import { useTrackedDocumentProcessingJob } from '@/hooks/useDocumentProcessingJob'

const EXAMPLE_LEGAL_URL =
  'https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01'

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
  const [expertFile, setExpertFile] = useState<File | null>(null)
  const expertFileInputRef = useRef<HTMLInputElement>(null)
  const [legalError, setLegalError] = useState<string | null>(null)
  const [expertError, setExpertError] = useState<string | null>(null)
  const [keyError, setKeyError] = useState<string | null>(null)

  const ensureMainSource = async (kind: 'legal' | 'expert', preferredId?: string) => {
    const project = queryClient.getQueryData<ProjectModel>(['project', projectId])
    const kb = queryClient.getQueryData<KnowledgeBaseResponse>(['project-kb', projectId])
    if (!project || !kb || project.key_knowledge_document_id) return
    const documents = kind === 'legal' ? kb.legal_documents : kb.expert_documents
    const target = documents.find((doc) => doc.id === preferredId) ?? documents[documents.length - 1]
    if (target) {
      setKeyMutation.mutate(target.id)
    }
  }

  const legalJob = useTrackedDocumentProcessingJob(projectId, async () => {
    const addedId = addLegalMutation.variables
    setLegalUrl('')
    await invalidateKb()
    await ensureMainSource('legal', addedId)
  })

  const expertJob = useTrackedDocumentProcessingJob(projectId, async () => {
    setExpertFile(null)
    if (expertFileInputRef.current) {
      expertFileInputRef.current.value = ''
    }
    await invalidateKb()
    await ensureMainSource('expert')
  })

  const addLegalMutation = useMutation({
    mutationFn: (documentId: string) => startLegalDocumentJob(projectId, documentId),
    onSuccess: (job) => {
      setLegalError(null)
      legalJob.track(job)
    },
    onError: (error: unknown) => setLegalError(toErrorMessage(error)),
  })

  const removeLegalMutation = useMutation({
    mutationFn: (documentId: string) => removeLegalDocument(projectId, documentId),
    onSuccess: invalidateKb,
    onError: (error: unknown) => setLegalError(toErrorMessage(error)),
  })

  const uploadExpertMutation = useMutation({
    mutationFn: (file: File) => startExpertUploadJob(projectId, file),
    onSuccess: (job) => {
      setExpertError(null)
      expertJob.track(job)
    },
    onError: (error: unknown) => setExpertError(toErrorMessage(error)),
  })

  const addExpertMutation = useMutation({
    mutationFn: (documentId: string) =>
      addExpertDocuments(projectId, { document_ids: [documentId] }),
    onSuccess: async (_data, documentId) => {
      setExpertError(null)
      setExpertId('')
      await invalidateKb()
      await ensureMainSource('expert', documentId)
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

  const handleUploadExpert = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!expertFile) {
      setExpertError('Choose a PDF or DOCX file.')
      return
    }
    uploadExpertMutation.mutate(expertFile)
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
        Attach a legal act or another structured document. Each document is loaded, summarized and
        indexed by the backend.
      </p>
      <p className="mt-1 text-sm text-slate-600">
        The <strong>main source</strong> is the document the assistant splits into sections on the domain map.
        The first document you add becomes the main source automatically; use{' '}
        <strong>Use as main source</strong> to pick a different one.
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
                disabled={addLegalMutation.isPending || legalJob.isRunning}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm disabled:opacity-60"
              >
                {processingButtonLabel(addLegalMutation.isPending, legalJob.isRunning, 'Add legal document')}
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              Adding a new act may take several minutes the first time (load → summarize → index).
            </p>
            {legalJob.job ? (
              <DocumentProcessingProgress job={legalJob.job} onDismiss={legalJob.dismiss} />
            ) : null}
            {legalJob.pollError ? (
              <p className="text-[11px] text-rose-800">
                Lost track of the processing: {toErrorMessage(legalJob.pollError)}
              </p>
            ) : null}
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
              <h4 className="text-sm font-semibold text-slate-900">Other documents</h4>
              <p className="mt-1 text-xs text-slate-600">
                Upload a structured PDF or DOCX that is not a statute. Headings become sections. After it is
                summarized, <strong>Use as main source</strong> makes it the source for the domain map.
              </p>
            </div>
          </div>

          <form onSubmit={handleUploadExpert} className="mt-3 space-y-2 rounded-lg border border-slate-200 bg-white p-3">
            <label className="text-xs font-medium text-slate-700" htmlFor="expert-doc-file">
              PDF or DOCX
            </label>
            <input
              id="expert-doc-file"
              ref={expertFileInputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(event) => setExpertFile(event.target.files?.[0] ?? null)}
              className="block w-full text-xs text-slate-700 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-2 file:py-1 file:text-xs file:font-medium file:text-slate-800"
            />
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={uploadExpertMutation.isPending || expertJob.isRunning || !expertFile}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-60"
              >
                {processingButtonLabel(uploadExpertMutation.isPending, expertJob.isRunning, 'Upload document')}
              </button>
            </div>
            <p className="text-[11px] text-slate-500">
              The first upload summarizes every section, same as a legal act.
            </p>
            {expertJob.job ? (
              <DocumentProcessingProgress job={expertJob.job} onDismiss={expertJob.dismiss} />
            ) : null}
            {expertJob.pollError ? (
              <p className="text-[11px] text-rose-800">
                Lost track of the processing: {toErrorMessage(expertJob.pollError)}
              </p>
            ) : null}
          </form>

          <form onSubmit={handleAddExpert} className="mt-3 space-y-2 rounded-lg border border-slate-200 bg-white p-3">
            <label className="text-xs font-medium text-slate-700" htmlFor="expert-doc-id">
              Or an existing document ID
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
              <li className="px-3 py-2 text-xs text-slate-500">No other documents yet.</li>
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
          <h4 className="text-sm font-semibold text-slate-900">Main source</h4>
          {keyError ? (
            <span className="text-xs font-medium text-rose-700">{keyError}</span>
          ) : null}
        </div>
        {keyDocumentId ? (
          <div className="mt-2 rounded-lg border border-emerald-200 bg-white px-3 py-2 text-sm">
            <div className="break-all font-medium text-slate-900">
              {keyDocumentSummary ? documentDisplayTitle(keyDocumentSummary) : keyDocumentId}
            </div>
            <div className="mt-0.5 break-all font-mono text-[11px] text-slate-500">{keyDocumentId}</div>
            {keyDocumentSummary?.content_summary ? (
              <p className="mt-1 text-xs text-slate-600">{keyDocumentSummary.content_summary}</p>
            ) : null}
          </div>
        ) : (
          <p className="mt-2 text-xs text-slate-600">
            No main source yet. Add a legal act or upload a document above; the first one becomes the main
            source for the domain map.
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
      <div className="min-w-0">
        <div className="break-all font-medium text-slate-800">{documentDisplayTitle(doc)}</div>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800">
            indexed
          </span>
          {isKey ? (
            <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-900">
              main source
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
      <div className="flex flex-wrap justify-end gap-2 pt-1">
        {!isKey ? (
          <button
            type="button"
            onClick={onSetKey}
            disabled={isBusy}
            title="Make this the document the assistant splits into sections on the domain map."
            className="rounded-md border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            Use as main source
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
    </li>
  )
}

const ELI_ACT_PATTERN = /\/eli\/cz\/sb\/(\d{4})\/(\d+)(?:\/|$)/

function documentDisplayTitle(doc: KnowledgeDocumentSummary): string {
  const title = doc.title?.trim()
  if (title && title !== doc.id) return title
  const eli = ELI_ACT_PATTERN.exec(doc.id)
  if (eli) return `Act ${eli[2]}/${eli[1]} Sb.`
  return title || doc.id
}

function processingButtonLabel(isStarting: boolean, isProcessing: boolean, idleLabel: string): string {
  if (isStarting) return 'Starting…'
  if (isProcessing) return 'Processing…'
  return idleLabel
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
