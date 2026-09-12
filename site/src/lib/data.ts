import raw from '../data/data.json'
import imgurRaw from '../data/imgur.json'

export type Pokemon = {
  name: string; base: string; shiny: boolean; mega: boolean; id: number | null
  drops: string[]; tier: string; type: string
  hunts: { normal?: string; wildscape?: string; hoenn?: string }
  tasks: { npc: string; loc: string }[]
  medal: { buff?: string; debuff?: string }
}
export type Den = { name: string; players: string; mobsCount: string; xp: number | string; time: string; mobs: string[]; xph: number | string; items: string[] }
export type Team = { name: string; fights: { npc: string; rec: string }[] }

export type Data = {
  pokemon: Pokemon[]
  items: Record<string, string[]>
  shinyRate: { columns: { rate: number; tiers: { tier: string; value: number | null }[] }[]; note: string; form: string }
  brokes: { note: string; max: { tier: string; max: string }[] }
  star: { note: string; steps: string[]; tiers: { tier: string; costs: { dd: number; kk: number }[] }[] }
  runes: { stats: { name: string; levels: { points: string; bonus: string }[] }[]; levels: string[]; shinyCharmTotal: number }
  damage: { tiers: string[]; roles: { role: string; values: string[] }[]; note: string }
  dungeons: { name: string; loc: string; hunts: string[]; city: string }[]
  dens: Den[]
  porygon: { title: string; text: string }[]
  gym: { note: string; cities: { city: string; tasks: string[]; dungeon: string; leader: string[] }[] }
  rocket: { note: string; teams: Team[]; giovanniNote: string }
  police: { note: string; teams: Team[] }
  linked: { note: string; tasks: { qty: number; pokemon: string; huntType: string; hunt: string; killsPerHour: number | string }[] }
  hazard: { npc: string; loc: string; task: string }[]
  bh: string
  talents: { item: string; pokemon: string; qty: number; type: string; n: number; buff: string }[]
  boost: { type: string; fragment: string; stone: string; items: string[] }[]
  fragments: { brackets: string[]; min: number[]; avg: number[]; max: number[]; note: string }
  faq: { q: string; a: string }[]
}

export const data = raw as unknown as Data

export const byName = new Map<string, Pokemon>(data.pokemon.map((p) => [p.name.toLowerCase(), p]))
export const findPokemon = (name: string) => byName.get(name.toLowerCase()) ?? byName.get(name.toLowerCase().replace(/^sh /, 'shiny '))

export const spriteUrl = (p: { id: number | null; shiny: boolean }) =>
  p.id ? `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/${p.shiny ? 'shiny/' : ''}${p.id}.png` : ''

export const TYPE_COLORS: Record<string, string> = {
  Normal: '#9ca3af', Fire: '#f97316', Water: '#3b82f6', Grass: '#22c55e', Electric: '#facc15', Ice: '#67e8f9',
  Fighting: '#b91c1c', Poison: '#a855f7', Ground: '#d97706', Flying: '#818cf8', Psychic: '#ec4899', Bug: '#84cc16',
  Rock: '#a16207', Ghost: '#6d28d9', Dragon: '#4f46e5', Dark: '#44403c', Steel: '#94a3b8', Fairy: '#f472b6', '?': '#52525b',
}
export const typeColor = (t: string) => TYPE_COLORS[t] ?? '#52525b'

export const TIER_ORDER = ['Mythic', 'Legendary', 'Ultra Rare', 'Super Rare', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'Moveset']
export const TIER_COLORS: Record<string, string> = {
  Mythic: 'linear-gradient(310deg,#e11d48,#f59e0b)', Legendary: 'linear-gradient(310deg,#7c3aed,#ec4899)',
  'Ultra Rare': 'linear-gradient(310deg,#0ea5e9,#8b5cf6)', 'Super Rare': 'linear-gradient(310deg,#0592aa,#22d3ee)',
  T1: '#ea580c', T2: '#d97706', T3: '#ca8a04', T4: '#65a30d', T5: '#16a34a', T6: '#0d9488', T7: '#52525b', Moveset: '#3f3f46',
}
export const tierRank = (t: string) => { const i = TIER_ORDER.indexOf(t); return i < 0 ? 99 : i }

export const fmt = (n: number | string) => (typeof n === 'number' ? n.toLocaleString('pt-BR') : n)

export const linkify = (text: string) =>
  text.split(/(https?:\/\/[^\s]+|(?:www\.|wiki\.|tinyurl\.com|imgur\.com|youtu\.be|discord\.gg)[^\s,)]+)/g)

const imgur = imgurRaw as Record<string, string[]>
/** URLs diretas de imagem para um link imgur (album ou imagem), se ja resolvido */
export const imgurImages = (url: string): string[] => imgur[url] ?? imgur[url.replace(/\/$/, '')] ?? []
