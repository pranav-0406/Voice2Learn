export function voiceDiagnostic(stage: string, startedAt?: number) {
  const now = performance.now()
  if (!import.meta.env.DEV) return now
  const elapsed = startedAt === undefined ? undefined : Math.round(now - startedAt)
  console.debug(`[voice] ${stage}`, elapsed === undefined ? { at: Math.round(now) } : { elapsedMs: elapsed })
  return now
}
