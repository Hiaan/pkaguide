import { useEffect, useRef, useState } from 'react'

type Link = { title: string; url: string }
type Msg = { role: 'user' | 'assistant'; content: string; links?: Link[]; error?: boolean }

const SUGGESTIONS = [
  'Como funciona o boost?',
  'Onde eu pego o shiny Torterra?',
  'Qual o melhor Pokémon para iniciantes?',
  'Como faço a Rocket semanal?',
]

// Só aparece quando o servidor informa que o chat está ativo (chave configurada).
export default function ChatWidget() {
  const [enabled, setEnabled] = useState(false)
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [hint, setHint] = useState(false)
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/chat').then((r) => (r.ok ? r.json() : null)).then((j) => setEnabled(!!j?.enabled)).catch(() => setEnabled(false))
  }, [])
  useEffect(() => {
    if (!enabled) return
    let seen = false
    try { seen = sessionStorage.getItem('chat-hint') === '1' } catch { /* sem storage */ }
    if (seen) return
    const t = setTimeout(() => setHint(true), 2500)
    return () => clearTimeout(t)
  }, [enabled])
  const closeHint = () => { setHint(false); try { sessionStorage.setItem('chat-hint', '1') } catch { /* ok */ } }
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }) }, [msgs, busy, open])

  if (!enabled) return null

  const send = async (q: string) => {
    const content = q.trim().slice(0, 400)
    if (!content || busy) return
    const next: Msg[] = [...msgs, { role: 'user', content }]
    setMsgs(next); setText(''); setBusy(true)
    try {
      const history = next.filter((m) => !m.error).slice(-6).map((m) => ({ role: m.role, content: m.content }))
      const r = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ messages: history }) })
      const j = await r.json().catch(() => ({}))
      if (!r.ok) setMsgs([...next, { role: 'assistant', content: j.error || 'Não consegui responder agora.', error: true }])
      else setMsgs([...next, { role: 'assistant', content: j.answer, links: j.links || [] }])
    } catch {
      setMsgs([...next, { role: 'assistant', content: 'Sem conexão com o assistente. Tente de novo.', error: true }])
    } finally { setBusy(false) }
  }

  return (
    <>
      {!open && (
        <div className="chat-launch">
          {hint && (
            <div className="chat-hint" onClick={() => { closeHint(); setOpen(true) }}>
              <button className="chat-hint-x" aria-label="Dispensar" onClick={(e) => { e.stopPropagation(); closeHint() }}>×</button>
              <b>Dúvida sobre o jogo?</b>
              <span>Pergunte ao guia, eu acho a página certa.</span>
            </div>
          )}
          <button className="chat-fab" onClick={() => { closeHint(); setOpen(true) }} aria-label="Abrir o assistente">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="#fff" aria-hidden="true"><path d="M12 2C6.5 2 2 6 2 11c0 2.4 1 4.6 2.7 6.2L4 22l4.3-2.1c1.1.3 2.4.5 3.7.5 5.5 0 10-4 10-9s-4.5-9-10-9z"/></svg>
            {hint && <span className="chat-dot">1</span>}
          </button>
        </div>
      )}
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Assistente do PKA GUIDE">
          <div className="chat-head">
            <b>Assistente do PKA GUIDE</b>
            <button className="chat-x" onClick={() => setOpen(false)} aria-label="Fechar">×</button>
          </div>
          <div className="chat-body">
            {msgs.length === 0 && (
              <div className="chat-hello">
                <p>Pergunte sobre o jogo e eu procuro no conteúdo do site e te mando para a página certa.</p>
                <div className="chat-sugs">{SUGGESTIONS.map((s) => <button key={s} className="chip" onClick={() => send(s)}>{s}</button>)}</div>
              </div>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}${m.error ? ' err' : ''}`}>
                <div className="chat-text">{m.content}</div>
                {m.links && m.links.length > 0 && (
                  <div className="chat-links">
                    {m.links.map((l) => <a key={l.url} className="chip orange" href={l.url} onClick={() => { if (window.innerWidth < 700) setOpen(false) }}>↗ {l.title}</a>)}
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="chat-msg assistant"><div className="chat-text chat-typing">Procurando no site…</div></div>}
            <div ref={end} />
          </div>
          <form className="chat-form" onSubmit={(e) => { e.preventDefault(); send(text) }}>
            <input value={text} maxLength={400} onChange={(e) => setText(e.target.value)} placeholder="Ex.: o que dropa o Charizard?" />
            <button className="btn btn-primary" disabled={busy || !text.trim()}>Enviar</button>
          </form>
          <div className="chat-foot">Só responde com o conteúdo do site. Pode errar: confira na página indicada.</div>
        </div>
      )}
    </>
  )
}
