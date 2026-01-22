import { ReactNode } from 'react'

interface AlertProps {
  children: ReactNode
  variant?: 'info' | 'success' | 'warning' | 'error'
}

export default function Alert({ children, variant = 'info' }: AlertProps) {
  const colors = {
    info: 'bg-blue-50 text-blue-800 border-blue-200',
    success: 'bg-green-50 text-green-800 border-green-200',
    warning: 'bg-yellow-50 text-yellow-800 border-yellow-200',
    error: 'bg-red-50 text-red-800 border-red-200',
  }

  return (
    <div className={`border rounded-lg p-4 ${colors[variant]}`}>
      {children}
    </div>
  )
}