import { useState } from 'react'
import { ArrowRight, CheckCircle2 } from 'lucide-react'
import Header from '../components/Header'
import { CATEGORIAS_PARCEIRO } from '../config/parceirosCategorias'
import { api } from '../services/api'

export default function SejaParceiro() {
  const [form, setForm] = useState({
    categoria: '',
    empresa: '',
    responsavel: '',
    email: '',
    telefone: '',
    cidade: '',
    mensagem: '',
  })
  const [errors, setErrors] = useState<Record<string, boolean>>({})
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)
  const [erro, setErro] = useState('')

  const set = (k: string, v: string) => {
    setForm((p) => ({ ...p, [k]: v }))
    if (errors[k]) setErrors((p) => ({ ...p, [k]: false }))
  }

  const enviar = async () => {
    const obrig = ['categoria', 'empresa', 'responsavel', 'email']
    const novo: Record<string, boolean> = {}
    obrig.forEach((k) => { if (!String((form as any)[k]).trim()) novo[k] = true })
    if (Object.keys(novo).length) { setErrors(novo); return }

    setEnviando(true)
    setErro('')
    try {
      await api.leads.parceiro(form)
      setEnviado(true)
    } catch {
      setErro('Não foi possível enviar agora. Tente novamente em instantes.')
    } finally {
      setEnviando(false)
    }
  }

  const inputClass = (campo: string) =>
    `w-full bg-white/[0.03] border rounded-sm px-5 py-4 text-white text-sm outline-none transition-all placeholder:text-white/15 ${
      errors[campo] ? 'border-red-500/60' : 'border-white/10 focus:border-[#c5a059]'
    }`
  const labelClass = 'block text-[10px] font-black uppercase tracking-[0.25em] text-white/40 mb-2'

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter'] selection:bg-[#c5a059] selection:text-[#010c20]">
      <Header />
      <main className="pt-[var(--header-h)] pb-24 px-6">
        <div className="max-w-3xl mx-auto pt-16">
          <div className="text-center mb-14">
            <span className="block text-[10px] font-black tracking-[0.4em] text-[#c5a059] uppercase mb-6">Parceiros Atlas</span>
            <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-5">
              Faça parte da rede.
            </h1>
            <p className="text-white/50 font-light leading-relaxed max-w-xl mx-auto">
              Conecte seu serviço ao ecossistema náutico do Yachts Atlas. Recebemos sua solicitação e retornamos com as condições do programa.
            </p>
          </div>

          {enviado ? (
            <div className="bg-[#021431] border border-[#c5a059]/30 rounded-sm p-14 text-center">
              <CheckCircle2 size={44} className="text-[#c5a059] mx-auto mb-6" />
              <h2 className="text-2xl font-serif font-bold text-white mb-3">Solicitação recebida</h2>
              <p className="text-white/50 font-light leading-relaxed max-w-md mx-auto">
                Obrigado. Nossa equipe vai analisar e retornar pelo e-mail informado com as condições da parceria.
              </p>
            </div>
          ) : (
            <div className="bg-[#021431] border border-white/5 rounded-sm p-8 md:p-12">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className={labelClass}>Categoria de Parceria</label>
                  <select className={`${inputClass('categoria')} appearance-none`} value={form.categoria} onChange={(e) => set('categoria', e.target.value)}>
                    <option value="" className="bg-[#010c20]">Selecione</option>
                    {CATEGORIAS_PARCEIRO.map((c) => (
                      <option key={c.id} value={c.id} className="bg-[#010c20]">{c.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Empresa</label>
                  <input className={inputClass('empresa')} value={form.empresa} onChange={(e) => set('empresa', e.target.value)} placeholder="Nome da empresa" />
                </div>
                <div>
                  <label className={labelClass}>Responsável</label>
                  <input className={inputClass('responsavel')} value={form.responsavel} onChange={(e) => set('responsavel', e.target.value)} placeholder="Nome completo" />
                </div>
                <div>
                  <label className={labelClass}>E-mail</label>
                  <input type="email" className={inputClass('email')} value={form.email} onChange={(e) => set('email', e.target.value)} placeholder="contato@empresa.com" />
                </div>
                <div>
                  <label className={labelClass}>Telefone / WhatsApp</label>
                  <input className={inputClass('telefone')} value={form.telefone} onChange={(e) => set('telefone', e.target.value)} placeholder="(00) 00000-0000" />
                </div>
                <div className="md:col-span-2">
                  <label className={labelClass}>Cidade / Região</label>
                  <input className={inputClass('cidade')} value={form.cidade} onChange={(e) => set('cidade', e.target.value)} placeholder="Ex: Ilhabela - SP" />
                </div>
                <div className="md:col-span-2">
                  <label className={labelClass}>Mensagem</label>
                  <textarea className={`${inputClass('mensagem')} min-h-[100px] resize-none`} value={form.mensagem} onChange={(e) => set('mensagem', e.target.value)} placeholder="Conte brevemente sobre o seu serviço." />
                </div>
              </div>

              {erro && <p className="text-red-400 text-xs mt-6">{erro}</p>}

              <button
                onClick={enviar}
                disabled={enviando}
                className="mt-8 w-full bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 text-[#010c20] py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all"
              >
                {enviando ? 'Enviando...' : <>Solicitar Parceria <ArrowRight size={16} /></>}
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
