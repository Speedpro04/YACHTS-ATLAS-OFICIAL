import { useState } from 'react'
import { api } from '../services/api'

export default function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [nome, setNome] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      if (isLogin) {
        const response = await api.auth.login(email, password)
        localStorage.setItem('yachts_token', response.access_token)
        window.location.href = '/'
      } else {
        await api.auth.signup({ email, password, nome })
        setIsLogin(true)
        setError('Conta criada! Faça login.')
      }
    } catch (err) {
      setError('Erro ao autenticar. Verifique seus dados.')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-gold-500 to-gold-400 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="text-navy-900 font-bold text-2xl">YA</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Yachts Atlas</h1>
          <p className="text-gray-400">Registro digital imutável para ativos náuticos</p>
        </div>
        
        <div className="card">
          <div className="flex mb-6 bg-navy-900 rounded-lg p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 rounded-lg font-medium transition-all ${
                isLogin ? 'bg-gold-500 text-navy-900' : 'text-gray-400'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 rounded-lg font-medium transition-all ${
                !isLogin ? 'bg-gold-500 text-navy-900' : 'text-gray-400'
              }`}
            >
              Cadastro
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm text-gray-400 mb-2">Nome</label>
                <input
                  type="text"
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="input w-full"
                  placeholder="Seu nome"
                  required
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input w-full"
                placeholder="seu@email.com"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Senha</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input w-full"
                placeholder="••••••••"
                required
              />
            </div>
            
            {error && (
              <div className="text-red-400 text-sm text-center">{error}</div>
            )}
            
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full"
            >
              {loading ? 'Aguarde...' : isLogin ? 'Entrar' : 'Cadastrar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}