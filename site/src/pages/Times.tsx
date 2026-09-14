import { useState } from 'react'
import teams2 from '../data/teams2.json'
import huntsRaw from '../data/hunts.json'
import { findPokemon, typeColor, type Pokemon } from '../lib/data'
import { Note, PokeName, SectionHead, Sprite, TierBadge } from '../components/ui'
import { VideoRefs } from './Videos'

/* ---------- Guia de hunt (Safnaw) ---------- */
type HuntCard = { name: string; hunt: string; tanks: string[]; dps: string[]; otherTanks: string[]; otherDps: string[]; smeargle: string[] }
const hunts = huntsRaw as { source: string; author: string; twitch: string; notes: string[]; elements: HuntCard[]; hunts: HuntCard[] }

/** Nomes do guia são shiny por padrão: tenta "Shiny X" antes de "X" */
const ShinyFirst = ({ name, onOpen }: { name: string; onOpen: (p: Pokemon) => void }) => {
  const starred = / estrelad[oa]$/i.test(name)
  const base = name.replace(/ estrelad[oa]$/i, '')
  const shiny = !/^(shiny|mega) /i.test(base) ? findPokemon(`Shiny ${base}`) : undefined
  const p = shiny ?? findPokemon(base)
  if (!p) return <span className="badge" style={{ padding: '4px 10px' }}>{name}</span>
  return (
    <span className="badge" style={{ padding: '2px 10px 2px 2px', cursor: 'pointer', gap: 6 }} onClick={() => onOpen(p)} title={starred ? 'Estrelado' : undefined}>
      <Sprite p={p} size="sm" />{p.name}{starred && ' ★'}
    </span>
  )
}

const HuntCardView = ({ c, onOpen }: { c: HuntCard; onOpen: (p: Pokemon) => void }) => {
  const color = typeColor(c.name)
  return (
    <div className="card" style={{ borderTop: `4px solid ${color}` }}>
      <div className="card-title">
        <span className="badge type" style={{ background: color }}>{c.name}</span>
        <h3>{c.hunt && c.hunt !== 'Em breve' ? `Hunt: ${c.hunt}` : 'Hunt: em breve'}</h3>
      </div>
      <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <h4 className="muted tiny" style={{ margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>🛡️ Lurar / Tanque (T1)</h4>
          <div className="tags">{c.tanks.map((n) => <ShinyFirst key={n} name={n} onOpen={onOpen} />)}</div>
          {c.otherTanks.length > 0 && <>
            <div className="muted tiny" style={{ margin: '8px 0 4px' }}>Outras opções T1</div>
            <div className="tags">{c.otherTanks.map((n) => <ShinyFirst key={n} name={n} onOpen={onOpen} />)}</div>
          </>}
        </div>
        <div>
          <h4 className="muted tiny" style={{ margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>⚔️ DPS / Dano (SR)</h4>
          <div className="tags">{c.dps.map((n) => <ShinyFirst key={n} name={n} onOpen={onOpen} />)}</div>
          {c.otherDps.length > 0 && <>
            <div className="muted tiny" style={{ margin: '8px 0 4px' }}>Outras opções SR</div>
            <div className="tags">{c.otherDps.map((n) => <ShinyFirst key={n} name={n} onOpen={onOpen} />)}</div>
          </>}
        </div>
      </div>
      {c.smeargle.length > 0 && (
        <div className="tags" style={{ marginTop: 12, alignItems: 'center' }}>
          <span className="muted tiny">🎨 Smeargle:</span>
          {c.smeargle.map((s) => <span key={s} className="badge type" style={{ background: typeColor(s === 'Metal' ? 'Steel' : s === 'Fly' ? 'Flying' : s) }}>{s}</span>)}
        </div>
      )}
    </div>
  )
}

function HuntGuide({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const [tab, setTab] = useState<'elements' | 'hunts'>('elements')
  const [q, setQ] = useState('')
  const s = q.trim().toLowerCase()
  const list = (tab === 'elements' ? hunts.elements : hunts.hunts).filter((c) => !s || c.name.toLowerCase().includes(s) || c.hunt.toLowerCase().includes(s) || [...c.tanks, ...c.dps, ...c.otherTanks, ...c.otherDps].some((n) => n.toLowerCase().includes(s)))
  return (
    <>
      <SectionHead title="Times recomendados por hunt" sub="Qual time usar para caçar cada elemento ou hunt específica: tanques T1 para lurar e Super Rare para o dano. Sem T2 ou T3 na rotação." />
      <div className="credit-doc">
        <span>✍️ Guia escrito por <b>{hunts.author}</b> · <a href={hunts.twitch} target="_blank" rel="noreferrer">twitch.tv/georgezanelato</a></span>
        <a href={hunts.source} target="_blank" rel="noreferrer">Ver planilha original no Google Sheets ↗</a>
      </div>
      <div className="toolbar">
        <button className={`chip orange ${tab === 'elements' ? 'active' : ''}`} onClick={() => setTab('elements')}>Por elemento <small>{hunts.elements.length}</small></button>
        <button className={`chip orange ${tab === 'hunts' ? 'active' : ''}`} onClick={() => setTab('hunts')}>Por hunt específica <small>{hunts.hunts.length}</small></button>
        <label className="search"><span className="ico">⌕</span><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Elemento, hunt ou Pokémon…" /></label>
      </div>
      <div className="grid grid-2">{list.map((c) => <HuntCardView key={c.name} c={c} onOpen={onOpen} />)}</div>
      {!list.length && <div className="empty">Nada encontrado</div>}
      <div style={{ marginTop: 22 }}><Note>{hunts.notes.map((n, i) => <span key={i} style={{ display: 'block', marginBottom: 6 }}>• {n}</span>)}</Note></div>
    </>
  )
}

/* ---------- Guia sem T2/T3 (cabeça do loxas) ---------- */
type Member = { name: string; tier: string; stars: number; offtank: boolean; note: string }
type Team = { element: string; initial: Member[]; upgrades: Member[]; pros: string; cons: string; note: string }
const guide2 = teams2 as { source: string; notes: string[]; teams: Team[]; incomplete: Team[] }

const MemberRow = ({ m, onOpen }: { m: Member; onOpen: (p: Pokemon) => void }) => (
  <div className="link-row">
    <PokeName name={m.name} onOpen={onOpen} />
    <span className="tags" style={{ marginLeft: 'auto' }}>
      {m.stars > 0 && <span className="badge shiny">{'★'.repeat(m.stars)}</span>}
      {m.offtank && <span className="badge mega">Offtank</span>}
      {m.note && <span className="badge" title={m.note}>⚠ {m.note}</span>}
      <TierBadge t={m.tier} />
    </span>
  </div>
)

function LoxasGuide({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const all = [...guide2.teams, ...guide2.incomplete]
  const [sel, setSel] = useState(all[0].element)
  const t = all.find((x) => x.element === sel) ?? all[0]
  const color = typeColor(t.element.split('/')[0])
  return (
    <>
      <SectionHead title="Times sem T2/T3 (lvl 350)" sub="Para quem não quer usar T2 e T3 e ainda está no começo do 350. Times básicos por elemento, só com T1 e Super Rare." />
      <div className="credit-doc">
        <span>✍️ Guia escrito por <b>cabeça do loxas</b>.</span>
        <a href={guide2.source} target="_blank" rel="noreferrer">Ver documento original no Google Docs ↗</a>
      </div>
      <div className="tags" style={{ marginBottom: 18 }}>
        {all.map((x) => {
          const c = typeColor(x.element.split('/')[0])
          const inc = guide2.incomplete.includes(x)
          return (
            <button key={x.element} className={`chip ${sel === x.element ? 'active' : ''}`} style={sel === x.element ? { background: c, boxShadow: `0 4px 14px ${c}66` } : {}} onClick={() => setSel(x.element)}>
              {x.element}{inc && <small>incompleto</small>}
            </button>
          )
        })}
      </div>
      <div className="card" style={{ borderTop: `4px solid ${color}`, maxWidth: 640 }}>
        <div className="card-title"><span className="badge type" style={{ background: color }}>{t.element}</span><h3>Time sugerido</h3><span className="muted small" style={{ marginLeft: 'auto' }}>{t.initial.length} Pokémon</span></div>
        {t.initial.length ? <div className="link-list">{t.initial.map((m, i) => <MemberRow key={i} m={m} onOpen={onOpen} />)}</div> : <p className="muted small" style={{ margin: 0 }}>Sem time completo por enquanto.</p>}
        {t.note && <p className="muted small" style={{ marginBottom: 0 }}>💬 {t.note}</p>}
      </div>
      <div style={{ marginTop: 22 }}>
        <Note>
          {guide2.notes.map((n, i) => <span key={i} style={{ display: 'block', marginBottom: 6 }}>• {n}</span>)}
          <span style={{ display: 'block', marginTop: 8 }} className="small">Legenda: ★ = estrelas recomendadas · Offtank = segura dano · ⚠ = observação do guia.</span>
        </Note>
      </div>
    </>
  )
}

export default function Times({ sub, onOpen }: { sub: string; onOpen: (p: Pokemon) => void }) {
  return <>{sub === 'sem-t2' ? <LoxasGuide onOpen={onOpen} /> : <HuntGuide onOpen={onOpen} />}<VideoRefs topic="times" /></>
}
