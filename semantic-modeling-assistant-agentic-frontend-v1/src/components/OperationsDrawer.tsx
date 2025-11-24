import { useOperationsStore } from '@/store/operationsStore'

export function OperationsDrawer() {
  const { visible } = useOperationsStore()

  return (
    <div className="border-t bg-white p-3">
      <div className="text-sm text-gray-600">
        {visible 
          ? "Operations drawer - placeholder for future usage." 
          : "Operations drawer will appear here when needed."}
      </div>
    </div>
  )
}
