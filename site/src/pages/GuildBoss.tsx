import { useState } from 'react'
import { findPokemon, type Pokemon } from '../lib/data'
import { Note, SectionHead, Sprite } from '../components/ui'

const VIDEO_ID = 'xPftbPsswsk'
const yt = (t: number) => `https://www.youtube.com/watch?v=${VIDEO_ID}&t=${t}s`
const img = (n: string) => `/guildboss/${n}.jpg`

/* ---------- componentes ---------- */
const Shot = ({ n, cap, t, onOpen }: { n: string; cap: string; t?: number; onOpen: (src: string, cap: string) => void }) => (
  <figure className="shot" onClick={() => onOpen(img(n), cap)}>
    <img src={img(n)} alt={cap} loading="lazy" />
    <figcaption>{cap}{t !== undefined && <a href={yt(t)} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}> · ver no vídeo ▶</a>}</figcaption>
  </figure>
)

const Poke = ({ name, role, onOpen }: { name: string; role?: string; onOpen: (p: Pokemon) => void }) => {
  const p = findPokemon(name)
  return (
    <div className="gb-poke" onClick={() => p && onOpen(p)} style={{ cursor: p ? 'pointer' : 'default' }}>
      {p ? <Sprite p={p} /> : <div className="sprite-fallback">?</div>}
      <b>{name}</b>
      {role && <span className="muted tiny">{role}</span>}
    </div>
  )
}

const Skill = ({ name, kind, children }: { name: string; kind: 'safe' | 'warn' | 'danger' | 'info'; children: React.ReactNode }) => (
  <div className={`skill ${kind}`}>
    <div className="skill-name">{name}</div>
    <div className="skill-desc">{children}</div>
  </div>
)

const Step = ({ n, children }: { n: number; children: React.ReactNode }) => (
  <div className="gb-step"><span className="n">{n}</span><div>{children}</div></div>
)

/* ---------- página ---------- */
export default function GuildBoss({ onOpen }: { onOpen: (p: Pokemon) => void }) {
  const [light, setLight] = useState<{ src: string; cap: string } | null>(null)
  const open = (src: string, cap: string) => setLight({ src, cap })
  const [boss, setBoss] = useState<'steelix' | 'jynx' | 'tentacruel' | 'marowak'>('steelix')

  return (
    <>
      <SectionHead title="Bosses de Guild" sub="Como fazer os Giant Bosses da guild jogando de tank, supp ou dano. Guia baseado no vídeo do AlastraSz, com os prints e os Pokémon que ele usa." />

      {/* vídeo fixado */}
      <div className="gb-video">
        <div className="gb-frame">
          <iframe src={`https://www.youtube.com/embed/${VIDEO_ID}`} title="Como Fazer os BOSSES DE GUILD No PokeAlliance (Tank, Supp e DPS) | AlastraSz" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowFullScreen />
        </div>
        <div className="gb-video-info">
          <div className="tiny muted" style={{ textTransform: 'uppercase', letterSpacing: '0.08em' }}>Vídeo de referência</div>
          <h3 style={{ margin: '4px 0 8px' }}>Como Fazer os BOSSES DE GUILD No PokeAlliance (Tank, Supp e DPS)</h3>
          <p className="muted small" style={{ margin: 0 }}>por <b style={{ color: 'var(--text)' }}>AlastraSz</b> · toda a explicação abaixo é dele. Os links "ver no vídeo" abrem o minuto exato.</p>
          <div className="tags" style={{ marginTop: 12 }}>
            {[['Recompensas', 0], ['Tank', 90], ['Supp', 144], ['Dano', 230], ['Meganium', 338], ['Marowak', 458], ['Como entrar', 505], ['Steelix', 574], ['Jynx', 770], ['Tentacruel', 1009], ['Loja', 1319]].map(([l, t]) => (
              <a key={l} className="chip" href={yt(t as number)} target="_blank" rel="noreferrer">{l} · {Math.floor((t as number) / 60)}:{String((t as number) % 60).padStart(2, '0')}</a>
            ))}
          </div>
        </div>
      </div>

      {/* resumo */}
      <div className="grid grid-4" style={{ marginBottom: 22 }}>
        {[
          { n: 'Giant Steelix', lvl: 250, custo: '$2.000', tempo: '~4 min', img: 'steelix' },
          { n: 'Giant Jynx', lvl: 275, custo: '$5.000', tempo: '~7 min', img: 'jynx' },
          { n: 'Giant Tentacruel', lvl: 300, custo: '$6.000', tempo: '~14 min', img: 'tentacruel' },
          { n: 'Giant Marowak', lvl: 400, custo: '$10.000', tempo: '—', img: 'marowak' },
        ].map((b) => {
          const p = findPokemon(b.n.replace('Giant ', ''))
          return (
            <div key={b.n} className="card gb-summary" onClick={() => setBoss(b.img as typeof boss)} style={boss === b.img ? { borderColor: 'var(--orange)' } : {}}>
              {p && <Sprite p={p} size="lg" />}
              <h3>{b.n}</h3>
              <div className="tags" style={{ justifyContent: 'center' }}><span className="badge">Lvl {b.lvl}+</span><span className="badge shiny">{b.custo} balance</span><span className="badge">{b.tempo}</span></div>
            </div>
          )
        })}
      </div>

      {/* 1. Recompensas */}
      <section className="gb-section">
        <h2>🎁 Recompensas</h2>
        <div className="gb-two">
          <div>
            <p>Cada boss dá <b>stones</b> (Novice, Elemental e Common) e dois itens <b>unique</b>: <b>moedas da guild</b> para gastar na loja e <b>shards</b> dos Pokémon mais raros (Charizard, Shiny Gengar, Shiny Alakazam, Shiny Scizor…), 5 aleatórios por boss.</p>
            <ul className="gb-list">
              <li>As stones são trocáveis: pode usar ou vender.</li>
              <li>Moedas e shards são unique. O que você comprar na loja da guild com as moedas também é unique (não dá para vender). <b>Pegue só o que for usar.</b></li>
              <li>Na data do vídeo as recompensas estavam <b>dobradas</b> (10 Novice, 6 moedas…). Aproveite enquanto durar.</li>
            </ul>
          </div>
          <Shot n="recompensas" cap="Recompensas de cada boss (Steelix, Jynx, Tentacruel)" t={5} onOpen={open} />
        </div>
      </section>

      {/* 2. Funções */}
      <section className="gb-section">
        <h2>🧩 As três funções: Tank, Supp e Dano</h2>
        <p className="muted">Precisa ter as três no grupo. O que importa de verdade é <b>ter gente participando</b>, não Pokémon forte.</p>
        <div className="grid grid-3">
          <div className="card">
            <div className="card-title"><span className="badge mega">🛡️ Tank</span><h3>Forretress</h3></div>
            <Poke name="Forretress" role="Tier 3 · só Defense 3" onOpen={onOpen} />
            <ul className="gb-list">
              <li>Tank principal nos três bosses (Tentacruel não exige, mas ajuda). Alastra usa um <b>T3 sem star, sem boost, sem treino</b>, só Defense 3.</li>
              <li><b>Protect</b>: imune a dano. <b>Harden</b>: sobe a defesa.</li>
              <li><b>Scrap Throw</b>: puxa o agro do boss para você (não aparece na Dex). <b>Nunca use como dano</b>: guarde para quando o boss trocar de alvo.</li>
              <li>Seja o <b>primeiro da fila</b> a entrar para segurar o agro desde o início.</li>
            </ul>
            <Shot n="tank" cap="Slide do Tank: Forretress T3 com Scrap Throw e Iron Spikes" t={90} onOpen={open} />
          </div>
          <div className="card">
            <div className="card-title"><span className="badge ok">💚 Supp</span><h3>2 curadores</h3></div>
            <div className="gb-pokes"><Poke name="Shiny Bellossom" onOpen={onOpen} /><Poke name="Shiny Hariyama" onOpen={onOpen} /></div>
            <ul className="gb-list">
              <li><b>Dois supps</b> em média (3 ou 4 se o time for de level baixo). Bellossom ou Hariyama, tanto faz.</li>
              <li>Não precisa de star: a primeira vez foi com duas Shiny Bellossom sem estrela. Um pouco de ataque ajuda na cura.</li>
              <li>A cura da Bellossom <b>marca os players</b> (sai uma semente) e cura todos os marcados, <b>mesmo fora da tela</b>.</li>
              <li>Alternativa: Shiny Pikachu, mas é level 50 e precisa compensar com boost/ataque. Não recomendado.</li>
            </ul>
            <Shot n="supp" cap="Slide do Supp: Shiny Bellossom e Shiny Hariyama (2x)" t={144} onOpen={open} />
          </div>
          <div className="card">
            <div className="card-title"><span className="badge bad">⚔️ Dano</span><h3>Qualquer um</h3></div>
            <div className="gb-pokes"><Poke name="Shiny Gengar" role="já é ghost" onOpen={onOpen} /><Poke name="Shiny Poliwrath" onOpen={onOpen} /><Poke name="Shiny Machamp" onOpen={onOpen} /></div>
            <ul className="gb-list">
              <li>T2, T1, SR, UR, lendário… <b>não importa</b>. Steelix com Poliwrath ou Machamp funciona.</li>
              <li>O único requisito: <b>Ghost</b> (held Y-Ghost ou um Pokémon fantasma). Com 20 pessoas no boss, sem ghost um trava o outro e ninguém desvia de mecânica.</li>
              <li>Quem é dano ou supp precisa de ghost; o tank não.</li>
            </ul>
            <Shot n="dano" cap="Slide do Dano: qualquer Pokémon + held Y-Ghost" t={230} onOpen={open} />
          </div>
        </div>
        <Note>Dica para líderes de guild: não exija level alto nem Pokémon caro dos membros. Steelix leva ~4 min, Jynx ~7 min e Tentacruel ~14 min. Em meia hora dá para fazer os três.</Note>
      </section>

      {/* 3. Extra Meganium */}
      <section className="gb-section">
        <h2>🌿 Extra: Shiny Meganium</h2>
        <div className="gb-two">
          <div>
            <Poke name="Shiny Meganium" role="T1 de dano com skills de suporte em área" onOpen={onOpen} />
            <p>Não bate efetivo em nenhum dos três bosses, mas é <b>muito boa</b>: dano de T1 normal mais três skills em área.</p>
            <div className="skills">
              <Skill name="Ingrain" kind="safe">Cura em área. Cooldown alto, então não serve como supp: é o Pokémon "backup" para quando o tank erra e toma muito dano.</Skill>
              <Skill name="Aromatherapy" kind="info">Tira miss em área. Pouco útil, mas às vezes ajuda.</Skill>
              <Skill name="Light Screen" kind="warn">O que faz ela valer a pena: <b>todo mundo em volta toma metade do dano</b> e ganha <b>Focus</b> (aumenta a próxima skill) e movement speed. Focus em 20 players ao mesmo tempo é muito forte.</Skill>
            </div>
          </div>
          <Shot n="meganium" cap="Dex da Shiny Meganium: Ingrain, Aromatherapy e Light Screen" t={338} onOpen={open} />
        </div>
      </section>

      {/* 4. Como entrar */}
      <section className="gb-section">
        <h2>🚪 Como entrar no boss</h2>
        <div className="gb-two">
          <div>
            <Step n={1}>O <b>líder da guild</b> abre a aba Boss e clica em <b>Unlock Boss</b>. O custo sai do <b>balance da guild</b>, não do seu dinheiro: Steelix $2.000, Jynx $5.000, Tentacruel $6.000, Marowak $10.000 (cada DD doado vira $1.000 de balance).</Step>
            <Step n={2}>Todo mundo recebe um <b>popup</b> para teleportar. Só entra quem <b>não está em batalha</b>. O boss fica aberto por <b>30 minutos</b> para dar join.</Step>
            <Step n={3}>Fechou o popup sem querer? Aba da guild → Boss → botão verde de <b>join</b>.</Step>
            <Step n={4}>Espere os <b>30 segundos</b> antes de soltar o primeiro Pokémon. O <b>tank entra primeiro</b> para guardar o Scrap Throw; se alguém apressado entrar antes, o boss pode matar quem não é tank.</Step>
          </div>
          <div>
            <Shot n="painel-guild" cap="Painel da guild: custo de cada boss em balance e o botão Unlock Boss" t={505} onOpen={open} />
            <Shot n="entrar-boss" cap="Popup 'Guild Boss aberto': fecha em 30 min, botão Entrar" t={545} onOpen={open} />
          </div>
        </div>
      </section>

      {/* bosses */}
      <div className="tags" style={{ margin: '8px 0 14px' }}>
        {(['steelix', 'jynx', 'tentacruel', 'marowak'] as const).map((b) => (
          <button key={b} className={`chip orange ${boss === b ? 'active' : ''}`} onClick={() => setBoss(b)}>{{ steelix: '🪨 Giant Steelix', jynx: '❄️ Giant Jynx', tentacruel: '🌊 Giant Tentacruel', marowak: '🦴 Giant Marowak' }[b]}</button>
        ))}
      </div>

      {boss === 'steelix' && (
        <section className="gb-section boss">
          <div className="gb-boss-head"><Sprite p={findPokemon('Steelix')!} size="lg" /><div><h2>Giant Steelix</h2><div className="tags"><span className="badge">Lvl 250+</span><span className="badge shiny">$2.000 balance</span><span className="badge">~4 min</span><span className="badge ok">O mais fácil</span></div></div></div>
          <p>Ele usa todas as skills logo no primeiro combo. São <b>quatro</b>:</p>
          <div className="skills">
            <Skill name="Iron Tail" kind="info">Gira e dá dano em todo mundo em volta. Dano baixo, sem preocupação.</Skill>
            <Skill name="Earth Power" kind="warn">Área <b>vermelha</b> ao redor dele. <b>Toda vez que ela explode, ele troca de alvo.</b> Tank: guarde o Scrap Throw para logo depois da explosão e calcule o tempo da skill subir e cair para puxar o agro de volta.</Skill>
            <Skill name="Dig" kind="danger">Entra na terra e, ao sair, dá dano em área que é <b>hit kill</b>, não importa o que você faça. Tank: use <b>Protect</b> uns 3 segundos depois do Dig começar (ele demora a sair). Supp e dano: <b>saiam correndo</b> da área.</Skill>
            <Skill name="Exclamação vermelha" kind="safe">Marca no chão. Só desviar.</Skill>
          </div>
          <div className="gb-shots">
            <Shot n="steelix-skills" cap="Slide das skills do Steelix: Earth Power (área vermelha) e Dig" t={640} onOpen={open} />
            <Shot n="steelix-earthpower" cap="Earth Power no jogo: círculo vermelho e exclamações no chão" t={615} onOpen={open} />
            <Shot n="steelix-dig" cap="Dig: o Charizard que não saiu tomou hit kill; o tank com Protect não tomou nada" t={745} onOpen={open} />
            <Shot n="steelix-mapa" cap="Giant Steelix no mapa" t={590} onOpen={open} />
          </div>
        </section>
      )}

      {boss === 'jynx' && (
        <section className="gb-section boss">
          <div className="gb-boss-head"><Sprite p={findPokemon('Jynx')!} size="lg" /><div><h2>Giant Jynx</h2><div className="tags"><span className="badge">Lvl 275+</span><span className="badge shiny">$5.000 balance</span><span className="badge">~7 min</span><span className="badge bad">Precisa de Guardian Elixir</span></div></div></div>
          <p>Um pouco mais difícil só porque ela dá <b>muito miss</b>: use <b>Guardian Elixir</b> e não economize (o loot dobrado paga). Ela solta praticamente todas as skills assim que te vê.</p>
          <div className="skills">
            <Skill name="Psywave · Icy Wind · Aurora Beam" kind="danger"><b>Três skills frontais</b> (Aurora Beam é linha reta). <b>Ninguém fica na frente dela.</b> Ela também tem Ice Beam.</Skill>
            <Skill name="Blizzard · Draining Kiss" kind="warn">Exclamação no chão. Só desviar (por isso o ghost). Se cair em cima do tank, ele usa <b>Protect</b>.</Skill>
            <Skill name="Heart Stamp" kind="info">Corações em volta: dano em área.</Skill>
            <Skill name="Lovely Kiss" kind="info">Só dá miss. Guardian Elixir resolve.</Skill>
          </div>
          <h3>Posicionamento (a parte que importa)</h3>
          <Step n={1}>O tank <b>não anda com a Jynx</b>: se ela vira, o frontal pega o time inteiro. Puxe ela para um <b>canto</b> e fique <b>100% parado</b>.</Step>
          <Step n={2}>Uma segunda pessoa <b>pisa no quadrado abaixo</b> dela para deixá-la <b>presa</b>. Assim ela não anda e todo frontal vai para o ar.</Step>
          <Step n={3}>Todo o dano fica <b>atrás</b> dela, seguro. Tank guarda o Scrap Throw para quando ela trocar de alvo (parece ser na exclamação no chão).</Step>
          <p className="muted small">Alastra suspeita que dá para ficar em cima da fogueira ao lado e dispensar a segunda pessoa, mas não testou. Na gravação a Jynx bugou e parou de usar skills depois do primeiro combo.</p>
          <div className="gb-shots">
            <Shot n="jynx-skills" cap="Slide da Jynx: Psywave e Icy Wind (frontais) e exclamações no chão" t={775} onOpen={open} />
            <Shot n="jynx-posicao" cap="Tank puxa a Jynx para o canto e alguém pisa embaixo dela" t={935} onOpen={open} />
            <Shot n="jynx-presa" cap="Jynx presa: ninguém no frontal, todo o dano atrás" t={965} onOpen={open} />
          </div>
        </section>
      )}

      {boss === 'tentacruel' && (
        <section className="gb-section boss">
          <div className="gb-boss-head"><Sprite p={findPokemon('Tentacruel')!} size="lg" /><div><h2>Giant Tentacruel</h2><div className="tags"><span className="badge">Lvl 300+</span><span className="badge shiny">$6.000 balance</span><span className="badge">~14 min</span><span className="badge bad">Mecânica mais difícil</span></div></div></div>
          <p>É o mais difícil e ao mesmo tempo o mais fácil: <b>não exige tank</b>, mas Alastra usa para manter ele controlado (ele bate poison e pode virar num supp). A dificuldade é a mecânica dos <b>tentáculos</b>: aqui <b>precisa de gente</b>. Nos outros bosses, com pouca gente você compensa ficando 15 ou 20 minutos; no Tentacruel, sem players não dá.</p>
          <div className="skills">
            <Skill name="Tentáculos pelo mapa" kind="danger">Do nada o boss <b>some</b> e nascem tentáculos pelo mapa inteiro. Todo mundo sai procurando e matando. <b>Cada tentáculo que ficar vivo recupera vida do boss</b>.</Skill>
            <Skill name="Tentaclada" kind="warn">Enquanto houver tentáculo vivo, de tempo em tempo nasce um em cima de cada pessoa e dá dano. Dá para desviar andando para o lado. Quando o boss some, <b>todo mundo toma de uma vez</b>.</Skill>
            <Skill name="Skills em área" kind="info">Quanto mais ele se mexe, mais skill ele spama. <b>Todo mundo em volta dele</b>, trapando, para ele ficar parado.</Skill>
          </div>
          <h3>Como o grupo do Alastra faz</h3>
          <Step n={1}>Todos em volta do boss, com <b>def em área</b> de <b>Luxray</b> e <b>Shiny Meganium</b>. O tank fica com o mouse no <b>Protect</b> para usar na hora da tentaclada.</Step>
          <Step n={2}>Boss some, todo mundo toma tentaclada: a <b>Meganium</b> usa a cura em área e todo mundo volta full life para sair caçando tentáculo.</Step>
          <Step n={3}>As <b>Bellossom</b> podem sair caçando tentáculo também: a cura delas continua chegando em quem está marcado, mesmo fora da tela.</Step>
          <Step n={4}>O tank <b>não sai</b> (dano do Forretress é inútil): fica posicionado onde o boss vai renascer para puxar o agro na hora. Quando o pessoal voltar, é só chegar batendo.</Step>
          <div className="gb-pokes"><Poke name="Forretress" role="tank (imune a poison)" onOpen={onOpen} /><Poke name="Shiny Meganium" role="def + cura em área" onOpen={onOpen} /><Poke name="Shiny Luxray" role="def em área" onOpen={onOpen} /><Poke name="Shiny Bellossom" role="supp" onOpen={onOpen} /></div>
          <div className="gb-shots">
            <Shot n="tentacruel-skills" cap="Slide do Tentacruel: tentáculos espalhados pelo mapa" t={1009} onOpen={open} />
            <Shot n="tentacruel-tentaculos" cap="Tentáculo nasce em cima de cada pessoa enquanto houver tentáculo vivo" t={1070} onOpen={open} />
            <Shot n="tentacruel-volta" cap="Todo mundo em volta do boss, com def em área (Luxray e Meganium)" t={1175} onOpen={open} />
            <Shot n="tentacruel-spawn" cap="Boss sumiu: tentáculos nasceram e todo mundo tomou tentaclada" t={1250} onOpen={open} />
            <Shot n="tentacruel-cura" cap="Cura em área da Shiny Meganium: todo mundo full life para caçar tentáculo" t={1290} onOpen={open} />
          </div>
        </section>
      )}

      {boss === 'marowak' && (
        <section className="gb-section boss">
          <div className="gb-boss-head"><Sprite p={findPokemon('Marowak')!} size="lg" /><div><h2>Giant Marowak</h2><div className="tags"><span className="badge">Lvl 400+</span><span className="badge shiny">$10.000 balance</span><span className="badge">sem dados de tempo</span></div></div></div>
          <p>A guild do Alastra <b>ainda não faz</b> o Marowak: é boss de nível 400 e poucos membros chegaram lá (a maioria está entre 300 e 350). O que ele sabe:</p>
          <ul className="gb-list">
            <li>Funciona como qualquer outro boss, com a diferença de que o pessoal usa <b>Dragonite</b> para tankar.</li>
            <li>Supp: os mesmos de sempre. A <b>Bellossom</b> bate efetivo nele (como a Hariyama bate na Jynx), mas o foco do supp é curar, então faz pouca diferença.</li>
            <li>A Shiny Meganium (planta) bate efetivo no Marowak.</li>
          </ul>
          <div className="gb-pokes"><Poke name="Shiny Dragonite" role="tank" onOpen={onOpen} /><Poke name="Shiny Bellossom" role="supp (efetivo)" onOpen={onOpen} /><Poke name="Shiny Hariyama" role="supp" onOpen={onOpen} /></div>
          <div className="gb-shots">
            <Shot n="marowak-tank" cap="Slide do Marowak: Dragonite como tank" t={458} onOpen={open} />
            <Shot n="marowak-supp" cap="Slide do Marowak: supps de sempre (Bellossom e Hariyama)" t={485} onOpen={open} />
          </div>
        </section>
      )}

      {/* loja */}
      <section className="gb-section">
        <h2>🏪 Loja da Guild</h2>
        <div className="gb-two">
          <div>
            <p>As moedas ganhas nos bosses são gastas aqui. No servidor do Alastra: <b>Mythic Orbs por 30</b> moedas e <b>Potent (boost stones) por 15</b>. Tudo que sai da loja é <b>unique</b>, então compre só o que for usar. O que vale mais depende do seu servidor e das suas prioridades.</p>
          </div>
          <Shot n="loja" cap="Loja da guild: Mythic Orbs de cada tipo por 30 moedas" t={1319} onOpen={open} />
        </div>
      </section>

      <Note>Resumo do Alastra: fazer boss é tranquilo e sem risco <b>se o tank jogar certinho</b>. Se o tank errar, vira bagunça. Jogando de supp ou dano: tenha ghost, desvie das exclamações e fique atrás do boss.</Note>
      <p className="muted small" style={{ textAlign: 'center' }}>Conteúdo do vídeo <a href={`https://www.youtube.com/watch?v=${VIDEO_ID}`} target="_blank" rel="noreferrer">"Como Fazer os BOSSES DE GUILD No PokeAlliance"</a> de <b>AlastraSz</b>. Prints retirados do vídeo.</p>

      {light && (
        <div className="lightbox" onClick={() => setLight(null)}>
          <img src={light.src} alt={light.cap} />
          <div className="lightbox-bar"><span className="small">{light.cap}</span><button className="chip" onClick={() => setLight(null)}>✕ Fechar</button></div>
        </div>
      )}
    </>
  )
}

