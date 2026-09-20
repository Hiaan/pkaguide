import { useMemo, useState } from 'react'
import tasksRaw from '../data/tasks.json'
import { findPokemon, type Pokemon } from '../lib/data'
import { Imgur, Note, SectionHead, Sprite } from '../components/ui'

type Obj = { text: string; qty: string; target: string }
type Rew = { kind: string; qty: string; label: string; img: string }
export type Task = { npc: string; npcImg: string; region: string; loc: string; objectives: Obj[]; rewards: Rew[]; alsoFor: string[] }
const db = tasksRaw as unknown as {
  source: string; updated: string; regions: string[]; tasks: Task[]
  byPokemon: Record<string, { name: string; tasks: number[] }>
}

const norm = (s: string) => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]+/g, ' ').trim()

const REGION_ICON: Record<string, string> = { Kanto: '🏙️', Johto: '⛩️', Hoenn: '🌋', 'Tasks Shiny': '✨', 'Outras Tasks': '📌' }

export const RewardChip = ({ r }: { r: Rew }) => (
  <span className={`reward ${r.kind}`}>
    {r.img ? <img src={r.img} alt="" loading="lazy" /> : <b className="reward-xp">XP</b>}
    <span><b>{r.qty}</b>{r.label && <small>{r.label}</small>}</span>
  </span>
)

export const TaskCard = ({ t, onOpen, highlight }: { t: Task; onOpen?: (p: Pokemon) => void; highlight?: string }) => (
  <div className="card task-card">
    <div className="task-head">
      {t.npcImg ? <img className="npc" src={t.npcImg} alt={t.npc} loading="lazy" /> : <div className="npc npc-none">?</div>}
      <div>
        <h3>{t.npc}</h3>
        <div className="tags">
          <span className="badge">{REGION_ICON[t.region] ?? '📍'} {t.region}</span>
          {t.loc && <Imgur href={t.loc} label="Onde fica" />}
        </div>
      </div>
    </div>
    <div className="task-objs">
      {t.objectives.map((o, i) => {
        const p = o.target ? findPokemon(o.target) : undefined
        const on = highlight && norm(o.target) === norm(highlight)
        return (
          <div className={`task-obj ${on ? 'on' : ''}`} key={i} onClick={() => p && onOpen?.(p)} style={{ cursor: p && onOpen ? 'pointer' : 'default' }}>
            {p ? <Sprite p={p} size="sm" /> : <span className="task-dot" />}
            <span>{o.qty ? <><b>{o.qty}x</b> {o.target}</> : o.text}</span>
          </div>
        )
      })}
    </div>
    <div className="task-rewards">
      <div className="task-label">Recompensa</div>
      <div className="rewards">{t.rewards.length ? t.rewards.map((r, i) => <RewardChip key={i} r={r} />) : <span className="muted small">não informada</span>}</div>
    </div>
  </div>
)

export default function Tasks({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const [q, setQ] = useState('')
  const [region, setRegion] = useState('')

  const { list, alvo } = useMemo(() => {
    const s = norm(q)
    let list = db.tasks.map((t, i) => ({ t, i }))
    if (region) list = list.filter((x) => x.t.region === region)
    if (!s) return { list, alvo: '' }
    const exact = db.byPokemon[s]
    const filtered = list.filter(({ t }) =>
      t.objectives.some((o) => norm(o.target).includes(s) || norm(o.text).includes(s)) ||
      norm(t.npc).includes(s) ||
      t.rewards.some((r) => norm(r.label).includes(s)),
    )
    return { list: filtered, alvo: exact ? exact.name : q }
  }, [q, region])

  const sug = useMemo(() => {
    const s = norm(q)
    if (s.length < 2) return []
    return Object.values(db.byPokemon).filter((p) => norm(p.name).includes(s)).slice(0, 8)
  }, [q])

  return (
    <>
      <SectionHead
        title="Tasks do Mundo"
        sub="Digite o nome do Pokémon e veja quais NPCs pedem ele, onde cada um fica e o que você ganha."
      />
      <div className="credit-doc">
        <span>📋 Dados da <b>wiki oficial</b> ({db.tasks.length} tasks) · mapas dos NPCs da planilha pública · atualizado em {db.updated}</span>
        <a href={db.source} target="_blank" rel="noreferrer">Ver na wiki ↗</a>
      </div>

      <div className="toolbar">
        <label className="search" style={{ flex: '1 1 320px' }}>
          <span className="ico">⌕</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Pokémon, NPC ou recompensa: Voltorb, Aaron, Ultra Potion…" autoFocus />
          {q && <button className="chip" style={{ padding: '2px 8px' }} onClick={() => setQ('')}>✕</button>}
        </label>
        <button className={`chip orange ${!region ? 'active' : ''}`} onClick={() => setRegion('')}>Todas</button>
        {db.regions.map((r) => (
          <button key={r} className={`chip orange ${region === r ? 'active' : ''}`} onClick={() => setRegion(r)}>
            {REGION_ICON[r] ?? '📍'} {r}
          </button>
        ))}
        <span className="count">{list.length} tasks</span>
      </div>

      {sug.length > 1 && (
        <div className="tags" style={{ marginBottom: 16 }}>
          {sug.map((p) => {
            const pk = findPokemon(p.name)
            return (
              <button key={p.name} className="chip" onClick={() => setQ(p.name)}>
                {pk && <Sprite p={pk} size="sm" />} {p.name} <small>{p.tasks.length}</small>
              </button>
            )
          })}
        </div>
      )}

      {!list.length && <div className="empty">Nenhuma task encontrada para "{q}".</div>}
      <div className="grid grid-2">
        {list.map(({ t, i }) => <TaskCard key={i} t={t} onOpen={onOpen} highlight={alvo} />)}
      </div>
      <Note>Aceite e entregue a task falando com o NPC. O painel Tasks no jogo (menu superior) só acompanha o progresso.</Note>
    </>
  )
}
