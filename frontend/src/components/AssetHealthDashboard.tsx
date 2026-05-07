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
  HelpCircle
} from 'lucide-react'
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

  // Calcula a porcentagem baseada apenas nos itens exibidos
  const calculateHealthPercentage = () => {
    if (!healthData) return 100
    let score = 0
    let total = displayCategories.length
    
    displayCategories.forEach(cat => {
      const status = healthData[cat.id]
      if (status === 'ok' || status === 'info') score += 100
      else if (status === 'warning') score += 50
      else if (status === 'critical') score += 0
      else if (status === 'na') total -= 1 // Ignora os N/A da média
    })
    
    if (total === 0) return 100
    return Math.round(score / total)
  }

  const percentage = calculateHealthPercentage()

  return (
    <div className="w-full space-y-6">
      {/* Relatório Básico / Barra de Porcentagem */}
      <div className="bg-[#021a3d]/50 border border-white/10 rounded-sm p-5 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-inner">
        <div>
           <h4 className="text-white text-sm font-bold flex items-center gap-2">
             <Zap size={16} className={percentage >= 80 ? "text-emerald-400" : percentage >= 50 ? "text-amber-400" : "text-rose-400"} />
             {mode === 'operational' ? 'Prontidão de Navegação' : 'Prontidão Operacional'}
           </h4>
           <p className="text-[10px] text-white/40 uppercase tracking-[0.2em] mt-1">
             {mode === 'operational' ? 'Itens Críticos para Saída Segura' : 'Relatório Básico de Saúde'}
           </p>
        </div>
        
        <div className="flex-1 max-w-md w-full">
           <div className="flex items-end justify-between mb-2">
              <span className={`text-[10px] font-black uppercase tracking-widest ${percentage >= 80 ? "text-emerald-400" : percentage >= 50 ? "text-amber-400" : "text-rose-400"}`}>
                Índice de Segurança
              </span>
              <span className="text-xl font-serif font-bold text-white tracking-tight">{percentage}%</span>
           </div>
           
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
        </div>
      </div>

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
