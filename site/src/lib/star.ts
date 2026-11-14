/**
 * Conta da Star: a taxa da máquina é paga em CADA fusão, não uma vez por estrela.
 * Para fazer um 5★ do zero: 32 Pokémon 0★ → 16 fusões de 1★, 8 de 2★, 4 de 3★, 2 de 4★ e 1 de 5★.
 * Para fazer um N★ do zero são 2^(N−k) fusões do nível k★.
 *
 * Subir de `from`★ para `to`★ partindo de UM Pokémon já com `from`★: em cada degrau j (from…to−1)
 * é preciso montar outra cópia j★ do zero e fundir as duas.
 */
export type StarCost = { dd: number; kk: number }

/** fusões feitas em cada nível: counts[k-1] = quantas fusões que geram k★ */
export function starFusions(from: number, to: number): number[] {
  const counts = [0, 0, 0, 0, 0]
  const build = (k: number) => { if (k <= 0) return; build(k - 1); build(k - 1); counts[k - 1]++ } // monta um k★ do zero
  if (from === 0) build(to)
  else for (let j = from; j < to; j++) { build(j); counts[j]++ }                                  // outra cópia j★ + fusão
  return counts
}

/** Pokémon 0★ consumidos (no 0★ conta o seu; partindo de 1★+ conta só as cópias novas) */
export function starPokes(from: number, to: number): number {
  if (from === 0) return 2 ** to
  let n = 0
  for (let j = from; j < to; j++) n += 2 ** j
  return n
}

export function starTotal(costs: StarCost[], from: number, to: number) {
  const counts = starFusions(from, to)
  let dd = 0, kk = 0
  counts.forEach((c, i) => { dd += c * (costs[i]?.dd ?? 0); kk += c * (costs[i]?.kk ?? 0) })
  return { dd, kk, counts, pokes: starPokes(from, to) }
}
