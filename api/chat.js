import fs from 'node:fs'
import Anthropic from '@anthropic-ai/sdk'
import { zodOutputFormat } from '@anthropic-ai/sdk/helpers/zod'
import { Index, tokens } from './_lib/search.js'
import { allowedOrigin, rateLimit, parseMessages } from './_lib/guard.js'
import { SYSTEM, REFUSAL, NOT_FOUND, OutputSchema, buildMessages, linksFor } from './_lib/prompt.js'

export const MODEL = 'claude-haiku-5-5'

let _kb, _idx
function load() {
  if (!_kb) {
    _kb = JSON.parse(fs.readFileSync(new URL('./_kb/kb.json', import.meta.url), 'utf8'))
    _idx = new Index(_kb)
  }
  return { kb: _kb, idx: _idx }
}

const reply = (status, json) => ({ status, json })

/** Núcleo testável: recebe a requisição já "achatada" e devolve {status, json}. */
export async function handleChat(req, deps = {}) {
  const env = deps.env || process.env
  const mock = env.CHAT_MOCK === '1'
  const enabled = mock || Boolean(env.ANTHROPIC_API_KEY)

  if (req.method === 'GET') return reply(200, { enabled })
  if (req.method !== 'POST') return reply(405, { error: 'Método não permitido.' })
  if (!enabled) return reply(503, { error: 'O chat ainda não está ativo.' })
  if (!deps.skipOrigin && !allowedOrigin(req.headers?.origin, req.headers?.referer)) return reply(403, { error: 'Origem não permitida.' })

  const parsed = parseMessages(req.body)
  if (parsed.error) return reply(400, { error: parsed.error })
  const msgs = parsed.messages

  // Trava 1 (custo zero): recupera trechos do site com as duas últimas perguntas (cobre "e o de fire?").
  const { kb: KB, idx } = load()
  const q = msgs.filter((m) => m.role === 'user').slice(-2).map((m) => m.content).join(' ')
  const r = idx.search(q, 6)
  if (!tokens(q).length || r.known === 0 || !r.hits.length) return reply(200, { answer: REFUSAL, links: [], refused: true })

  const ip = req.headers?.['x-forwarded-for']?.split(',')[0].trim() || req.ip || 'anon'
  const limited = deps.skipLimit ? null : rateLimit(ip)
  if (limited) return reply(429, { error: limited === 'global' ? 'O chat atingiu o limite de hoje. Volte amanhã!' : 'Muitas perguntas seguidas. Espere um pouco.' })

  if (mock) {
    const h = r.hits[0]
    return reply(200, { answer: `[modo teste] ${h.t}: ${String(h.x).slice(0, 220)}…`, links: linksFor([h.id], r.hits, KB) })
  }

  // Trava 2: o modelo só vê os trechos e devolve in_scope + ids de fontes.
  let out
  try {
    const client = deps.client || new Anthropic({ apiKey: env.ANTHROPIC_API_KEY, maxRetries: 1, timeout: 20_000 })
    const msg = await client.messages.parse({
      model: MODEL,
      max_tokens: 600,
      system: SYSTEM,
      messages: buildMessages(msgs, r.hits),
      output_config: { effort: 'low', format: zodOutputFormat(OutputSchema) },
    })
    if (msg.stop_reason === 'refusal') return reply(200, { answer: REFUSAL, links: [], refused: true })
    out = msg.parsed_output
  } catch (e) {
    console.error('chat error', e?.status || '', e?.message || e)
    return reply(502, { error: 'O assistente não respondeu agora. Tente de novo em instantes.' })
  }

  // Trava 3: o servidor decide o que sai. Fora de escopo => texto fixo, nada do modelo passa.
  if (!out || out.in_scope !== true) return reply(200, { answer: REFUSAL, links: [], refused: true })
  const links = linksFor(out.sources, r.hits, KB)
  const answer = String(out.answer || '').replace(/https?:\/\/\S+/g, '').trim().slice(0, 1200)
  if (!answer) return reply(200, { answer: NOT_FOUND, links: [] })
  return reply(200, { answer, links })
}

// Adaptador da Vercel (Node)
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store')
  let body = req.body
  if (typeof body === 'string') { try { body = JSON.parse(body) } catch { body = null } }
  const out = await handleChat({ method: req.method, headers: req.headers, body, ip: req.socket?.remoteAddress })
  res.status(out.status).json(out.json)
}
