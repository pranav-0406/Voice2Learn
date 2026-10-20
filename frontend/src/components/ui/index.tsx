import React from 'react'
import { motion } from 'framer-motion'
import { X } from 'lucide-react'

export function Card({
  children,
  className = '',
  id,
}: {
  children: React.ReactNode
  className?: string
  id?: string
}) {
  return (
    <section className={`card ${className}`} id={id}>
      {children}
    </section>
  )
}

export function Button({
  children,
  className = '',
  variant = 'primary',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'quiet'
}) {
  return (
    <button className={`button ${variant} ${className}`} {...props}>
      {children}
    </button>
  )
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return <span className="spinner" aria-label={label} role="status" />
}

export function Notice({
  children,
  tone = 'error',
}: {
  children: React.ReactNode
  tone?: 'error' | 'info'
}) {
  return (
    <p className={`notice ${tone}`} role="alert">
      {children}
    </p>
  )
}

export function Stat({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
}) {
  return (
    <Card className="stat">
      <span>{icon}</span>
      <small>{label}</small>
      <strong>{value}</strong>
    </Card>
  )
}

export function Page({ children, id }: { children: React.ReactNode; id?: string }) {
  return (
    <motion.div
      className="page"
      id={id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  )
}

export function PageError({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <Page>
      <Card className="empty">
        <X size={28} aria-hidden="true" />
        <h2>We couldn’t load this yet.</h2>
        <p>{message}</p>
        <Button variant="secondary" onClick={onRetry ?? (() => window.location.reload())}>
          Try again
        </Button>
      </Card>
    </Page>
  )
}

export function DashboardSkeleton() {
  return (
    <div className="skeleton-stack" aria-label="Loading content" aria-busy="true">
      <div className="skeleton stats" />
      <div className="skeleton hero" />
      <div className="skeleton block" />
    </div>
  )
}
