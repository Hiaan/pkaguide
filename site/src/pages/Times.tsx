import { useState } from 'react'
import teamsRaw from '../data/teams.json'
import { typeColor, type Pokemon } from '../lib/data'
import { Note, PokeName, SectionHead, TierBadge } from '../components/ui'

type Member = { name: string; tier: string; stars: number; offtank: boolean; note: string }
type Team = { element: string; initial: Member[]; upgrades: Member[]; pros: string; cons: string; note: string }
const teams = teamsRaw as { source: string; notes: string[]; teams: Team[]; incomplete: Team[] }

const CREDITS = 'Shaolin Pig Slayer (moon), Lucyaya (moon)'

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

export default function Times({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const all = [...teams.teams, ...teams.incomplete]
  const [sel, setSel] = useState(all[0].element)
  const t = all.find((x) => x.element === sel)!
  const color = typeColor(t.element.split('/')[0])
  return (
    <>
      <SectionHead
        title="Times para iniciar Hoenn"
        sub="Sugestões de times mono-elemento baratos para começar em Hoenn (lvl 250+). Não são os times ideais, são os mais acessíveis."
      />
      <div className="credit-doc">
        <span>✍️ Guia escrito por <b>{CREDITS}</b>.</span>
        <a href={teams.source} target="_blank" rel="noreferrer">Ver documento original no Google Docs ↗</a>
      </div>
      <div className="tags" style={{ marginBottom: 18 }}>
        {all.map((x) => {
          const c = typeColor(x.element.split('/')[0])
          const inc = teams.incomplete.includes(x)
          return (
            <button key={x.element} className={`chip ${sel === x.element ? 'active' : ''}`} style={sel === x.element ? { background: c, boxShadow: `0 4px 14px ${c}66` } : {}} onClick={() => setSel(x.element)}>
              {x.element}{inc && <small>incompleto</small>}
            </button>
          )
        })}
      </div>

      <div className="grid grid-2">
        <div className="card" style={{ borderTop: `4px solid ${color}` }}>
          <div className="card-title"><span className="badge type" style={{ background: color }}>{t.element}</span><h3>Time inicial</h3><span className="muted small" style={{ marginLeft: 'auto' }}>{t.initial.length} Pokémon</span></div>
          <div className="link-list">{t.initial.map((m, i) => <MemberRow key={i} m={m} onOpen={onOpen} />)}</div>
          {t.note && <p className="muted small" style={{ marginBottom: 0 }}>{t.note}</p>}
        </div>
        <div style={{ display: 'grid', gap: 14, alignContent: 'start' }}>
          {t.upgrades.length > 0 && (
            <div className="card">
              <div className="card-title"><h3>O que pode melhorar</h3></div>
              <div className="link-list">{t.upgrades.map((m, i) => <MemberRow key={i} m={m} onOpen={onOpen} />)}</div>
            </div>
          )}
          {(t.pros || t.cons) && (
            <div className="grid" style={{ gridTemplateColumns: '1fr' }}>
              {t.pros && <div className="card" style={{ borderLeft: '4px solid #22c55e' }}><b style={{ color: '#86efac' }}>▲ Prós</b><p className="small" style={{ margin: '6px 0 0', lineHeight: 1.55, color: '#d4d4d8' }}>{t.pros}</p></div>}
              {t.cons && <div className="card" style={{ borderLeft: '4px solid #ef4444' }}><b style={{ color: '#fca5a5' }}>▼ Contras</b><p className="small" style={{ margin: '6px 0 0', lineHeight: 1.55, color: '#d4d4d8' }}>{t.cons}</p></div>}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: 22 }}>
        <Note>
          {teams.notes.map((n, i) => <span key={i} style={{ display: 'block', marginBottom: 6 }}>• {n.charAt(0) + n.slice(1).toLowerCase()}</span>)}
          <span style={{ display: 'block', marginTop: 8 }} className="small">Legenda: ★ = estrelas recomendadas · Offtank = segura dano · ⚠ = observação do guia.</span>
        </Note>
      </div>
    </>
  )
}
