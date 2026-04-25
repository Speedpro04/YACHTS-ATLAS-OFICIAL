import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo } from '../types'
import { Ship, Plus, Trash2 } from 'lucide-react'

export default function Ativos() {
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    tipo: 'iate',
    marca: '',
    modelo: '',
    ano_fabricacao: new Date().getFullYear(),
  })
  
  useEffect(() => {
    loadAtivos()
  }, [])
  
  const loadAtivos = async () => {
    try {
      const data = await api.ativos.list()
      setAtivos(data)
    } catch (err) {
      console.error('Erro:', err)
    } finally {
      setLoading(false)
    }
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.ativos.create(formData)
      setShowForm(false)
      setFormData({ tipo: 'iate', marca: '', modelo: '', ano_fabricacao: new Date().getFullYear() })
      loadAtivos()
    } catch (err) {
      console.error('Erro ao criar:', err)
    }
  }
  
  const handleDelete = async (id: string) => {
    if (confirm('Tem certeza que deseja excluir este ativo?')) {
      try {
        await api.ativos.delete(id)
        loadAtivos()
      } catch (err) {
        console.error('Erro ao excluir:', err)
      }
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
    <div className="space-y-6 pb-20 md:pb-0">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Meus Ativos</h1>
          <p className="text-gray-400">Gerencie seus ativos náuticos</p>
        </div>
        <button 
          onClick={() => setShowForm(!showForm)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus size={18} />
          <span className="hidden sm:inline">Novo Ativo</span>
        </button>
      </div>
      
      {showForm && (
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Cadastrar Novo Ativo</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Tipo</label>
                <select
                  value={formData.tipo}
                  onChange={(e) => setFormData({...formData, tipo: e.target.value})}
                  className="input w-full"
                >
                  <option value="iate">Iate</option>
                  <option value="lancha">Lancha</option>
                  <option value="veleiro">Veleiro</option>
                  <option value="jetski">Jet-ski</option>
                  <option value="barco_pesca">Barco de Pesca</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Ano de Fabricação</label>
                <input
                  type="number"
                  value={formData.ano_fabricacao}
                  onChange={(e) => setFormData({...formData, ano_fabricacao: parseInt(e.target.value)})}
                  className="input w-full"
                  min="1900"
                  max={new Date().getFullYear()}
                  required
                />
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Marca</label>
                <input
                  type="text"
                  value={formData.marca}
                  onChange={(e) => setFormData({...formData, marca: e.target.value})}
                  className="input w-full"
                  placeholder="Azimut, Sunseeker, etc"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Modelo</label>
                <input
                  type="text"
                  value={formData.modelo}
                  onChange={(e) => setFormData({...formData, modelo: e.target.value})}
                  className="input w-full"
                  placeholder="78 Flybridge, etc"
                  required
                />
              </div>
            </div>
            <div className="flex gap-4">
              <button type="submit" className="btn-primary">Cadastrar</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
            </div>
          </form>
        </div>
      )}
      
      <div className="card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-navy-900">
              <th className="text-left text-gray-400 text-sm font-medium py-3 px-4">Ativo</th>
              <th className="text-left text-gray-400 text-sm font-medium py-3 px-4 hidden md:table-cell">Tipo</th>
              <th className="text-left text-gray-400 text-sm font-medium py-3 px-4">Classificação</th>
              <th className="text-left text-gray-400 text-sm font-medium py-3 px-4 hidden sm:table-cell">Progresso</th>
              <th className="text-right text-gray-400 text-sm font-medium py-3 px-4">Ações</th>
            </tr>
          </thead>
          <tbody>
            {ativos.map((ativo) => (
              <tr key={ativo.id} className="border-b border-navy-900/50 hover:bg-navy-900/50">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-navy-900 rounded-lg flex items-center justify-center">
                      <Ship size={20} className="text-gold-500" />
                    </div>
                    <div>
                      <div className="text-white font-medium">{ativo.marca} {ativo.modelo}</div>
                      <div className="text-gray-500 text-sm">{ativo.ano_fabricacao}</div>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4 hidden md:table-cell">
                  <span className="text-gray-300 capitalize">{ativo.tipo}</span>
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    ativo.classificacao === 'gold' ? 'bg-gold-500 text-navy-900' :
                    ativo.classificacao === 'silver' ? 'bg-silver text-navy-900' :
                    'bg-bronze text-navy-900'
                  }`}>
                    ★ {ativo.classificacao}
                  </span>
                </td>
                <td className="py-3 px-4 hidden sm:table-cell">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-navy-900 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gold-500 rounded-full"
                        style={{ width: `${ativo.progresso}%` }}
                      />
                    </div>
                    <span className="text-gray-400 text-sm">{ativo.progresso}%</span>
                  </div>
                </td>
                <td className="py-3 px-4 text-right">
                  <button 
                    onClick={() => handleDelete(ativo.id)}
                    className="p-2 text-gray-400 hover:text-red-400 transition-all"
                  >
                    <Trash2 size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {ativos.length === 0 && (
          <div className="text-center py-12">
            <Ship size={48} className="mx-auto text-gray-500 mb-4" />
            <p className="text-gray-400">Nenhum ativo cadastrado</p>
          </div>
        )}
      </div>
    </div>
  )
}