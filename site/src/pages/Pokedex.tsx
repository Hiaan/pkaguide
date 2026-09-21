import tasksRaw from '../data/tasks.json'
import { RewardChip, type Task } from './Tasks'
const taskDb = tasksRaw as unknown as { source: string; tasks: Task[]; byPokemon: Record<string, { name: string; tasks: number[] }> }
import { useMemo, useState } from 'react'
import { data, TIER_ORDER, TYPE_COLORS, tierRank, type Pokemon } from '../lib/data'
import { Note } from '../components/ui'
import Medals from './Medals'
import { Imgur, PokeCard, PokeName, Search, SectionHead, TierBadge, TypeBadge, sortPoke } from '../components/ui'

type Props = { sub: string; onOpen: (p: Pokemon) => void }

const useFilter = () => {
  const [q, setQ] = useState('')
  const [tier, setTier] = useState('')
  const [type, setType] = useState('')
  const [variant, setVariant] = useState<'all' | 'normal' | 'shiny'>('all')
  const list = useMemo(() => {
    const s = q.trim().toLowerCase()
    return data.pokemon
      .filter((p) => (!s || p.name.toLowerCase().includes(s) || p.drops.some((d) => d.includes(s))))
      .filter((p) => !tier || p.tier === tier)
      .filter((p) => !type || p.type === type)
      .filter((p) => variant === 'all' || (variant === 'shiny') === p.shiny)
      .sort(sortPoke)
  }, [q, tier, type, variant])
  const tiers = TIER_ORDER.filter((t) => data.pokemon.some((p) => p.tier === t))
  const types = Object.keys(TYPE_COLORS).filter((t) => data.pokemon.some((p) => p.type === t))
  const bar = (
    <div className="toolbar">
      <Search value={q} onChange={setQ} placeholder="Nome do Pokémon ou item que dropa…" />
      <select className="select" value={tier} onChange={(e) => setTier(e.target.value)}>
        <option value="">Todos os tiers</option>
        {tiers.map((t) => <option key={t}>{t}</option>)}
      </select>
      <select className="select" value={type} onChange={(e) => setType(e.target.value)}>
        <option value="">Todos os tipos</option>
        {types.map((t) => <option key={t}>{t}</option>)}
      </select>
      <div style={{ display: 'flex', gap: 4 }}>
        {(['all', 'normal', 'shiny'] as const).map((v) => (
          <button key={v} className={`chip orange ${variant === v ? 'active' : ''}`} onClick={() => setVariant(v)}>
            {v === 'all' ? 'Todos' : v === 'normal' ? 'Normal' : '✦ Shiny'}
          </button>
        ))}
      </div>
      <span className="count">{list.length} Pokémon</span>
    </div>
  )
  return { list, bar }
}

export default function Pokedex({ sub, onOpen }: Props) {
  const { list, bar } = useFilter()

  if (sub === 'tierlist') {
    const grouped = TIER_ORDER.map((t) => [t, list.filter((p) => p.tier === t)] as const).filter(([, l]) => l.length)
    return (
      <>
        <SectionHead title="Tier List" sub="Tier e moveset de cada Pokémon. Quanto mais alto o tier, mais raro e mais forte. Clique para abrir a ficha." />
        {bar}
        {grouped.map(([t, l]) => (
          <div key={t} style={{ marginBottom: 22 }}>
            <div className="card-title"><TierBadge t={t} /><span className="muted small">{l.length}</span></div>
            <div className="grid grid-poke">{l.map((p) => <PokeCard key={p.name} p={p} onOpen={onOpen} />)}</div>
          </div>
        ))}
      </>
    )
  }

  if (sub === 'hunts') {
    const rows = list.filter((p) => Object.keys(p.hunts).length)
    return (
      <>
        <SectionHead title="Localizações (Hunts)" sub="Onde caçar cada Pokémon. Wildscape precisa lvl 150+, Hoenn lvl 250+. Os links abrem o mapa no imgur." />
        {bar}
        <div className="table-wrap">
          <table>
            <thead><tr><th>Pokémon</th><th>Tier</th><th>Hunt normal</th><th>Wildscape (150+)</th><th>Hoenn (250+)</th></tr></thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.name}>
                  <td><PokeName name={p.name} onOpen={onOpen} /></td>
                  <td><TierBadge t={p.tier} /></td>
                  <td><Imgur href={p.hunts.normal ?? ''} /></td>
                  <td><Imgur href={p.hunts.wildscape ?? ''} /></td>
                  <td><Imgur href={p.hunts.hoenn ?? ''} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && <div className="empty">Nada encontrado</div>}
      </>
    )
  }

  if (sub.startsWith('simulador')) return <Medals />

  if (sub === 'tasks') {
    const nk = (s: string) => s.toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]+/g, ' ').trim()
    const rows = list.map((p) => ({ p, ts: (taskDb.byPokemon[nk(p.name)]?.tasks ?? []).map((i) => taskDb.tasks[i]) })).filter((r) => r.ts.length)
    return (
      <>
        <SectionHead title="Tasks por Pokémon" sub="Quais NPCs pedem cada Pokémon, quanto precisa derrotar e o que ganha. Fonte: Tasks do Mundo da wiki oficial." />
        {bar}
        <div className="table-wrap">
          <table>
            <thead><tr><th>Pokémon</th><th>Tasks (NPC · região · objetivo · recompensa)</th></tr></thead>
            <tbody>
              {rows.map(({ p, ts }) => (
                <tr key={p.name}>
                  <td><PokeName name={p.name} onOpen={onOpen} /></td>
                  <td>
                    {ts.map((t, i) => {
                      const o = t.objectives.find((x) => nk(x.target) === nk(p.name))
                      return (
                        <div key={i} className="ptask">
                          {t.npcImg && <img src={t.npcImg} alt="" loading="lazy" />}
                          <b>{t.npc}</b>
                          <span className="muted small">{t.region}</span>
                          {o && <span className="chip">{o.text}</span>}
                          {t.objectives.length > 1 && <span className="muted tiny">+{t.objectives.length - 1} objetivo(s)</span>}
                          {t.rewards.map((r, j) => <RewardChip key={j} r={r} />)}
                          {t.loc && <Imgur href={t.loc} label="Local" />}
                        </div>
                      )
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!rows.length && <div className="empty">Nada encontrado</div>}
        <Note>Dados da página <a href={taskDb.source} target="_blank" rel="noreferrer">Tasks do Mundo</a> da wiki PokeAlliance, atualizados todo dia. Para ver a task completa, abra a aba 📋 Tasks.</Note>
      </>
    )
  }

  if (sub === 'medals') {
    const rows = list.filter((p) => p.medal.buff || p.medal.debuff)
    const buffs = [...new Set(rows.map((p) => p.medal.buff!).filter(Boolean))].sort()
    return (
      <>
        <SectionHead title="Medalhas" sub="Cada medalha dá um buff e um debuff. Use a busca por Pokémon ou veja abaixo agrupado por buff." />
        {bar}
        <div className="grid grid-3">
          {buffs.map((b) => (
            <div className="card" key={b}>
              <div className="card-title"><span className="badge ok">▲ {b}</span></div>
              <div className="link-list">
                {rows.filter((p) => p.medal.buff === b).map((p) => (
                  <div className="link-row" key={p.name}>
                    <PokeName name={p.name} onOpen={onOpen} />
                    <span className="badge bad" style={{ marginLeft: 'auto' }}>▼ {p.medal.debuff}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        {!rows.length && <div className="empty">Nada encontrado</div>}
      </>
    )
  }

  // default: pokédex grid
  return (
    <>
      <SectionHead title="Pokédex" sub="Todos os Pokémon da planilha em um só lugar: drops, tier, moveset, hunts, task e medalha. Clique em qualquer card." />
      {bar}
      <div className="grid grid-poke">{list.map((p) => <PokeCard key={p.name} p={p} onOpen={onOpen} />)}</div>
      {!list.length && <div className="empty">Nenhum Pokémon encontrado</div>}
    </>
  )
}

export const tierSorted = (l: Pokemon[]) => [...l].sort((a, b) => tierRank(a.tier) - tierRank(b.tier))
export { TypeBadge }
