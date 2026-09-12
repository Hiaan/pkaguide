import { useState } from 'react'
import { data, findPokemon, fmt, type Pokemon } from '../lib/data'
import { Imgur, Note, PokeName, Search, SectionHead, Sprite } from '../components/ui'

type Props = { sub: string; onOpen: (p: Pokemon) => void }

export default function Dungeons({ sub, onOpen }: Props) {
  if (sub === 'dens') return <Dens onOpen={onOpen} />
  if (sub === 'porygon') return <Porygon />
  return (
    <>
      <SectionHead title="Dungeons (Arcane Shards)" sub="Cada dungeon tem três hunts. Clique no mapa pra ver como chegar." />
      <div className="grid grid-3">
        {data.dungeons.map((d) => (
          <div className="card" key={d.name}>
            <div className="card-title">
              <h3>{d.name}</h3>
              {d.city && <span className="badge">{d.city}</span>}
            </div>
            <div style={{ display: 'flex', gap: 6, marginBottom: 12, justifyContent: 'space-around' }}>
              {d.hunts.map((h) => {
                const p = findPokemon(h)
                return (
                  <div key={h} style={{ textAlign: 'center', cursor: p ? 'pointer' : 'default' }} onClick={() => p && onOpen(p)}>
                    {p ? <Sprite p={p} /> : <div className="sprite-fallback">?</div>}
                    <div className="tiny" style={{ fontWeight: 700 }}>{h}</div>
                  </div>
                )
              })}
            </div>
            <Imgur href={d.loc} label="Como chegar" />
          </div>
        ))}
      </div>
    </>
  )
}

function Dens({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const [q, setQ] = useState('')
  const s = q.trim().toLowerCase()
  const list = data.dens.filter((d) => !s || d.name.toLowerCase().includes(s) || d.mobs.some((m) => m.toLowerCase().includes(s)) || d.items.some((i) => i.toLowerCase().includes(s)))
  const sorted = [...list].sort((a, b) => (Number(b.xph) || 0) - (Number(a.xph) || 0))
  return (
    <>
      <SectionHead title="Dens (Hazard / Mega Dens)" sub="Mobs, XP, tempo e drops de cada den. Ordenado por XP/h. Busque pelo nome, por um mob ou por um item." />
      <div className="toolbar">
        <Search value={q} onChange={setQ} placeholder="Den, mob ou item…" />
        <span className="count">{list.length} dens</span>
      </div>
      <div className="grid grid-2">
        {sorted.map((d) => {
          const p = findPokemon(d.name)
          return (
            <div className="card" key={d.name}>
              <div className="card-title">
                {p && <Sprite p={p} size="sm" />}
                <h3>{d.name}</h3>
                <span className="badge" style={{ marginLeft: 'auto' }}>👥 {d.players || '?'}</span>
              </div>
              <div className="result" style={{ marginBottom: 12, gridTemplateColumns: 'repeat(4, 1fr)' }}>
                <div className="stat" style={{ padding: 10 }}><div className="v" style={{ fontSize: 16 }}>{d.mobsCount || '—'}</div><div className="l">Mobs</div></div>
                <div className="stat" style={{ padding: 10 }}><div className="v" style={{ fontSize: 16 }}>{d.xp ? fmt(d.xp) : '—'}</div><div className="l">XP</div></div>
                <div className="stat" style={{ padding: 10 }}><div className="v" style={{ fontSize: 16 }}>{d.time ? d.time.slice(0, 5) : '—'}</div><div className="l">Tempo</div></div>
                <div className="stat hi" style={{ padding: 10 }}><div className="v" style={{ fontSize: 16 }}>{d.xph ? fmt(Math.round(Number(d.xph) / 1000)) + 'k' : '—'}</div><div className="l">XP/h</div></div>
              </div>
              {d.mobs.length > 0 && (
                <div style={{ marginBottom: 10 }}>
                  <h4 className="muted tiny" style={{ margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Mobs</h4>
                  <div className="tags">{d.mobs.map((m) => <span key={m} className="badge" style={{ padding: '2px 6px 2px 2px' }}><PokeName name={m} onOpen={onOpen} /></span>)}</div>
                </div>
              )}
              {d.items.length > 0 && (
                <div>
                  <h4 className="muted tiny" style={{ margin: '0 0 6px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Drops</h4>
                  <div className="tags">{d.items.map((i) => <span key={i} className="badge item" style={{ cursor: 'default' }}>{i}</span>)}</div>
                </div>
              )}
            </div>
          )
        })}
      </div>
      {!list.length && <div className="empty">Nada encontrado</div>}
    </>
  )
}

function Porygon() {
  return (
    <>
      <SectionHead title="Quest do Porygon (Dr. Vektor)" sub="Passo a passo da dungeon solo do Porygon." />
      <div className="grid grid-2">
        {data.porygon.map((s, i) => (
          <div className="card" key={i} style={s.title.includes('Boss') ? { gridColumn: '1 / -1', borderColor: 'rgba(249,115,22,0.4)' } : {}}>
            <h3>{s.title}</h3>
            <p style={{ margin: 0, whiteSpace: 'pre-line', lineHeight: 1.6, fontSize: 13.5, color: '#d4d4d8' }}>{s.text}</p>
          </div>
        ))}
      </div>
      <Note>Máquina de shards: as dungeons acima dropam arcane shards. Veja como chegar em cada uma na aba Dungeons.</Note>
    </>
  )
}
