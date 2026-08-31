import { useState, useEffect } from 'react'
import { Ativo } from '../types'
import { api } from '../services/api'
import {
  ArrowLeft, Ship, FileText, Wrench, Zap, Cpu, Shield, Paintbrush, Armchair,
  FileCheck, Camera, ShieldCheck, Sailboat, Plus, CalendarClock,
  Award, ChevronRight, X, Download, Upload, Lock,
  Users, ClipboardCheck, Waves, AlertTriangle, TrendingUp, Globe, Anchor,
  Droplets, PenLine, HelpCircle
} from 'lucide-react'
import SecureCameraUpload from './SecureCameraUpload'
import FichaServicoForm from './FichaServicoForm'
import ConsentimentoTitular from './ConsentimentoTitular'
import CoberturaFotos from './CoberturaFotos'
import RetificarRegistro from './RetificarRegistro'
import CategoriaForm from './CategoriaForm'
import { SERVICOS } from '../config/servicosCategorias'
import { CATEGORIAS as DOSSIE_CATS, type Categoria as DossieCat } from '../config/dossieCategorias'
import { ACEITA_DOCUMENTO, ROTULO_DOCUMENTO, TAMANHO_MAXIMO_MB } from '../utils/arquivos'

type Health = 'ok' | 'warning' | 'critical' | 'info' | 'na'

interface Categoria {
  key: string
  titulo: string
  subtitulo: string
  icon: typeof Ship
  healthKey?: string
}

function categorias(tipo: Ativo['tipo']): Categoria[] {
  const base: Categoria[] = [
    { key: 'documentacao', titulo: 'Documentação', subtitulo: 'Legal & Conformidade', icon: FileText, healthKey: 'documentacao' },
    { key: 'seguro', titulo: 'Seguro', subtitulo: 'Apólice & Cobertura', icon: ShieldCheck },
    { key: 'manutencao', titulo: 'Manutenção', subtitulo: 'Serviços & Revisões', icon: Wrench, healthKey: 'manutencao' },
    { key: 'operacao', titulo: 'Diário de Bordo', subtitulo: 'Operação & Idas ao Mar', icon: Anchor },
    { key: 'drenagem', titulo: 'Drenagem / Porão', subtitulo: 'Bombas & Alarmes', icon: Droplets, healthKey: 'drenagem' },
    { key: 'fotos', titulo: 'Fotos', subtitulo: 'Registro Visual', icon: Camera },
    { key: 'motor', titulo: 'Motor', subtitulo: 'Propulsão & Mecânica', icon: Zap, healthKey: 'motor' },
    { key: 'casco', titulo: 'Casco', subtitulo: 'Estrutura & Integridade', icon: Waves, healthKey: 'casco' },
    // Sinistro tem aba própria porque raramente fica num sistema só: encalhe
    // atinge casco, hélice, eixo e leme; incêndio atinge motor, elétrica e
    // interior. E é aqui que a ocorrência ganha desfecho — o antes e o depois.
    { key: 'sinistros', titulo: 'Sinistros', subtitulo: 'Ocorrências & Reparos', icon: AlertTriangle },
    { key: 'eletrica', titulo: 'Elétrica', subtitulo: 'Eletrônica & Navegação', icon: Cpu, healthKey: 'eletrica' },
    { key: 'seguranca', titulo: 'Segurança', subtitulo: 'Salvatagem & Proteção', icon: Shield, healthKey: 'seguranca' },
    { key: 'pintura', titulo: 'Pintura', subtitulo: 'Estética & Superfície', icon: Paintbrush, healthKey: 'pintura' },
    { key: 'interior', titulo: 'Interior', subtitulo: 'Acomodações & Conforto', icon: Armchair, healthKey: 'interior' },
    { key: 'dossie', titulo: 'Dossiê', subtitulo: 'Integridade Certificada', icon: FileCheck, healthKey: 'dossie' },
  ]
  if (tipo === 'veleiro') {
    return base.map((c) =>
      c.key === 'motor'
        ? { key: 'velame', titulo: 'Mastro & Velame', subtitulo: 'Rigging & Velas', icon: Sailboat, healthKey: 'motor' }
        : c
    )
  }
  if (tipo === 'jetski') {
    return base.filter((c) => !['interior', 'pintura'].includes(c.key))
  }
  return base
}

const HEALTH_STYLE: Record<Health, { dot: string; label: string; text: string }> = {
  ok: { dot: 'bg-emerald-400', label: 'Em dia', text: 'text-emerald-400' },
  warning: { dot: 'bg-amber-400', label: 'Atenção', text: 'text-amber-400' },
  critical: { dot: 'bg-rose-400', label: 'Crítico', text: 'text-rose-400' },
  info: { dot: 'bg-blue-400', label: 'Informativo', text: 'text-blue-400' },
  na: { dot: 'bg-white/20', label: 'Sem registro', text: 'text-white/30' },
}

// Rótulo do selo em INGLÊS, igual ao valor que o banco guarda e ao que a
// página pública de verificação mostra. O painel traduzia para "Ouro/Prata"
// desde 26/06/2026, e a página pública nunca traduziu — mesmo ativo aparecia
// "Ouro" para a marina e "GOLD" para o comprador que escaneia o QR. Selo é
// nome de grau, não texto corrido: mantê-lo idêntico nas duas pontas é o que
// permite a marina e o comprador falarem da mesma coisa.
const CLASSIF: Record<string, { label: string; cls: string }> = {
  gold: { label: 'Gold', cls: 'bg-[#c5a059] text-[#010c20] border-[#c5a059]' },
  silver: { label: 'Silver', cls: 'bg-white/80 text-[#010c20] border-white' },
  bronze: { label: 'Bronze', cls: 'bg-[#a06a3c]/20 text-[#c98b54] border-[#a06a3c]/40' },
}

// Categorias ricas do dossiê (dossieCategorias.ts) que NÃO estão no painel
// operacional — procedência, especificações, laudos de terceiros e seguro.
// Abrem o CategoriaForm e fluem para o dossiê via `registros`.
const DOSSIE_EXTRA_IDS = [
  'proprietarios', 'especificacoes', 'sistemas_auxiliares',
  'inspecao_tecnica', 'auditoria_casco', 'sinistros',
  'avaliacao_mercado', 'relatorio_seguradora', 'compliance_imo',
  'tripulacao', 'tenders_toys', 'areas',
]
const DOSSIE_EXTRA_ICONS: Record<string, typeof Ship> = {
  proprietarios: Users, especificacoes: Ship, sistemas_auxiliares: Cpu,
  inspecao_tecnica: ClipboardCheck, auditoria_casco: Waves, sinistros: AlertTriangle,
  avaliacao_mercado: TrendingUp, relatorio_seguradora: ShieldCheck, compliance_imo: Globe,
  tripulacao: Users, tenders_toys: Sailboat, areas: Armchair,
}

interface Props {
  ativo: Ativo
  onBack: () => void
  /** Portal do Proprietário: mesmo painel da marina, mas 100% visualização — zero preenchimento. */
  readOnly?: boolean
  /** Esconde o banner interno (usado quando a página já tem seu próprio cabeçalho, ex. Portal do Proprietário). */
  hideHeader?: boolean
}

export default function AtivoHub({ ativo, onBack, readOnly = false, hideHeader = false }: Props) {
  const [secao, setSecao] = useState<Categoria | null>(null)
  const [dossieAberta, setDossieAberta] = useState<DossieCat | null>(null)
  const [contagem, setContagem] = useState<Record<string, number>>({})
  const [cameraAberta, setCameraAberta] = useState(false)
  const [criterioAberto, setCriterioAberto] = useState(false)
  // Somente leitura (Portal do Proprietário): sem card de Dossiê (emissão é ação
  // exclusiva da marina) e sem a seção "Dossiê Completo & Laudos" (só tem formulário
  // de criação, nenhuma visualização de registros existentes).
  const cats = categorias(ativo.tipo).filter((c) => !readOnly || c.key !== 'dossie')
  const classif = CLASSIF[ativo.classificacao] || CLASSIF.bronze
  const comprimento = ativo.comprimento_pes || 0
  const dossieExtra = readOnly ? [] : DOSSIE_CATS.filter((c) => DOSSIE_EXTRA_IDS.includes(c.id) && comprimento >= c.porteMinimoPes)

  // Contagem real por categoria (dá vida aos cards).
  //
  // Lê as DUAS tabelas. Antes contava só `registros`, e por isso os cards de
  // Documentação e Fotos diziam "Sem registro" mesmo com 21 PDFs e 8 fotos
  // guardados: esses dois vivem em `documentos`, não em `registros`. A marina
  // subia o arquivo, via o painel dizer que não havia nada, e não tinha como
  // saber se o upload tinha funcionado.
  const carregarContagem = async () => {
    const c: Record<string, number> = {}
    const [regs, docs] = await Promise.allSettled([
      api.registros.list(ativo.id),
      api.documentos.list(ativo.id),
    ])

    if (regs.status === 'fulfilled' && Array.isArray(regs.value)) {
      regs.value.forEach((r: any) => { c[r.categoria] = (c[r.categoria] || 0) + 1 })
    }

    if (docs.status === 'fulfilled' && Array.isArray(docs.value)) {
      docs.value.forEach((d: any) => {
        // Foto entra no card de Fotos qualquer que seja a galeria; a vitrine
        // fica de fora, como no resto do sistema (é apresentação, não acervo).
        if (d.tipo === 'foto') {
          if (d.categoria !== 'vitrine') c.fotos = (c.fotos || 0) + 1
          return
        }
        // Documento conta na própria categoria — a apólice aparece em Seguro,
        // o laudo em Casco — e todos somam no card de Documentação, que é a
        // porta de entrada do cofre. O `!==` evita contar duas vezes o que já
        // é da própria documentação.
        if (d.categoria && d.categoria !== 'documentacao') {
          c[d.categoria] = (c[d.categoria] || 0) + 1
        }
        c.documentacao = (c.documentacao || 0) + 1
      })
    }

    setContagem(c)
  }

  useEffect(() => { carregarContagem() /* eslint-disable-next-line */ }, [ativo.id, secao])

  const statusDe = (c: Categoria): Health =>
    (c.healthKey ? (ativo.health_status?.[c.healthKey] as Health) : undefined) || 'na'

  // CONFORMIDADE — a saude do ativo, que e outra pergunta que o selo.
  //
  // O selo (Gold/Silver/Bronze) e o antigo "Saude X%" vinham AMBOS do mesmo
  // numero: asset_score_service, que pesa abrangencia de cadastro, volume de
  // manutencao, documentos e laudo de casco. Nenhum desses quatro le o campo
  // `status` do registro -- um barco com sinistro aberto pontua igual a um
  // impecavel, desde que tenha o mesmo numero de registros. O selo mede o
  // trabalho da MARINA; nao mede o estado do BARCO.
  //
  // Esta media le `health_status`, que ja chega do backend e OLHA o status.
  // Mesma regra do dossie (ok=100, atencao=50, critico=0; categoria sem
  // registro fica fora da conta) -- ver "Como Ler Este Indice" no PDF.
  //
  // null quando nada foi avaliado: melhor nao exibir indicador do que exibir
  // um inventado. E o denominador anda SEMPRE junto, porque 100% sobre duas
  // categorias nao e a mesma noticia que 100% sobre onze.
  const catsComSaude = cats.filter((c) => c.healthKey)
  const catsAvaliadas = catsComSaude.filter((c) => statusDe(c) !== 'na')
  const peso = (h: Health) => (h === 'ok' || h === 'info' ? 100 : h === 'warning' ? 50 : 0)
  const conformidade = catsAvaliadas.length
    ? Math.round(catsAvaliadas.reduce((s, c) => s + peso(statusDe(c)), 0) / catsAvaliadas.length)
    : null
  const corConf = conformidade === null
    ? 'text-white/40'
    : conformidade >= 80 ? 'text-emerald-400'
    : conformidade >= 50 ? 'text-amber-400' : 'text-rose-400'

  return (
    <div className="animate-in fade-in slide-in-from-right-6 duration-500 space-y-8">
      {/* ===== BLOCO DE CIMA — Dados da embarcação ===== */}
      {!hideHeader && (
      <div className="relative rounded-sm overflow-hidden border border-white/10">
        <div className="absolute inset-0">
          <img src="/boat-picture-light.jpg" alt="" className="w-full h-full object-cover opacity-25" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#010c20] via-[#010c20]/90 to-[#021a3d]/60" />
        </div>
        <div className="relative z-10 p-8">
          <button onClick={onBack} className="flex items-center gap-2 text-white/50 hover:text-[#c5a059] transition-all mb-6 text-[10px] font-black uppercase tracking-[0.2em]">
            <ArrowLeft size={14} /> Voltar à frota
          </button>
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <div className="w-16 h-16 bg-[#010c20] border border-[#c5a059]/30 rounded-sm flex items-center justify-center text-[#c5a059] shadow-xl">
                <Ship size={34} strokeWidth={1} />
              </div>
              <div>
                <h1 className="text-3xl font-serif font-bold text-white tracking-tight">{ativo.nome_reg || `${ativo.marca} ${ativo.modelo}`}</h1>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[10px] font-black uppercase tracking-[0.25em] text-white/40">
                  <span className="capitalize">{ativo.tipo.replace('_', ' ')}</span>
                  <span className="text-[#c5a059]">•</span>
                  <span>{ativo.comprimento_pes || '—'} pés</span>
                  <span className="text-[#c5a059]">•</span>
                  <span>{ativo.ano_fabricacao}</span>
                  <span className="text-[#c5a059]">•</span>
                  <span>#{String(ativo.id).slice(0, 8).toUpperCase()}</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* "Indice de Custodia", nao um selo solto: e o rotulo que o
                  dossie (dossie_pdf.py) e a pagina publica (Verificacao.tsx)
                  ja usam para o MESMO numero. So o painel mostrava o grau nu,
                  e ao lado a palavra "Saude" -- que e o que ele nao mede. */}
              <span className={`px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border ${classif.cls}`}>
                <Award size={11} className="inline mr-1.5 -mt-0.5" />
                Índice de Custódia: {classif.label}
              </span>

              {/* Aqui ficava "Saude {ativo.progresso}%" -- o MESMO numero do
                  selo, repetido em percentual e com o rotulo errado. No lugar
                  dele, a conformidade, que e a saude de verdade, sempre com o
                  denominador. Clicar abre o criterio. */}
              <button
                type="button"
                onClick={() => setCriterioAberto((v) => !v)}
                aria-expanded={criterioAberto}
                title="Como este número é calculado"
                className="flex items-center gap-2 px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border border-white/15 bg-white/5 hover:bg-white/10 transition-colors"
              >
                <span className={corConf}>
                  {conformidade === null
                    ? 'Conformidade —'
                    : `Conformidade ${conformidade}%`}
                </span>
                <span className="text-white/35 normal-case tracking-normal font-bold">
                  {conformidade === null
                    ? `nenhum dos ${catsComSaude.length} sistemas avaliado`
                    : `${catsAvaliadas.length} de ${catsComSaude.length} sistemas`}
                </span>
                <HelpCircle size={11} className="text-white/40" />
              </button>
              <span className="flex items-center gap-2 px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border border-white/10 text-white/30" title="Registros são imutáveis — não podem ser editados">
                <Lock size={11} /> Imutável
              </span>
              {/* Câmera do celular direto para o cofre.
                  Escondida no Portal do Proprietário (readOnly): a custódia é
                  da marina, e quem alimenta o cofre é quem responde por ele.
                  O armador consulta; material dele entra pela mão do gerente. */}
              {!readOnly && (
                <button
                  onClick={() => setCameraAberta(true)}
                  className="flex items-center gap-2 px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.25em] border border-[#c5a059]/40 text-[#c5a059] bg-[#c5a059]/[0.08] hover:bg-[#c5a059]/[0.16] transition-colors"
                  title="Fotografar agora e enviar ao cofre"
                >
                  <Camera size={11} /> Fotografar
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Criterio da Conformidade.
          ESPELHA o calculo logo acima E a secao "Como Ler Este Indice" do
          dossie. Mexeu na regra, corrige os dois textos: criterio publicado
          errado e pior do que criterio nao publicado. */}
      {criterioAberto && (
        <div className="bg-[#021a3d]/40 border border-white/10 rounded-sm p-5 space-y-4 text-white/65 animate-in fade-in duration-200">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-white text-sm font-bold">Como estes dois números são calculados</h3>
            <button
              type="button"
              onClick={() => setCriterioAberto(false)}
              className="text-[10px] font-black uppercase tracking-wider text-white/40 hover:text-white/70 transition-colors"
            >
              Fechar
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-2">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#c5a059]">
                Índice de Custódia — o trabalho da marina
              </p>
              <p className="text-xs leading-relaxed">
                Mede <strong className="text-white/85">quanto da embarcação está documentado</strong>:
                abrangência das categorias com registro, volume de manutenção, documentos
                verificados e presença de laudo de casco. <strong className="text-white/85">Não
                avalia a condição do barco</strong> — a plataforma não inspeciona. Gold a partir
                de 90, Silver a partir de 60.
              </p>
            </div>

            <div className="space-y-2">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400/80">
                Conformidade — o estado do ativo
              </p>
              <p className="text-xs leading-relaxed">
                Média dos sistemas <strong className="text-white/85">que possuem registro</strong>:
                conforme vale 100, atenção 50, crítico 0. Sistema sem nenhum registro não entra
                na conta — não soma nem penaliza. Por isso o número vem sempre com o
                denominador: 100% sobre dois sistemas descreve uma amostra pequena, não uma
                embarcação em ordem.
              </p>
            </div>
          </div>

          <p className="text-[11px] leading-relaxed text-white/40 border-t border-white/10 pt-3">
            São perguntas diferentes e podem divergir: um barco muito bem documentado com uma
            avaria em aberto tem Índice de Custódia alto e Conformidade baixa. O Dossiê de
            Custódia traz os dois, e a seção <em>“Como Ler Este Índice”</em> detalha o critério —
            incluindo dois agravamentos que só existem no documento: ressalva em casco ou
            sinistro em aberto valem zero, e o mesmo para EPIRB com homologação ANATEL pendente.
          </p>
        </div>
      )}

      {/* ===== CONSENTIMENTO DO TITULAR ===== */}
      {/* Fica ENTRE os dados da embarcação e o painel técnico, de propósito:
          é atributo do ativo, não de um pedido. E fica visível sem clique
          porque a ausência dele é o que impede a liberação do dossiê — se
          estivesse dentro de uma aba, a marina só descobriria o problema no
          momento em que o comprador estivesse esperando. */}
      {!hideHeader && <ConsentimentoTitular ativoId={String(ativo.id)} />}

      {/* ===== BLOCO DE BAIXO — Painel Técnico (cards) ===== */}
      {!secao ? (
        <div className="space-y-6 animate-in fade-in duration-300">
          <div>
            <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
              <Wrench size={20} className="text-[#c5a059]" /> Painel Técnico
            </h2>
            <p className="text-white/30 text-[10px] mt-1.5 uppercase tracking-[0.3em] font-black">
              Acesso às categorias da embarcação
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-5">
            {cats.map((c) => {
              const n = contagem[c.key] || 0
              const st = statusDe(c)
              const hs = HEALTH_STYLE[st]
              const temRegistro = n > 0
              return (
                <button
                  key={c.key}
                  onClick={() => setSecao(c)}
                  className="group relative text-left bg-[#021431] border border-white/[0.06] rounded-sm p-7 transition-all duration-500 hover:border-[#c5a059]/40 hover:-translate-y-0.5 hover:bg-[#021a3d] shadow-xl overflow-hidden"
                >
                  <div className="absolute top-0 right-0 w-24 h-24 bg-[#c5a059]/0 group-hover:bg-[#c5a059]/5 blur-2xl rounded-full transition-all duration-700" />
                  <div className="relative z-10">
                    <div className="w-12 h-12 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] mb-6 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                      <c.icon size={22} strokeWidth={1.5} />
                    </div>
                    <h3 className="text-white text-base font-serif font-bold tracking-tight group-hover:text-[#c5a059] transition-colors">{c.titulo}</h3>
                    <p className="text-[9px] text-white/30 uppercase tracking-[0.2em] font-black mt-1">{c.subtitulo}</p>
                    <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/5">
                      <span className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${temRegistro ? 'bg-[#c5a059]' : hs.dot}`} />
                        <span className={`text-[9px] font-black uppercase tracking-[0.15em] ${temRegistro ? 'text-[#c5a059]' : hs.text}`}>
                          {temRegistro ? `${n} ${n === 1 ? 'registro' : 'registros'}` : 'Sem registro'}
                        </span>
                      </span>
                      <ChevronRight size={15} className="text-white/15 group-hover:text-[#c5a059] group-hover:translate-x-0.5 transition-all" />
                    </div>
                  </div>
                </button>
              )
            })}
          </div>

          {/* ===== Dossiê Completo & Laudos de Terceiros ===== */}
          {dossieExtra.length > 0 && (
            <div className="space-y-5 pt-4">
              <div>
                <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
                  <FileCheck size={20} className="text-[#c5a059]" /> Dossiê Completo & Laudos
                </h2>
                <p className="text-white/30 text-[10px] mt-1.5 uppercase tracking-[0.3em] font-black">
                  Procedência · especificações · laudos de terceiros · seguro — entram no dossiê
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-5">
                {dossieExtra.map((c) => {
                  const Icon = DOSSIE_EXTRA_ICONS[c.id] || FileCheck
                  const n = contagem[c.id] || 0
                  const temRegistro = n > 0
                  return (
                    <button
                      key={c.id}
                      onClick={() => setDossieAberta(c)}
                      className="group relative text-left bg-[#021431] border border-white/[0.06] rounded-sm p-7 transition-all duration-500 hover:border-[#c5a059]/40 hover:-translate-y-0.5 hover:bg-[#021a3d] shadow-xl overflow-hidden"
                    >
                      <div className="absolute top-0 right-0 w-24 h-24 bg-[#c5a059]/0 group-hover:bg-[#c5a059]/5 blur-2xl rounded-full transition-all duration-700" />
                      <div className="relative z-10">
                        <div className="w-12 h-12 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] mb-6 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                          <Icon size={22} strokeWidth={1.5} />
                        </div>
                        <h3 className="text-white text-base font-serif font-bold tracking-tight group-hover:text-[#c5a059] transition-colors">{c.label}</h3>
                        <p className="text-[9px] text-white/30 uppercase tracking-[0.2em] font-black mt-1 line-clamp-2">{c.descricao}</p>
                        <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/5">
                          <span className="flex items-center gap-2">
                            <span className={`w-1.5 h-1.5 rounded-full ${temRegistro ? 'bg-[#c5a059]' : 'bg-white/20'}`} />
                            <span className={`text-[9px] font-black uppercase tracking-[0.15em] ${temRegistro ? 'text-[#c5a059]' : 'text-white/30'}`}>
                              {temRegistro ? `${n} ${n === 1 ? 'registro' : 'registros'}` : 'Sem registro'}
                            </span>
                          </span>
                          <ChevronRight size={15} className="text-white/15 group-hover:text-[#c5a059] group-hover:translate-x-0.5 transition-all" />
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      ) : secao.key === 'fotos' ? (
        <CoberturaFotos ativo={ativo} onBack={() => setSecao(null)} readOnly={readOnly} />
      ) : secao.key === 'documentacao' ? (
        <UploadSecao categoria={secao} ativo={ativo} onBack={() => setSecao(null)} readOnly={readOnly} />
      ) : secao.key === 'dossie' ? (
        <DossieGeradorView ativo={ativo} onBack={() => setSecao(null)} />
      ) : (
        <SecaoDetalhe categoria={secao} ativo={ativo} onBack={() => setSecao(null)} readOnly={readOnly} />
      )}

      {dossieAberta && (
        <CategoriaForm
          categoria={dossieAberta}
          ativoId={ativo.id}
          ativoNome={`${ativo.marca} ${ativo.modelo}`}
          onClose={() => setDossieAberta(null)}
          onSaved={carregarContagem}
        />
      )}

      {cameraAberta && (
        <SecureCameraUpload
          ativoId={ativo.id}
          onUploadSuccess={() => {
            setCameraAberta(false)
            carregarContagem()
          }}
          onClose={() => setCameraAberta(false)}
        />
      )}
    </div>
  )
}

/* ===== Gerador de Dossiê - Controle de 4/Ano + Design Premium ===== */
function DossieGeradorView({ ativo, onBack }: { ativo: Ativo; onBack: () => void }) {
  const [loading, setLoading] = useState(false)
  // Nasce SEM número: o saldo vem do servidor. Começava em `remaining: 4`, e
  // isso fazia a tela afirmar "4 restantes" por um instante antes de saber —
  // que é exatamente a mentira que estamos consertando, só que mais curta.
  const [limite, setLimite] = useState<{ allowed: boolean; remaining: number; limiteAnual: number; resetDate?: Date }>(
    { allowed: true, remaining: 0, limiteAnual: 0 },
  )

  // O saldo vem do SERVIDOR, não do navegador.
  //
  // Ficava no `localStorage`, numa chave por ativo. A marina emitia três no
  // Chrome e o Edge continuava mostrando "4 restantes" — cada janela contava
  // sozinha, e o banco, que registra cada emissão com hash e hora, não era
  // consultado. Pior: como a trava era só aqui, trocar de navegador liberava
  // emissão sem fim.
  //
  // O que decide o que o gerente faz é o número NA TELA: ele lê "ainda pode
  // gerar" e promete o dossiê ao cliente. Por isso o conserto não é só gravar
  // certo — é a tela perguntar a quem sabe.
  const verificarLimite = async () => {
    try {
      const s = await api.dossie.saldo(ativo.id)
      setLimite({
        allowed: !!s.permitido,
        remaining: s.restantes ?? 0,
        limiteAnual: s.limite ?? 0,
        resetDate: s.reset_em ? new Date(s.reset_em) : undefined,
      })
    } catch {
      // Falhar aqui não pode travar a marina: o servidor recusa a emissão de
      // qualquer forma, então o botão segue habilitado e o erro aparece lá.
      setLimite({ allowed: true, remaining: 0, limiteAnual: 0 })
    }
  }

  useEffect(() => {
    verificarLimite()
  }, [ativo.id])

  const gerarPdf = async () => {
    if (!limite.allowed) return
    setLoading(true)
    try {
      const url = await api.dossie.pdfUrl(ativo.id)
      await verificarLimite()
      const a = document.createElement('a')
      a.href = url
      a.download = `dossie_${ativo.marca.toLowerCase()}_${ativo.modelo.toLowerCase()}_${ativo.id.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch (err: any) {
      alert('Erro ao gerar dossiê: ' + (err?.message || err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
          <ArrowLeft size={16} />
        </button>
        <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <FileCheck size={20} className="text-[#c5a059]" /> Gerar Dossiê de Custódia
          <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· Integridade Certificada</span>
        </h2>
      </div>

      <div className="bg-[#021431] border border-[#c5a059]/20 rounded-sm p-8 space-y-6">
        <div className="space-y-2">
          <h3 className="text-lg font-serif font-bold text-white">Relatório de Custódia Digital & Conformidade</h3>
          <p className="text-white/60 text-sm leading-relaxed">
            O Dossiê da embarcação compila todas as informações técnicas inseridas no painel técnico, diário de bordo e documentos. O documento gerado possui hash criptográfico SHA-256 e selo de conformidade com a LESTA e as normas da Marinha do Brasil (NORMAM).
          </p>
        </div>

        {/* Quadro de Saldo */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4 border-t border-white/5">
          <div className="bg-[#010c20]/50 border border-white/5 rounded-sm p-4 text-center">
            <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Limite por Ativo</p>
            <p className="text-2xl font-serif font-bold text-white mt-1">
              {limite.limiteAnual ? `${limite.limiteAnual} / Ano` : '—'}
            </p>
          </div>
          <div className="bg-[#010c20]/50 border border-white/5 rounded-sm p-4 text-center">
            <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Saldo Disponível</p>
            {/* Enquanto o servidor não respondeu, "—". Número antes da resposta
                seria chute, e chute na tela é o que gerou este conserto. */}
            <p className={`text-2xl font-serif font-bold mt-1 ${limite.remaining > 0 ? 'text-[#c5a059]' : 'text-rose-400'}`}>
              {limite.limiteAnual ? `${limite.remaining} dossiês` : '—'}
            </p>
          </div>
          <div className="bg-[#010c20]/50 border border-white/5 rounded-sm p-4 text-center">
            <p className="text-[9px] font-black uppercase tracking-widest text-white/40">Renovação de Limite</p>
            <p className="text-xs font-bold text-white mt-2">
              {limite.resetDate ? limite.resetDate.toLocaleDateString('pt-BR') : 'Sem restrições'}
            </p>
          </div>
        </div>

        {/* Estado da Geração */}
        {limite.allowed ? (
          <div className="flex flex-col items-center justify-center p-6 bg-white/[0.01] border border-dashed border-white/10 rounded-sm">
            {loading ? (
              <div className="text-center space-y-4">
                <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full mx-auto" />
                <p className="text-[10px] font-black text-[#c5a059] uppercase tracking-[0.2em]">Compilando registros e assinaturas digitais...</p>
                <p className="text-white/30 text-[9px] uppercase tracking-widest">Isso pode levar alguns instantes para consolidar fotos e vídeos.</p>
              </div>
            ) : (
              <div className="text-center space-y-4 w-full">
                <FileCheck size={48} className="mx-auto text-white/10" />
                <button
                  onClick={gerarPdf}
                  className="mx-auto flex items-center gap-3 bg-gradient-to-r from-[#c5a059] to-[#b38f4d] hover:from-[#d4b36d] hover:to-[#c5a059] text-[#010c20] px-8 py-4 rounded-sm text-xs font-black uppercase tracking-[0.25em] transition-all shadow-xl hover:scale-[1.02]"
                >
                  <Download size={16} /> Emitir Dossiê Criptografado
                </button>
                <p className="text-[9px] text-white/20 uppercase tracking-widest">
                  O download do arquivo PDF iniciará automaticamente
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-amber-500/10 border border-[#c5a059]/40 rounded-sm p-6 text-center space-y-3">
            <AlertTriangle className="mx-auto text-[#c5a059]" size={32} />
            <h3 className="text-white text-base font-bold font-serif">Limite Anual Atingido</h3>
            <p className="text-white/60 text-xs max-w-sm mx-auto">
              Esta embarcação atingiu o limite de 4 dossiês gerados por ano para evitar descontrole de versões.
            </p>
            {limite.resetDate && (
              <p className="text-[#c5a059] text-xs font-black uppercase tracking-wider mt-2">
                Próxima emissão disponível em: {limite.resetDate.toLocaleDateString('pt-BR')}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

/* ===== Documentação — UPLOAD real (Supabase Storage), cofre de documentos ===== */
function UploadSecao({ categoria, ativo, onBack, readOnly = false }: { categoria: Categoria; ativo: Ativo; onBack: () => void; readOnly?: boolean }) {
  const Icon = categoria.icon
  const [docs, setDocs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [descricao, setDescricao] = useState('')

  const carregar = async () => {
    setLoading(true)
    try {
      const data = await api.documentos.list(ativo.id)
      const arr = Array.isArray(data) ? data : []
      setDocs(arr.filter((d: any) => d.categoria === categoria.key))
    } catch {
      setDocs([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() /* eslint-disable-next-line */ }, [categoria.key, ativo.id])

  const handleFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || !files.length) return
    setUploading(true)
    try {
      for (const file of Array.from(files)) {
        const fd = new FormData()
        fd.append('file', file)
        await api.documentos.upload(ativo.id, 'documento', categoria.key, fd, null, descricao.trim() || undefined)
      }
      setDescricao('')
      await carregar()
    } catch {
      alert('Falha no upload. O primeiro envio pode levar ~20s (servidor acordando). Tente novamente se preciso.')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
          <ArrowLeft size={16} />
        </button>
        <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <Icon size={20} className="text-[#c5a059]" /> {categoria.titulo}
          <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· {categoria.subtitulo}</span>
        </h2>
      </div>

      {/* Descrição do que está sendo catalogado (opcional, salva com o arquivo) — some no modo visualização */}
      {!readOnly && (
      <div className="space-y-1.5">
        <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">O que é este documento?</label>
        <input
          type="text"
          value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          placeholder="Ex: TIE 2024 · Certificado de registro · Nota fiscal do motor"
          className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/20"
        />
        <p className="text-[9px] text-white/25 uppercase tracking-widest">Salva junto com o(s) arquivo(s) que você enviar a seguir.</p>
      </div>
      )}

      {!readOnly && (
      <label className={`block border border-dashed rounded-sm p-10 text-center transition-all ${
        uploading ? 'border-[#c5a059]/40 bg-[#c5a059]/5 pointer-events-none cursor-default'
        : 'border-white/10 hover:border-[#c5a059]/50 bg-white/[0.02] cursor-pointer'}`}>
        <input type="file" className="hidden" multiple accept={ACEITA_DOCUMENTO} disabled={uploading} onChange={handleFiles} />
        {uploading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full mb-4" />
            <span className="text-[10px] font-black text-[#c5a059] uppercase tracking-widest">Enviando e selando (SHA-256)...</span>
          </div>
        ) : (
          <>
            <Upload size={32} className="mx-auto text-white/15 mb-4" />
            <p className="text-white text-xs font-black uppercase tracking-widest mb-1">Enviar Documento</p>
            <p className="text-white/25 text-[10px] uppercase tracking-widest">{ROTULO_DOCUMENTO} até {TAMANHO_MAXIMO_MB}MB · pode selecionar várias</p>
          </>
        )}
      </label>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12"><div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full" /></div>
      ) : docs.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-12 bg-white/[0.01] border border-dashed border-white/10 rounded-sm">
          <Icon size={40} strokeWidth={1} className="text-white/10 mb-4" />
          <p className="text-white/50 text-sm font-bold uppercase tracking-[0.2em]">Cofre vazio</p>
        </div>
      ) : (
        <div className="space-y-2">
          {docs.map((d) => (
            <div key={d.id} className="bg-[#021431] border border-white/5 rounded-sm p-4 flex items-center justify-between gap-4 hover:border-[#c5a059]/20 transition-all">
              <div className="flex items-center gap-4 min-w-0">
                <div className="w-10 h-10 flex-shrink-0 bg-[#050b18] border border-white/5 rounded-sm flex items-center justify-center text-[#c5a059]"><FileText size={18} /></div>
                <div className="min-w-0">
                  <p className="text-white text-sm font-bold truncate">{d.descricao || d.nome_arquivo}</p>
                  <p className="text-white/30 text-[9px] uppercase tracking-widest mt-0.5 truncate">{d.descricao ? `${d.nome_arquivo} · ` : ''}{((d.tamanho_bytes || 0) / 1024).toFixed(0)} KB · {d.created_at ? new Date(d.created_at).toLocaleDateString('pt-BR') : ''}</p>
                </div>
              </div>
              <a href={d.url_arquivo} target="_blank" rel="noopener noreferrer" download className="flex-shrink-0 text-white/30 hover:text-[#c5a059] p-2 transition-all"><Download size={18} /></a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ===== Painel de uma categoria — FUNCIONAL (lista + cria registro real) ===== */
const STATUS_OPCOES = [
  { v: 'registrado', label: 'Registrado' },
  { v: 'concluido', label: 'Concluído' },
  { v: 'pendente', label: 'Pendente' },
  { v: 'atencao', label: 'Atenção' },
]
const STATUS_COR: Record<string, string> = {
  registrado: 'text-[#c5a059] border-[#c5a059]/30 bg-[#c5a059]/10',
  concluido: 'text-emerald-400 border-emerald-400/30 bg-emerald-400/10',
  pendente: 'text-amber-400 border-amber-400/30 bg-amber-400/10',
  atencao: 'text-rose-400 border-rose-400/30 bg-rose-400/10',
}

function SecaoDetalhe({ categoria, ativo, onBack, readOnly = false }: { categoria: Categoria; ativo: Ativo; onBack: () => void; readOnly?: boolean }) {
  const Icon = categoria.icon
  const isManut = categoria.key === 'manutencao'
  const cfg = SERVICOS[categoria.key]
  const [registros, setRegistros] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  // Registro selecionado para retificação (null = painel fechado)
  const [retificando, setRetificando] = useState<any | null>(null)
  const agora = new Date()
  const hojeLocal = new Date(agora.getTime() - agora.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
  const formVazio = { titulo: '', responsavel: '', data: hojeLocal, hora: agora.toTimeString().slice(0, 5), local: '', custo: '', observacao: '', status: 'registrado' }
  const [form, setForm] = useState(formVazio)

  const carregar = async () => {
    setLoading(true)
    try {
      const data = await api.registros.list(ativo.id)
      const arr = Array.isArray(data) ? data : []
      setRegistros(arr.filter((r: any) => r.categoria === categoria.key))
    } catch {
      setRegistros([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { carregar() /* eslint-disable-next-line */ }, [categoria.key, ativo.id])

  const salvar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.titulo.trim()) return
    setSaving(true)
    try {
      const dados: Record<string, string> = {}
      if (form.responsavel.trim()) dados.responsavel = form.responsavel.trim()
      if (form.data) dados.data_servico = form.data
      if (form.hora) dados.hora = form.hora
      if (form.local.trim()) dados.local = form.local.trim()
      if (form.custo.trim()) dados.custo = form.custo.trim()
      await api.registros.create({
        ativo_id: ativo.id,
        categoria: categoria.key,
        titulo: form.titulo.trim(),
        observacao: form.observacao.trim() || undefined,
        dados,
        status: form.status as any,
      })
      setForm(formVazio)
      setShowForm(false)
      await carregar()
    } catch {
      alert('Não foi possível salvar o registro. Verifique a conexão com o servidor.')
    } finally {
      setSaving(false)
    }
  }

  const inputCls = 'w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-3 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/20'

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
            <ArrowLeft size={16} />
          </button>
          <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
            <Icon size={20} className="text-[#c5a059]" /> {categoria.titulo}
            <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· {categoria.subtitulo}</span>
          </h2>
        </div>
        {!readOnly && (
        <button onClick={() => setShowForm((s) => !s)} className="flex items-center gap-2 bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-6 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.2em] transition-all">
          {showForm ? <X size={15} /> : <Plus size={15} />}
          {showForm ? 'Fechar' : isManut ? 'Nova Ordem de Serviço' : 'Adicionar Registro'}
        </button>
        )}
      </div>

      {!readOnly && showForm && cfg && (
        <FichaServicoForm
          categoriaKey={categoria.key}
          categoriaTitulo={categoria.titulo}
          ativoId={ativo.id}
          config={cfg}
          onSaved={() => { setShowForm(false); carregar() }}
          onCancel={() => setShowForm(false)}
        />
      )}

      {retificando && (
        <RetificarRegistro
          registro={retificando}
          ativoId={ativo.id}
          onPronto={() => { setRetificando(null); carregar() }}
          onCancelar={() => setRetificando(null)}
        />
      )}

      {!readOnly && showForm && !cfg && (
        <form onSubmit={salvar} className="bg-[#021431] border border-white/10 rounded-sm p-6 space-y-4 animate-in slide-in-from-top-2 duration-300">
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">{isManut ? 'Serviço executado' : 'Título'}</label>
              <input className={inputCls} value={form.titulo} onChange={(e) => setForm({ ...form, titulo: e.target.value })} placeholder={isManut ? 'Ex: Revisão dos motores' : 'Ex: Renovação do seguro'} required />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Quem fez / responsável</label>
              <input className={inputCls} value={form.responsavel} onChange={(e) => setForm({ ...form, responsavel: e.target.value })} placeholder="Técnico, empresa, marina..." />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Data do serviço</label>
              <input type="date" className={inputCls} value={form.data} onChange={(e) => setForm({ ...form, data: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Hora</label>
              <input type="time" className={inputCls} value={form.hora} onChange={(e) => setForm({ ...form, hora: e.target.value })} />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Local / Oficina</label>
              <input className={inputCls} value={form.local} onChange={(e) => setForm({ ...form, local: e.target.value })} placeholder="Opcional" />
            </div>
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Custo (R$)</label>
              <input className={inputCls} value={form.custo} onChange={(e) => setForm({ ...form, custo: e.target.value })} placeholder="Opcional" />
            </div>
          </div>
          <div className="space-y-1.5">
            <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Observação</label>
            <textarea className={inputCls + ' resize-none'} rows={2} value={form.observacao} onChange={(e) => setForm({ ...form, observacao: e.target.value })} placeholder="Detalhes do registro..." />
          </div>
          <div className="flex items-end justify-between gap-4 flex-wrap">
            <div className="space-y-1.5">
              <label className="text-[9px] font-black uppercase tracking-[0.25em] text-white/40">Status</label>
              <select className={inputCls + ' min-w-[160px]'} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                {STATUS_OPCOES.map((s) => <option key={s.v} value={s.v} className="bg-[#010c20]">{s.label}</option>)}
              </select>
            </div>
            <button type="submit" disabled={saving} className="bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 text-[#010c20] px-8 py-3 rounded-sm text-[10px] font-black uppercase tracking-[0.2em] transition-all">
              {saving ? 'Salvando...' : 'Salvar Registro'}
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin w-8 h-8 border-2 border-[#c5a059] border-t-transparent rounded-full" />
        </div>
      ) : registros.length === 0 ? (
        <div className="flex flex-col items-center justify-center text-center py-16 bg-white/[0.01] border border-dashed border-white/10 rounded-sm">
          <Icon size={40} strokeWidth={1} className="text-white/10 mb-4" />
          <p className="text-white/50 text-sm font-bold uppercase tracking-[0.2em]">Nada registrado ainda</p>
          {!readOnly && (
            <p className="text-white/25 text-xs mt-2">Clique em "{isManut ? 'Nova Ordem de Serviço' : 'Adicionar Registro'}" para criar o primeiro.</p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {registros.map((r) => (
            <div
              key={r.id}
              className={`rounded-sm p-5 transition-all border ${
                r.situacao === 'retificado'
                  ? 'bg-[#021431]/50 border-amber-500/25 opacity-70'
                  : r.situacao === 'retificador'
                  ? 'bg-[#021431] border-blue-500/25'
                  : 'bg-[#021431] border-white/5 hover:border-[#c5a059]/20'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className={`font-bold text-sm ${r.situacao === 'retificado' ? 'text-white/60 line-through decoration-amber-500/50' : 'text-white'}`}>
                    {r.titulo || '(sem título)'}
                  </p>
                  {(r.dados?.responsavel || r.dados?.data_servico || r.dados?.local || r.dados?.custo) && (
                    <p className="text-white/45 text-[11px] mt-1">
                      {r.dados?.responsavel ? `Por ${r.dados.responsavel}` : ''}
                      {r.dados?.data_servico ? ` · ${String(r.dados.data_servico).split('-').reverse().join('/')}` : ''}
                      {r.dados?.hora ? ` às ${r.dados.hora}` : ''}
                      {r.dados?.local ? ` · ${r.dados.local}` : ''}
                      {r.dados?.custo ? ` · R$ ${r.dados.custo}` : ''}
                    </p>
                  )}
                  {r.observacao && <p className="text-white/40 text-xs mt-2 leading-relaxed">{r.observacao}</p>}

                  {/* Cadeia de retificação — o erro e a correção ficam os dois à vista */}
                  {r.situacao === 'retificado' && (
                    <p className="mt-2 text-[11px] leading-relaxed text-amber-300/80 bg-amber-500/[0.07] border-l-2 border-amber-500 rounded-sm px-3 py-2">
                      <strong className="uppercase tracking-wider text-[9px]">Retificado posteriormente.</strong>{' '}
                      {r.retificado_motivo}{' '}
                      <span className="text-white/35">Este registro permanece selado e íntegro.</span>
                    </p>
                  )}
                  {r.situacao === 'retificador' && r.motivo_retificacao && (
                    <p className="mt-2 text-[11px] leading-relaxed text-blue-300/80 bg-blue-500/[0.07] border-l-2 border-blue-500 rounded-sm px-3 py-2">
                      <strong className="uppercase tracking-wider text-[9px]">Corrige um registro anterior.</strong>{' '}
                      {r.motivo_retificacao}
                    </p>
                  )}
                </div>
                <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
                  <span className={`px-3 py-1 rounded-sm text-[8px] font-black uppercase tracking-[0.15em] border ${STATUS_COR[r.status] || STATUS_COR.registrado}`}>
                    {r.status}
                  </span>
                  {r.situacao === 'retificado' && (
                    <span className="px-3 py-1 rounded-sm text-[8px] font-black uppercase tracking-[0.15em] border text-amber-500 border-amber-500/25 bg-amber-500/5">
                      Retificado
                    </span>
                  )}
                  {r.situacao === 'retificador' && (
                    <span className="px-3 py-1 rounded-sm text-[8px] font-black uppercase tracking-[0.15em] border text-blue-400 border-blue-500/25 bg-blue-500/5">
                      Retificação
                    </span>
                  )}
                  {/* Só o registro vigente pode ser retificado: o já retificado
                      tem sucessor, e o banco recusa retificar o mesmo alvo 2×. */}
                  {!readOnly && r.situacao !== 'retificado' && (
                    <button
                      onClick={() => setRetificando(r)}
                      title="Corrigir este registro — o original permanece no histórico"
                      className="mt-1 flex items-center gap-1.5 text-[8px] font-black uppercase tracking-[0.15em]
                                 text-white/30 hover:text-blue-300 transition-colors"
                    >
                      <PenLine size={11} /> Retificar
                    </button>
                  )}
                </div>
              </div>
              {/* Métricas-chave da ficha rica */}
              {(r.dados?.horimetro || r.dados?.valor || r.dados?.tipo || r.dados?.peca_descricao) && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {r.dados?.tipo && <span className="text-[9px] font-black uppercase tracking-widest text-white/50 bg-white/5 border border-white/10 px-2.5 py-1 rounded-sm">{r.dados.tipo}</span>}
                  {r.dados?.horimetro && <span className="text-[9px] font-black uppercase tracking-widest text-[#c5a059] bg-[#c5a059]/10 border border-[#c5a059]/20 px-2.5 py-1 rounded-sm">{r.dados.horimetro}h motor</span>}
                  {r.dados?.valor && <span className="text-[9px] font-black uppercase tracking-widest text-emerald-300/80 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-sm">R$ {r.dados.valor}</span>}
                  {r.dados?.peca_descricao && <span className="text-[9px] font-black uppercase tracking-widest text-white/50 bg-white/5 border border-white/10 px-2.5 py-1 rounded-sm">Peça: {r.dados.peca_descricao}</span>}
                </div>
              )}

              {/* Evidências seladas (SHA-256) */}
              {Array.isArray(r.dados?.evidencias) && r.dados.evidencias.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-3 items-end">
                  {r.dados.evidencias.map((ev: any, i: number) => {
                    const isImg = /\.(png|jpe?g|webp)$/i.test(ev.nome || ev.url || '')
                    const isVid = /\.(mp4|mov|qt|webm)$/i.test(ev.nome || ev.url || '')
                    
                    if (isImg) {
                      return (
                        <a key={i} href={ev.url} target="_blank" rel="noopener noreferrer" title={`${ev.slot} · SHA-256 ${ev.hash?.slice(0, 12)}…`}
                          className="group relative w-14 h-14 rounded-sm overflow-hidden border border-white/10 hover:border-[#c5a059]/50 transition-all shrink-0">
                          <img src={ev.url} alt={ev.slot} className="w-full h-full object-cover" loading="lazy" />
                          <span className="absolute bottom-0 inset-x-0 bg-[#010c20]/80 text-[#c5a059] text-[6px] font-black uppercase tracking-wider text-center py-0.5">
                            {ev.slot === 'peca_nova' ? 'nova' : ev.slot === 'peca_velha' ? 'velha' : 'foto'}
                          </span>
                        </a>
                      )
                    } else if (isVid) {
                      return (
                        <div key={i} className="flex flex-col gap-1 shrink-0">
                          <video 
                            src={ev.url} 
                            controls 
                            preload="metadata"
                            className="w-48 h-28 rounded-sm border border-white/10 hover:border-[#c5a059]/50 bg-black outline-none" 
                          />
                          <span className="text-[7px] text-[#c5a059] font-black uppercase tracking-widest text-center" title={`${ev.slot} · SHA-256: ${ev.hash}`}>
                            🎥 {ev.slot}
                          </span>
                        </div>
                      )
                    } else {
                      return (
                        <a key={i} href={ev.url} target="_blank" rel="noopener noreferrer" title={`SHA-256 ${ev.hash?.slice(0, 16)}…`}
                          className="flex items-center gap-1.5 text-[9px] font-black uppercase tracking-widest text-[#c5a059] bg-[#c5a059]/10 border border-[#c5a059]/20 px-2.5 py-1.5 rounded-sm hover:bg-[#c5a059]/20 transition-all shrink-0">
                          <FileText size={11} /> {ev.slot === 'nota_fiscal' ? 'Nota fiscal' : 'Doc'} <Lock size={9} />
                        </a>
                      )
                    }
                  })}
                </div>
              )}

              <div className="mt-3 pt-3 border-t border-white/5 flex flex-wrap items-center gap-x-4 gap-y-1 text-white/25 text-[9px] font-black uppercase tracking-[0.2em]">
                <span className="flex items-center gap-2"><CalendarClock size={12} />{r.created_at ? new Date(r.created_at).toLocaleString('pt-BR') : ''}</span>
                {r.dados?.enviado_por && <span className="flex items-center gap-1.5"><Lock size={10} /> Enviado por {r.dados.enviado_por}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
