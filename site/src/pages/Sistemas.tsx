import { useState } from 'react'
import { data, fmt } from '../lib/data'
import { Note, SectionHead, TierBadge } from '../components/ui'

export default function Sistemas({ sub }: { sub: string }) {
  if (sub === 'runes') return <Runes />
  if (sub === 'damage') return <Damage />
  if (sub === 'rates') return <Rates />
  return <Star />
}

/* ---------- STAR (calculadora) ---------- */
const STAR_PCT: Record<string, number> = { T3: 2, T2: 4, T1: 6, 'Super Rare': 8, 'Ultra Rare': 10, Legendary: 15 }

function Star() {
  const [tier, setTier] = useState('Legendary')
  const [from, setFrom] = useState(0)
  const [to, setTo] = useState(2)
  const t = data.star.tiers.find((x) => x.tier === tier)!
  const lo = Math.min(from, to), hi = Math.max(from, to)
  const steps = t.costs.slice(lo, hi)
  const dd = steps.reduce((a, c) => a + c.dd, 0)
  const kk = steps.reduce((a, c) => a + c.kk, 0)
  const pct = STAR_PCT[tier] ?? 0
  return (
    <>
      <SectionHead title="Star Ascension" sub="Calcule quanto custa subir as estrelas de um Pokémon. Valores considerando a opção de 100% de sucesso." />
      <div className="calc">
        <div className="card">
          <div className="field">
            <label>Tier do Pokémon</label>
            <div className="tags">
              {data.star.tiers.map((x) => (
                <button key={x.tier} className={`chip orange ${tier === x.tier ? 'active' : ''}`} onClick={() => setTier(x.tier)}>{x.tier}</button>
              ))}
            </div>
          </div>
          <div className="field">
            <label>Star atual</label>
            <div className="stars">{[0, 1, 2, 3, 4].map((n) => <button key={n} className={`star-btn ${from === n ? 'on' : ''}`} onClick={() => { setFrom(n); if (to <= n) setTo(n + 1) }}>{n === 0 ? '0' : `${n}★`}</button>)}</div>
          </div>
          <div className="field">
            <label>Star objetivo</label>
            <div className="stars">{[1, 2, 3, 4, 5].map((n) => <button key={n} className={`star-btn ${to === n ? 'on' : ''}`} disabled={n <= from} onClick={() => setTo(n)}>{n}★</button>)}</div>
          </div>
          <div className="result">
            <div className="stat hi"><div className="v">{dd} 💎</div><div className="l">Custo total DD</div></div>
            <div className="stat"><div className="v">{kk} 💸</div><div className="l">Custo total KK</div></div>
            <div className="stat"><div className="v">{steps.length}</div><div className="l">Pokés necessários</div></div>
            <div className="stat"><div className="v">+{pct * hi}%</div><div className="l">Dano com {hi}★</div></div>
          </div>
        </div>
        <div>
          <div className="table-wrap" style={{ marginBottom: 16 }}>
            <table>
              <thead><tr><th>Tier</th>{data.star.steps.map((s) => <th key={s} colSpan={2} style={{ textAlign: 'center' }}>{s.replace('star', '★')}</th>)}</tr>
                <tr><th></th>{data.star.steps.map((s) => [<th key={s + 'dd'} className="num">DD</th>, <th key={s + 'kk'} className="num">KK</th>])}</tr></thead>
              <tbody>
                {data.star.tiers.map((x) => (
                  <tr key={x.tier} style={x.tier === tier ? { background: 'rgba(249,115,22,0.08)' } : {}}>
                    <td><TierBadge t={x.tier} /></td>
                    {x.costs.map((c, i) => [
                      <td key={i + 'd'} className="num" style={x.tier === tier && i >= lo && i < hi ? { color: 'var(--orange)', fontWeight: 800 } : {}}>{c.dd}</td>,
                      <td key={i + 'k'} className="num" style={x.tier === tier && i >= lo && i < hi ? { color: 'var(--yellow)', fontWeight: 800 } : {}}>{c.kk}</td>,
                    ])}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Note>{data.star.note}</Note>
        </div>
      </div>
    </>
  )
}

/* ---------- RUNAS ---------- */
function Runes() {
  const r = data.runes
  return (
    <>
      <SectionHead title="Runas" sub="Pontos necessários para subir cada runa e o bônus por nível. Valores com '?' ainda não foram confirmados pela comunidade." />
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Nível</th>{r.stats.map((s) => <th key={s.name} colSpan={2} style={{ textAlign: 'center' }}>{s.name}</th>)}</tr>
            <tr><th></th>{r.stats.map((s) => [<th key={s.name + 'p'} className="num">Pts</th>, <th key={s.name + 'b'} className="num">Bônus</th>])}</tr>
          </thead>
          <tbody>
            {r.levels.map((lv, i) => (
              <tr key={lv}>
                <td><b>{lv.replace('->', '→')}</b></td>
                {r.stats.map((s) => [
                  <td key={s.name + 'p'} className="num">{s.levels[i].points || <span className="muted">—</span>}</td>,
                  <td key={s.name + 'b'} className="num" style={{ color: '#86efac' }}>{s.levels[i].bonus || <span className="muted">—</span>}</td>,
                ])}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small" style={{ marginTop: 12 }}>Shiny Charm: total estimado de {fmt(r.shinyCharmTotal)} pontos até o nível 5.</p>
    </>
  )
}

/* ---------- DANO ---------- */
function Damage() {
  const d = data.damage
  return (
    <>
      <SectionHead title="Dano de referência" sub="DPS esperado por função e tier no lvl 150, sem bônus de attack. Use pra saber se o seu Pokémon está no padrão." />
      <div className="table-wrap">
        <table>
          <thead><tr><th>Função</th>{d.tiers.map((t) => <th key={t} className="num">{t === 'Legandary' ? 'Legendary' : t}</th>)}</tr></thead>
          <tbody>
            {d.roles.map((r) => (
              <tr key={r.role}><td><b>{r.role}</b></td>{r.values.map((v, i) => <td key={i} className="num">{v === '-' ? <span className="muted">—</span> : fmt(Number(v))}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small" style={{ marginTop: 12 }}>{d.note}</p>
    </>
  )
}

/* ---------- SHINY RATE + BROKES ---------- */
function Rates() {
  const sr = data.shinyRate
  const br = data.brokes
  const tiers = sr.columns[0].tiers.map((t) => t.tier)
  return (
    <>
      <SectionHead title="Shiny Rate & Brokes" sub="Média de Pokémon normais por shiny (quanto menor, melhor) e máximo de brokes por tier." />
      <div className="grid grid-2">
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <h3>Normais por shiny, por shiny rate</h3>
          <div className="table-wrap" style={{ boxShadow: 'none' }}>
            <table>
              <thead><tr><th>Tier</th>{sr.columns.map((c) => <th key={c.rate} className="num">Rate {c.rate}</th>)}</tr></thead>
              <tbody>
                {tiers.map((t, i) => (
                  <tr key={t}><td><TierBadge t={t} /></td>{sr.columns.map((c) => <td key={c.rate} className="num">{c.tiers[i].value ?? <span className="muted">—</span>}</td>)}</tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="muted small" style={{ marginBottom: 0 }}>{sr.note} <a href={sr.form} target="_blank" rel="noreferrer">Enviar dados →</a></p>
        </div>
        <div className="card">
          <h3>Máximo de brokes (shiny)</h3>
          <div className="table-wrap" style={{ boxShadow: 'none' }}>
            <table>
              <thead><tr><th>Tier</th><th className="num">Max broke</th></tr></thead>
              <tbody>{br.max.map((m) => <tr key={m.tier}><td><TierBadge t={m.tier} /></td><td className="num"><b>{isNaN(Number(m.max)) ? m.max : fmt(Number(m.max))}</b></td></tr>)}</tbody>
            </table>
          </div>
        </div>
        <Note>{br.note}</Note>
      </div>
    </>
  )
}
