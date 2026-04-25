import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo, Documento } from '../types'
import { Ship, Plus, CheckCircle, AlertCircle } from 'lucide-react'

export default function Dashboard() {
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    loadDashboard()
  }, [])
  
  const loadDashboard = async () => {
    try {
      const data = await api.ativos.list()
      setAtivos(data)
    } catch (err) {
      console.error('Erro ao carregar:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const stats = {
    total: ativos.length,
    bronze: ativos.filter(a => a.classificacao === 'bronze').length,
    silver: ativos.filter(a => a.classificacao === 'silver').length,
    gold: ativos.filter(a => a.classificacao === 'gold').length,
  }
  
  const getClassificacaoColor = (classificacao: string) => {
    switch (classificacao) {
      case 'gold': return 'bg-gold-500'
      case 'silver': return 'bg-silver'
      case 'bronze': return 'bg-bronze'
      default: return 'bg-gray-500'
    }
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full"></div>
      </div>
    )
  }
  
  return (
    <div className="space-y-8 pb-20 md:pb-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">Visão geral dos seus ativos</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus size={18} />
          <span className="hidden sm:inline">Novo Ativo</span>
        </button>
      </div>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-gray-400 text-sm mb-1">Total de Ativos</div>
          <div className="text-3xl font-bold text-white">{stats.total}</div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm mb-1">Bronze</div>
          <div className="text-3xl font-bold text-bronze">{stats.bronze}</div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm mb-1">Silver</div>
          <div className="text-3xl font-bold text-silver">{stats.silver}</div>
        </div>
        <div className="card">
          <div className="text-gray-400 text-sm mb-1">Gold</div>
          <div className="text-3xl font-bold text-gold-500">{stats.gold}</div>
        </div>
      </div>
      
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Seus Ativos</h2>
        
        {ativos.length === 0 ? (
          <div className="card text-center py-12">
            <Ship size={48} className="mx-auto text-gray-500 mb-4" />
            <h3 className="text-white font-medium mb-2">Nenhum ativo cadastrado</h3>
            <p className="text-gray-400 text-sm mb-4">Comece adicionando seu primeiro ativo náutico</p>
            <button className="btn-primary inline-flex items-center gap-2">
              <Plus size={18} />
              Adicionar Ativo
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ativos.map((ativo) => (
              <div key={ativo.id} className="card hover:border-gold-500/30">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-navy-900 rounded-lg flex items-center justify-center">
                    <Ship size={24} className="text-gold-500" />
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getClassificacaoColor(ativo.classificacao)} text-navy-900`}>
                    ★ {ativo.classificacao.toUpperCase()}
                  </span>
                </div>
                
                <h3 className="text-white font-semibold mb-1">
                  {ativo.marca} {ativo.modelo}
                </h3>
                <p className="text-gray-400 text-sm mb-4">
                  {ativo.ano_fabricacao} • {ativo.tipo}
                </p>
                
                <div className="mb-3">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-400">Progresso</span>
                    <span className="text-white">{ativo.progresso}%</span>
                  </div>
                  <div className="h-2 bg-navy-900 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-gold-500 to-gold-400 rounded-full transition-all"
                      style={{ width: `${ativo.progresso}%` }}
                    />
                  </div>
                </div>
                
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  {ativo.progresso === 100 ? (
                    <CheckCircle size={16} className="text-green-500" />
                  ) : (
                    <AlertCircle size={16} className="text-yellow-500" />
                  )}
                  <span>{ativo.progresso === 100 ? 'Certificação completa' : 'Complete a documentação'}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}