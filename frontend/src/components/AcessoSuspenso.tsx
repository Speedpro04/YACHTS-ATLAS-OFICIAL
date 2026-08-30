import { AlertCircle, ArrowRight, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

/**
 * Tela de regularização — o que a marina vê quando o pagamento está pendente
 * ou em atraso.
 *
 * Existe para não devolver um erro genérico: sem explicação, a marina acha que
 * perdeu a senha e liga em vez de pagar. Aqui ela lê o motivo e tem o botão que
 * resolve na mesma tela.
 *
 * O texto e o link vêm do backend (app/core/acesso.py) — a regra de cobrança
 * mora num lugar só, e o frontend não decide nada sobre dinheiro.
 */
export interface Bloqueio {
  motivo: string
  mensagem: string
  dias_em_atraso?: number | null
  link_pagamento?: string | null
}

const TITULOS: Record<string, string> = {
  pagamento_pendente: 'Pagamento em confirmação',
  inadimplente: 'Acesso suspenso',
  assinatura_cancelada: 'Assinatura encerrada',
}

// O botão diz o que a pessoa vai fazer, e isso muda com o motivo: quem
// cancelou não tem nada a regularizar — vai assinar de novo.
const ACOES: Record<string, string> = {
  pagamento_pendente: 'Concluir pagamento',
  inadimplente: 'Regularizar pagamento',
  assinatura_cancelada: 'Assinar novamente',
}

export default function AcessoSuspenso({ bloqueio }: { bloqueio: Bloqueio }) {
  const { signOut } = useAuth()
  const titulo = TITULOS[bloqueio.motivo] ?? 'Acesso indisponível'
  const acao = ACOES[bloqueio.motivo] ?? 'Regularizar pagamento'

  return (
    <div className="min-h-screen bg-[#010c20] flex items-center justify-center px-6 font-['Inter']">
      <div className="w-full max-w-lg text-center">
        <img
          src="/logo-transparent.png"
          alt="Yachts Atlas"
          className="w-[200px] h-auto object-contain mx-auto mb-12"
        />

        <div className="border border-[#c5a059]/30 bg-white/[0.03] rounded-sm p-10">
          <div className="w-14 h-14 rounded-full bg-[#c5a059]/10 border border-[#c5a059]/30 flex items-center justify-center mx-auto mb-8">
            <AlertCircle size={24} className="text-[#c5a059]" />
          </div>

          <h1 className="text-2xl font-serif font-bold text-white mb-5 tracking-tight">
            {titulo}
          </h1>

          <p className="text-white/50 text-sm leading-relaxed mb-10">
            {bloqueio.mensagem}
          </p>

          {bloqueio.link_pagamento && (
            <a
              href={bloqueio.link_pagamento}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] py-4 rounded-sm text-[11px] font-black uppercase tracking-[0.25em] flex items-center justify-center gap-3 transition-all hover:-translate-y-0.5"
            >
              {acao}
              <ArrowRight size={15} />
            </a>
          )}

          <button
            onClick={signOut}
            className="mt-6 text-white/30 hover:text-[#c5a059] text-[10px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-2 mx-auto transition-colors"
          >
            <LogOut size={13} />
            Sair
          </button>
        </div>

        <p className="text-white/20 text-[10px] uppercase tracking-[0.2em] mt-8">
          Dúvidas? Fale com a Yachts Atlas
        </p>
      </div>
    </div>
  )
}
