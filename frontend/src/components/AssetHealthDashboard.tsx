import { 
  FileText, 
  Wrench, 
  Zap, 
  Cpu, 
  Shield, 
  Paintbrush, 
  Armchair, 
  FileCheck,
  AlertCircle,
  CheckCircle2,
  Info,
  HelpCircle,
  ChevronDown
} from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

export type HealthStatus = 'ok' | 'warning' | 'critical' | 'info' | 'na'

interface HealthItemProps {
  category: string
  status: HealthStatus
  label: string
  icon: React.ElementType
  onClick?: () => void
}

const statusColors = {
  ok: 'text-emerald-500 border-emerald-500/20 bg-emerald-500/5',
  warning: 'text-amber-500 border-amber-500/20 bg-amber-500/5',
  critical: 'text-rose-500 border-rose-500/20 bg-rose-500/5',
  info: 'text-blue-500 border-blue-500/20 bg-blue-500/5',
  na: 'text-zinc-500 border-zinc-500/20 bg-zinc-500/5',
}

const statusIcons = {
  ok: CheckCircle2,
  warning: AlertCircle,
  critical: AlertCircle,
  info: Info,
  na: HelpCircle,
}

function HealthItem({ status, label, icon: Icon, onClick }: HealthItemProps) {
  const StatusIcon = statusIcons[status]
  
  return (
    <button 
      onClick={onClick}
      className={`group relative flex flex-col items-center justify-center p-6 rounded-sm border transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] ${statusColors[status]}`}
    >
      <div className="mb-4 relative">
        <Icon size={32} strokeWidth={1.5} className="group-hover:scale-110 transition-transform duration-500" />
        <div className="absolute -top-1 -right-1">
          <StatusIcon size={14} className="fill-current bg-[#010c20] rounded-full" />
        </div>
      </div>
      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-center leading-tight">
        {label}
      </span>
      
      {/* Glow Effect */}
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 blur-xl transition-opacity duration-500 -z-10 ${
        status === 'ok' ? 'bg-emerald-500/20' : 
        status === 'warning' ? 'bg-amber-500/20' : 
        status === 'critical' ? 'bg-rose-500/20' : 
        status === 'info' ? 'bg-blue-500/20' : 'bg-zinc-500/20'
      }`}></div>
    </button>
  )
}

interface AssetHealthDashboardProps {
  healthData?: Record<string, HealthStatus>
  onCategoryClick?: (category: string) => void
  mode?: 'full' | 'operational'
}

export default function AssetHealthDashboard({ healthData, onCategoryClick, mode = 'full' }: AssetHealthDashboardProps) {
  const { t } = useTranslation()

  const categories = [
    { id: 'documentacao', icon: FileText },
    { id: 'manutencao', icon: Wrench },
    { id: 'motor', icon: Zap },
    { id: 'eletrica', icon: Cpu },
    { id: 'seguranca', icon: Shield },
    { id: 'pintura', icon: Paintbrush },
    { id: 'interior', icon: Armchair },
    { id: 'dossie', icon: FileCheck },
  ]

  // Se for o Relatório Básico (operacional), removemos documentos, pintura, interior e dossiê.
  // Focamos apenas no que importa para o barco sair com segurança.
  const displayCategories = mode === 'operational' 
    ? categories.filter(c => ['manutencao', 'motor', 'eletrica', 'seguranca'].includes(c.id))
    : categories;

  // Quantas categorias têm registro. É o DENOMINADOR, e ele fica visível:
  // 100% sobre 2 categorias não é a mesma notícia que 100% sobre 8.
  const avaliadas = displayCategories.filter(
    c => healthData?.[c.id] && healthData[c.id] !== 'na'
  ).length

  // Calcula a porcentagem baseada apenas nos itens exibidos.
  //
  // Devolve null quando NADA foi avaliado. Antes devolvia 100 em dois
  // caminhos — sem healthData, e com todas as categorias 'na' — e um barco
  // recém-cadastrado, sem um único registro, exibia "Índice de Segurança
  // 100%" com a barra verde cheia. O backend já tratava isso: `_prontidao`
  // retorna None porque "melhor não exibir indicador do que exibir um
  // inventado".
  const calculateHealthPercentage = () => {
    if (!healthData) return null
    let score = 0
    let total = displayCategories.length

    displayCategories.forEach(cat => {
      const status = healthData[cat.id]
      if (status === 'ok' || status === 'info') score += 100
      else if (status === 'warning') score += 50
      else if (status === 'critical') score += 0
      else if (status === 'na') total -= 1 // Ignora os N/A da média
    })

    if (total === 0) return null
    return Math.round(score / total)
  }

  const percentage = calculateHealthPercentage()
  const semDados = percentage === null
  const corIndice = semDados
    ? 'text-white/40'
    : percentage >= 80 ? 'text-emerald-400'
    : percentage >= 50 ? 'text-amber-400' : 'text-rose-400'

  const [criterioAberto, setCriterioAberto] = useState(false)

  return (
    <div className="w-full space-y-6">
      {/* Relatório Básico / Barra de Porcentagem */}
      <div className="bg-[#021a3d]/50 border border-white/10 rounded-sm p-5 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-inner">
        <div>
           <h4 className="text-white text-sm font-bold flex items-center gap-2">
             <Zap size={16} className={corIndice} />
             {mode === 'operational' ? 'Prontidão de Navegação' : 'Prontidão Operacional'}
           </h4>
           <p className="text-[10px] text-white/40 uppercase tracking-[0.2em] mt-1">
             {mode === 'operational' ? 'Itens Críticos para Saída Segura' : 'Relatório Básico de Saúde'}
           </p>
        </div>
        
        <div className="flex-1 max-w-md w-full">
           <div className="flex items-end justify-between mb-2">
              <span className={`text-[10px] font-black uppercase tracking-widest ${corIndice}`}>
                Índice de Segurança
              </span>
              <span className="text-xl font-serif font-bold text-white tracking-tight">
                {semDados ? '—' : `${percentage}%`}
              </span>
           </div>

           {/* Sem nenhum sistema avaliado não existe barra: barra vazia lê-se
               como "zero, ruim" e barra cheia como "tudo certo". Nenhuma das
               duas é verdade quando ninguém olhou nada ainda. */}
           {!semDados && (
             <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/10 relative">
                <div
                  className={`absolute top-0 left-0 h-full rounded-full transition-all duration-1000 ${
                    percentage >= 80 ? "bg-gradient-to-r from-emerald-500/50 to-emerald-400" :
                    percentage >= 50 ? "bg-gradient-to-r from-amber-500/50 to-amber-400" :
                    "bg-gradient-to-r from-rose-500/50 to-rose-400"
                  }`}
                  style={{ width: `${percentage}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 w-full h-full animate-[shimmer_2s_infinite]"></div>
                </div>
             </div>
           )}

           {/* O denominador anda junto com o número, sempre. */}
           <div className="flex items-center justify-between gap-3 mt-2">
             <span className="text-[10px] text-white/40 leading-tight">
               {semDados
                 ? `Nenhum dos ${displayCategories.length} sistemas possui registro.`
                 : `Calculado sobre ${avaliadas} de ${displayCategories.length} sistemas com registro.`}
             </span>
             <button
               type="button"
               onClick={() => setCriterioAberto(v => !v)}
               aria-expanded={criterioAberto}
               className="shrink-0 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-white/50 hover:text-white/80 transition-colors"
             >
               Saiba mais
               <ChevronDown
                 size={12}
                 className={`transition-transform duration-300 ${criterioAberto ? 'rotate-180' : ''}`}
               />
             </button>
           </div>
        </div>
      </div>

      {/* Critério do índice.
          Espelha `calculateHealthPercentage` LOGO ACIMA — mexeu no cálculo,
          corrige o texto. Critério publicado errado é pior do que critério
          não publicado: aqui ele deixa de ser opinião e passa a ser algo que
          a marina pode defender na frente do comprador. */}
      {criterioAberto && (
        <div className="bg-[#021a3d]/30 border border-white/10 rounded-sm p-5 space-y-4 text-white/60">
          <p className="text-xs leading-relaxed">
            O Índice de Segurança resume o estado dos sistemas a partir
            <strong className="text-white/80"> exclusivamente</strong> dos registros
            já selados. Não é vistoria nem laudo pericial: mede o que foi
            registrado, não o que existe a bordo.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {[
              ['Conforme', 'Sem pendência ou ressalva.', '100', 'text-emerald-400'],
              ['Atenção', 'Pendência ou ressalva técnica.', '50', 'text-amber-400'],
              ['Crítico', 'Ressalva de risco à segurança.', '0', 'text-rose-400'],
              ['Não avaliado', 'Sem nenhum registro.', 'fora da média', 'text-zinc-400'],
            ].map(([nome, desc, peso, cor]) => (
              <div key={nome} className="flex items-baseline gap-2 text-[11px]">
                <span className={`font-bold uppercase tracking-wider ${cor} shrink-0`}>{nome}</span>
                <span className="flex-1 leading-snug">{desc}</span>
                <span className="font-mono text-white/70 shrink-0">{peso}</span>
              </div>
            ))}
          </div>

          <p className="text-xs leading-relaxed">
            <strong className="text-white/80">Cálculo.</strong> É a média dos pesos das
            categorias avaliadas. Categoria sem registro não entra na conta — não soma
            nem penaliza. Por isso o índice vem sempre acompanhado de quantas categorias
            possuem registro: 100% sobre duas categorias descreve uma amostra pequena,
            não uma embarcação em ordem. Sem nenhum registro o índice não é exibido, em
            vez de exibir um número inventado.
          </p>

          <p className="text-[11px] leading-relaxed text-white/40">
            O Dossiê de Custódia aplica o mesmo critério, com dois agravamentos que só
            existem lá: ressalva em casco ou sinistro em aberto vale zero, e o mesmo
            para EPIRB com homologação ANATEL pendente. A seção “Como Ler Este Índice”,
            no dossiê, traz o critério completo.
          </p>
        </div>
      )}

      {/* Grid de Ícones */}
      <div className={`grid gap-4 w-full ${mode === 'operational' ? 'grid-cols-2 md:grid-cols-4' : 'grid-cols-2 md:grid-cols-4'}`}>
      {displayCategories.map((cat) => (
        <HealthItem 
          key={cat.id}
          category={cat.id}
          status={healthData?.[cat.id] || 'na'}
          label={t(`asset_health.${cat.id}`)}
          icon={cat.icon}
          onClick={() => onCategoryClick?.(cat.id)}
        />
      ))}
      </div>
    </div>
  )
}
