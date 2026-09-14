import { useEffect, useMemo, useState } from 'react'
import videosRaw from '../data/videos.json'
import refsRaw from '../data/video_refs.json'
import { Note, SectionHead } from '../components/ui'

export type Video = { id: string; title: string; channel: string; views: number; duration: number; topics: Record<string, number>; lang: string | null }
type Refs = { topics: Record<string, { label: string; route: string }>; refs: Record<string, { id: string; t: number; snippet: string }[]> }
export const videos = videosRaw as unknown as Video[]
export const videoRefs = refsRaw as unknown as Refs
const byId = new Map(videos.map((v) => [v.id, v]))

const fmtViews = (n: number) => (n >= 1e6 ? (n / 1e6).toFixed(1) + 'M' : n >= 1e3 ? Math.round(n / 1e3) + 'k' : String(n))
const fmtDur = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
const fmtT = (s: number) => (s >= 3600 ? `${Math.floor(s / 3600)}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` : fmtDur(s))
const ytUrl = (id: string, t?: number) => `https://www.youtube.com/watch?v=${id}${t ? `&t=${t}s` : ''}`
const thumb = (id: string) => `https://i.ytimg.com/vi/${id}/mqdefault.jpg`
const PRIORITY = ['Empregolista', 'Canal Do Loxas']

const norm = (s: string) => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]+/g, ' ')

/* ---------- Card de vídeo ---------- */
export const VideoCard = ({ v, t, snippet, compact }: { v: Video; t?: number; snippet?: string; compact?: boolean }) => (
  <a className={`vcard ${compact ? 'compact' : ''}`} href={ytUrl(v.id, t)} target="_blank" rel="noreferrer">
    <div className="vthumb">
      <img src={thumb(v.id)} alt="" loading="lazy" />
      <span className="vdur">{t ? `▶ ${fmtT(t)}` : fmtDur(v.duration)}</span>
    </div>
    <div className="vbody">
      <div className="vtitle">{v.title}</div>
      <div className="vmeta">
        <span className={`badge ${PRIORITY.includes(v.channel) ? 'shiny' : ''}`}>{v.channel}</span>
        <span className="muted tiny">👁 {fmtViews(v.views)}</span>
        {v.lang && <span className="muted tiny" title="Transcrição indexada: aparece na busca por pergunta">📝</span>}
      </div>
      {snippet && <div className="vsnip">“…{snippet}…”</div>}
    </div>
  </a>
)

/** Faixa "vídeos de referência" para um tema (usada no FAQ e nos guias) */
export const VideoRefs = ({ topic, max = 3, title }: { topic: string; max?: number; title?: string }) => {
  const refs = (videoRefs.refs[topic] ?? []).slice(0, max)
  if (!refs.length) return null
  return (
    <div className="vrefs">
      <div className="vrefs-title">🎬 {title ?? `Vídeos sobre ${videoRefs.topics[topic]?.label ?? topic}`}</div>
      <div className="vrefs-list">
        {refs.map((r) => { const v = byId.get(r.id); return v ? <VideoCard key={r.id} v={v} t={r.t} snippet={r.snippet} compact /> : null })}
      </div>
    </div>
  )
}

/* ---------- Página ---------- */
export default function Videos({ sub }: { sub: string }) {
  if (sub === 'perguntar') return <Ask />
  if (sub === 'temas') return <Temas />
  if (sub === 'canais') return <Canais />
  return <Ask />
}

function Canais() {
  const rows = useMemo(() => {
    const m = new Map<string, { n: number; views: number; top: Video }>()
    for (const v of videos) {
      const r = m.get(v.channel) ?? { n: 0, views: 0, top: v }
      r.n++; r.views += v.views; if (v.views > r.top.views) r.top = v
      m.set(v.channel, r)
    }
    return [...m.entries()].sort((a, b) => b[1].views - a[1].views)
  }, [])
  return (
    <>
      <SectionHead title="Criadores de conteúdo" sub="Canais que mais falam de PokeAlliance, ordenados pelo total de visualizações dos vídeos sobre o jogo." />
      <div className="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Canal</th><th className="num">Vídeos</th><th className="num">Views (total)</th><th>Vídeo mais visto</th></tr></thead>
          <tbody>
            {rows.map(([c, r], i) => (
              <tr key={c}>
                <td className="muted">{i + 1}</td>
                <td><span className={`badge ${PRIORITY.includes(c) ? 'shiny' : ''}`}>{c}</span></td>
                <td className="num">{r.n}</td>
                <td className="num"><b>{fmtViews(r.views)}</b></td>
                <td style={{ whiteSpace: 'normal', maxWidth: 420 }}><a href={ytUrl(r.top.id)} target="_blank" rel="noreferrer">{r.top.title}</a> <span className="muted tiny">({fmtViews(r.top.views)})</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function Temas() {
  const [sel, setSel] = useState(Object.keys(videoRefs.topics)[0])
  const refs = videoRefs.refs[sel] ?? []
  return (
    <>
      <SectionHead title="Vídeos por tema" sub="Para cada assunto do jogo, os vídeos que mais falam dele, já no minuto certo." />
      <div className="tags" style={{ marginBottom: 18 }}>
        {Object.entries(videoRefs.topics).map(([k, t]) => (
          <button key={k} className={`chip ${sel === k ? 'active' : ''}`} onClick={() => setSel(k)}>{t.label}<small>{(videoRefs.refs[k] ?? []).length}</small></button>
        ))}
      </div>
      <div className="grid grid-3">
        {refs.map((r) => { const v = byId.get(r.id); return v ? <VideoCard key={r.id} v={v} t={r.t} snippet={r.snippet} /> : null })}
      </div>
      {!refs.length && <div className="empty">Nenhum vídeo indexado para este tema ainda.</div>}
      {videoRefs.topics[sel]?.route && videoRefs.topics[sel].route !== 'faq' && (
        <p className="muted small" style={{ marginTop: 16 }}>Ver a seção do site sobre isso: <a href={`#/${videoRefs.topics[sel].route}`}>{videoRefs.topics[sel].label} →</a></p>
      )}
    </>
  )
}

type Chunk = [number, string]
let transcriptsCache: Record<string, Chunk[]> | null = null

function Ask() {
  const [q, setQ] = useState('')
  const [tr, setTr] = useState<Record<string, Chunk[]> | null>(transcriptsCache)
  useEffect(() => {
    if (tr) return
    import('../data/transcripts.json').then((m) => { transcriptsCache = m.default as unknown as Record<string, Chunk[]>; setTr(transcriptsCache) })
  }, [tr])

  const results = useMemo(() => {
    if (!tr) return []
    const terms = norm(q).split(' ').filter((w) => w.length >= 3)
    if (!terms.length) return []
    const out: { v: Video; t: number; snippet: string; score: number }[] = []
    for (const [id, chunks] of Object.entries(tr)) {
      const v = byId.get(id); if (!v) continue
      let best: { t: number; snippet: string; score: number } | null = null
      let total = 0
      chunks.forEach((c, i) => {
        const txt = norm(c[1] + ' ' + (chunks[i + 1]?.[1] ?? ''))
        const sc = terms.reduce((a, w) => a + (txt.includes(w) ? 1 : 0), 0)
        if (sc) { total += sc; if (!best || sc > best.score) best = { t: c[0], snippet: c[1].slice(0, 200), score: sc } }
      })
      if (best && (best as { score: number }).score >= Math.min(terms.length, 2)) {
        const b = best as { t: number; snippet: string; score: number }
        out.push({ v, t: b.t, snippet: b.snippet, score: b.score * 10 + Math.log10(total + 1) * 3 + Math.log10(v.views + 10) + (PRIORITY.includes(v.channel) ? 2 : 0) })
      }
    }
    return out.sort((a, b) => b.score - a.score).slice(0, 24)
  }, [q, tr])

  const suggestions = ['como upar rápido', 'como fazer dinheiro', 'como estrelar pokemon', 'o que fazer no level 150', 'como boostar', 'melhor time', 'shiny máxima broke', 'como ir para hoenn', 'rockets giovanni', 'dungeon shards']
  return (
    <>
      <SectionHead title="Pergunte aos vídeos" sub="Digite uma dúvida e a busca procura dentro das transcrições. O link abre o vídeo no minuto em que o assunto é falado." />
      <div className="toolbar">
        <label className="search" style={{ flex: '1 1 100%' }}><span className="ico">⌕</span><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ex: como estrelar um pokémon, o que fazer no 150, onde caçar…" autoFocus /></label>
      </div>
      {!q.trim() && (
        <div className="tags" style={{ marginBottom: 18 }}>
          {suggestions.map((s) => <button key={s} className="chip" onClick={() => setQ(s)}>{s}</button>)}
        </div>
      )}
      {!tr && <Note>Carregando transcrições…</Note>}
      {q.trim() && tr && !results.length && <div className="empty">Nenhum vídeo fala sobre isso com essas palavras. Tenta reformular.</div>}
      <div className="grid grid-3">
        {results.map((r) => <VideoCard key={r.v.id} v={r.v} t={r.t} snippet={r.snippet} />)}
      </div>
    </>
  )
}
