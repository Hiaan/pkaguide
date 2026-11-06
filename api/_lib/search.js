// Busca no conteúdo do site (BM25 simples, sem dependências e sem custo de API).
// Também decide se uma pergunta tem a ver com o conhecimento do PKA GUIDE.

export const norm = (s) => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')

const STOP = new Set((
  'a o os as um uma uns umas de do da dos das em no na nos nas por para pra com sem sobre e ou mas que qual quais quem como onde quando porque pq ' +
  'me te se eu tu ele ela nos voce voces meu minha meus minhas seu sua seus suas isso isto esse essa esses essas aquele aquela ' +
  'ser estar ter ha foi sao era vai vou pode posso podem quero queria preciso gostaria tem tenho tinha ja mais menos muito muita pouco ' +
  'tipo coisa coisas bem so tambem ainda entao assim la aqui ai eh e ne dá da dar fazer faz faco fala falar diz dizer me mostra mostrar ' +
  'qual qualquer todo toda todos todas cada algum alguma ao aos num numa pelo pela pelos pelas ate depois antes'
).split(/\s+/))

const stem = (w) => (w.length > 4 && w.endsWith('s') && !w.endsWith('ss') ? w.slice(0, -1) : w)

export function tokens(s) {
  return norm(s).split(/[^a-z0-9]+/).filter((w) => w.length > 1 && !STOP.has(w)).map(stem)
}

export class Index {
  constructor(docs) {
    this.docs = docs
    this.tf = []        // por doc: Map(termo -> peso)
    this.len = []
    this.df = new Map()
    for (const d of docs) {
      const m = new Map()
      const add = (arr, w) => { for (const t of arr) m.set(t, (m.get(t) || 0) + w) }
      add(tokens(d.t), 3)          // título pesa mais
      if (d.g) add(tokens(d.g), 2) // nomes alternativos (ex.: variantes shiny)
      add(tokens(d.x), 1)
      let l = 0
      for (const v of m.values()) l += v
      this.tf.push(m); this.len.push(l)
      for (const t of m.keys()) this.df.set(t, (this.df.get(t) || 0) + 1)
    }
    this.avg = this.len.reduce((a, b) => a + b, 0) / Math.max(1, this.len.length)
    this.N = docs.length
  }

  idf(t) {
    const n = this.df.get(t) || 0
    return Math.log(1 + (this.N - n + 0.5) / (n + 0.5))
  }

  /** devolve os melhores trechos e a qualidade da correspondência */
  search(query, k = 6) {
    const q = [...new Set(tokens(query))]
    const known = q.filter((t) => this.df.has(t))
    const k1 = 1.2, b = 0.75
    const scored = []
    for (let i = 0; i < this.N; i++) {
      const tf = this.tf[i]
      let s = 0, hit = 0
      for (const t of known) {
        const f = tf.get(t)
        if (!f) continue
        hit++
        s += this.idf(t) * ((f * (k1 + 1)) / (f + k1 * (1 - b + (b * this.len[i]) / this.avg)))
      }
      if (s > 0) scored.push({ i, s, hit })
    }
    scored.sort((a, c) => c.s - a.s)
    const top = scored.slice(0, k).map((x) => ({ ...this.docs[x.i], score: x.s, hit: x.hit }))
    // especificidade: o termo mais raro da pergunta que existe na base (palavra comum não prova assunto)
    const rare = known.reduce((m, t) => Math.max(m, this.idf(t)), 0)
    return { hits: top, best: top[0]?.score || 0, rare, terms: q.length, known: known.length }
  }
}
