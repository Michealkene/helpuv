import { ReactNode } from 'react'

interface TableProps {
  children: ReactNode
}

export default function Table({ children }: TableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        {children}
      </table>
    </div>
  )
}