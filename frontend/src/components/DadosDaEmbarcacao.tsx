import { useEffect, useState } from 'react'
import { ArrowLeft, ClipboardList, Ship, User } from 'lucide-react'
import { Ativo } from '../types'
import { api } from '../services/api'

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

type Situacao = 'sem_email' | 'nunca_entrou' | 'entrou' | 'outra_conta'

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

export default function DadosDaEmbarcacao({ ativo, onBack, readOnly = false }: {
  ativo: Ativo
  onBack: () => void
  readOnly?: boolean
}) {
  const [portal, setPortal] = useState<{ situacao: Situacao; ultimo_acesso: string | null } | null>(null)
  const [erroPortal, setErroPortal] = useState(false)

  // A pergunta "o cliente está usando o Portal?" é da Marina. No Portal, quem
  // lê é o próprio dono — não faz sentido, e o servidor recusaria.
  useEffect(() => {
    if (readOnly) return
    let vivo = true
    api.ativos.acessoDoProprietario(ativo.id)
      .then((r) => { if (vivo) setPortal(r) })
      .catch(() => { if (vivo) setErroPortal(true) })
    return () => { vivo = false }
  }, [ativo.id, readOnly])

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
      acesso = {
        cor: 'text-emerald-300',
        frase: `Último acesso ao Portal em ${d.toLocaleDateString('pt-BR')} às ${d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}.`,
      }
    } else if (portal.situacao === 'outra_conta') {
      acesso = { cor: 'text-white/40', frase: 'Este e-mail pertence a uma conta que não é de proprietário — o acesso ao Portal não pode ser medido.' }
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
          <h3 className="text-white text-base font-serif font-bold tracking-tight flex items-center gap-2.5 mb-3">
            <User size={16} className="text-[#c5a059]" /> Proprietário
          </h3>
          <Linha rotulo="Nome" valor={texto(ativo.proprietario_nome)} />
          <Linha rotulo="CPF / CNPJ" valor={texto(ativo.proprietario_documento)} />
          <Linha rotulo="E-mail" valor={texto(ativo.proprietario_email)} />
          <Linha rotulo="WhatsApp" valor={texto(ativo.proprietario_telefone)} />

          {acesso && (
            <p className={`text-[11px] leading-relaxed mt-4 ${acesso.cor}`}>{acesso.frase}</p>
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
