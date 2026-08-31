import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'

interface AuthContextType {
  session: Session | null
  loading: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  session: null,
  loading: true,
  signOut: async () => {},
})

/**
 * Sessão do usuário — com o cliente Supabase carregado SOB DEMANDA.
 *
 * Este provider envolve a aplicação inteira, então o que ele importa no topo
 * entra no chunk de entrada de TODA visita. Até 31/08/2026 ele importava
 * `supabase` estaticamente, e por isso quem só abria a landing ou conferia um
 * QR baixava e instanciava o cliente de banco antes de ver a primeira letra —
 * a landing não fala com banco nenhum.
 *
 * O `import type` acima não custa nada: tipo é apagado no build. O peso vinha
 * do import de valor, que instancia `createClient` ao carregar o módulo.
 *
 * POR QUE ISSO NÃO ATRASA QUEM ESTÁ LOGADO
 * ----------------------------------------
 * A checagem de sessão JÁ era assíncrona: `getSession()` devolve promessa e
 * existe `loading: true` até ela responder. O import dinâmico entra antes
 * dessa promessa, no mesmo estado de carregamento que já existia — quem
 * consome o contexto (`PrivateRoute`) espera por `loading` de qualquer forma.
 *
 * O QUE NÃO PODE ACONTECER
 * ------------------------
 * `loading` virar `false` antes de a sessão ser conhecida. Isso faria o
 * `PrivateRoute` concluir "não está logado" e chutar para o login uma marina
 * que estava autenticada — no meio do trabalho dela. Por isso `setLoading`
 * só é chamado depois da resposta, e também no `catch`: falha ao carregar o
 * cliente deixa o app sem sessão, mas nunca preso numa tela de carregamento.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Guarda contra atualizar estado depois de desmontado: a promessa do
    // import pode resolver quando o componente já saiu.
    let ativo = true
    let cancelar: (() => void) | undefined

    import('../services/api')
      .then(({ supabase }) => {
        supabase.auth.getSession().then(({ data: { session } }) => {
          if (!ativo) return
          setSession(session)
          setLoading(false)
        })

        const { data: { subscription } } = supabase.auth.onAuthStateChange(
          (_event, session) => {
            if (ativo) setSession(session)
          },
        )
        cancelar = () => subscription.unsubscribe()
      })
      .catch(() => {
        // Sem cliente não há sessão — mas o app precisa sair do limbo.
        if (ativo) setLoading(false)
      })

    return () => {
      ativo = false
      cancelar?.()
    }
  }, [])

  const signOut = async () => {
    const { supabase } = await import('../services/api')
    await supabase.auth.signOut()
    localStorage.removeItem('yachts_token')
  }

  return (
    <AuthContext.Provider value={{ session, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook de acesso ao contexto. Usado por PrivateRoute, Dashboard e
 * AcessoSuspenso — sem ele o login inteiro para de compilar.
 */
export const useAuth = () => useContext(AuthContext)
