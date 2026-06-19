import { useEffect, useState } from 'react'
import { Anchor, Scale, Globe, ShieldCheck, ExternalLink, Loader2, BookOpen, Sparkles } from 'lucide-react'
import { api } from '../services/api'

interface Norma {
  codigo: string
  titulo: string
  descricao?: string
  orgao: string
  serie?: string
  jurisdicao?: string
  versao?: string
  fonte_url?: string
  obrigatoria?: boolean
}

const ORGAO_META: Record<string, { icon: any; label: string }> = {
  NORMAM: { icon: Anchor, label: 'NORMAM · Marinha do Brasil' },
  ABNT: { icon: Scale, label: 'ABNT · Brasil' },
  ISO: { icon: Globe, label: 'ISO · Internacional' },
}

export default function NormasTecnicas() {
  const [normas, setNormas] = useState<Norma[]>([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    api.normas
      .list()
      .then((r) => setNormas(r?.normas || []))
      .catch((e) => setErro(e?.message || 'Falha ao carregar normas'))
      .finally(() => setLoading(false))
  }, [])

  const grupos = normas.reduce<Record<string, Norma[]>>((acc, n) => {
    ;(acc[n.orgao] = acc[n.orgao] || []).push(n)
    return acc
  }, {})

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#c5a059]/30 bg-[#c5a059]/5 mb-4">
          <BookOpen size={12} className="text-[#c5a059]" />
          <span className="text-[9px] font-black tracking-[0.3em] text-[#c5a059] uppercase">Conformidade Regulatória</span>
        </div>
        <h1 className="text-3xl md:text-4xl font-serif font-bold text-white tracking-tight mb-2">
          Normas Técnicas Náuticas
        </h1>
        <p className="text-white/40 text-sm font-light max-w-2xl">
          Consulte as normas que regem o seu ativo. Para dúvidas, fale com a{' '}
          <span className="text-[#c5a059] font-medium">Capitã Solara</span> — a assistente de IA no canto
          da tela responde com base apenas em normas verificadas, sempre citando a fonte.
        </p>
      </div>

      {/* Dica da Capitã */}
      <div className="mb-10 p-5 border border-[#c5a059]/20 bg-[#c5a059]/[0.04] rounded-sm flex items-center gap-4">
        <div className="w-10 h-10 flex-shrink-0 rounded-full bg-gradient-to-br from-[#c5a059] to-[#b38f4d] flex items-center justify-center text-[#010c20]">
          <Sparkles size={18} />
        </div>
        <p className="text-white/60 text-sm font-light">
          <span className="text-white font-medium">Precisa de ajuda rápida?</span> Toque na{' '}
          <span className="text-[#c5a059]">Capitã Solara</span> no canto inferior direito e pergunte,
          por exemplo: <em className="text-white/70">"o que exige a NORMAM-211?"</em>
        </p>
      </div>

      {/* Catálogo */}
      <div className="space-y-10">
        {loading && (
          <div className="flex items-center gap-3 text-white/40 text-sm">
            <Loader2 size={16} className="animate-spin text-[#c5a059]" /> Carregando normas…
          </div>
        )}

        {erro && !loading && (
          <div className="p-6 border border-amber-500/30 bg-amber-500/5 rounded-sm text-amber-200/80 text-sm">
            Não foi possível carregar o catálogo agora. ({erro})
          </div>
        )}

        {!loading && !erro && normas.length === 0 && (
          <div className="p-6 border border-white/10 bg-white/[0.02] rounded-sm text-white/50 text-sm">
            Nenhuma norma publicada ainda. O catálogo aparecerá aqui assim que for liberado.
          </div>
        )}

        {Object.entries(grupos).map(([orgao, lista]) => {
          const meta = ORGAO_META[orgao] || { icon: ShieldCheck, label: orgao }
          const Icon = meta.icon
          return (
            <div key={orgao}>
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 bg-[#c5a059]/10 border border-[#c5a059]/20 flex items-center justify-center text-[#c5a059] rounded-sm">
                  <Icon size={16} />
                </div>
                <span className="text-[10px] font-black tracking-[0.25em] text-white/60 uppercase">{meta.label}</span>
              </div>
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {lista.map((n) => (
                  <div
                    key={n.codigo}
                    className="group bg-[#021431] border border-white/5 p-6 rounded-sm hover:border-[#c5a059]/30 transition-all duration-500"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[#c5a059] font-serif font-bold tracking-tight">{n.codigo}</span>
                      {n.versao && (
                        <span className="text-[8px] text-white/30 uppercase tracking-[0.2em] font-black">{n.versao}</span>
                      )}
                    </div>
                    <h3 className="text-white text-sm font-bold mb-2 leading-snug">{n.titulo}</h3>
                    {n.descricao && (
                      <p className="text-white/40 text-xs leading-relaxed font-light line-clamp-4">{n.descricao}</p>
                    )}
                    {n.fonte_url && (
                      <a
                        href={n.fonte_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 mt-4 text-[9px] font-black tracking-[0.2em] text-white/40 hover:text-[#c5a059] uppercase transition-all"
                      >
                        Fonte oficial <ExternalLink size={11} />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
