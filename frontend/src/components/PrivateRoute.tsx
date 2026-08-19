import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { api, ApiError } from '../services/api'
import AcessoSuspenso, { Bloqueio } from './AcessoSuspenso'

/**
 * Portão único das rotas autenticadas.
 *
 * Ter sessão do Supabase não é o mesmo que poder usar o Atlas: o login acontece
 * no navegador, mas quem sabe se a marina está em dia é o backend. Por isso,
 * com sessão em mãos, perguntamos a ele — e um 402 vira a tela de regularização
 * em vez de um painel que carrega quebrado.
 *
 * Fica aqui, e não no Login, para valer também para quem já estava logado
 * quando o corte por inadimplência aconteceu.
 */
export default function PrivateRoute() {
  const { session, loading } = useAuth()
  const [verificando, setVerificando] = useState(true)
  const [bloqueio, setBloqueio] = useState<Bloqueio | null>(null)

  useEffect(() => {
    if (!session) {
      setVerificando(false)
      return
    }

    let ativo = true
    setVerificando(true)

    api.auth.me()
      .then(() => { if (ativo) setBloqueio(null) })
      .catch((err) => {
        if (!ativo) return
        // Só o 402 bloqueia. Backend fora do ar ou rede caindo não pode virar
        // "sua conta está suspensa" na cara de quem está em dia — o porteiro
        // do backend continua protegendo os dados de qualquer forma.
        const detalhe = err instanceof ApiError && err.status === 402
          ? (err.details as { detail?: Bloqueio } | null)?.detail
          : null
        setBloqueio(detalhe ?? null)
      })
      .finally(() => { if (ativo) setVerificando(false) })

    return () => { ativo = false }
  }, [session])

  if (loading || (session && verificando)) {
    return (
      <div className="min-h-screen bg-[#010c20] flex items-center justify-center">
        <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full"></div>
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (bloqueio) {
    return <AcessoSuspenso bloqueio={bloqueio} />
  }

  return <Outlet />
}
