import { format, formatDistanceToNow } from 'date-fns'
import clsx, { ClassValue } from 'clsx'

/**
 * Merge class names with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

/**
 * Format price in cents to display string
 */
export function formatPrice(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}

/**
 * Format date to readable string
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  return format(new Date(dateString), 'MMM d, yyyy')
}

/**
 * Format date with time
 */
export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  return format(new Date(dateString), 'MMM d, yyyy h:mm a')
}

/**
 * Format date as relative time
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  return formatDistanceToNow(new Date(dateString), { addSuffix: true })
}

/**
 * Format number with commas
 */
export function formatNumber(num: number): string {
  return num.toLocaleString()
}

/**
 * Get enrichment level display text
 */
export function getEnrichmentLabel(level: string): string {
  switch (level) {
    case 'phone_only':
      return 'Phone Only'
    case 'email_and_phone':
      return 'Email + Phone'
    default:
      return level
  }
}

/**
 * Get enrichment level badge color
 */
export function getEnrichmentBadgeClass(level: string): string {
  switch (level) {
    case 'phone_only':
      return 'badge-primary'
    case 'email_and_phone':
      return 'badge-success'
    default:
      return 'badge-primary'
  }
}

/**
 * Get status badge color
 */
export function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'paid':
      return 'badge-success'
    case 'pending':
      return 'badge-warning'
    case 'failed':
      return 'badge-danger'
    case 'refunded':
      return 'badge-primary'
    default:
      return 'badge-primary'
  }
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * Generate URL-safe slug
 */
export function generateSlug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .trim()
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * Get error message from API error
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'object' && error !== null && 'detail' in error) {
    return String((error as { detail: string }).detail)
  }
  return 'An unexpected error occurred'
}
