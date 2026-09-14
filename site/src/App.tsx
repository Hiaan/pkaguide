import { useCallback, useEffect, useMemo, useState } from 'react'
import { data, type Pokemon } from './lib/data'
import { PokeModal, Sprite } from './components/ui'
import Pokedex from './pages/Pokedex'
import Itens from './pages/Itens'
import Sistemas from './pages/Sistemas'
import Dungeons from './pages/Dungeons'
import Desafios from './pages/Desafios'
import FAQ from './pages/FAQ'
import Sugestoes from './pages/Sugestoes'
import Times from './pages/Times'
import Ferramentas from './pages/Ferramentas'
import Videos, { videos as allVideos } from './pages/Videos'

const SECTIONS = [
  { id: 'pokedex', label: 'Pokédex', ico: '🔴', subs: [['grid', 'Pokémon'], ['tierlist', 'Tier List'], ['hunts', 'Localizações'], ['tasks', 'Tasks'], ['medals', 'Medalhas']] },
  { id: 'itens', label: 'Itens', ico: '🎒', subs: [['drops', 'Buscar drop'], ['talents', 'PokeTalents'], ['boost', 'Boost']] },
  { id: 'sistemas', label: 'Sistemas', ico: '⚙️', subs: [['star', 'Star'], ['runes', 'Runas'], ['damage', 'Dano'], ['rates', 'Shiny Rate & Brokes']] },
  { id: 'dungeons', label: 'Dungeons', ico: '🏰', subs: [['list', 'Dungeons'], ['dens', 'Dens'], ['porygon', 'Porygon']] },
  { id: 'desafios', label: 'Desafios', ico: '⚔️', subs: [['gym', 'Ginásios'], ['rocket', 'Rockets'], ['police', 'Polícia'], ['hazard', 'Hazard Tasks'], ['linked', 'Linked Tasks'], ['bh', 'Brotherhood']] },
  { id: 'times', label: 'Times', ico: '🧭', subs: [['hunt', 'Por hunt (Safnaw)'], ['sem-t2', 'Sem T2/T3 (loxas)']] },
  { id: 'videos', label: 'Vídeos', ico: '🎬', subs: [['perguntar', 'Pergunte aos vídeos'], ['temas', 'Por tema'], ['canais', 'Canais']] },
  { id: 'ferramentas', label: 'Ferramentas', ico: '🧰', subs: [] },
  { id: 'faq', label: 'FAQ', ico: '💬', subs: [] },
  { id: 'sugestoes', label: 'Sugestões', ico: '💡', subs: [] },
] as const

type SectionId = (typeof SECTIONS)[number]['id']

const parseHash = (): [SectionId, string] => {
  const [sec = 'pokedex', sub = ''] = location.hash.replace(/^#\/?/, '').split('/').map(decodeURIComponent)
  const s = SECTIONS.find((x) => x.id === sec) ?? SECTIONS[0]
  return [s.id, sub || (s.subs[0]?.[0] ?? '')]
}

export default function App() {
  const [[section, sub], setRoute] = useState(parseHash)
  const [selected, setSelected] = useState<Pokemon | null>(null)
  const [item, setItem] = useState('')
  const [quick, setQuick] = useState('')

  useEffect(() => {
    const h = () => setRoute(parseHash())
    window.addEventListener('hashchange', h)
    return () => window.removeEventListener('hashchange', h)
  }, [])
  const go = useCallback((sec: string, s?: string) => { location.hash = `#/${sec}${s ? '/' + s : ''}`; window.scrollTo({ top: 0 }) }, [])
  const openItem = useCallback((it: string) => { setSelected(null); setItem(it); go('itens', 'drops') }, [go])
  const current = SECTIONS.find((s) => s.id === section)!

  const quickResults = useMemo(() => {
    const s = quick.trim().toLowerCase()
    if (s.length < 2) return []
    const out: { label: string; kind: string; p?: Pokemon; run: () => void }[] = []
    for (const p of data.pokemon) if (p.name.toLowerCase().includes(s)) out.push({ label: p.name, kind: 'Pokémon', p, run: () => setSelected(p) })
    for (const it of Object.keys(data.items)) if (it.includes(s)) out.push({ label: it, kind: 'Item', run: () => openItem(it) })
    for (const f of data.faq) if (f.q.toLowerCase().includes(s)) out.push({ label: f.q, kind: 'FAQ', run: () => go('faq') })
    for (const d of data.dens) if (d.name.toLowerCase().includes(s)) out.push({ label: d.name, kind: 'Den', run: () => go('dungeons', 'dens') })
    for (const v of allVideos.slice(0, 400)) if (v.title.toLowerCase().includes(s)) out.push({ label: v.title, kind: 'Vídeo', run: () => window.open(`https://www.youtube.com/watch?v=${v.id}`, '_blank') })
    return out.slice(0, 14)
  }, [quick, go, openItem])

  return (
    <div className="app">
      <a className="credit" href="https://docs.google.com/spreadsheets/d/1GCH3PmFKQrBj7AA51hgqfg6Q2SrvNgrNlxgIidVeTMU/edit?pli=1&gid=696731486#gid=696731486" target="_blank" rel="noreferrer">
        <span className="credit-ico">📊</span>
        <span>
          <b>FEITO E ATUALIZADO DIARIAMENTE</b> com base na <b>Pokédex Pública PokeAlliance</b> <span className="credit-by">(By Mts Vitor)</span>
          <span className="credit-link">Abrir planilha original →</span>
        </span>
      </a>
      <header className="hero">
        <div className="hero-inner">
          <img className="hero-logo" src="/logo.png" alt="PokeAlliance" />
          <div>
            <h1 className="hero-title">Guia <span>PokeAlliance</span></h1>
            <p className="hero-sub">Pokédex, drops, hunts, tier list, dungeons, gyms, rockets e tudo que a planilha tem, bonito e organizado.</p>
          </div>
          <div className="hero-actions">
            <a className="btn" href="https://discord.gg/pokealliance" target="_blank" rel="noreferrer">Discord</a>
            <a className="btn" href="https://wiki.pokealliance.com" target="_blank" rel="noreferrer">Wiki</a>
            <a className="btn btn-primary" href="https://pokealliance.com" target="_blank" rel="noreferrer">Jogar</a>
          </div>
        </div>
        <div className="hero-search">
          <label className="search" style={{ position: 'relative', zIndex: 41 }}>
            <span className="ico">⌕</span>
            <input value={quick} onChange={(e) => setQuick(e.target.value)} placeholder="Busca rápida: Pokémon, item, den ou dúvida…" onKeyDown={(e) => { if (e.key === 'Enter' && quickResults[0]) { quickResults[0].run(); setQuick('') } if (e.key === 'Escape') setQuick('') }} />
            {quick && <button className="chip" style={{ padding: '2px 8px' }} onClick={() => setQuick('')}>✕</button>}
          </label>
          {quickResults.length > 0 && (
            <div className="quick">
              {quickResults.map((r, i) => (
                <div className="quick-row" key={i} onClick={() => { r.run(); setQuick('') }}>
                  {r.p ? <Sprite p={r.p} size="sm" /> : <span style={{ width: 40, textAlign: 'center' }}>{r.kind === 'Item' ? '🎒' : r.kind === 'Den' ? '🏰' : r.kind === 'Vídeo' ? '🎬' : '💬'}</span>}
                  <span>{r.label}</span>
                  <span className="kind">{r.kind}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </header>

      <nav className="nav">
        <div className="nav-inner">
          {SECTIONS.map((s) => (
            <button key={s.id} className={`nav-item ${section === s.id ? 'active' : ''}`} onClick={() => go(s.id)}>
              <span className="ico">{s.ico}</span>{s.label}
            </button>
          ))}
        </div>
      </nav>

      {current.subs.length > 0 && (
        <div className="subnav">
          {current.subs.map(([id, label]) => (
            <button key={id} className={`chip ${sub === id ? 'active' : ''}`} onClick={() => go(section, id)}>{label}</button>
          ))}
        </div>
      )}

      <main className="main">
        {section === 'pokedex' && <Pokedex sub={sub} onOpen={setSelected} />}
        {section === 'itens' && <Itens sub={sub} onOpen={setSelected} item={item} setItem={setItem} />}
        {section === 'sistemas' && <Sistemas sub={sub} />}
        {section === 'dungeons' && <Dungeons sub={sub} onOpen={setSelected} />}
        {section === 'desafios' && <Desafios sub={sub} onOpen={setSelected} />}
        {section === 'times' && <Times sub={sub} onOpen={setSelected} />}
        {section === 'videos' && <Videos sub={sub} />}
        {section === 'ferramentas' && <Ferramentas />}
        {section === 'faq' && <FAQ />}
        {section === 'sugestoes' && <Sugestoes />}
      </main>

      <footer className="footer">
        <button className="btn btn-primary footer-cta" onClick={() => go('sugestoes')}>💡 Sugestões para melhorar o site? Clique aqui</button>
        <br />
        Feito pela comunidade a partir da <a href="https://docs.google.com/spreadsheets/d/1GCH3PmFKQrBj7AA51hgqfg6Q2SrvNgrNlxgIidVeTMU" target="_blank" rel="noreferrer">planilha pública</a> · Sprites via PokeAPI · Não afiliado oficialmente ao PokeAlliance
      </footer>

      {selected && <PokeModal p={selected} onClose={() => setSelected(null)} onOpen={setSelected} onItem={openItem} />}
    </div>
  )
}
