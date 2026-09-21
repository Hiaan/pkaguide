import { useEffect, useMemo, useState } from 'react'
import { data } from '../lib/data'
import { Note, SectionHead, Sprite } from '../components/ui'

/* ---------------- atributos ---------------- */
type StatKey = string
const STATS: Record<StatKey, { label: string; group: string; icon: string }> = {
  'Damage Boost': { label: 'Dano', group: 'Combate', icon: '⚔️' },
  'Critical Chance': { label: 'Chance de crítico', group: 'Combate', icon: '🎯' },
  'Critical Damage': { label: 'Dano crítico', group: 'Combate', icon: '💥' },
  'Precision Percent': { label: 'Precisão', group: 'Combate', icon: '🔭' },
  'Life Leech': { label: 'Roubo de vida', group: 'Combate', icon: '🩸' },
  'Defense Boost': { label: 'Defesa', group: 'Defesa', icon: '🛡️' },
  'HP Boost': { label: 'Vida (HP)', group: 'Defesa', icon: '❤️' },
  'Evasion Percent': { label: 'Evasão', group: 'Defesa', icon: '💨' },
  'Critical Resistance': { label: 'Resistência a crítico', group: 'Defesa', icon: '🧱' },
  'Pokemon Speed': { label: 'Velocidade do Pokémon', group: 'Velocidade', icon: '⚡' },
  'Character Speed': { label: 'Velocidade do personagem', group: 'Velocidade', icon: '👟' },
  'Fly Speed': { label: 'Velocidade de Fly', group: 'Velocidade', icon: '🕊️' },
  'Ride Speed': { label: 'Velocidade de Ride', group: 'Velocidade', icon: '🐎' },
  'Surf Speed': { label: 'Velocidade de Surf', group: 'Velocidade', icon: '🌊' },
  'Catch Rate': { label: 'Chance de catch', group: 'Captura e loot', icon: '🔴' },
  'Shiny Catch Rate': { label: 'Catch de shiny', group: 'Captura e loot', icon: '✨' },
  'Shiny Charm Rate': { label: 'Shiny Charm', group: 'Captura e loot', icon: '🍀' },
  'Loot Boost': { label: 'Loot', group: 'Captura e loot', icon: '💰' },
  'Fishing Skill': { label: 'Skill de pesca', group: 'Pesca e Headbutt', icon: '🎣' },
  'Extra Fishing': { label: 'Pesca extra', group: 'Pesca e Headbutt', icon: '🐟' },
  'Shiny Fishing Rate': { label: 'Shiny na pesca', group: 'Pesca e Headbutt', icon: '🌟' },
  'Headbutt Skill': { label: 'Skill de Headbutt', group: 'Pesca e Headbutt', icon: '🌳' },
  'Shiny Headbutt Rate': { label: 'Shiny no Headbutt', group: 'Pesca e Headbutt', icon: '🌠' },
}
const TYPO: Record<string, string> = {
  'critical change': 'Critical Chance', 'critital damage': 'Critical Damage', 'fly spped': 'Fly Speed',
  'hp boost': 'HP Boost', 'pokemon speed': 'Pokemon Speed', 'shing fishing rate': 'Shiny Fishing Rate',
}
const fixStat = (s?: string): StatKey | null => {
  if (!s || !s.trim() || s.trim() === '-') return null
  const k = TYPO[s.trim().toLowerCase()] ?? s.trim()
  return STATS[k] ? k : null
}
const GROUPS = ['Combate', 'Defesa', 'Velocidade', 'Captura e loot', 'Pesca e Headbutt']

/** valores reais observados no nível Bronze (vídeo do Empregolista "Conheci o sistema de medalhas") */
const REF_BRONZE: Record<StatKey, { b?: number; d?: number }> = {
  'Damage Boost': { b: 0.2 },
  'Defense Boost': { b: 0.2 },
  'Shiny Catch Rate': { b: 0.5 },
  'Shiny Charm Rate': { b: 0.4 },
  'Catch Rate': { d: 1 },
  'Evasion Percent': { d: 1 },
  'Surf Speed': { d: 5 },
  'Shiny Headbutt Rate': { d: 4 },
}
/** estimativa de Bronze p/ atributos que o vídeo não mostrou (mesma escala dos parecidos) */
const EST_BRONZE = (k: StatKey): { b: number; d: number } => {
  const g = STATS[k].group
  if (g === 'Velocidade') return { b: 1, d: 5 }
  if (k.startsWith('Shiny')) return { b: 0.5, d: 4 }
  if (g === 'Pesca e Headbutt') return { b: 1, d: 4 }
  return { b: 0.2, d: 1 }
}
/** bônus cresce 1× por nível; penalidade cai até zerar no Orichalcum */
const bonusAt = (base: number, lvl: number) => base * lvl
const penalAt = (base: number, lvl: number) => base * (MAXL - lvl) / (MAXL - 1)
const REF_VIDEO = 'https://www.youtube.com/watch?v=z_wIlJXEU7E&t=455s'

/* ---------------- medalhas ---------------- */
type Medal = { name: string; id: number; buff: StatKey | null; debuff: StatKey | null }
const MEDALS: Medal[] = data.pokemon
  .filter((p) => !p.shiny && !p.mega && p.id && p.id <= 151 && (p.medal?.buff || p.medal?.debuff))
  .map((p) => ({ name: p.name, id: p.id!, buff: fixStat(p.medal.buff), debuff: fixStat(p.medal.debuff) }))
  .sort((a, b) => a.id - b.id)
const BY_NAME = new Map(MEDALS.map((m) => [m.name, m]))
const POKE = new Map(data.pokemon.map((p) => [p.name, p]))

const LEVELS = [
  { n: 'Bronze', c: '#cd7f32' }, { n: 'Silver', c: '#cbd5e1' }, { n: 'Gold', c: '#facc15' },
  { n: 'Diamond', c: '#7dd3fc' }, { n: 'Emerald', c: '#34d399' }, { n: 'Orichalcum', c: '#fb923c' },
]
const MAXL = LEVELS.length

type Slot = { m: string; lvl: number } | null
type Vals = Record<string, { b?: number; d?: number }>

const PRESETS_KEY = 'pka-medal-presets'
const VALS_KEY = 'pka-medal-vals'
const load = <T,>(k: string, d: T): T => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d } catch { return d } }
const save = (k: string, v: unknown) => { try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* sem storage */ } }
const encode = (slots: Slot[]) => slots.map((s) => (s ? `${s.m}.${s.lvl}` : '')).join(',')
const decode = (str: string): Slot[] => {
  const out: Slot[] = Array(10).fill(null)
  str.split(',').slice(0, 10).forEach((x, i) => {
    const [m, l] = x.split('.')
    if (m && BY_NAME.has(m)) out[i] = { m, lvl: Math.min(MAXL, Math.max(1, Number(l) || 1)) }
  })
  return out
}

const GOALS: { id: string; label: string; want: StatKey[]; avoid: StatKey[] }[] = [
  { id: 'dano', label: '⚔️ Dano', want: ['Damage Boost', 'Critical Chance', 'Critical Damage', 'Precision Percent', 'Life Leech'], avoid: ['Damage Boost', 'Critical Chance', 'Critical Damage'] },
  { id: 'tank', label: '🛡️ Tank / Hazard', want: ['Defense Boost', 'HP Boost', 'Evasion Percent', 'Critical Resistance', 'Life Leech'], avoid: ['Defense Boost', 'HP Boost'] },
  { id: 'catch', label: '✨ Caçar shiny', want: ['Shiny Catch Rate', 'Shiny Charm Rate', 'Catch Rate', 'Loot Boost'], avoid: ['Shiny Catch Rate', 'Shiny Charm Rate'] },
  { id: 'loot', label: '💰 Loot', want: ['Loot Boost', 'Damage Boost', 'Pokemon Speed', 'Critical Chance'], avoid: ['Damage Boost', 'Loot Boost'] },
  { id: 'move', label: '🏃 Deslocamento', want: ['Character Speed', 'Fly Speed', 'Ride Speed', 'Surf Speed'], avoid: ['Character Speed', 'Fly Speed'] },
  { id: 'pesca', label: '🎣 Pesca', want: ['Shiny Fishing Rate', 'Shiny Headbutt Rate', 'Shiny Charm Rate'], avoid: ['Shiny Fishing Rate', 'Fishing Skill'] },
]

function autoBuild(goal: (typeof GOALS)[number], lvl: number): Slot[] {
  const want = new Set(goal.want), avoid = new Set(goal.avoid)
  const scored = MEDALS.filter((m) => m.buff && want.has(m.buff)).map((m) => {
    let s = 10 - goal.want.indexOf(m.buff!)
    if (m.debuff && avoid.has(m.debuff)) s -= 14        // tira justamente o que o objetivo mais quer
    else if (m.debuff && want.has(m.debuff)) s -= 10   // tira outro atributo do objetivo
    if (!m.debuff) s += 4                              // sem penalidade nenhuma
    return { m, s }
  }).sort((a, b) => b.s - a.s)
  const picked: Slot[] = [], per: Record<string, number> = {}
  for (const { m } of scored) {
    if (picked.length >= 10) break
    if ((per[m.buff!] ?? 0) >= 3) continue
    per[m.buff!] = (per[m.buff!] ?? 0) + 1
    picked.push({ m: m.name, lvl })
  }
  for (const { m } of scored) { if (picked.length >= 10) break; if (!picked.some((p) => p?.m === m.name)) picked.push({ m: m.name, lvl }) }
  while (picked.length < 10) picked.push(null)
  return picked
}

/* ---------------- página ---------------- */
export default function Medals() {
  const initial = (() => { const m = location.hash.match(/[?&]s=([^&]+)/); return m ? decode(decodeURIComponent(m[1])) : Array(10).fill(null) })()
  const [slots, setSlots] = useState<Slot[]>(initial)
  const [sel, setSel] = useState<number | null>(null)          // espaço selecionado no anel
  const [q, setQ] = useState('')
  const [fBuff, setFBuff] = useState('')
  const [defLvl, setDefLvl] = useState(1)
  const [preset, setPreset] = useState(0)
  const [vals, setVals] = useState<Vals>(() => load(VALS_KEY, {}))
  const [presets, setPresets] = useState<(string | null)[]>(() => load(PRESETS_KEY, [null, null, null, null, null]))
  const [copied, setCopied] = useState(false)
  const [hover, setHover] = useState<string | null>(null)

  useEffect(() => save(VALS_KEY, vals), [vals])
  useEffect(() => save(PRESETS_KEY, presets), [presets])
  useEffect(() => { setPresets((xs) => xs.map((x, j) => (j === preset ? encode(slots) : x))) }, [slots, preset]) // o preset ativo acompanha a montagem

  const used = new Set(slots.filter(Boolean).map((s) => s!.m))
  const filled = slots.filter(Boolean).length
  const setSlot = (i: number, s: Slot) => setSlots((xs) => xs.map((x, j) => (j === i ? s : x)))

  const addMedal = (name: string) => {
    if (used.has(name)) { setSel(slots.findIndex((s) => s?.m === name)); return }
    const i = sel !== null && !slots[sel] ? sel : slots.findIndex((s) => !s)
    if (i < 0) return
    setSlot(i, { m: name, lvl: defLvl }); setSel(i)
  }

  /* ---------- ficha ---------- */
  const result = useMemo(() => {
    type R = { up: number; down: number; ex: number; exact: boolean; ref: boolean; src: { m: string; lvl: number; sign: 1 | -1 }[] }
    const r: Record<StatKey, R> = {}
    const get = (k: StatKey) => (r[k] ??= { up: 0, down: 0, ex: 0, exact: true, ref: false, src: [] })
    for (const s of slots) {
      if (!s) continue
      const med = BY_NAME.get(s.m)!
      const v = vals[`${s.m}:${s.lvl}`] ?? {}
      if (med.buff) {
        const x = get(med.buff); x.up += s.lvl; x.src.push({ m: s.m, lvl: s.lvl, sign: 1 })
        const ref = REF_BRONZE[med.buff]?.b
        if (v.b != null) x.ex += v.b
        else if (ref != null) { x.ex += bonusAt(ref, s.lvl); if (s.lvl > 1) x.exact = false; x.ref = true }
        else { x.ex += bonusAt(EST_BRONZE(med.buff).b, s.lvl); x.exact = false }
      }
      if (med.debuff && s.lvl < MAXL) {
        const x = get(med.debuff); x.down += MAXL - s.lvl; x.src.push({ m: s.m, lvl: s.lvl, sign: -1 })
        const ref = REF_BRONZE[med.debuff]?.d
        if (v.d != null) x.ex -= v.d
        else if (ref != null) { x.ex -= penalAt(ref, s.lvl); if (s.lvl > 1) x.exact = false; x.ref = true }
        else { x.ex -= penalAt(EST_BRONZE(med.debuff).d, s.lvl); x.exact = false }
      }
    }
    return r
  }, [slots, vals])

  const conflicts = Object.entries(result).filter(([, x]) => x.up > 0 && x.down > 0)
  const shareUrl = `${location.origin}${location.pathname}#/sistemas/medals?s=${encodeURIComponent(encode(slots))}`

  const list = MEDALS.filter((m) => {
    const s = q.trim().toLowerCase()
    if (fBuff && m.buff !== fBuff) return false
    if (!s) return true
    return m.name.toLowerCase().includes(s) || String(m.id) === s ||
      (m.buff && STATS[m.buff].label.toLowerCase().includes(s)) || (m.debuff && STATS[m.debuff].label.toLowerCase().includes(s))
  })

  const selSlot = sel !== null ? slots[sel] : null
  const selMed = selSlot ? BY_NAME.get(selSlot.m)! : null
  const hovMed = hover ? BY_NAME.get(hover) : null

  return (
    <>
      <SectionHead title="Simulador de Medalhas" sub="Monte seus 10 emblemas como no painel do jogo e veja na hora como fica o personagem: o que sobe, o que cai e onde uma medalha anula a outra." />

      <div className="md-goals">
        <span className="md-label">Montar sozinho:</span>
        {GOALS.map((g) => <button key={g.id} className="chip" onClick={() => { setSlots(autoBuild(g, defLvl)); setSel(null) }}>{g.label}</button>)}
        <span className="md-label" style={{ marginLeft: 8 }}>Nível:</span>
        {LEVELS.map((l, i) => (
          <button key={l.n} className="chip md-lvl" title={`Deixar todas em ${l.n}`}
            style={defLvl === i + 1 ? { background: l.c, color: '#111', borderColor: l.c } : { borderColor: l.c + '77', color: l.c }}
            onClick={() => { setDefLvl(i + 1); setSlots((xs) => xs.map((s) => (s ? { ...s, lvl: i + 1 } : s))) }}>{l.n}</button>
        ))}
      </div>

      {/* ============ painel no estilo do jogo ============ */}
      <div className="emb">
        <div className="emb-title"><span className="emb-ball" />Emblema Pokémon</div>

        <div className="emb-body">
          {/* esquerda: estatísticas */}
          <div className="emb-stats">
            <div className="emb-h">Estatísticas dos Emblemas</div>
            {!filled && <p className="muted small">Clique num espaço do anel ou numa medalha da direita.</p>}
            {filled > 0 && slots.every((s) => !s || s.lvl <= 2) && <p className="muted tiny" style={{ margin: '0 0 8px' }}>Em Bronze as penalidades pesam mais que os bônus. Troque o nível acima para ver como fica evoluindo.</p>}
            {conflicts.length > 0 && <div className="md-warn">⚠️ Se anulando: {conflicts.map(([k]) => STATS[k].label).join(', ')}</div>}
            {GROUPS.map((g) => {
              const rows = Object.entries(result).filter(([k]) => STATS[k].group === g)
              if (!rows.length) return null
              return (
                <div key={g} className="md-group">
                  <div className="md-gtitle">{g}</div>
                  {rows.sort((a, b) => b[1].ex - a[1].ex).map(([k, x]) => {
                    const net = Math.round(x.ex * 100) / 100
                    return (
                      <div key={k} className="md-stat" title={x.src.map((s) => `${s.sign > 0 ? '▲' : '▼'} ${s.m} (${LEVELS[s.lvl - 1].n})`).join('\n')}>
                        <span className="md-sico">{STATS[k].icon}</span>
                        <span className="md-slabel">{STATS[k].label}</span>
                        <span className={`md-net ${net > 0 ? 'up' : net < 0 ? 'down' : ''}`}>
                          {x.exact ? '' : '~'}{net > 0 ? '+' : ''}{net.toFixed(net % 1 && Math.abs(net * 10) % 1 ? 2 : 1)}%
                        </span>
                      </div>
                    )
                  })}
                </div>
              )
            })}
          </div>

          {/* centro: anel com 10 espaços */}
          <div className="emb-ring-wrap">
            <div className="emb-ring">
              <div className="emb-center"><div className="emb-core" /></div>
              {slots.map((s, i) => {
                const ang = (i / 10) * 2 * Math.PI - Math.PI / 2 + Math.PI / 10
                const x = 50 + 42 * Math.cos(ang), y = 50 + 42 * Math.sin(ang)
                const lv = s ? LEVELS[s.lvl - 1] : null
                const pk = s ? POKE.get(s.m) : null
                return (
                  <button key={i} className={`emb-slot ${s ? 'on' : ''} ${sel === i ? 'sel' : ''}`}
                    style={{ left: `${x}%`, top: `${y}%`, ...(lv ? { boxShadow: `0 0 0 3px ${lv.c}, 0 0 18px ${lv.c}88` } : {}) }}
                    onClick={() => setSel(sel === i ? null : i)} title={s ? `${s.m} · ${lv!.n}` : `Espaço ${i + 1}`}>
                    {s && pk ? <Sprite p={pk} size="sm" /> : <span>+</span>}
                  </button>
                )
              })}
            </div>

            {/* detalhe do espaço selecionado */}
            <div className="emb-detail">
              {selSlot && selMed ? (
                <>
                  <div className="emb-detail-top">
                    <b>{selSlot.m}</b>
                    <button className="chip" onClick={() => { setSlot(sel!, null); setSel(null) }}>Remover</button>
                  </div>
                  <div className="tags" style={{ margin: '6px 0' }}>
                    {LEVELS.map((l, j) => (
                      <button key={l.n} className="chip md-lvl" onClick={() => setSlot(sel!, { ...selSlot, lvl: j + 1 })}
                        style={selSlot.lvl === j + 1 ? { background: l.c, color: '#111', borderColor: l.c } : { borderColor: l.c + '66', color: l.c }}>{l.n}</button>
                    ))}
                  </div>
                  {selMed.buff && <div className="md-eff up">▲ {STATS[selMed.buff].label}</div>}
                  {selMed.debuff && <div className={`md-eff down ${selSlot.lvl === MAXL ? 'zero' : ''}`}>▼ {STATS[selMed.debuff].label}{selSlot.lvl === MAXL ? ' (zerada no Orichalcum)' : ''}</div>}
                  <div className="md-vals">
                    <span className="muted tiny">Valores que o jogo mostra neste nível:</span>
                    <label>+ bônus %<input type="number" step="0.1" value={vals[`${selSlot.m}:${selSlot.lvl}`]?.b ?? ''} placeholder={selSlot.lvl === 1 && selMed.buff && REF_BRONZE[selMed.buff]?.b != null ? String(REF_BRONZE[selMed.buff].b) : ''}
                      onChange={(e) => setVals((o) => ({ ...o, [`${selSlot.m}:${selSlot.lvl}`]: { ...o[`${selSlot.m}:${selSlot.lvl}`], b: e.target.value === '' ? undefined : Number(e.target.value) } }))} /></label>
                    {selMed.debuff && selSlot.lvl < MAXL && (
                      <label>− penal. %<input type="number" step="0.1" value={vals[`${selSlot.m}:${selSlot.lvl}`]?.d ?? ''} placeholder={selSlot.lvl === 1 && REF_BRONZE[selMed.debuff]?.d != null ? String(REF_BRONZE[selMed.debuff].d) : ''}
                        onChange={(e) => setVals((o) => ({ ...o, [`${selSlot.m}:${selSlot.lvl}`]: { ...o[`${selSlot.m}:${selSlot.lvl}`], d: e.target.value === '' ? undefined : Number(e.target.value) } }))} /></label>
                    )}
                  </div>
                </>
              ) : sel !== null ? (
                <span className="muted small">Espaço {sel + 1} vazio: escolha uma medalha à direita.</span>
              ) : hovMed ? (
                <>
                  <b>#{hovMed.id} {hovMed.name}</b>
                  {hovMed.buff && <div className="md-eff up">▲ {STATS[hovMed.buff].label}</div>}
                  {hovMed.debuff ? <div className="md-eff down">▼ {STATS[hovMed.debuff].label}</div> : <div className="muted small">sem penalidade</div>}
                </>
              ) : (
                <span className="muted small">{filled}/10 emblemas · passe o mouse numa medalha para ver o efeito</span>
              )}
            </div>
          </div>

          {/* direita: grade de medalhas */}
          <div className="emb-grid-wrap">
            <div className="emb-search">
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Procurar" />
              <select value={fBuff} onChange={(e) => setFBuff(e.target.value)} title="Filtrar pelo bônus">
                <option value="">Todos os bônus</option>
                {GROUPS.map((g) => (
                  <optgroup key={g} label={g}>
                    {Object.entries(STATS).filter(([, s]) => s.group === g).map(([k, s]) => <option key={k} value={k}>{s.icon} {s.label}</option>)}
                  </optgroup>
                ))}
              </select>
            </div>
            <div className="emb-grid">
              {list.map((m) => {
                const pk = POKE.get(m.name)
                return (
                  <button key={m.name} className={`emb-medal ${used.has(m.name) ? 'used' : ''}`}
                    onMouseEnter={() => setHover(m.name)} onMouseLeave={() => setHover(null)}
                    onClick={() => addMedal(m.name)} title={`#${m.id} ${m.name}\n▲ ${m.buff ? STATS[m.buff].label : '—'}\n▼ ${m.debuff ? STATS[m.debuff].label : 'nenhuma'}`}>
                    {pk && <Sprite p={pk} size="sm" />}
                  </button>
                )
              })}
              {!list.length && <span className="muted small">Nenhuma medalha.</span>}
            </div>
          </div>
        </div>

        <div className="emb-foot">
          <div className="tags">
            <button className="chip" onClick={() => { setSlots(Array(10).fill(null)); setSel(null) }}>Limpar</button>
            <button className="chip" onClick={() => { navigator.clipboard?.writeText(shareUrl); setCopied(true); setTimeout(() => setCopied(false), 1800) }}>
              {copied ? '✓ Link copiado' : '🔗 Compartilhar'}
            </button>
          </div>
          <div className="emb-presets">
            {presets.map((p, i) => (
              <button key={i} className={preset === i ? 'on' : ''} title={p ? `${p.split(',').filter(Boolean).length} emblemas` : 'vazio'}
                onClick={() => { setPreset(i); setSlots(p ? decode(p) : Array(10).fill(null)); setSel(null) }}>{i + 1}</button>
            ))}
          </div>
        </div>
      </div>

      <Note>
        {'Valores sem ~ são exatos, vindos do nível Bronze mostrado no '}
        <a href={REF_VIDEO} target="_blank" rel="noreferrer">vídeo do Empregolista</a>
        {' (dano +0,2%, defesa +0,2%, catch de shiny +0,5%, Shiny Charm +0,4%; penalidades de catch −1%, evasão −1%, surf −5%). Valores com ~ são estimativa: o bônus sobe 1× a cada nível e a penalidade cai até zerar no Orichalcum, e atributos que o vídeo não mostrou usam a escala de um parecido. Digite o valor do painel do jogo na medalha para trocar a estimativa pelo valor real. Regras: 10 espaços, 5 presets, sem repetir medalha, troca só em Protection Zone.'}
      </Note>
    </>
  )
}
