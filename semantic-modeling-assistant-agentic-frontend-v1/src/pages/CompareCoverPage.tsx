export function CompareCoverPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <button className="px-2 py-1 border rounded-card">Project KB</button>
        <button className="px-2 py-1 border rounded-card">Global KB</button>
        <label className="flex items-center gap-2 ml-4 text-sm">
          <input type="checkbox" /> Coverage ON
        </label>
      </div>
      <div className="grid grid-cols-[280px,1fr,320px] gap-4">
        <div className="bg-white border rounded-card p-3">Docs & Outline</div>
        <div className="bg-white border rounded-card p-3">Document Viewer</div>
        <div className="bg-white border rounded-card p-3">Matched Ontology</div>
      </div>
    </div>
  )
}
