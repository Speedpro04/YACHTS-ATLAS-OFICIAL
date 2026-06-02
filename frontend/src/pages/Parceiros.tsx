import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search, ArrowRight, Phone, Mail, Globe, MapPin, BadgeCheck,
  Briefcase, ShieldCheck, Tractor, Forklift, Truck, Container, Cog, Wrench, Hammer,
} from 'lucide-react'
import {
  CATEGORIAS_PARCEIRO, categoriasParceiroPorGrupo, type CategoriaParceiro,
} from '../config/parceirosCategorias'
import { api } from '../services/api'

const ICONES: Record<string, React.ElementType> = {
  Briefcase, ShieldCheck, Tractor, Forklift, Truck, Container, Cog, Wrench, Hammer,
}

interface Parceiro {
  id: string
  categoria: string
  nome: string
  cidade?: string
  telefone?: string
  email?: string
  site?: string
  verificado?: boolean
}

// Rede em formação (programa fundador). A lista cresce conforme parceiros entram.
const PARCEIROS: Parceiro[] = []

export default function Parceiros() {
  const navigate = useNavigate()
  const [filtro, setFiltro] = useState<string>('todos')
  const [busca, setBusca] = useState('')

  const grupos = categoriasParceiroPorGrupo()

  const visiveis = PARCEIROS.filter((p) => {
    const okCat = filtro === 'todos' || p.categoria === filtro
    const okBusca = p.nome.toLowerCase().includes(busca.toLowerCase())
    return okCat && okBusca
  })

  const labelCategoria = (id: string) =>
    CATEGORIAS_PARCEIRO.find((c) => c.id === id)?.label || id

  return (
    <div className="space-y-12 animate-in fade-in duration-700">
      {/* Cabeçalho */}
      <div className="border-b border-white/5 pb-10">
        <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-3">Parceiros Atlas</h1>
        <p className="text-white/50 font-light leading-relaxed max-w-2xl">
          Conectamos você aos melhores serviços náuticos. O Yachts Atlas é a ponte —
          o contato e a contratação são feitos <span className="text-white/80">direto com o parceiro</span>.
        </p>
      </div>

      {/* Busca */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20" size={18} />
          <input
            type="text"
            placeholder="Buscar parceiro..."
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            className="w-full bg-[#021431] border border-white/10 rounded-sm pl-12 pr-5 py-4 text-white text-sm outline-none focus:border-[#c5a059] transition-all placeholder:text-white/15"
          />
        </div>
      </div>

      {/* Filtro por categoria (agrupado) */}
      <div className="space-y-5">
        <button
          onClick={() => setFiltro('todos')}
          className={`text-[10px] font-black uppercase tracking-[0.25em] px-5 py-2.5 rounded-sm border transition-all ${
            filtro === 'todos' ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' : 'border-white/10 text-white/50 hover:text-white hover:border-white/20'
          }`}
        >
          Todas as categorias
        </button>

        {grupos.map(({ grupo, label, categorias }) => (
          <div key={grupo} className="space-y-3">
            <p className="text-[9px] font-black uppercase tracking-[0.3em] text-white/25">{label}</p>
            <div className="flex flex-wrap gap-2">
              {categorias.map((cat: CategoriaParceiro) => {
                const Icon = ICONES[cat.icon] || Briefcase
                const ativo = filtro === cat.id
                return (
                  <button
                    key={cat.id}
                    onClick={() => setFiltro(cat.id)}
                    className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] px-4 py-2.5 rounded-sm border transition-all ${
                      ativo ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' : 'bg-[#021431] border-white/10 text-white/50 hover:text-white hover:border-[#c5a059]/30'
                    }`}
                  >
                    <Icon size={14} />
                    {cat.label}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Lista de parceiros (grid p/ 4+ por linha) */}
      {visiveis.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {visiveis.map((p) => {
            const cat = CATEGORIAS_PARCEIRO.find((c) => c.id === p.categoria)
            const Icon = cat ? ICONES[cat.icon] || Briefcase : Briefcase
            return (
              <div key={p.id} className="bg-[#021431] border border-white/5 rounded-sm p-6 hover:border-[#c5a059]/40 transition-all duration-500 flex flex-col">
                <div className="flex items-start justify-between mb-5">
                  <div className="w-12 h-12 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059]">
                    <Icon size={22} strokeWidth={1.5} />
                  </div>
                  {p.verificado && (
                    <span className="flex items-center gap-1.5 text-[8px] font-black uppercase tracking-widest text-[#c5a059]">
                      <BadgeCheck size={13} /> Verificado
                    </span>
                  )}
                </div>
                <h3 className="text-lg font-serif font-bold text-white tracking-tight">{p.nome}</h3>
                <p className="text-[9px] text-white/30 uppercase tracking-[0.25em] font-black mt-1">{labelCategoria(p.categoria)}</p>
                {p.cidade && (
                  <p className="flex items-center gap-2 text-[11px] text-white/40 mt-3">
                    <MapPin size={12} className="text-[#c5a059]/50" /> {p.cidade}
                  </p>
                )}

                {/* Contatos diretos (clicáveis de verdade) */}
                <div className="mt-auto pt-6 flex items-center gap-2">
                  {p.telefone && (
                    <a
                      href={`https://wa.me/${p.telefone.replace(/\D/g, '')}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => api.parceiros.registrarClique({ partner_id: p.id, categoria: p.categoria, tipo_contato: 'whatsapp' })}
                      className="flex-1 flex items-center justify-center gap-2 border border-white/10 hover:border-[#c5a059]/40 hover:text-[#c5a059] text-white/60 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-widest transition-all"
                    >
                      <Phone size={13} /> Contatar
                    </a>
                  )}
                  {p.email && (
                    <a
                      href={`mailto:${p.email}`}
                      onClick={() => api.parceiros.registrarClique({ partner_id: p.id, categoria: p.categoria, tipo_contato: 'email' })}
                      className="w-10 h-10 flex items-center justify-center border border-white/10 hover:border-[#c5a059]/40 hover:text-[#c5a059] text-white/40 rounded-sm transition-all"
                      title="E-mail"
                    >
                      <Mail size={15} />
                    </a>
                  )}
                  {p.site && (
                    <a
                      href={p.site}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => api.parceiros.registrarClique({ partner_id: p.id, categoria: p.categoria, tipo_contato: 'site' })}
                      className="w-10 h-10 flex items-center justify-center border border-white/10 hover:border-[#c5a059]/40 hover:text-[#c5a059] text-white/40 rounded-sm transition-all"
                      title="Site"
                    >
                      <Globe size={15} />
                    </a>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        /* Estado de rede em formação — honesto (programa fundador) */
        <div className="bg-[#021431] border border-white/5 border-dashed rounded-sm text-center py-24 px-6">
          <h3 className="text-2xl font-serif font-bold text-white mb-3">Rede em formação</h3>
          <p className="text-white/40 font-light max-w-md mx-auto leading-relaxed mb-8">
            {filtro === 'todos'
              ? 'Estamos selecionando os primeiros parceiros de cada categoria. Seja um dos fundadores da rede Atlas.'
              : `Ainda não há parceiros listados em "${labelCategoria(filtro)}". Seja o primeiro desta categoria.`}
          </p>
          <button
            onClick={() => navigate('/seja-parceiro')}
            className="inline-flex items-center gap-3 bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all"
          >
            Seja um Parceiro <ArrowRight size={16} />
          </button>
        </div>
      )}

      {/* CTA — Seja Parceiro (página real) */}
      <div className="bg-[#021431] border border-[#c5a059]/20 p-12 rounded-sm text-center">
        <h3 className="text-3xl font-serif font-bold text-white mb-4">Torne-se um Parceiro Atlas.</h3>
        <p className="text-white/40 max-w-2xl mx-auto mb-10 text-sm font-light leading-relaxed">
          Conecte o seu serviço ao ecossistema náutico do Yachts Atlas e alcance proprietários e marinas que buscam fornecedores de confiança.
        </p>
        <button
          onClick={() => navigate('/seja-parceiro')}
          className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-12 py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.4em] transition-all"
        >
          Solicitar Credenciamento
        </button>
      </div>
    </div>
  )
}
