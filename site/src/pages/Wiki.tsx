import { useEffect, useMemo, useRef, useState } from 'react'
import { marked } from 'marked'
import wikiRaw from '../data/wiki.json'
import { Note, SectionHead } from '../components/ui'

type Page = { path: string; url: string; section: string; sectionLabel: string; icon: string; title: string; summary: string; headings: string[]; md: string }
const wiki = wikiRaw as unknown as { source: string; updated: string; pages: Page[] }

const norm = (s: string) => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '')

marked.setOptions({ gfm: true, breaks: false })

/** reescreve links internos da wiki para abrirem a própria página aqui */
const fixLinks = (html: string) =>
  html
    // links internos da wiki abrem aqui mesmo
    .replace(/href="\/(sistemas|guias|itens|quests|tutoriais|roadmap)\/([^"]+)"/g, 'href="#/wiki/$1/$2"')
    .replace(/href="https?:\/\/wiki\.pokealliance\.com\/(sistemas|guias|itens|quests|tutoriais|roadmap)\/([^"]+)"/g, 'href="#/wiki/$1/$2"')
    // imagens e demais links relativos apontam para a wiki
    .replace(/src="\//g, `src="${wiki.source}/`)
    .replace(/href="\/(?!\/)/g, `href="${wiki.source}/`)
    .replace(/<img /g, '<img loading="lazy" ')
    .replace(/<a href="http/g, '<a target="_blank" rel="noreferrer" href="http')

export default function Wiki({ sub, go }: { sub: string; go: (sec: string, s?: string) => void }) {
  const [q, setQ] = useState('')
  const bodyRef = useRef<HTMLDivElement>(null)

  const page = useMemo(() => wiki.pages.find((p) => p.path === sub), [sub])
  const html = useMemo(() => (page ? fixLinks(marked.parse(page.md) as string) : ''), [page])

  useEffect(() => {
    if (page) window.scrollTo({ top: 0 })
  }, [page])

  const results = useMemo(() => {
    const s = norm(q.trim())
    if (!s) return wiki.pages
    return wiki.pages
      .map((p) => {
        const inTitle = norm(p.title).includes(s)
        const inSum = norm(p.summary).includes(s)
        const inHead = p.headings.some((h) => norm(h).includes(s))
        const body = norm(p.md)
        const hits = inTitle || inSum || inHead || body.includes(s)
        const score = (inTitle ? 100 : 0) + (inHead ? 20 : 0) + (inSum ? 10 : 0) + (body.split(s).length - 1)
        return hits ? { p, score } : null
      })
      .filter(Boolean)
      .sort((a, b) => b!.score - a!.score)
      .map((r) => r!.p)
  }, [q])

  /* ---------- página aberta ---------- */
  if (page) {
    const idx = wiki.pages.findIndex((p) => p.path === page.path)
    const prev = wiki.pages[idx - 1], next = wiki.pages[idx + 1]
    return (
      <>
        <div className="wiki-bar">
          <button className="chip" onClick={() => go('wiki')}>← Todas as páginas</button>
          <span className="badge">{page.icon} {page.sectionLabel}</span>
          <a className="chip" href={page.url} target="_blank" rel="noreferrer">Ver na wiki oficial ↗</a>
        </div>
        <div className="wiki-layout">
          <article className="wiki-doc" ref={bodyRef} dangerouslySetInnerHTML={{ __html: html }} />
          {page.headings.length > 2 && (
            <aside className="wiki-toc">
              <div className="wiki-toc-title">Nesta página</div>
              {page.headings.map((h) => (
                <a key={h} href={`#${h}`} onClick={(e) => {
                  e.preventDefault()
                  const el = [...(bodyRef.current?.querySelectorAll('h2') ?? [])].find((x) => x.textContent?.trim() === h)
                  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }}>{h}</a>
              ))}
            </aside>
          )}
        </div>
        <div className="wiki-nav">
          {prev ? <button className="chip" onClick={() => go('wiki', prev.path)}>← {prev.title}</button> : <span />}
          {next && <button className="chip" onClick={() => go('wiki', next.path)}>{next.title} →</button>}
        </div>
      </>
    )
  }

  /* ---------- índice ---------- */
  const bySection = Object.entries(
    results.reduce<Record<string, Page[]>>((acc, p) => {
      (acc[p.sectionLabel] ??= []).push(p)
      return acc
    }, {}),
  )

  return (
    <>
      <SectionHead
        title="Wiki"
        sub="Todos os guias da wiki oficial do PokeAlliance, com busca no texto inteiro. Atualizado automaticamente."
      />
      <div className="credit-doc">
        <span>📚 Conteúdo da <b>wiki oficial</b>, mantida pelos administradores · {wiki.pages.length} páginas · atualizado em {wiki.updated}</span>
        <a href={wiki.source} target="_blank" rel="noreferrer">Abrir wiki.pokealliance.com ↗</a>
      </div>
      <div className="toolbar">
        <label className="search" style={{ flex: '1 1 100%' }}>
          <span className="ico">⌕</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar em todos os guias: star, boost, helds, prey, guild…" autoFocus />
          {q && <button className="chip" style={{ padding: '2px 8px' }} onClick={() => setQ('')}>✕</button>}
        </label>
        <span className="count">{results.length} de {wiki.pages.length} páginas</span>
      </div>
      {!results.length && <div className="empty">Nada encontrado. Tente outra palavra.</div>}
      {bySection.map(([label, pages]) => (
        <div key={label} style={{ marginBottom: 24 }}>
          <div className="card-title"><h3>{pages[0].icon} {label}</h3><span className="muted small">{pages.length}</span></div>
          <div className="grid grid-3">
            {pages.map((p) => (
              <div className="card wiki-card" key={p.path} onClick={() => go('wiki', p.path)}>
                <h3>{p.title}</h3>
                {p.summary && <p className="muted small">{p.summary}</p>}
                {p.headings.length > 0 && (
                  <div className="tags" style={{ marginTop: 10 }}>
                    {p.headings.slice(0, 3).map((h) => <span key={h} className="badge">{h}</span>)}
                    {p.headings.length > 3 && <span className="badge">+{p.headings.length - 3}</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
      <Note>O conteúdo é da wiki oficial e é copiado automaticamente todos os dias. Em caso de divergência, vale a wiki.</Note>
    </>
  )
}
