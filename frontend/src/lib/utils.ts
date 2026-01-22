import { format } from 'date-fns'
import clsx, { ClassValue } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

export function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'MMM dd, yyyy')
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'MMM dd, yyyy hh:mm a')
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num)
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str
  return str.slice(0, length) + '...'
}

