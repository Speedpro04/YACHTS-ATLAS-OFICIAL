import { useState } from 'react'
import { ArrowRight, CheckCircle2, FileCheck } from 'lucide-react'
import Header from '../components/Header'
import { api } from '../services/api'
import {
  soDDDeNumero,
  mascaraTelefone,
  telefoneCompleto,
  comDDI,
  emailValido,
  MSG_TELEFONE_INCOMPLETO,
  MSG_EMAIL_INVALIDO,
} from '../utils/telefone'

const FINALIDADES = [
  { id: 'venda', label: 'Compra / Venda do ativo' },
  { id: 'seguro', label: 'Seguro (cotação / renovação)' },
  { id: 'outro', label: 'Outro' },
]

export default function SolicitarDossie() {
  const [form, setForm] = useState({
    solicitante_nome: '',
    solicitante_email: '',
    solicitante_telefone: '',
    finalidade: '',
    marina_nome: '',
    ativo_id: '',
    mensagem: '',
  })
  const [errors, setErrors] = useState<Record<string, boolean>>({})
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState(false)
  const [erro, setErro] = useState('')

  const set = (k: string, v: string) => {
    // Telefone guardado como dígitos puros; "+55" é rótulo, máscara é só tela.
    setForm((p) => ({
      ...p, [k]: k === 'solicitante_telefone' ? soDDDeNumero(v) : v,
    }))
    if (errors[k]) setErrors((p) => ({ ...p, [k]: false }))
  }

  const enviar = async () => {
    const obrig = ['solicitante_nome', 'solicitante_email', 'finalidade']
    const novo: Record<string, boolean> = {}
    obrig.forEach((k) => { if (!String((form as any)[k]).trim()) novo[k] = true })
    if (Object.keys(novo).length) { setErrors(novo); return }

    if (!emailValido(form.solicitante_email)) {
      setErrors({ solicitante_email: true }); setErro(MSG_EMAIL_INVALIDO); return
    }
    // Telefone é opcional aqui. Mas se foi digitado, tem de estar completo:
    // meio número é pior que nenhum — parece que dá para ligar, e não dá.
    if (form.solicitante_telefone && !telefoneCompleto(form.solicitante_telefone)) {
      setErrors({ solicitante_telefone: true }); setErro(MSG_TELEFONE_INCOMPLETO); return
    }

    setEnviando(true)
    setErro('')
    try {
      await api.dossie.solicitar({
        solicitante_nome: form.solicitante_nome,
        solicitante_email: form.solicitante_email,
        solicitante_telefone: form.solicitante_telefone
          ? comDDI(form.solicitante_telefone) : undefined,
        finalidade: (form.finalidade || 'outro') as 'venda' | 'seguro' | 'outro',
        marina_nome: form.marina_nome || undefined,
        ativo_id: form.ativo_id || undefined,
        mensagem: form.mensagem || undefined,
      })
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
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#c5a059]/30 bg-[#c5a059]/5 mb-6">
              <FileCheck size={14} className="text-[#c5a059]" />
              <span className="text-[10px] font-black tracking-[0.3em] text-[#c5a059] uppercase">Dossiê de Integridade</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-serif font-bold text-white tracking-tight mb-5">
              Solicitar Dossiê
            </h1>
            <p className="text-white/50 font-light leading-relaxed max-w-xl mx-auto">
              Receba o dossiê auditável de um ativo — válido para compra, venda e seguro.
              A Yachts Atlas analisa o pedido e libera o acesso seguro do documento.
            </p>
          </div>

          {enviado ? (
            <div className="bg-[#021431] border border-[#c5a059]/30 rounded-sm p-14 text-center">
              <CheckCircle2 size={44} className="text-[#c5a059] mx-auto mb-6" />
              <h2 className="text-2xl font-serif font-bold text-white mb-3">Pedido recebido</h2>
              <p className="text-white/50 font-light leading-relaxed max-w-md mx-auto">
                Obrigado. Assim que a Yachts Atlas liberar, você recebe no e-mail informado
                um link seguro para abrir o dossiê pelo celular.
              </p>
            </div>
          ) : (
            <div className="bg-[#021431] border border-white/5 rounded-sm p-8 md:p-12">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className={labelClass}>Seu nome *</label>
                  <input className={inputClass('solicitante_nome')} value={form.solicitante_nome} onChange={(e) => set('solicitante_nome', e.target.value)} placeholder="Nome completo" />
                </div>
                <div>
                  <label className={labelClass}>E-mail *</label>
                  <input type="email" className={inputClass('solicitante_email')} value={form.solicitante_email} onChange={(e) => set('solicitante_email', e.target.value)} placeholder="seu@email.com" />
                </div>
                <div>
                  <label className={labelClass}>Telefone / WhatsApp</label>
                  <div className="flex items-center gap-2">
                    <span className="text-white/40 select-none">+55</span>
                    <input type="tel" inputMode="numeric" className={inputClass('solicitante_telefone')} value={mascaraTelefone(form.solicitante_telefone)} onChange={(e) => set('solicitante_telefone', e.target.value)} placeholder="(12) 97813-8934" />
                  </div>
                </div>
                <div>
                  <label className={labelClass}>Finalidade *</label>
                  <select className={`${inputClass('finalidade')} appearance-none`} value={form.finalidade} onChange={(e) => set('finalidade', e.target.value)}>
                    <option value="" className="bg-[#010c20]">Selecione</option>
                    {FINALIDADES.map((f) => (
                      <option key={f.id} value={f.id} className="bg-[#010c20]">{f.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Marina (se souber)</label>
                  <input className={inputClass('marina_nome')} value={form.marina_nome} onChange={(e) => set('marina_nome', e.target.value)} placeholder="Nome da Marina" />
                </div>
                <div>
                  <label className={labelClass}>Código do ativo (se souber)</label>
                  <input className={inputClass('ativo_id')} value={form.ativo_id} onChange={(e) => set('ativo_id', e.target.value)} placeholder="Ex: YA-IATE-2020-XXXX" />
                </div>
                <div className="md:col-span-2">
                  <label className={labelClass}>Mensagem</label>
                  <textarea className={`${inputClass('mensagem')} min-h-[100px] resize-none`} value={form.mensagem} onChange={(e) => set('mensagem', e.target.value)} placeholder="Qual embarcação? Qualquer detalhe que ajude a localizar o ativo." />
                </div>
              </div>

              {erro && <p className="text-red-400 text-xs mt-6">{erro}</p>}

              <button
                onClick={enviar}
                disabled={enviando}
                className="mt-8 w-full bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-50 text-[#010c20] py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] flex items-center justify-center gap-3 transition-all"
              >
                {enviando ? 'Enviando...' : <>Solicitar Dossiê <ArrowRight size={16} /></>}
              </button>

              <p className="text-[9px] text-white/20 uppercase tracking-[0.2em] text-center mt-6">
                O pagamento do dossiê é tratado diretamente com a Marina responsável.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
