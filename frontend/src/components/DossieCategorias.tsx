import { useEffect, useState } from 'react'
import {
  FileText, Anchor, Users, Ship, Gauge, Cpu, Wrench, ClipboardCheck,
  Waves, AlertTriangle, Camera, Sailboat, Armchair, TrendingUp, ShieldCheck, Globe, ChevronRight,
} from 'lucide-react'
import { categoriasParaPorte, categoriasPorGrupo, type Categoria } from '../config/dossieCategorias'
import { api } from '../services/api'
import CategoriaForm from './CategoriaForm'

const ICONES: Record<string, React.ElementType> = {
  Anchor, Users, FileText, Ship, Gauge, Cpu, Wrench, ClipboardCheck,
  Waves, AlertTriangle, Camera, Sailboat, Armchair, TrendingUp, ShieldCheck, Globe,
}

interface Props {
  ativoId: string
  ativoNome: string
  comprimentoPes: number
}

export default function DossieCategorias({ ativoId, ativoNome, comprimentoPes }: Props) {
  const [aberta, setAberta] = useState<Categoria | null>(null)
  const [contagem, setContagem] = useState<Record<string, number>>({})

  const carregar = () => {
    api.registros
      .list(ativoId)
      .then((data: any[]) => {
        const c: Record<string, number> = {}
        ;(data || []).forEach((r) => {
          c[r.categoria] = (c[r.categoria] || 0) + 1
        })
        setContagem(c)
      })
      .catch(() => {})
  }

  useEffect(() => {
    if (ativoId) carregar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ativoId])

  const disponiveis = categoriasParaPorte(comprimentoPes)
  const grupos = categoriasPorGrupo(disponiveis)

  return (
    <div className="space-y-10">
      <div>
        <h3 className="text-xl font-serif font-bold text-white tracking-tight">Dossiê do Ativo</h3>
        <p className="text-[10px] text-white/30 uppercase tracking-[0.3em] font-black mt-2">
          Categorias aplicáveis a este porte ({comprimentoPes} pés)
        </p>
      </div>

      {grupos.map(({ grupo, label, categorias }) => (
        <div key={grupo} className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#c5a059]">{label}</span>
            <div className="h-px flex-1 bg-white/5" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {categorias.map((cat) => {
              const Icon = ICONES[cat.icon] || FileText
              const n = contagem[cat.id] || 0
              return (
                <button
                  key={cat.id}
                  onClick={() => setAberta(cat)}
                  className="group bg-[#0a2540] border border-white/5 rounded-sm p-5 text-left hover:border-[#c5a059]/40 transition-all duration-500 hover:-translate-y-0.5 relative"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-11 h-11 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all">
                      <Icon size={20} strokeWidth={1.5} />
                    </div>
                    {n > 0 ? (
                      <span className="text-[9px] font-black uppercase tracking-widest text-[#c5a059] bg-[#c5a059]/10 border border-[#c5a059]/20 px-2 py-1 rounded-sm">
                        {n} registro{n > 1 ? 's' : ''}
                      </span>
                    ) : (
                      <span className="text-[9px] font-black uppercase tracking-widest text-white/20">vazio</span>
                    )}
                  </div>
                  <p className="text-white font-bold text-sm tracking-wide group-hover:text-[#c5a059] transition-colors">{cat.label}</p>
                  <p className="text-[10px] text-white/30 leading-relaxed mt-1.5 line-clamp-2">{cat.descricao}</p>
                  <div className="mt-4 flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-white/20 group-hover:text-[#c5a059] transition-colors">
                    Abrir <ChevronRight size={12} />
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ))}

      {aberta && (
        <CategoriaForm
          categoria={aberta}
          ativoId={ativoId}
          ativoNome={ativoNome}
          onClose={() => setAberta(null)}
          onSaved={carregar}
        />
      )}
    </div>
  )
}
