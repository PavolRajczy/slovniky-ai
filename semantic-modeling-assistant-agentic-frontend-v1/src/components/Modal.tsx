import { PropsWithChildren } from 'react'

export function Modal({ title, onClose, children }: PropsWithChildren<{ title: string; onClose: () => void }>) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-white rounded-drawer shadow-xl w-full max-w-2xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="font-semibold text-lg">{title}</div>
          <button className="px-2 py-1" onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}
