// Travas de uso: validação de entrada, origem, limite por IP e teto global diário.
// O limite em memória é "melhor esforço" (cada instância da função tem o seu); o teto
// definitivo de gasto é o limite mensal configurado no Console da Anthropic.

export const LIMITS = {
  maxMessages: 6,        // turnos mantidos da conversa
  maxChars: 400,         // por mensagem do usuário
  perMinute: 8,
  perDay: 60,
  globalPerDay: Number(process.env.CHAT_DAILY_CAP) || 3000,
}

const hits = new Map()   // ip -> { min: number[], day: number[] }
let global = { day: '', n: 0 }

const today = () => new Date().toISOString().slice(0, 10)
const safeOrigin = (u) => { try { return new URL(u).origin } catch { return '' } }

export function allowedOrigin(origin, referer) {
  const extra = (process.env.ALLOWED_ORIGINS || '').split(',').map((s) => s.trim()).filter(Boolean)
  const ok = ['https://pkaguide.vercel.app', ...extra]
  const o = origin || (referer ? safeOrigin(referer) : '')
  if (!o) return false                       // navegador sempre manda Origin/Referer no POST
  if (/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(o)) return true
  return ok.includes(o)
}

export function rateLimit(ip, now = Date.now()) {
  const d = today()
  if (global.day !== d) global = { day: d, n: 0 }
  if (global.n >= LIMITS.globalPerDay) return 'global'
  const h = hits.get(ip) || { min: [], day: [] }
  h.min = h.min.filter((t) => now - t < 60_000)
  h.day = h.day.filter((t) => now - t < 86_400_000)
  if (h.min.length >= LIMITS.perMinute) return 'minute'
  if (h.day.length >= LIMITS.perDay) return 'day'
  h.min.push(now); h.day.push(now)
  hits.set(ip, h)
  if (hits.size > 5000) for (const k of hits.keys()) { hits.delete(k); if (hits.size < 4000) break }
  global.n++
  return null
}
export const _resetLimits = () => { hits.clear(); global = { day: '', n: 0 } }

/** Aceita só {messages:[{role:'user'|'assistant',content:string}]} terminando em 'user'. */
export function parseMessages(body) {
  const arr = body && Array.isArray(body.messages) ? body.messages : null
  if (!arr || !arr.length) return { error: 'Mensagem vazia.' }
  const out = []
  for (const m of arr.slice(-LIMITS.maxMessages)) {
    if (!m || (m.role !== 'user' && m.role !== 'assistant') || typeof m.content !== 'string') return { error: 'Formato inválido.' }
    const max = m.role === 'user' ? LIMITS.maxChars : 600
    const c = m.content.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '').trim().slice(0, max)
    if (!c) return { error: 'Mensagem vazia.' }
    out.push({ role: m.role, content: c })
  }
  while (out.length && out[0].role !== 'user') out.shift()
  if (!out.length || out[out.length - 1].role !== 'user') return { error: 'A última mensagem precisa ser sua pergunta.' }
  return { messages: out }
}
