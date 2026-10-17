import { useEffect, useMemo, useState } from 'react'
import { data, findPokemon, fmt } from '../lib/data'
import { Note, SectionHead, TierBadge, TypeIcon } from '../components/ui'

/* =====================================================================
   O que buscar agora: calculadora de custo x ganho de dano.
   Base: vídeo "TOME CUIDADO COM A SUA PROGRESSÃO NO POKE ALLIANCE" (Empregolista)
   e as páginas Boost, Treinamento, Talentos, Medal System e Star da wiki do jogo.
   ===================================================================== */

const VIDEO = 'J5xVz_ylLgE'
const yt = (t = 0) => `https://www.youtube.com/watch?v=${VIDEO}${t ? `&t=${t}s` : ''}`

/* ---------- valores do jogo ---------- */
const STAR_PCT: Record<string, number> = { T3: 2, T2: 4, T1: 6, 'Super Rare': 8, 'Ultra Rare': 10, Legendary: 15 }
const TIERS = ['T7', 'T6', 'T5', 'T4', 'T3', 'T2', 'T1', 'Super Rare', 'Ultra Rare', 'Legendary', 'Mythic']
const DMG_TIER: Record<string, string> = { 'Super Rare': 'SR', 'Ultra Rare': 'UR', Legendary: 'Legandary' }
const RUNE_ATTACK = [0, 2, 4, 6, 8]            // runa de Attack: nível 0 a 4 (+2% por nível)
const TRAIN_PCT = 0.1                          // wiki: Attack +0,1% de dano por nível
/** vídeo: ataque 3 = 16%, ataque 4 = 19%, ataque 5 = 22% (+3% por tier). Os demais seguem o mesmo padrão. */
const heldPct = (t: number) => (t <= 0 ? 0 : 7 + 3 * t)
const HELD_CONFIRMED = new Set([3, 4, 5])
const BOOST_CLASS: Record<string, 'caro' | 'medio' | 'barato'> = { Ground: 'caro', Bug: 'barato', Fairy: 'barato', Dragon: 'barato' }
const MAX_BOOST = 50

const ROLES = data.damage.roles
const baseDamage = (role: string, tier: string): number | null => {
  const r = ROLES.find((x) => x.role === role)
  const i = data.damage.tiers.indexOf(DMG_TIER[tier] ?? tier)
  const v = r && i >= 0 ? Number(r.values[i]) : NaN
  return Number.isFinite(v) ? v : null
}

/* ---------- tipos ---------- */
type Slot = {
  id: string; name: string; tier: string; type: string; role: string
  stars: number; held: number; boost: number; training: number; talent: number
  price: number | null       // preço de 1 cópia no market (kk), para estrelar
  boostKK: number | null     // kk por ponto de boost (se vazio, usa a faixa do elemento)
}
type G = { rune: number; medal: number; guild: number; other: number; mode: 'soma' | 'produto' }
type Prices = {
  held: Record<number, number | null>          // custo (kk) de subir o held do tier N para N+1
  boost: { caro: number; medio: number; barato: number }
  boostPct: number                             // % de dano por ponto de boost
  trainKK: number | null                       // kk por nível de treino de Attack
}

const DEFAULT_G: G = { rune: 0, medal: 0, guild: 0, other: 0, mode: 'soma' }
const DEFAULT_PRICES: Prices = {
  held: { 3: 4.5, 4: 34 },                     // valores citados no vídeo; os outros você preenche
  boost: { caro: 1.4, medio: 0.8, barato: 0.2 },
  boostPct: 0.5,
  trainKK: null,
}

const uid = () => Math.random().toString(36).slice(2, 9)
const newSlot = (p: Partial<Slot> = {}): Slot => ({
  id: uid(), name: '', tier: 'T1', type: '', role: 'DPS HardCC',
  stars: 0, held: 0, boost: 0, training: 0, talent: 0, price: null, boostKK: null, ...p,
})

/* ---------- contas ---------- */
type Part = [string, number]
function parts(s: Slot, g: G, pr: Prices): Part[] {
  return [
    ['Estrelas', s.stars * (STAR_PCT[s.tier] ?? 0)],
    ['Held X-Attack', heldPct(s.held)],
    ['Boost', s.boost * pr.boostPct],
    ['Treino de Attack', s.training * TRAIN_PCT],
    ['Talentos ofensivos', s.talent],
    ['Runas (Attack)', RUNE_ATTACK[g.rune] ?? 0],
    ['Medalhas', g.medal],
    ['Guild', g.guild],
    ['Outros', g.other],
  ]
}
const totalOf = (s: Slot, g: G, pr: Prices) => {
  const p = parts(s, g, pr)
  return g.mode === 'soma' ? p.reduce((a, [, v]) => a + v, 0) : (p.reduce((a, [, v]) => a * (1 + v / 100), 1) - 1) * 100
}

type Opt = { key: string; slot: Slot; label: string; next: Slot; gain: number; rel: number; kk: number | null; dd: number; note: string }

function buildOpts(s: Slot, g: G, pr: Prices, ddKK: number): Opt[] {
  const base = totalOf(s, g, pr)
  const out: Opt[] = []
  const push = (key: string, label: string, next: Slot, kk: number | null, dd: number, note: string) => {
    const after = totalOf(next, g, pr)
    out.push({ key, slot: s, label, next, gain: after - base, rel: ((1 + after / 100) / (1 + base / 100) - 1) * 100, kk, dd, note })
  }

  // Star: precisa de outra cópia do Pokémon (cada estrela dobra o número de cópias) + a taxa da máquina
  const st = data.star.tiers.find((t) => t.tier === s.tier)
  if (st && s.stars < 5) {
    const mc = st.costs[s.stars]
    const copies = 2 ** s.stars
    const kk = s.price === null ? null : s.price * copies + mc.kk + mc.dd * ddKK
    push('star', `Estrela ${s.stars + 1}★`, { ...s, stars: s.stars + 1 }, kk, mc.dd,
      `${copies} cópia${copies > 1 ? 's' : ''} do Pokémon + máquina (${mc.dd} DD e ${mc.kk} kk)`)
  }

  // Held X-Attack: +3% por tier
  if (s.held < 7) {
    push('held', `Held ataque ${s.held + 1}`, { ...s, held: s.held + 1 }, pr.held[s.held] ?? null, 0,
      `${heldPct(s.held)}% → ${heldPct(s.held + 1)}%${HELD_CONFIRMED.has(s.held + 1) ? '' : ' (valor extrapolado)'}`)
  }

  // Boost: sobe até o próximo múltiplo de 5 (uma faixa de pedra)
  if (s.boost < MAX_BOOST) {
    const step = Math.min(MAX_BOOST - s.boost, 5 - (s.boost % 5))
    const cls = BOOST_CLASS[s.type] ?? 'medio'
    const per = s.boostKK ?? pr.boost[cls]
    push('boost', `Boost +${s.boost} → +${s.boost + step}`, { ...s, boost: s.boost + step }, step * per, 0,
      `${step} ponto${step > 1 ? 's' : ''} × ${per.toLocaleString('pt-BR')} kk`)
  }

  // Treino de Attack: +10 níveis
  push('train', `Treino Attack +10 níveis`, { ...s, training: s.training + 10 }, pr.trainKK === null ? null : 10 * pr.trainKK, 0,
    `${s.training} → ${s.training + 10} (+${(10 * TRAIN_PCT).toFixed(1)}%)`)

  return out
}

const per1 = (o: Opt) => (o.kk !== null && o.gain > 0 ? o.kk / o.gain : null)
const sortOpts = (a: Opt, b: Opt) => {
  const x = per1(a), y = per1(b)
  if (x === null && y === null) return 0
  if (x === null) return 1
  if (y === null) return -1
  return x - y
}

/** compra sempre a melhoria com menor custo por +1% até chegar na meta */
function plan(slot: Slot, g: G, pr: Prices, ddKK: number, target: number) {
  let cur = slot, gained = 0, cost = 0
  const steps: { opt: Opt; gained: number; cost: number }[] = []
  for (let i = 0; i < 80 && gained < target; i++) {
    const best = buildOpts(cur, g, pr, ddKK).filter((o) => per1(o) !== null).sort(sortOpts)[0]
    if (!best) break
    gained += best.gain; cost += best.kk ?? 0; cur = best.next
    steps.push({ opt: best, gained, cost })
  }
  return { steps, reached: gained >= target, gained, cost }
}

/* ---------- formatação ---------- */
const fmtKK = (n: number) =>
  n >= 1000 ? (n / 1000).toLocaleString('pt-BR', { maximumFractionDigits: 2 }) + ' kkk' : n.toLocaleString('pt-BR', { maximumFractionDigits: 1 }) + ' kk'
const fmtPct = (n: number, d = 1) => (n > 0 ? '+' : '') + n.toLocaleString('pt-BR', { maximumFractionDigits: d }) + '%'

/* ---------- persistência ---------- */
const KEY = 'pka-prog-v1'
const DD_KEY = 'pka-dd-kk'
type Saved = { slots: Slot[]; g: G; pr: Prices }
const loadSaved = (): Saved | null => { try { const v = localStorage.getItem(KEY); return v ? JSON.parse(v) : null } catch { return null } }
const loadDD = () => { try { return Number(localStorage.getItem(DD_KEY)) || 0 } catch { return 0 } }

/* ---------- pequenas peças ---------- */
function NumIn({ v, on, ph, min = 0, max, step = 1, w = 86 }: { v: number | null; on: (n: number | null) => void; ph?: string; min?: number; max?: number; step?: number; w?: number }) {
  return (
    <input className="pg-in" type="number" inputMode="decimal" min={min} max={max} step={step} value={v ?? ''} placeholder={ph}
      style={{ width: w }} onChange={(e) => on(e.target.value === '' ? null : Math.max(min, max != null ? Math.min(max, Number(e.target.value)) : Number(e.target.value)))} />
  )
}
const Field = ({ l, children, hint }: { l: string; children: React.ReactNode; hint?: string }) => (
  <label className="pg-field"><span>{l}</span>{children}{hint && <small>{hint}</small>}</label>
)

const POKE_NAMES = data.pokemon.filter((p) => p.tier && p.tier !== '?').map((p) => p.name)

/* =====================================================================
   Página
   ===================================================================== */
export default function Progressao() {
  const saved = useMemo(loadSaved, [])
  const [slots, setSlots] = useState<Slot[]>(saved?.slots?.length ? saved.slots : [newSlot()])
  const [g, setG] = useState<G>({ ...DEFAULT_G, ...(saved?.g ?? {}) })
  const [pr, setPr] = useState<Prices>({ ...DEFAULT_PRICES, ...(saved?.pr ?? {}), boost: { ...DEFAULT_PRICES.boost, ...(saved?.pr?.boost ?? {}) } })
  const [ddKK, setDdKK] = useState(loadDD)
  const [target, setTarget] = useState(5)
  const [planId, setPlanId] = useState('')

  useEffect(() => { try { localStorage.setItem(KEY, JSON.stringify({ slots, g, pr })) } catch { /* sem storage */ } }, [slots, g, pr])
  useEffect(() => { try { localStorage.setItem(DD_KEY, String(ddKK)) } catch { /* sem storage */ } }, [ddKK])

  const upd = (id: string, patch: Partial<Slot>) => setSlots((xs) => xs.map((s) => (s.id === id ? { ...s, ...patch } : s)))
  const pick = (id: string, name: string) => {
    const p = findPokemon(name)
    if (p) upd(id, { name: p.name, tier: p.tier && TIERS.includes(p.tier) ? p.tier : 'T1', type: p.type === '?' ? '' : p.type, stars: 0 })
    else upd(id, { name })
  }

  const loadVideoTeam = () => {
    const mk = (name: string, o: Partial<Slot>) => { const p = findPokemon(name); return newSlot({ name: p?.name ?? name, tier: p?.tier ?? 'T1', type: p?.type ?? '', ...o }) }
    setSlots([
      mk('Shiny Steelix', { held: 4, boost: 15, price: 30 }),
      mk('Shiny Marowak', { held: 4, boost: 15, training: 57 }),
      mk('Shiny Nidoqueen', { held: 4, boost: 15 }),
      mk('Shiny Rhydon', { held: 4, boost: 15, stars: 2 }),
      mk('Shiny Pupitar', { held: 4, boost: 18 }),
      mk('Shiny Torterra', { held: 4, boost: 25 }),
    ])
  }

  const all = useMemo(() => slots.filter((s) => s.name).flatMap((s) => buildOpts(s, g, pr, ddKK)).sort(sortOpts), [slots, g, pr, ddKK])
  const priced = all.filter((o) => per1(o) !== null)
  const best = priced[0]
  const planSlot = slots.find((s) => s.id === planId && s.name) ?? slots.find((s) => s.name)
  const pl = useMemo(() => (planSlot ? plan(planSlot, g, pr, ddKK, target) : null), [planSlot, g, pr, ddKK, target])

  return (
    <>
      <SectionHead title="O que buscar agora" sub="Escolha seus Pokémon, diga como eles estão hoje e veja onde cada kk rende mais dano: subir o Held, o Boost, estrelar ou treinar." />

      <div className="pg-credit">
        <span>🎬 Método do vídeo <b>“Tome cuidado com a sua progressão no PokeAlliance”</b> (Empregolista): compare o <b>custo por +1% de dano</b> antes de gastar. Os valores de mercado mudam, então os preços são editáveis.</span>
        <a className="chip" href={yt()} target="_blank" rel="noreferrer">▶ Assistir</a>
      </div>

      {/* ---------- 1. time ---------- */}
      <h3 className="pg-h">1. Seus Pokémon</h3>
      <div className="pg-bar">
        <button className="btn" onClick={() => setSlots((xs) => [...xs, newSlot()])} disabled={slots.length >= 8}>+ Adicionar Pokémon</button>
        <button className="btn" onClick={loadVideoTeam}>📺 Carregar o time do vídeo</button>
        <button className="btn" onClick={() => setSlots([newSlot()])}>Limpar</button>
      </div>
      <datalist id="pg-pokes">{POKE_NAMES.map((n) => <option key={n} value={n} />)}</datalist>

      <div className="pg-slots">
        {slots.map((s) => {
          const p = parts(s, g, pr)
          const tot = totalOf(s, g, pr)
          const base = baseDamage(s.role, s.tier)
          const hasStar = !!data.star.tiers.find((t) => t.tier === s.tier)
          const cls = BOOST_CLASS[s.type] ?? 'medio'
          return (
            <div className="card pg-slot" key={s.id}>
              <div className="pg-slot-head">
                <input className="pg-in pg-name" list="pg-pokes" value={s.name} placeholder="Digite o nome do Pokémon…" onChange={(e) => pick(s.id, e.target.value)} />
                <select className="pg-in" value={s.tier} onChange={(e) => upd(s.id, { tier: e.target.value, stars: 0 })} title="Tier">
                  {TIERS.map((t) => <option key={t}>{t}</option>)}
                </select>
                {s.type && <span className="pg-type"><TypeIcon t={s.type} size={20} /></span>}
                {slots.length > 1 && <button className="pg-x" title="Remover" onClick={() => setSlots((xs) => xs.filter((x) => x.id !== s.id))}>✕</button>}
              </div>

              <div className="pg-grid">
                <Field l={`Estrelas${hasStar ? ` (+${STAR_PCT[s.tier]}% cada)` : ''}`} hint={hasStar ? undefined : 'este tier não tem Star'}>
                  <div className="pg-stars">
                    {[0, 1, 2, 3, 4, 5].map((n) => (
                      <button key={n} className={s.stars === n ? 'on' : ''} disabled={!hasStar && n > 0} onClick={() => upd(s.id, { stars: n })}>{n === 0 ? '0' : `${n}★`}</button>
                    ))}
                  </div>
                </Field>
                <Field l="Held X-Attack" hint={s.held ? `+${heldPct(s.held)}% de dano` : 'sem held de ataque'}>
                  <select className="pg-in" value={s.held} onChange={(e) => upd(s.id, { held: Number(e.target.value) })}>
                    <option value={0}>Nenhum</option>
                    {[1, 2, 3, 4, 5, 6, 7].map((t) => <option key={t} value={t}>Ataque {t} ({heldPct(t)}%{HELD_CONFIRMED.has(t) ? '' : '~'})</option>)}
                  </select>
                </Field>
                <Field l="Boost" hint={`+${(s.boost * pr.boostPct).toLocaleString('pt-BR')}% de dano`}>
                  <NumIn v={s.boost} on={(n) => upd(s.id, { boost: n ?? 0 })} max={MAX_BOOST} w={70} />
                </Field>
                <Field l="Treino de Attack (nível)" hint={`+${(s.training * TRAIN_PCT).toLocaleString('pt-BR', { maximumFractionDigits: 1 })}% de dano`}>
                  <NumIn v={s.training} on={(n) => upd(s.id, { training: n ?? 0 })} w={70} />
                </Field>
                <Field l="Talentos ofensivos do elemento (%)" hint="até 29% na wiki">
                  <NumIn v={s.talent} on={(n) => upd(s.id, { talent: n ?? 0 })} max={29} w={70} />
                </Field>
                <Field l="Função (dano de referência)">
                  <select className="pg-in" value={s.role} onChange={(e) => upd(s.id, { role: e.target.value })}>
                    {ROLES.map((r) => <option key={r.role}>{r.role}</option>)}
                  </select>
                </Field>
                {hasStar && (
                  <Field l="Preço de 1 cópia no market (kk)" hint="usado para estrelar">
                    <NumIn v={s.price} on={(n) => upd(s.id, { price: n })} ph="ex.: 30" step={0.5} w={90} />
                  </Field>
                )}
                <Field l={`kk por ponto de Boost`} hint={`vazio = padrão da faixa ${cls}`}>
                  <NumIn v={s.boostKK} on={(n) => upd(s.id, { boostKK: n })} ph={String(pr.boost[cls])} step={0.1} w={90} />
                </Field>
              </div>

              <div className="pg-sum">
                <div className="pg-sum-top">
                  <span>Bônus de dano total</span>
                  <b>{fmtPct(tot)}</b>
                  {base !== null && <span className="muted small">≈ {fmt(Math.round(base * (1 + tot / 100)))} de dano (base {fmt(base)} no lvl 150)</span>}
                </div>
                <div className="pg-parts">
                  {p.filter(([, v]) => v > 0).map(([l, v]) => <span key={l}>{l} <b>{fmtPct(v)}</b></span>)}
                  {p.every(([, v]) => v === 0) && <span className="muted">nenhum bônus informado ainda</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* ---------- 2. bônus do personagem ---------- */}
      <h3 className="pg-h">2. Bônus que valem para todos</h3>
      <div className="card pg-global">
        <div className="pg-grid">
          <Field l="Runa de Attack" hint={`+${RUNE_ATTACK[g.rune]}% de dano`}>
            <select className="pg-in" value={g.rune} onChange={(e) => setG({ ...g, rune: Number(e.target.value) })}>
              {RUNE_ATTACK.map((v, i) => <option key={i} value={i}>Nível {i} (+{v}%)</option>)}
            </select>
          </Field>
          <Field l="Medalhas — Damage Boost (%)" hint="some no simulador de medalhas">
            <NumIn v={g.medal} on={(n) => setG({ ...g, medal: n ?? 0 })} step={0.1} w={80} />
          </Field>
          <Field l="Benefício de Guild (%)" hint="veja no painel da Guild">
            <NumIn v={g.guild} on={(n) => setG({ ...g, guild: n ?? 0 })} step={0.5} w={80} />
          </Field>
          <Field l="Outros bônus (%)" hint="buffs, eventos, etc.">
            <NumIn v={g.other} on={(n) => setG({ ...g, other: n ?? 0 })} step={0.5} w={80} />
          </Field>
          <Field l="1 DD vale quantos kk?" hint="para somar a taxa da Star">
            <NumIn v={ddKK || null} on={(n) => setDdKK(n ?? 0)} ph="ex.: 45" w={80} />
          </Field>
          <Field l="Como os bônus se combinam" hint="o jogo não diz; o vídeo soma">
            <select className="pg-in" value={g.mode} onChange={(e) => setG({ ...g, mode: e.target.value as G['mode'] })}>
              <option value="soma">Somam (como no vídeo)</option>
              <option value="produto">Multiplicam</option>
            </select>
          </Field>
        </div>
      </div>

      {/* ---------- 3. preços ---------- */}
      <h3 className="pg-h">3. Preços e valores (edite com o que você vê no market)</h3>
      <div className="card pg-global">
        <div className="pg-grid">
          {[3, 4, 5, 6].map((t) => (
            <Field key={t} l={`Held ataque ${t} → ${t + 1} (kk)`} hint={HELD_CONFIRMED.has(t) && pr.held[t] != null && DEFAULT_PRICES.held[t] != null ? 'valor do vídeo' : undefined}>
              <NumIn v={pr.held[t] ?? null} on={(n) => setPr({ ...pr, held: { ...pr.held, [t]: n } })} ph="preço" step={0.5} w={86} />
            </Field>
          ))}
          <Field l="Boost: elemento caro (kk/ponto)" hint="Ground ≈ 1,4 no vídeo">
            <NumIn v={pr.boost.caro} on={(n) => setPr({ ...pr, boost: { ...pr.boost, caro: n ?? 0 } })} step={0.1} w={80} />
          </Field>
          <Field l="Boost: elemento médio (kk/ponto)" hint="estimado">
            <NumIn v={pr.boost.medio} on={(n) => setPr({ ...pr, boost: { ...pr.boost, medio: n ?? 0 } })} step={0.1} w={80} />
          </Field>
          <Field l="Boost: elemento barato (kk/ponto)" hint="Bug, Fairy, Dragon ≈ 0,2">
            <NumIn v={pr.boost.barato} on={(n) => setPr({ ...pr, boost: { ...pr.boost, barato: n ?? 0 } })} step={0.1} w={80} />
          </Field>
          <Field l="Dano por ponto de Boost (%)" hint="vídeo: cerca de 0,5%">
            <NumIn v={pr.boostPct} on={(n) => setPr({ ...pr, boostPct: n ?? 0.5 })} step={0.05} w={80} />
          </Field>
          <Field l="Treino: kk por nível" hint="cargas do Punching Bag">
            <NumIn v={pr.trainKK} on={(n) => setPr({ ...pr, trainKK: n })} ph="preço" step={0.1} w={80} />
          </Field>
        </div>
        <p className="muted small" style={{ margin: '10px 2px 0' }}>
          Dica do vídeo: em Pokémon de <b>duplo elemento</b>, veja qual das duas pedras está mais barata e use o preço dela. Elemento Ground é dos mais caros do jogo; Bug, Fairy e Dragon são bem baratos.
        </p>
      </div>

      {/* ---------- 4. resultado ---------- */}
      <h3 className="pg-h">4. O que comprar primeiro</h3>
      {!all.length && <div className="empty">Escolha pelo menos um Pokémon acima para ver o ranking.</div>}
      {best && (
        <div className="pg-best">
          <span>🏆 Melhor custo-benefício agora</span>
          <b>{best.slot.name}: {best.label}</b>
          <span>{fmtPct(best.gain)} de dano por {fmtKK(best.kk ?? 0)} — <b>{fmtKK(per1(best) ?? 0)} por +1%</b></span>
        </div>
      )}
      {all.length > 0 && (
        <div className="table-wrap">
          <table className="pg-table">
            <thead><tr><th>#</th><th>Pokémon</th><th>Melhoria</th><th className="num">Ganho</th><th className="num">No dano total</th><th className="num">Custo</th><th className="num">Custo por +1%</th></tr></thead>
            <tbody>
              {all.map((o, i) => {
                const c = per1(o)
                const rank = c === null ? null : priced.indexOf(o) + 1
                return (
                  <tr key={o.slot.id + o.key} className={rank === 1 ? 'pg-first' : c === null ? 'pg-nop' : ''}>
                    <td className="muted">{rank ?? '—'}</td>
                    <td><b>{o.slot.name}</b> <TierBadge t={o.slot.tier} /></td>
                    <td>{o.label}<small className="pg-note">{o.note}</small></td>
                    <td className="num">{fmtPct(o.gain, 2)}</td>
                    <td className="num muted">{fmtPct(o.rel, 2)}</td>
                    <td className="num">{o.kk === null ? <span className="muted">informe o preço</span> : <>{fmtKK(o.kk)}{o.dd > 0 && <small className="pg-note">{o.dd} DD{ddKK ? ' já somados' : ' fora da conta'}</small>}</>}</td>
                    <td className="num">{c === null ? <span className="muted">—</span> : <b>{fmtKK(c)}</b>}</td>
                    <td style={{ display: 'none' }}>{i}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="muted small" style={{ marginTop: 8 }}>
        “Ganho” é em pontos percentuais de dano (como o vídeo conta: Star 6%, Held 3%); “No dano total” é o aumento sobre o dano que o Pokémon já tem hoje.
        Opções sem preço ficam no fim: preencha os campos de cima para elas entrarem no ranking.
      </p>

      {/* ---------- 5. planejador ---------- */}
      <h3 className="pg-h">5. Quanto custa chegar na meta?</h3>
      <div className="card">
        <div className="pg-grid" style={{ marginBottom: 6 }}>
          <Field l="Pokémon">
            <select className="pg-in" value={planSlot?.id ?? ''} onChange={(e) => setPlanId(e.target.value)}>
              {slots.filter((s) => s.name).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </Field>
          <Field l="Quero ganhar mais (% de dano)">
            <NumIn v={target} on={(n) => setTarget(n ?? 0)} step={0.5} w={80} />
          </Field>
        </div>
        {!planSlot && <p className="muted">Escolha um Pokémon acima.</p>}
        {pl && planSlot && (
          pl.steps.length ? (
            <>
              <ol className="pg-plan">
                {pl.steps.map((st, i) => (
                  <li key={i}>
                    <span className="pg-plan-n">{i + 1}</span>
                    <div><b>{st.opt.label}</b><small className="pg-note">{st.opt.note}</small></div>
                    <span className="num">{fmtKK(st.opt.kk ?? 0)}</span>
                    <span className="num muted">{fmtPct(st.gained)} acumulado</span>
                  </li>
                ))}
              </ol>
              <div className="pg-plan-sum">
                {pl.reached ? '✅' : '⚠️'} Para {fmtPct(pl.gained)} a mais em <b>{planSlot.name}</b>: <b>{fmtKK(pl.cost)}</b>
                {!pl.reached && <span className="muted"> (as opções com preço acabaram antes da meta de {fmtPct(target)}; preencha mais preços)</span>}
              </div>
            </>
          ) : <p className="muted">Nenhuma melhoria com preço para este Pokémon. Preencha os preços acima.</p>
        )}
      </div>

      {/* ---------- o que o vídeo ensina ---------- */}
      <h3 className="pg-h">O que o vídeo ensina</h3>
      <div className="pg-lessons">
        {[
          ['Meça antes de gastar', 'Bata no dummy do Trainer com o Hunt Analyzer e veja se o dano da sua rotação já fecha. A meta da rotação 2-2-2 no exemplo do vídeo é cerca de 560 mil.', 1070],
          ['Star: +6% por estrela em T1 e +8% em Super Rare', 'Para estrelar um Shiny Steelix o vídeo contou ~36 a 37 kk (Pokémon a 30 kk + máquina ~6 kk) por +6%. Em Super Rare a conta passa de 100 kk, e muitas vezes vale mais um Held ataque 5 ou 6.', 302],
          ['Held X-Attack: +3% por tier', 'Ataque 3 = 16%, ataque 4 = 19%, ataque 5 = 22%. Subir do 3 para o 4 custa ~4,5 kk (baratíssimo). Do 4 para o 5, ~34 kk por +3%: aí o Boost já ganha.', 363],
          ['Boost: cerca de 0,5% por ponto', 'Na wiki, 1 ponto de Boost equivale a 3 níveis no cálculo de dano (+50 = 150 níveis). No vídeo, +15→+25 num Steelix custou ~14 kk por ~5% e o time todo (+15→+25) saiu por ~58 kk para ~5% em cada Pokémon.', 442],
          ['Treino de Attack: +0,1% por nível', 'Barato e rápido até uns 30 a 35 níveis; depois o Pokémon precisa ficar treinando. O vídeo deixou o treino fora da conta, por isso aqui o preço é opcional.', 253],
          ['Cuidado com Super Rare ou mais', 'Estrelar custa muito; quase sempre é mais barato subir Boost e Held. Só estrele quando não restar opção melhor.', 679],
        ].map(([t, d, s]) => (
          <div className="card" key={t as string}>
            <h4>{t}</h4>
            <p>{d}</p>
            <a href={yt(s as number)} target="_blank" rel="noreferrer">▶ trecho no vídeo</a>
          </div>
        ))}
      </div>

      <Note>
        Valores confirmados no vídeo e na wiki: Star por tier, ataque do Held 3/4/5, 0,1% por nível de treino e a regra do Boost. <b>Extrapolados</b> (marcados com ~): Held ataque 1, 2, 6 e 7 seguem o mesmo +3% por tier. <b>Estimativas minhas</b>: preço por ponto de Boost em elementos médios, e os preços de Held acima do ataque 5. O jogo não informa se Star, Held, Boost e treino somam ou multiplicam; por padrão a calculadora soma, como o vídeo faz.
        Fontes: <a href="https://wiki.pokealliance.com/sistemas/boost" target="_blank" rel="noreferrer">Boost</a>, <a href="https://wiki.pokealliance.com/sistemas/treinamento" target="_blank" rel="noreferrer">Treinamento</a>, <a href="https://wiki.pokealliance.com/sistemas/talentos" target="_blank" rel="noreferrer">Talentos</a> e <a href="https://wiki.pokealliance.com/sistemas/helds" target="_blank" rel="noreferrer">Helds</a> da wiki.
      </Note>
    </>
  )
}
