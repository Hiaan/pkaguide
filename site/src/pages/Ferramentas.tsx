import { SectionHead } from '../components/ui'

type Tool = { url: string; name: string; tag: string; title: string; sub: string; lead: string; features: { ico: string; title: string; desc: string }[]; note?: string }

const TOOLS: Record<string, Tool> = {
  overlay: {
    url: 'https://github.com/Hiaan/pkaguide/releases/latest/download/PKA.GUIDE.Setup.exe',
    name: 'PKA GUIDE', tag: 'Overlay para Windows',
    title: 'PKA GUIDE Overlay',
    sub: 'Passe o mouse em um item dentro do jogo e veja na hora para que ele serve: PokeTalent, boost, material ou só NPC.',
    lead: 'Baixe, clique em Instalar agora e pronto: ele cria o atalho e fica como uma barrinha no canto da tela. Lê o tooltip por captura de tela (não lê memória do jogo) e se atualiza sozinho.',
    features: [
      { ico: '🖱️', title: 'Passe o mouse e pronto', desc: 'Funciona no depot, na bag e no loot. O painel abre só quando reconhece um item e fecha sozinho.' },
      { ico: '⌨️', title: 'Ou use uma tecla sua', desc: 'Nas configurações dá para trocar para o modo tecla de atalho: ele só lê a tela quando você aperta a tecla que escolher.' },
      { ico: '➕', title: 'Cadastre o que falta', desc: 'Item que ainda não está na base aparece como "não cadastrado" e você mesmo registra para que serve.' },
      { ico: '🟢', title: 'Cores por destino', desc: 'Verde: usar ou vender para player (PokeTalent). Amarelo: boost. Azul: material. Cinza: só NPC.' },
      { ico: '🔄', title: 'Sempre atualizado', desc: 'A base de itens vem deste site todo dia, e o app avisa quando tem versão nova com um botão de atualizar.' },
      { ico: '🛡️', title: 'Seguro para o anticheat', desc: 'Só captura de tela e OCR. Nada é injetado no cliente, nenhuma memória é lida, nenhum comando é enviado ao jogo.' },
    ],
    note: 'Windows 10/11. O instalador tem ~86 MB por causa do modelo de OCR embutido. O Windows pode mostrar um aviso de "editor desconhecido": clique em "Mais informações" e "Executar assim mesmo". Para remover, use Aplicativos Instalados do Windows.',
  },
  criticalcatch: {
    url: 'https://criticalcatch-pkatools.vercel.app/',
    name: 'Critical Catch', tag: 'PKA Tools',
    title: 'Ferramentas de catch',
    sub: 'Ferramentas interativas para o dia a dia no PokeAlliance, no site Critical Catch.',
    lead: 'Ferramentas de catch, médias, times e calculadora de dano em um só lugar.',
    features: [
      { ico: '🎯', title: 'Ferramentas de catch', desc: 'Acompanhe brokes, chance de catch e o quanto falta para a máxima do seu shiny.' },
      { ico: '📈', title: 'Médias', desc: 'Média de catches por tier e por Pokémon, com base nos dados da comunidade.' },
      { ico: '🧩', title: 'Times', desc: 'Monte e compare rotações de Pokémon para cada hunt.' },
      { ico: '💥', title: 'Calculadora de dano', desc: 'Simule o dano dos seus Pokémon considerando tier, star, boost e talentos.' },
    ],
  },
  pokeforge: {
    url: 'https://pokeforge-pka.netlify.app/',
    name: 'PokéForge', tag: 'Calculadora de builds',
    title: 'Calculadora de builds',
    sub: 'Planeje o custo total do seu próximo Pokémon: cópias, estrelas, treino e boost em um único orçamento.',
    lead: 'Do primeiro treino à build completa. Informe o preço do diamante no seu servidor, escolha tier e metas, e veja o orçamento em tempo real.',
    features: [
      { ico: '⭐', title: 'Fusões de STAR', desc: 'Quantas cópias 0★ e quantas taxas de fusão para chegar da estrela atual à desejada, com a árvore de fusões.' },
      { ico: '🏋️', title: 'Treinamento', desc: 'Oito atributos (Attack, Critical, Defense, HP, Precision, Evasion…) com cargas e diamantes por pacote de 20.000.' },
      { ico: '🔥', title: 'Boost probabilístico', desc: 'Stones esperadas em média, reserva com 95% de segurança e pior caso, considerando as falhas acumuladas.' },
      { ico: '💎', title: 'Orçamento ao vivo', desc: 'Converte tudo para Cash pelo preço do diamante, salva no navegador e exporta ou imprime a build.' },
    ],
    note: 'Treino é estimado e boost depende de tentativas. Os preços e taxas são os que você informa, então mantenha-os atualizados com o mercado.',
  },
}

export default function Ferramentas({ sub }: { sub: string }) {
  const t = TOOLS[sub] ?? TOOLS.criticalcatch
  return (
    <>
      <SectionHead title={t.title} sub={t.sub} />
      <div className="sug">
        <div className="sug-hero">
          <h2><span>{t.name}</span> · {t.tag}</h2>
          <p>{t.lead}{sub === 'overlay' ? '' : ' Abre em uma nova aba.'}</p>
          <a className="btn btn-primary" style={{ fontSize: 17, padding: '16px 30px' }} href={t.url} target="_blank" rel="noreferrer">{sub === 'overlay' ? '⬇ Baixar' : '🚀 Abrir'} {t.name} ↗</a>
          <div className="muted small" style={{ marginTop: 12 }}>{t.url.replace('https://', '').replace(/\/$/, '')}</div>
        </div>
        <div className="sug-steps" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
          {t.features.map((f) => (
            <a key={f.title} className="card" href={t.url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}>
              <div style={{ fontSize: 30, marginBottom: 8 }}>{f.ico}</div>
              <b>{f.title}</b>
              <p className="muted small" style={{ margin: '6px 0 0', lineHeight: 1.5 }}>{f.desc}</p>
            </a>
          ))}
        </div>
        {t.note && <p className="muted small" style={{ marginTop: 18 }}>{t.note}</p>}
      </div>
    </>
  )
}
