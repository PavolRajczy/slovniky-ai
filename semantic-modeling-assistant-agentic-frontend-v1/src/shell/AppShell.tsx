import { PropsWithChildren, useState } from 'react'
import { Link, useRouterState } from '@tanstack/react-router'
import { ProjectSelector } from '../components/ProjectSelector'
import { OntologySelector } from '../components/OntologySelector'
import { OperationsDrawer } from '../components/OperationsDrawer'
import { BigAutopilotModal } from '../components/BigAutopilotModal'
import { ElementCoveragePanel } from '../components/ElementCoveragePanel'
import { useOperationsStore } from '@/store/operationsStore'

export function AppShell({ children }: PropsWithChildren) {
  const [rightOpen, setRightOpen] = useState(true)
  const [bottomOpen, setBottomOpen] = useState(false)
  const [showAutopilotModal, setShowAutopilotModal] = useState(false)
  const route = useRouterState()
  const ops = useOperationsStore()

  return (
    <div className="h-full grid grid-rows-[auto,1fr,auto]">
      {/* Top Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white shadow">
        <div className="flex items-center gap-3">
          <ProjectSelector />
          <span className="text-gray-300">|</span>
          <OntologySelector />
        </div>
        <div className="flex items-center gap-3">
          {ops.bigAutopilotRunning && (
            <div className="flex items-center gap-2 text-sm bg-purple-50 px-3 py-1 rounded-card">
              <span className="animate-pulse">🤖</span>
              <span className="font-medium">Big Autopilot Running</span>
              {ops.bigAutopilotProgress.currentAreaName && (
                <span className="text-gray-600">
                  • {ops.bigAutopilotProgress.currentAreaName}
                </span>
              )}
            </div>
          )}
          {ops.bigAutopilotRunning && ops.bigAutopilotProgress.currentIterationName && (
            <div className="flex items-center gap-2 text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded-card max-w-md">
              <span className="font-medium">Executing:</span>
              <span className="truncate">{ops.bigAutopilotProgress.currentIterationName}</span>
            </div>
          )}
          {ops.bigAutopilotRunning ? (
            <button
              className="px-4 py-1 bg-red-600 text-white rounded-card hover:bg-red-700"
              onClick={() => ops.requestStopBigAutopilot()}
              disabled={ops.bigAutopilotStopRequested}
            >
              {ops.bigAutopilotStopRequested ? '⏳ Stopping...' : '⏹ Stop Autopilot'}
            </button>
          ) : (
            <button
              className="px-4 py-1 bg-purple-600 text-white rounded-card hover:bg-purple-700"
              onClick={() => setShowAutopilotModal(true)}
            >
              🤖 Autopilot
            </button>
          )}
        </div>
      </div>
      {/* Body */}
      <div className="grid grid-cols-[240px,1fr,360px] gap-0 h-full">
        {/* Left Nav */}
        <nav className="bg-white border-r p-3 space-y-2">
          <NavLink to="/" label="Storyboard" />
          <NavLink to="/workbench" label="Workbench" />
          <NavLink to="/compare" label="Compare & Cover" />
          <div className="h-px bg-gray-200 my-2" />
          <NavLink to="/ontology" label="Ontology" />
          <NavLink to="/kb" label="Knowledge Base" />
          <NavLink to="/settings" label="Settings" />
        </nav>
        {/* Central Workspace */}
        <main className="p-4 overflow-auto h-full">{children}</main>
        {/* Right Panel - Sticky positioned */}
        <aside className="bg-white border-l p-3 relative">
          <div className="sticky top-0 max-h-screen overflow-y-auto">
            <ElementCoveragePanel />
          </div>
        </aside>
      </div>
      {/* Bottom Drawer */}
      <OperationsDrawer />
      
      {/* Big Autopilot Modal */}
      {showAutopilotModal && (
        <BigAutopilotModal onClose={() => setShowAutopilotModal(false)} />
      )}
    </div>
  )
}

function NavLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      to={to}
      activeOptions={{ exact: true }}
      className="block px-3 py-2 rounded-card hover:bg-gray-100 [aria-current=page]:bg-primary-600 [aria-current=page]:text-white"
    >
      {label}
    </Link>
  )
}
