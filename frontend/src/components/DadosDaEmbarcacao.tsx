import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, ClipboardList, PenLine, Ship, User } from 'lucide-react'
import { Ativo } from '../types'
import { api } from '../services/api'
import {
  soDDDeNumero, mascaraTelefone, telefoneCompleto, comDDI,
  emailValido, MSG_EMAIL_INVALIDO, MSG_TELEFONE_INCOMPLETO,
} from '../utils/telefone'

/**
 * O cadastro da embarcação, depois de salvo.
 *
 * POR QUE EXISTE (15/09/2026). O formulário de cadastro coletava boca, calado,
 * motor, tanque e o contato do dono — e depois de salvo nada disso aparecia em
 * tela nenhuma. A página do barco mostrava marca, modelo, pés e ano; o resto
 * só existia dentro do PDF. E o e-mail do dono, que é a chave dele para o
 * Portal, não aparecia NEM no PDF: três barcos estavam sem e-mail e nada
 * avisava que aqueles donos nunca conseguiriam entrar.
 *
 * É UM CARD, NÃO UMA CATEGORIA. Fica na grade do Painel Técnico por decisão do
 * Marcos — tudo no mesmo lugar —, mas não tem registro, não tem estado e não
 * entra na Conformidade. Por isso não tem `healthKey` em `categorias()`.
 *
 * SÓ LEITURA, por enquanto. Corrigir o cadastro é decisão pendente.
 */

type Situacao = 'sem_email' | 'nunca_entrou' | 'entrou'

const TIPO: Record<string, string> = {
  iate: 'Iate', lancha: 'Lancha', veleiro: 'Veleiro', jetski: 'Jet Ski', barco_pesca: 'Barco de Pesca',
}

function numero(v: number | null | undefined, sufixo = ''): string | null {
  if (v === null || v === undefined || v === 0 || Number.isNaN(Number(v))) return null
  return `${Number(v).toLocaleString('pt-BR')}${sufixo}`
}

function texto(v: string | null | undefined): string | null {
  const limpo = (v || '').trim()
  return limpo || null
}

function Linha({ rotulo, valor }: { rotulo: string; valor: string | null }) {
  return (
    <div className="py-3 border-b border-white/5 flex items-baseline justify-between gap-4">
      <span className="text-[9px] uppercase tracking-[0.25em] text-white/30 font-black">{rotulo}</span>
      {valor
        ? <span className="text-white/85 text-sm text-right break-all">{valor}</span>
        : <span className="text-white/20 text-sm">—</span>}
    </div>
  )
}

function Campo({ rotulo, valor, onChange, placeholder, ajuda, tipo = 'text', prefixo }: {
  rotulo: string
  valor: string
  onChange: (v: string) => void
  placeholder?: string
  ajuda?: string
  tipo?: string
  prefixo?: string
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-[9px] uppercase tracking-[0.25em] text-white/30 font-black">{rotulo}</label>
      <div className="flex items-center gap-2">
        {prefixo && <span className="text-white/35 text-sm">{prefixo}</span>}
        <input
          type={tipo}
          value={valor}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-2.5 text-white text-sm focus:border-[#c5a059] outline-none transition-all placeholder:text-white/15"
        />
      </div>
      {ajuda && <p className="text-white/25 text-[10px] leading-relaxed">{ajuda}</p>}
    </div>
  )
}

export default function DadosDaEmbarcacao({ ativo, onBack, readOnly = false, onSalvo }: {
  ativo: Ativo
  onBack: () => void
  readOnly?: boolean
  /** Devolve o dono novo para quem segura o ativo — senão o rodapé do card
   *  continuaria dizendo "Proprietário sem e-mail" com o e-mail já salvo. */
  onSalvo?: (dados: Partial<Ativo>) => void
}) {
  const [portal, setPortal] = useState<{ situacao: Situacao; ultimo_acesso: string | null; visitas: number } | null>(null)
  const [erroPortal, setErroPortal] = useState(false)
  const [editando, setEditando] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [erroForm, setErroForm] = useState<string | null>(null)
  const [form, setForm] = useState({ nome: '', documento: '', email: '', telefone: '' })
  // Correção de cadastro ou transferência de propriedade? Só a Marina sabe, e
  // a diferença decide se isso vira elo na cadeia de proprietários do dossiê.
  const [evento, setEvento] = useState<'correcao' | 'transferencia'>('correcao')
  const [tipoTransferencia, setTipoTransferencia] = useState('Compra e Venda')
  const [dataTransferencia, setDataTransferencia] = useState('')

  // A pergunta "o cliente está usando o Portal?" é da Marina. No Portal, quem
  // lê é o próprio dono — não faz sentido, e o servidor recusaria.
  const lerPortal = useCallback(() => {
    if (readOnly) return
    api.ativos.acessoDoProprietario(ativo.id)
      .then((r) => setPortal(r))
      .catch(() => setErroPortal(true))
  }, [ativo.id, readOnly])

  useEffect(() => { lerPortal() }, [lerPortal])

  function abrirEdicao() {
    setForm({
      nome: ativo.proprietario_nome || '',
      documento: ativo.proprietario_documento || '',
      email: ativo.proprietario_email || '',
      // O campo guarda DDD + número; o "+55" é rótulo, não conteúdo.
      telefone: soDDDeNumero(ativo.proprietario_telefone || ''),
    })
    setEvento('correcao')
    setTipoTransferencia('Compra e Venda')
    setDataTransferencia(new Date().toISOString().slice(0, 10))
    setErroForm(null)
    setEditando(true)
  }

  async function salvar() {
    const email = form.email.trim().toLowerCase()
    if (email && !emailValido(email)) {
      setErroForm(MSG_EMAIL_INVALIDO)
      return
    }
    if (email && form.telefone && !telefoneCompleto(form.telefone)) {
      setErroForm(MSG_TELEFONE_INCOMPLETO)
      return
    }
    setSalvando(true)
    setErroForm(null)
    try {
      const salvo = await api.ativos.definirProprietario(ativo.id, {
        proprietario_email: email || null,
        proprietario_telefone: form.telefone ? `+${comDDI(form.telefone)}` : null,
        proprietario_nome: form.nome.trim() || null,
        // Já chega mascarado do banco e a função no servidor é idempotente:
        // reenviar o mascarado não estraga o que está guardado.
        proprietario_documento: form.documento.trim() || null,
        evento,
        ...(evento === 'transferencia'
          ? { tipo_transferencia: tipoTransferencia, data_transferencia: dataTransferencia }
          : {}),
      })
      onSalvo?.({
        proprietario_email: salvo?.proprietario_email ?? null,
        proprietario_telefone: salvo?.proprietario_telefone ?? null,
        proprietario_nome: salvo?.proprietario_nome ?? null,
        proprietario_documento: salvo?.proprietario_documento ?? null,
      })
      setEditando(false)
      lerPortal()
    } catch (e: any) {
      setErroForm(e?.message || 'Não foi possível salvar. Tente de novo.')
    } finally {
      setSalvando(false)
    }
  }

  const embarcacao: [string, string | null][] = [
    ['Nome', texto(ativo.nome_reg)],
    ['Tipo', TIPO[ativo.tipo] || texto(ativo.tipo)],
    ['Fabricante / Marca', texto(ativo.marca)],
    ['Modelo', texto(ativo.modelo)],
    ['Comprimento', numero(ativo.comprimento_pes, ' pés')],
    ['Ano de fabricação', ativo.ano_fabricacao ? String(ativo.ano_fabricacao) : null],
    ['Boca (largura)', numero(ativo.largura, ' m')],
    ['Calado', numero(ativo.calado, ' m')],
    ['Material do casco', texto(ativo.material_casco)],
    ['Passageiros', numero(ativo.capacidade_passageiros)],
    ['Cabines', numero(ativo.num_cabines)],
    ['Tanque', numero(ativo.capacidade_tanque, ' L')],
    ['Modelo do motor', texto(ativo.modelo_motor)],
    ['Potência (por motor)', numero(ativo.potencia_motor, ' HP')],
    ['Nº de motores', numero(ativo.num_motores)],
    ['Combustível', texto(ativo.tipo_combustivel)],
  ]

  const semEmail = !texto(ativo.proprietario_email)

  let acesso: { cor: string; frase: string } | null = null
  if (!readOnly) {
    if (semEmail) {
      acesso = { cor: 'text-amber-300', frase: 'Sem e-mail cadastrado — o proprietário não consegue entrar no Portal.' }
    } else if (erroPortal) {
      acesso = { cor: 'text-white/40', frase: 'Não foi possível verificar o acesso ao Portal agora.' }
    } else if (!portal) {
      acesso = { cor: 'text-white/30', frase: 'Verificando o acesso ao Portal…' }
    } else if (portal.situacao === 'entrou' && portal.ultimo_acesso) {
      const d = new Date(portal.ultimo_acesso)
      const vezes = portal.visitas > 1 ? ` · ${portal.visitas} visitas` : ''
      acesso = {
        cor: 'text-emerald-300',
        frase: `Última visita ao Portal em ${d.toLocaleDateString('pt-BR')} às ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}${vezes}.`,
      }
    } else {
      acesso = { cor: 'text-white/50', frase: 'O proprietário ainda não entrou no Portal.' }
    }
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-3 duration-300">
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="w-10 h-10 flex items-center justify-center border border-white/10 rounded-sm text-white/40 hover:text-[#c5a059] hover:border-[#c5a059]/40 transition-all">
          <ArrowLeft size={16} />
        </button>
        <h2 className="text-xl font-serif font-bold text-white tracking-tight flex items-center gap-3">
          <ClipboardList size={20} className="text-[#c5a059]" /> Dados da Embarcação
          <span className="text-white/20 text-[10px] font-black uppercase tracking-[0.3em] hidden sm:inline">· Cadastro & Proprietário</span>
        </h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-[#021431] border border-white/[0.06] rounded-sm p-7">
          <h3 className="text-white text-base font-serif font-bold tracking-tight flex items-center gap-2.5 mb-3">
            <Ship size={16} className="text-[#c5a059]" /> Embarcação
          </h3>
          {embarcacao.map(([r, v]) => <Linha key={r} rotulo={r} valor={v} />)}
        </div>

        <div className="bg-[#021431] border border-white/[0.06] rounded-sm p-7 self-start">
          <div className="flex items-center justify-between gap-4 mb-3">
            <h3 className="text-white text-base font-serif font-bold tracking-tight flex items-center gap-2.5">
              <User size={16} className="text-[#c5a059]" /> Proprietário
            </h3>
            {/* Editar é da Marina: ela é quem afirma de quem é o barco. No
                Portal o próprio dono lê a tela, e lá não há botão nenhum. */}
            {!readOnly && !editando && (
              <button
                onClick={abrirEdicao}
                className="flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.2em] text-white/40 hover:text-[#c5a059] border border-white/10 hover:border-[#c5a059]/40 rounded-sm px-3 py-2 transition-all"
              >
                <PenLine size={12} /> Editar
              </button>
            )}
          </div>

          {!editando ? (
            <>
              <Linha rotulo="Nome" valor={texto(ativo.proprietario_nome)} />
              <Linha rotulo="CPF / CNPJ" valor={texto(ativo.proprietario_documento)} />
              <Linha rotulo="E-mail" valor={texto(ativo.proprietario_email)} />
              <Linha rotulo="WhatsApp" valor={texto(ativo.proprietario_telefone)} />

              {acesso && (
                <p className={`text-[11px] leading-relaxed mt-4 ${acesso.cor}`}>{acesso.frase}</p>
              )}
            </>
          ) : (
            <div className="space-y-4">
              <Campo rotulo="Nome" valor={form.nome} onChange={(v) => setForm({ ...form, nome: v })}
                     placeholder="Nome completo ou razão social" />
              <Campo rotulo="CPF / CNPJ" valor={form.documento} onChange={(v) => setForm({ ...form, documento: v })}
                     placeholder="000.000.000-00"
                     ajuda="Guardamos mascarado: os dígitos do meio nunca entram no banco." />
              <Campo rotulo="E-mail" valor={form.email} onChange={(v) => setForm({ ...form, email: v })}
                     placeholder="dono@email.com" tipo="email"
                     ajuda="É a chave do dono para entrar no Portal." />
              <Campo rotulo="WhatsApp" valor={mascaraTelefone(form.telefone)}
                     onChange={(v) => setForm({ ...form, telefone: soDDDeNumero(v) })}
                     placeholder="(12) 99118-7251" prefixo="+55"
                     ajuda="Por onde o código de acesso também é enviado." />

              {/* O QUE ACONTECEU AQUI. Trocar o dono nem sempre é venda — na
                  maioria das vezes é corrigir um e-mail digitado errado. Se
                  toda correção virasse elo da cadeia de proprietários, o
                  dossiê encheria de erro de digitação e a cadeia deixaria de
                  valer como prova. Quem sabe a diferença é a Marina. */}
              <div className="pt-2 border-t border-white/5 space-y-2">
                <p className="text-[9px] uppercase tracking-[0.25em] text-white/30 font-black">O que aconteceu</p>
                <div className="flex flex-wrap gap-2">
                  {([
                    ['correcao', 'Correção de cadastro'],
                    ['transferencia', 'Transferência de propriedade'],
                  ] as const).map(([valor, rotulo]) => (
                    <button
                      key={valor}
                      onClick={() => setEvento(valor)}
                      className={`px-4 py-2 rounded-sm text-[9px] font-black uppercase tracking-[0.15em] border transition-all ${
                        evento === valor
                          ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]'
                          : 'border-white/10 text-white/40 hover:text-white/70 hover:border-white/25'
                      }`}
                    >
                      {rotulo}
                    </button>
                  ))}
                </div>
                <p className="text-white/25 text-[10px] leading-relaxed">
                  {evento === 'transferencia'
                    ? 'Entra no Dossiê Atlas, na seção Histórico de Proprietários. O registro é selado: depois só se corrige por retificação.'
                    : 'Não gera registro no dossiê. É o caso do e-mail ou do nome digitado errado.'}
                </p>

                {evento === 'transferencia' && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="space-y-1.5">
                      <label className="text-[9px] uppercase tracking-[0.25em] text-white/30 font-black">Tipo</label>
                      <select
                        value={tipoTransferencia}
                        onChange={(e) => setTipoTransferencia(e.target.value)}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-2.5 text-white text-sm focus:border-[#c5a059] outline-none"
                      >
                        {['Compra e Venda', 'Herança', 'Doação'].map((t) => (
                          <option key={t} value={t} className="bg-[#010c20]">{t}</option>
                        ))}
                      </select>
                    </div>
                    <div className="space-y-1.5">
                      <label className="text-[9px] uppercase tracking-[0.25em] text-white/30 font-black">Data</label>
                      <input
                        type="date"
                        value={dataTransferencia}
                        onChange={(e) => setDataTransferencia(e.target.value)}
                        className="w-full bg-white/[0.03] border border-white/10 rounded-sm px-4 py-2.5 text-white text-sm focus:border-[#c5a059] outline-none"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Apagar o e-mail é o caminho de "barco vendido": o vínculo cai
                  inteiro, de propósito. O histórico selado não se mexe — mas
                  ninguém pode descobrir isso depois de salvar. */}
              {!form.email.trim() && (ativo.proprietario_email || '').trim() && (
                <p className="text-amber-300 text-[11px] leading-relaxed">
                  Sem e-mail, o vínculo do proprietário é desfeito: nome, CPF/CNPJ e WhatsApp
                  saem junto e o dono perde o acesso ao Portal. É o caminho de barco vendido.
                  O histórico da embarcação não muda.
                </p>
              )}

              {erroForm && <p className="text-rose-300 text-[11px] leading-relaxed">{erroForm}</p>}

              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={salvar}
                  disabled={salvando}
                  className="bg-[#c5a059] hover:bg-[#b38f4d] disabled:opacity-40 text-[#010c20] px-6 py-2.5 rounded-sm text-[9px] font-black uppercase tracking-[0.2em] transition-all"
                >
                  {salvando ? 'Salvando' : !form.email.trim() && (ativo.proprietario_email || '').trim()
                    ? 'Remover vínculo' : 'Salvar'}
                </button>
                <button
                  onClick={() => { setEditando(false); setErroForm(null) }}
                  className="text-white/40 hover:text-white/70 text-[9px] font-black uppercase tracking-[0.2em] transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Letra miúda, e precisa estar certa: a especificação, o nome e o
          documento SAEM no Dossiê Atlas (dossie_data.py). E-mail e WhatsApp
          não saem — o dossiê circula entre corretor, comprador e seguradora. */}
      <p className="text-white/25 text-[10px] leading-relaxed max-w-3xl">
        As especificações, o nome e o CPF/CNPJ do proprietário saem impressos no Dossiê Atlas.
        O e-mail e o WhatsApp não saem: servem apenas para o acesso ao Portal do Proprietário.
      </p>
    </div>
  )
}
