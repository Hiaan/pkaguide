// Testes offline do chat: SDK real + fetch falso (nenhuma chamada de rede, custo zero).
import assert from 'node:assert/strict'
import Anthropic from '@anthropic-ai/sdk'
import { handleChat, MODEL } from '../chat.js'
import { _resetLimits, parseMessages } from '../_lib/guard.js'
import { REFUSAL } from '../_lib/prompt.js'

const ORIGIN = { origin: 'https://pkaguide.vercel.app' }
let n = 0
const ok = (name) => console.log('  ok', ++n, name)

// cliente com fetch falso: guarda o último corpo e devolve o que o teste mandar
function fake(modelJson) {
  const st = { calls: 0, body: null }
  const fetch = async (_url, init) => {
    st.calls++
    st.body = JSON.parse(init.body)
    const text = typeof modelJson === 'function' ? modelJson(st.body) : JSON.stringify(modelJson)
    return new Response(JSON.stringify({
      id: 'msg_x', type: 'message', role: 'assistant', model: MODEL, stop_reason: 'end_turn', stop_sequence: null,
      content: [{ type: 'text', text }], usage: { input_tokens: 10, output_tokens: 10 },
    }), { status: 200, headers: { 'content-type': 'application/json' } })
  }
  return { st, client: new Anthropic({ apiKey: 'sk-test', fetch, maxRetries: 0 }) }
}
const post = (content, deps, extra = {}) =>
  handleChat({ method: 'POST', headers: ORIGIN, body: { messages: [{ role: 'user', content }] }, ...extra }, { env: { ANTHROPIC_API_KEY: 'sk-test' }, ...deps })

// 1) formato do pedido ao modelo
{
  _resetLimits()
  const { st, client } = fake((b) => JSON.stringify({ in_scope: true, answer: 'Resposta.', sources: [] }))
  await post('como funciona o lucky amulet', { client })
  assert.equal(st.calls, 1)
  assert.equal(st.body.model, 'claude-haiku-5-5'); ok('modelo claude-haiku-5-5')
  for (const k of ['temperature', 'top_p', 'top_k', 'thinking']) assert.ok(!(k in st.body), k)
  ok('sem temperature/top_p/top_k/thinking')
  assert.equal(st.body.output_config.effort, 'low')
  assert.equal(st.body.output_config.format.type, 'json_schema'); ok('structured output + effort low')
  assert.ok(st.body.max_tokens <= 600); ok('max_tokens limitado')
  const last = st.body.messages.at(-1).content
  assert.ok(typeof last === 'string' && last.includes('<trechos>') && last.includes('Pergunta do usuário')); ok('contexto vai só na pergunta')
  assert.ok(st.body.system.includes('in_scope=false')); ok('system prompt com regra de escopo')
}

// 2) fora do assunto sem trecho => recusa grátis (modelo nem é chamado)
{
  _resetLimits()
  const { st, client } = fake({ in_scope: true, answer: 'x', sources: [] })
  const r = await post('qual a capital da frança', { client })
  assert.equal(r.status, 200); assert.equal(r.json.answer, REFUSAL); assert.equal(st.calls, 0); ok('sem termos do site: recusa sem chamar a IA')
}

// 3) o modelo marca fora de escopo => texto fixo, resposta dele descartada
{
  _resetLimits()
  const { client } = fake({ in_scope: false, answer: 'Paris é a capital da França.', sources: [1] })
  const r = await post('me escreve um código em python para ordenar uma lista', { client })
  assert.equal(r.json.answer, REFUSAL); assert.deepEqual(r.json.links, []); assert.ok(!JSON.stringify(r.json).includes('Paris'))
  ok('in_scope=false descarta o texto do modelo')
}

// 4) links só dos ids enviados; id inventado e URL no texto são removidos
{
  _resetLimits()
  const { st, client } = fake((b) => {
    const ids = [...b.messages.at(-1).content.matchAll(/<trecho id="(\d+)"/g)].map((m) => Number(m[1]))
    return JSON.stringify({ in_scope: true, answer: 'Veja https://evil.example/x o Lucky Amulet soma.', sources: [999999, ids[0], ids[0]] })
  })
  const r = await post('como funciona o lucky amulet', { client })
  assert.equal(r.status, 200)
  assert.ok(!r.json.answer.includes('http')); ok('URL no texto do modelo é removida')
  assert.equal(r.json.links.length, 1); assert.ok(r.json.links[0].url.startsWith('#/')); ok('links só de ids enviados, sem duplicar, internos')
}

// 5) resposta no escopo sem fontes: ok, sem links
{
  _resetLimits()
  const { client } = fake({ in_scope: true, answer: 'Não encontrei isso no site.', sources: [] })
  const r = await post('qual o limite de broke do t1', { client })
  assert.deepEqual(r.json.links, []); ok('sem fontes => sem links')
}

// 6) falha do modelo => 502 genérico, sem vazar detalhe
{
  _resetLimits()
  const client = new Anthropic({ apiKey: 'sk-test', maxRetries: 0, fetch: async () => new Response('{"error":{"type":"api_error","message":"segredo interno"}}', { status: 500 }) })
  const r = await post('como funciona o boost', { client })
  assert.equal(r.status, 502); assert.ok(!JSON.stringify(r.json).includes('segredo')); ok('erro do provedor => 502 genérico')
}

// 7) origem, método, entrada e limites
{
  _resetLimits()
  const { client } = fake({ in_scope: true, answer: 'a', sources: [] })
  let r = await handleChat({ method: 'POST', headers: { origin: 'https://outro-site.com' }, body: { messages: [{ role: 'user', content: 'boost' }] } }, { env: { ANTHROPIC_API_KEY: 'k' }, client })
  assert.equal(r.status, 403); ok('origem de outro site bloqueada')
  r = await handleChat({ method: 'POST', headers: {}, body: { messages: [{ role: 'user', content: 'boost' }] } }, { env: { ANTHROPIC_API_KEY: 'k' }, client })
  assert.equal(r.status, 403); ok('sem Origin/Referer bloqueada')
  r = await handleChat({ method: 'GET', headers: {} }, { env: {} }); assert.deepEqual(r.json, { enabled: false }); ok('GET sem chave => enabled:false')
  r = await handleChat({ method: 'GET', headers: {} }, { env: { ANTHROPIC_API_KEY: 'k' } }); assert.deepEqual(r.json, { enabled: true }); ok('GET com chave => enabled:true')
  r = await handleChat({ method: 'POST', headers: ORIGIN, body: { messages: [{ role: 'user', content: 'boost' }] } }, { env: {} }); assert.equal(r.status, 503); ok('POST sem chave => 503')
  assert.ok(parseMessages({ messages: [{ role: 'system', content: 'x' }] }).error); ok('role system do cliente rejeitado')
  assert.ok(parseMessages({ messages: [{ role: 'user', content: 'a'.repeat(5000) }] }).messages[0].content.length === 400); ok('pergunta cortada em 400 caracteres')
  assert.ok(parseMessages({ messages: [{ role: 'assistant', content: 'oi' }] }).error); ok('precisa terminar em pergunta do usuário')
  _resetLimits()
  const codes = []
  for (let i = 0; i < 10; i++) codes.push((await post('como funciona o boost', { client }, { headers: { ...ORIGIN, 'x-forwarded-for': '1.2.3.4' } })).status)
  assert.ok(codes.includes(429) && codes.slice(0, 8).every((c) => c === 200)); ok('limite por IP: 8/min, depois 429')
}

// 8) modo mock (sem chave) devolve link interno
{
  _resetLimits()
  const r = await handleChat({ method: 'POST', headers: ORIGIN, body: { messages: [{ role: 'user', content: 'onde eu pego o shiny torterra' }] } }, { env: { CHAT_MOCK: '1' } })
  assert.equal(r.status, 200); assert.ok(r.json.links[0].url.startsWith('#/')); ok('modo mock')
}
console.log(`\n${n} verificações passaram`)
