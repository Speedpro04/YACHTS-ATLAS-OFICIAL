import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import {
  Building2, 
  MapPin, 
  Phone, 
  Mail, 
  Globe, 
  ChevronRight, 
  ChevronLeft, 
  CheckCircle2, 
  ShieldCheck,
  Building,
  ArrowRight,
  Loader2,
  Lock,
  Eye,
  EyeOff
} from 'lucide-react'
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


// A regra da senha vive AQUI e em mais nenhum lugar da tela.
//
// Ela espelha o que o Supabase Auth exige (mínimo 10 · minúscula · maiúscula ·
// dígito). Estavam desencontrados: a tela pedia 6 caracteres e o servidor
// recusava — a marina digitava algo que a página aceitava e levava erro
// genérico do backend, sem saber qual campo estava errado. Mudou a regra lá?
// Muda aqui, e o texto da tela acompanha sozinho.
const SENHA_MINIMO = 10

const REGRAS_SENHA: { texto: string; ok: (s: string) => boolean }[] = [
  { texto: `Pelo menos ${SENHA_MINIMO} caracteres`, ok: (v) => v.length >= SENHA_MINIMO },
  { texto: 'Uma letra maiúscula', ok: (v) => /[A-Z]/.test(v) },
  { texto: 'Uma letra minúscula', ok: (v) => /[a-z]/.test(v) },
  { texto: 'Um número', ok: (v) => /[0-9]/.test(v) },
]

const senhaValida = (v: string) => REGRAS_SENHA.every((r) => r.ok(v))

export default function RegistroMarina() {
  const { t } = useTranslation()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [freeMode, setFreeMode] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showPasswordConfirm, setShowPasswordConfirm] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    cnpj: '',
    email: '',
    password: '',
    passwordConfirm: '',
    phone: '',
    zip_code: '',
    address: '',
    number: '',
    complement: '',
    neighborhood: '',
    city: '',
    state: '',
    website: '',
    // Quem indicou. A página promete que a marina que indica participa dos
    // dossiês da indicada — e esse vínculo só pode ser capturado aqui:
    // depois ninguém lembra quem indicou quem.
    indicada_por: ''
  })

  // Auto-fill address from CEP
  useEffect(() => {
    const fetchAddress = async () => {
      const cleanCep = formData.zip_code.replace(/\D/g, '')
      if (cleanCep.length === 8) {
        try {
          const response = await fetch(`https://viacep.com.br/ws/${cleanCep}/json/`)
          const data = await response.json()
          if (!data.erro) {
            setFormData(prev => ({
              ...prev,
              address: data.logradouro,
              neighborhood: data.bairro,
              city: data.localidade,
              state: data.uf
            }))
          }
        } catch (err) {
          console.error('Erro ao buscar CEP:', err)
        }
      }
    }
    fetchAddress()
  }, [formData.zip_code])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    // O telefone é guardado como DÍGITOS puros; o "+55" é rótulo ao lado do
    // campo e a máscara é só apresentação. Ver utils/telefone.
    setFormData({ ...formData, [name]: name === 'phone' ? soDDDeNumero(value) : value })
  }

  // Fallback quando o cadastro falha antes de o backend dizer a oferta.
  // Usa o preço oficial: prometer US$ 200 sem confirmar vaga fundadora vira estorno.
  const STRIPE_MARINA_LINK = 'https://buy.stripe.com/7sY7sL4KVbU02Sd7QA1wY01'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError('')

    // E-mail e telefone conferidos AQUI, e não pelo `required` do input.
    //
    // O formulário tem 4 etapas e só a etapa atual existe no DOM. Na etapa 4,
    // onde fica o botão de enviar, os campos da etapa 1 já saíram da página —
    // e `required` não valida o que não está lá. O atributo estava inerte.
    //
    // Custou caro: em 25/08/2026 uma marina concluiu o cadastro e pagou
    // US$ 250 com `telefone` gravado vazio. O telefone é por onde ela seria
    // atendida, e ninguém percebeu porque nada reclamou.
    if (!emailValido(formData.email)) {
      setSubmitError(MSG_EMAIL_INVALIDO)
      return
    }
    if (!telefoneCompleto(formData.phone)) {
      setSubmitError(MSG_TELEFONE_INCOMPLETO)
      return
    }

    if (!senhaValida(formData.password)) {
      setSubmitError(
        `A senha precisa de ${SENHA_MINIMO} caracteres, com maiúscula, minúscula e número.`
      )
      return
    }
    if (formData.password !== formData.passwordConfirm) {
      setSubmitError('As senhas não conferem.')
      return
    }

    setLoading(true)
    try {
      const res = await api.leads.registrarMarina({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        cnpj: formData.cnpj,
        // Sai com o DDI colado: 13 dígitos começando em 55 é a única forma que
        // o backend aceita sem precisar inferir DDD nenhum.
        phone: comDDI(formData.phone),
        city: formData.city,
        state: formData.state,
        website: formData.website,
        indicada_por: formData.indicada_por,
      })

      if (res.modo === 'gratis') {
        // Marina fundadora pré-autorizada: acesso liberado, sem checkout.
        setFreeMode(true)
        setSuccess(true)
        return
      }
      // Checkout escolhido pelo backend: fundadora (USD 200) enquanto houver
      // uma das 20 vagas, oficial (USD 250) depois.
      window.location.href = res.checkout_url || STRIPE_MARINA_LINK
    } catch {
      // Em caso de falha, não trava a marina: segue para o fluxo pago.
      window.location.href = STRIPE_MARINA_LINK
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen bg-[#010c20] flex items-center justify-center p-6 font-['Inter']">
        <div className="max-w-md w-full text-center space-y-8 animate-in fade-in zoom-in duration-700">
          <div className="w-24 h-24 bg-gold-500/10 rounded-full flex items-center justify-center mx-auto border border-gold-500/20 shadow-[0_0_50px_rgba(197,160,89,0.2)]">
            <CheckCircle2 size={48} className="text-gold-500" />
          </div>
          {freeMode ? (
            <>
              <h2 className="text-4xl font-serif font-bold text-white tracking-tight">Bem-vinda, Marina Fundadora.</h2>
              <p className="text-white/60 leading-relaxed font-light text-sm">
                Seu acesso está liberado — <strong className="text-gold-500">6 meses de cortesia</strong> (custódia + dossiês).
                Entre com o e-mail e a senha que você acabou de criar.
              </p>
              <a
                href="/login"
                className="inline-flex items-center justify-center gap-3 bg-gold-500 hover:bg-gold-400 text-[#010c20] px-12 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all"
              >
                Entrar no Cofre <ArrowRight size={16} />
              </a>
            </>
          ) : (
            <>
              <h2 className="text-4xl font-serif font-bold text-white tracking-tight">Protocolo Concluído.</h2>
              <p className="text-white/40 leading-relaxed font-light uppercase tracking-[0.2em] text-[10px]">
                Sua marina foi integrada ao ecossistema Atlas. <br /> Redirecionando para o cofre de segurança...
              </p>
              <div className="flex justify-center">
                <Loader2 className="animate-spin text-gold-500/30" size={24} />
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#010c20] text-white font-['Inter'] selection:bg-gold-500 selection:text-[#010c20]">
      <Header />
      
      <main className="pt-[var(--header-h)] pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          
          {/* Progress Header */}
          <div className="mb-20 text-center">
            <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8">
               <ShieldCheck size={14} className="text-gold-500" />
               <span className="text-[10px] font-bold text-white uppercase tracking-widest">{t('marina_onboarding.onboarding_badge')}</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-serif font-bold text-white mb-6 tracking-tight">
              {t('marina_onboarding.registration_title')} <span className="text-transparent bg-clip-text bg-gradient-to-r from-gold-500 to-gold-200 italic">{t('marina_onboarding.registration_highlight')}</span>
            </h1>
            <p className="text-white/30 uppercase tracking-[0.4em] text-[10px] font-black">
              Digital Maritime Asset Hub <span className="text-gold-500 mx-3">•</span> {t('marina_onboarding.step_of', { step })}
            </p>
          </div>

          <div className="relative">
            {/* Steps Indicator */}
            <div className="absolute -left-12 top-0 bottom-0 hidden lg:flex flex-col items-center gap-4">
              {[1, 2, 3, 4].map((s) => (
                <div 
                  key={s}
                  className={`w-1 h-20 rounded-full transition-all duration-700 ${s <= step ? 'bg-gold-500 shadow-[0_0_15px_rgba(197,160,89,0.5)]' : 'bg-white/5'}`}
                />
              ))}
            </div>

            <form onSubmit={handleSubmit} className="relative z-10">
              <div className="bg-white/[0.02] border border-white/5 backdrop-blur-3xl p-8 md:p-16 rounded-sm shadow-2xl shadow-black/50">
                
                {step === 1 && (
                  <div className="space-y-12 animate-in slide-in-from-right-8 duration-700">
                    <div className="grid md:grid-cols-2 gap-12">
                      {/* Nome */}
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <Building2 size={14} /> {t('marina_onboarding.field_name')}
                        </label>
                        <input 
                          type="text" 
                          name="name"
                          value={formData.name}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_name')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* CNPJ */}
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <ShieldCheck size={14} /> {t('marina_onboarding.field_cnpj')}
                        </label>
                        <input 
                          type="text" 
                          name="cnpj"
                          value={formData.cnpj}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_cnpj')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* E-mail */}
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <Mail size={14} /> {t('marina_onboarding.field_email')}
                        </label>
                        <input 
                          type="email" 
                          name="email"
                          value={formData.email}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_email')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Telefone */}
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <Phone size={14} /> {t('marina_onboarding.field_phone')}
                        </label>
                        {/* O "+55" é rótulo FIXO, fora do campo. Dentro dele,
                            "55978138934" é indistinguível de um celular do DDD
                            55 (Santa Maria/RS) — e nenhuma regra desempata. */}
                        <div className="flex items-center gap-3 border-b border-white/10 focus-within:border-gold-500 transition-all">
                          <span className="text-lg font-serif text-white/40 select-none">+55</span>
                          <input
                            type="tel"
                            inputMode="numeric"
                            name="phone"
                            value={mascaraTelefone(formData.phone)}
                            onChange={handleChange}
                            required
                            placeholder="(12) 97813-8934"
                            className="w-full bg-white/5 px-0 py-4 text-lg font-serif focus:outline-none transition-all placeholder:text-white/20"
                          />
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4 group max-w-md">
                      <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                        <Globe size={14} /> {t('marina_onboarding.field_website')}
                      </label>
                      <input
                        type="url"
                        name="website"
                        value={formData.website}
                        onChange={handleChange}
                        placeholder={t('marina_onboarding.placeholder_website')}
                        className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                      />
                    </div>

                    {/* Senha de acesso — a própria marina cria, direto no site oficial */}
                    <div className="grid md:grid-cols-2 gap-12 pt-4 border-t border-white/5">
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <Lock size={14} /> Senha de acesso
                        </label>
                        <div className="relative">
                          <input
                            type={showPassword ? 'text' : 'password'}
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            minLength={SENHA_MINIMO}
                            placeholder={`Mínimo ${SENHA_MINIMO} caracteres`}
                            className="w-full bg-white/5 border-b border-white/10 px-0 py-4 pr-10 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword((v) => !v)}
                            aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
                            className="absolute right-0 top-1/2 -translate-y-1/2 text-white/30 hover:text-gold-500 transition-colors"
                          >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                          </button>
                        </div>

                        {/* Requisitos à vista, marcando sozinhos conforme a
                            marina digita. Esconder a regra e só recusar depois
                            é o que gera "não consigo cadastrar" no telefone. */}
                        <ul className="space-y-1.5 pt-1">
                          {REGRAS_SENHA.map((r) => {
                            const cumprida = r.ok(formData.password)
                            return (
                              <li
                                key={r.texto}
                                className={`flex items-center gap-2 text-[11px] transition-colors ${
                                  cumprida ? 'text-emerald-400/80' : 'text-white/30'
                                }`}
                              >
                                <span className="text-[13px] leading-none w-3">
                                  {cumprida ? '✓' : '·'}
                                </span>
                                {r.texto}
                              </li>
                            )
                          })}
                        </ul>
                      </div>
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <Lock size={14} /> Confirmar senha
                        </label>
                        <div className="relative">
                          <input
                            type={showPasswordConfirm ? 'text' : 'password'}
                            name="passwordConfirm"
                            value={formData.passwordConfirm}
                            onChange={handleChange}
                            required
                            minLength={6}
                            placeholder="Repita a senha"
                            className="w-full bg-white/5 border-b border-white/10 px-0 py-4 pr-10 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPasswordConfirm((v) => !v)}
                            aria-label={showPasswordConfirm ? 'Ocultar senha' : 'Mostrar senha'}
                            className="absolute right-0 top-1/2 -translate-y-1/2 text-white/30 hover:text-gold-500 transition-colors"
                          >
                            {showPasswordConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {step === 2 && (
                  <div className="space-y-12 animate-in slide-in-from-left-8 duration-700">
                    <div className="grid md:grid-cols-3 gap-12">
                      {/* CEP */}
                      <div className="space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <MapPin size={14} /> {t('marina_onboarding.field_zip')}
                        </label>
                        <input 
                          type="text" 
                          name="zip_code"
                          value={formData.zip_code}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_zip')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Endereço */}
                      <div className="md:col-span-2 space-y-4 group">
                        <label className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          <Building size={14} /> {t('marina_onboarding.field_address')}
                        </label>
                        <input 
                          type="text" 
                          name="address"
                          value={formData.address}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_address')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Número */}
                      <div className="space-y-4 group">
                        <label className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          {t('marina_onboarding.field_number')}
                        </label>
                        <input 
                          type="text" 
                          name="number"
                          value={formData.number}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_number')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Complemento */}
                      <div className="space-y-4 group">
                        <label className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          {t('marina_onboarding.field_complement')}
                        </label>
                        <input 
                          type="text" 
                          name="complement"
                          value={formData.complement}
                          onChange={handleChange}
                          placeholder={t('marina_onboarding.placeholder_complement')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Bairro */}
                      <div className="space-y-4 group">
                        <label className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          {t('marina_onboarding.field_neighborhood')}
                        </label>
                        <input 
                          type="text" 
                          name="neighborhood"
                          value={formData.neighborhood}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_neighborhood')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Cidade */}
                      <div className="space-y-4 group">
                        <label className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          {t('marina_onboarding.field_city')}
                        </label>
                        <input 
                          type="text" 
                          name="city"
                          value={formData.city}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_city')}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                      </div>

                      {/* Estado */}
                      <div className="space-y-4 group">
                        <label className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          {t('marina_onboarding.field_state')}
                        </label>
                        <input 
                          type="text" 
                          name="state"
                          value={formData.state}
                          onChange={handleChange}
                          required
                          placeholder={t('marina_onboarding.placeholder_state')}
                          maxLength={2}
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5 uppercase"
                        />
                      </div>

                      {/* Quem indicou — opcional, e o único momento em que dá
                          para capturar. Depois do cadastro ninguém lembra quem
                          indicou quem, e é esse vínculo que garante o bônus da
                          marina que trouxe a indicada. */}
                      <div className="space-y-4 group md:col-span-2">
                        <label className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40 group-focus-within:text-gold-500 transition-colors">
                          Alguma marina indicou o Yachts Atlas para você?
                        </label>
                        <input
                          type="text"
                          name="indicada_por"
                          value={formData.indicada_por}
                          onChange={handleChange}
                          placeholder="Nome ou e-mail da marina que indicou (opcional)"
                          className="w-full bg-white/5 border-b border-white/10 px-0 py-4 text-lg font-serif focus:outline-none focus:border-gold-500 transition-all placeholder:text-white/5"
                        />
                        <p className="text-[11px] text-white/30 leading-relaxed">
                          A marina que indica participa dos dossiês gerados por você durante o período fundador.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {step === 3 && (
                  <div className="animate-in fade-in duration-700 bg-[#010c20] border border-[#c5a059] p-10 md:p-14 rounded-sm shadow-[0_0_40px_rgba(197,160,89,0.05)]">
                    <h2 className="text-2xl md:text-3xl font-serif font-semibold text-center text-[#c5a059] mb-10 tracking-tight uppercase">{t('marina_onboarding.step_3_title')}</h2>
                    
                    <div className="space-y-8">
                      <div className="border-t border-[#c5a059]/30 pt-8">
                        <h3 className="text-[#c5a059] font-bold mb-3 uppercase text-[13px] tracking-widest flex items-center gap-2"><Building2 size={14} /> {t('marina_onboarding.benefit_marina_title')}</h3>
                        <p className="text-white/80 font-light text-[14px] leading-relaxed">
                          {t('marina_onboarding.benefit_marina_text')}
                        </p>
                      </div>

                      <div className="border-t border-[#c5a059]/30 pt-8">
                        <h3 className="text-[#c5a059] font-bold mb-3 uppercase text-[13px] tracking-widest flex items-center gap-2"><ShieldCheck size={14} /> {t('marina_onboarding.benefit_insurance_title')}</h3>
                        <p className="text-white/80 font-light text-[14px] leading-relaxed">
                          {t('marina_onboarding.benefit_insurance_text')}
                        </p>
                      </div>

                      <div className="border-t border-[#c5a059]/30 pt-8">
                        <h3 className="text-[#c5a059] font-bold mb-3 uppercase text-[13px] tracking-widest flex items-center gap-2"><Globe size={14} /> {t('marina_onboarding.benefit_owner_title')}</h3>
                        <p className="text-white/80 font-light text-[14px] leading-relaxed">
                          {t('marina_onboarding.benefit_owner_text')}
                        </p>
                      </div>

                      <div className="border-t border-[#c5a059]/30 pt-10 mt-6">
                        <p className="text-white/80 font-light text-[14px] leading-relaxed italic opacity-90 text-center px-4">
                          {t('marina_onboarding.closing_text')}
                        </p>
                      </div>
                      
                      <div className="text-center pt-10">
                         <p className="text-[#c5a059] text-[10px] font-black uppercase tracking-[0.4em]">{t('marina_onboarding.signature')}</p>
                      </div>
                    </div>
                  </div>
                )}

                {step === 4 && (
                  <div className="space-y-10 animate-in slide-in-from-right-8 duration-700">
                    <div className="text-center mb-12">
                       <h2 className="text-3xl font-serif font-bold text-white mb-4">{t('marina_onboarding.payment_title')}</h2>
                       <p className="text-gold-500 text-4xl font-serif font-bold">$250<span className="text-sm text-white/40 font-['Inter'] font-light"> / mês</span></p>
                    </div>

                    <div className="bg-white/5 border border-white/10 p-10 rounded-sm space-y-8">
                       <div className="flex items-center justify-between border-b border-white/5 pb-6">
                          <div className="flex items-center gap-4">
                             <div className="w-12 h-12 bg-gold-500/10 rounded-full flex items-center justify-center text-gold-500">
                                <ShieldCheck size={24} />
                             </div>
                             <div>
                                <h3 className="text-sm font-black uppercase tracking-widest text-white">Marina Standard</h3>
                                <p className="text-[10px] text-white/30 uppercase tracking-[0.2em] mt-1">Plano Anual Recorrente</p>
                             </div>
                          </div>
                          <div className="text-right">
                             <span className="text-2xl font-serif font-bold text-gold-500">$250</span>
                             <span className="text-[10px] text-white/20 uppercase ml-2">/ mês</span>
                          </div>
                       </div>
                       
                       <div className="space-y-4">
                          <div className="flex items-center gap-3 text-white/60 text-xs">
                             <CheckCircle2 size={14} className="text-gold-500" />
                             <span>Gestão ilimitada de ativos náuticos</span>
                          </div>
                          <div className="flex items-center gap-3 text-white/60 text-xs">
                             <CheckCircle2 size={14} className="text-gold-500" />
                             <span>Emissão de Dossiês Atlas</span>
                          </div>
                          <div className="flex items-center gap-3 text-white/60 text-xs">
                             <CheckCircle2 size={14} className="text-gold-500" />
                             <span>Acesso ao ecossistema de brokers e seguros</span>
                          </div>
                       </div>

                       <div className="pt-6 border-t border-white/5">
                          <div className="flex items-center gap-4 p-4 bg-gold-500/5 border border-gold-500/10 rounded-sm">
                             <Lock className="text-gold-500" size={18} />
                             <p className="text-[10px] text-white/60 leading-relaxed">
                                Você será redirecionado para o ambiente seguro do <strong>Stripe</strong> para processar sua assinatura internacional em USD.
                             </p>
                          </div>
                       </div>

                       <div className="pt-2">
                          <div className="p-4 bg-[#021431] border border-[#c5a059]/30 rounded-sm">
                             <p className="text-[#E5D5B7] text-[10px] font-black uppercase tracking-[0.25em] mb-2">
                                Clausula Comercial de Dossies
                             </p>
                             <p className="text-white/70 text-[12px] leading-relaxed">
                                Para parceiros aprovados no contrato fundador: receita de dossies com retencao integral por 18 meses,
                                com marco inicial na ativacao da conta e demais condicoes definidas em instrumento contratual.
                             </p>
                          </div>
                       </div>
                    </div>
                  </div>
                )}

                {submitError && step === 4 && (
                  <div className="mt-10 bg-red-500/10 border border-red-500/40 p-4 rounded-sm">
                    <p className="text-red-400 text-xs font-bold text-center">{submitError}</p>
                  </div>
                )}

                <div className="mt-20 flex flex-col md:flex-row items-center justify-between gap-10">
                   <p className="text-[9px] text-white/20 uppercase tracking-widest max-w-xs leading-loose">
                     {t('marina_onboarding.footer_terms')}
                   </p>
                   
                   <div className="flex gap-6">
                      {step > 1 && (
                        <button 
                          type="button"
                          onClick={() => setStep(step - 1)}
                          className="group border border-white/10 hover:border-white/30 px-10 py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3"
                        >
                          <ChevronLeft size={16} /> {t('marina_onboarding.back_step')}
                        </button>
                      )}

                      {step < 4 ? (
                        <button 
                          type="button"
                          onClick={() => setStep(step + 1)}
                          className="bg-gold-500 hover:bg-gold-400 text-[#010c20] px-16 py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-4 shadow-2xl shadow-gold-500/10"
                        >
                          {step === 3 ? t('marina_onboarding.advance_payment') : t('marina_onboarding.next_step')} <ChevronRight size={18} />
                        </button>
                      ) : (
                        <button 
                          type="submit"
                          disabled={loading}
                          className="bg-gold-500 hover:bg-gold-400 text-[#010c20] px-16 py-5 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-4 shadow-2xl shadow-gold-500/10 disabled:opacity-50"
                        >
                          {loading ? <Loader2 className="animate-spin" /> : <>{t('marina_onboarding.payment_cta')} <ArrowRight size={18} /></>}
                        </button>
                      )}
                   </div>

                   {/* O que acontece depois do botão. Prazo que o cliente não
                       conhece é armadilha: a vaga fundadora fica presa por 3h
                       (MINUTOS_DE_RESERVA_VAGA) e some depois disso — quem
                       voltar tarde pagaria US$ 250 sem entender por quê. */}
                   <p className="mt-8 text-center text-[11px] leading-relaxed text-white/35 max-w-md mx-auto">
                     Ao concluir, você verá um <strong className="text-white/60 font-semibold">vídeo curto</strong> do
                     fundador explicando como o sistema funciona — e em seguida
                     finaliza o pagamento.
                     <br />
                     Sua vaga fica <strong className="text-gold-500/80 font-semibold">reservada por 3 horas</strong> para
                     você concluir com calma.
                     <br />
                     {/* Depois de pagar, a marina sai daqui para a Stripe. Sem
                         dizer o que esperar, ela fica sem saber se deu certo —
                         e o acesso, que é liberado na hora, passa despercebido. */}
                     Após o pagamento, você recebe um <strong className="text-white/60 font-semibold">e-mail de
                     confirmação</strong> e seu acesso é liberado imediatamente.
                   </p>
                </div>
              </div>
            </form>
          </div>
        </div>
      </main>

      <footer className="py-20 text-center border-t border-white/5 opacity-20">
         <p className="text-[9px] font-black uppercase tracking-[0.5em]">Yachts Atlas • Differentiated Asset Control</p>
      </footer>
    </div>
  )
}
