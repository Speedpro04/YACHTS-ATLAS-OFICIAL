import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Ativo } from '../types'
import { Ship, Plus, CheckCircle, AlertCircle, TrendingUp, Anchor, Download, Zap, Cpu, Shield, Wrench, Paintbrush, Armchair, FileCheck, FileText } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [ativos, setAtivos] = useState<Ativo[]>([])
  const [dossierCount, setDossierCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      const [ativosData, plansData] = await Promise.allSettled([
        api.ativos.list(),
        api.pagamentos.planos(),
      ])
      if (ativosData.status === 'fulfilled') setAtivos(ativosData.value)
      if (plansData.status === 'fulfilled' && plansData.value?.dossier_count != null) {
        setDossierCount(plansData.value.dossier_count)
      }
    } catch (err) {
      console.error('Erro ao carregar:', err)
    } finally {
      setLoading(false)
    }
  }

  const stats = {
    total: ativos.length,
    gold: ativos.filter(a => a.classificacao === 'gold').length,
    compliance: Math.round(ativos.reduce((acc, curr) => acc + curr.progresso, 0) / (ativos.length || 1)),
    dossiers: dossierCount ?? 0,
    revenue: (dossierCount ?? 0) * 400,
  }

  // Gera um relatório executivo da frota (branded) e abre o diálogo de
  // impressão — o usuário salva como PDF. Sem dependências externas.
  const generateReport = () => {
    const esc = (s: unknown) =>
      String(s ?? '—').replace(/[&<>"']/g, (c) =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c] as string))

    const tipoLabel: Record<string, string> = {
      iate: 'Iate', lancha: 'Lancha', veleiro: 'Veleiro', jetski: 'Jet Ski', barco_pesca: 'Barco de Pesca',
    }
    const statusLabel: Record<string, string> = {
      ativo: 'Ativo', inativo: 'Inativo', vendido: 'Vendido', manutencao: 'Manutenção',
    }

    const carimbo = new Date().toLocaleString('pt-BR')

    const rows = ativos.length
      ? ativos.map((a, i) => `
          <tr>
            <td class="num">${String(i + 1).padStart(2, '0')}</td>
            <td>${esc(tipoLabel[a.tipo] ?? a.tipo)}</td>
            <td><strong>${esc(a.marca)} ${esc(a.modelo)}</strong></td>
            <td class="num">${esc(a.ano_fabricacao)}</td>
            <td class="num">${esc(a.comprimento_pes)} pés</td>
            <td>${esc(a.proprietario_nome)}</td>
            <td><span class="tag tag-${esc(a.classificacao)}">${esc(a.classificacao)}</span></td>
            <td>${esc(statusLabel[a.status] ?? a.status)}</td>
            <td class="num">${esc(a.progresso)}%</td>
          </tr>`).join('')
      : `<tr><td colspan="9" class="empty">Nenhum ativo cadastrado nesta frota.</td></tr>`

    const card = (label: string, value: string | number) => `
      <div class="card">
        <span class="card-label">${label}</span>
        <span class="card-value">${value}</span>
      </div>`

    const html = `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<title>Relatório de Frota — Marina Hub</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Georgia, 'Times New Roman', serif; color: #010c20; padding: 48px 56px; }
  .eyebrow { font-family: Arial, sans-serif; font-size: 9px; letter-spacing: .42em; font-weight: 800;
             text-transform: uppercase; color: #c5a059; }
  h1 { font-size: 38px; line-height: 1.05; margin: 10px 0 4px; }
  h1 em { color: #c5a059; }
  .sub { font-family: Arial, sans-serif; font-size: 12px; color: #5b6473; }
  .rule { height: 2px; background: #c5a059; width: 64px; margin: 18px 0 28px; }
  .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 34px; }
  .card { border: 1px solid #e3e6ec; border-top: 3px solid #c5a059; padding: 16px 18px; border-radius: 2px; }
  .card-label { display: block; font-family: Arial, sans-serif; font-size: 8.5px; letter-spacing: .26em;
                font-weight: 800; text-transform: uppercase; color: #8a93a3; margin-bottom: 8px; }
  .card-value { font-size: 28px; font-weight: 700; color: #010c20; }
  h2 { font-size: 14px; font-family: Arial, sans-serif; letter-spacing: .2em; text-transform: uppercase;
       color: #021a3d; margin-bottom: 12px; border-bottom: 1px solid #e3e6ec; padding-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 11px; }
  thead th { text-align: left; font-size: 8.5px; letter-spacing: .14em; text-transform: uppercase;
             color: #8a93a3; padding: 8px 10px; border-bottom: 1.5px solid #010c20; }
  tbody td { padding: 9px 10px; border-bottom: 1px solid #eef0f4; color: #2b3340; }
  tbody tr:nth-child(even) td { background: #fafbfc; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  td.empty { text-align: center; color: #8a93a3; padding: 28px; font-style: italic; }
  .tag { font-size: 8.5px; font-weight: 800; letter-spacing: .1em; text-transform: uppercase;
         padding: 2px 8px; border-radius: 999px; color: #fff; }
  .tag-gold { background: #c5a059; } .tag-silver { background: #9ca3af; } .tag-bronze { background: #b08d57; }
  footer { margin-top: 34px; padding-top: 16px; border-top: 1px solid #e3e6ec;
           font-family: Arial, sans-serif; font-size: 9px; color: #8a93a3; display: flex; justify-content: space-between; }
  @page { margin: 16mm; }
  @media print { body { padding: 0; } tr { page-break-inside: avoid; } }
</style>
</head>
<body>
  <div class="eyebrow">Marina Hub · Custódia Digital</div>
  <h1>Relatório de <em>Frota</em></h1>
  <div class="sub">Gerado em ${carimbo} · Auditoria e rastreamento em tempo real</div>
  <div class="rule"></div>

  <div class="cards">
    ${card('Total de Ativos', stats.total)}
    ${card('Compliance Médio', stats.compliance + '%')}
    ${card('Ativos Gold', stats.gold)}
    ${card('Dossiês Gerados', stats.dossiers)}
  </div>

  <h2>Inventário de Ativos</h2>
  <table>
    <thead>
      <tr>
        <th>#</th><th>Tipo</th><th>Embarcação</th><th>Ano</th><th>Comprimento</th>
        <th>Proprietário</th><th>Classe</th><th>Status</th><th>Compliance</th>
      </tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>

  <footer>
    <span>Yachts Atlas — Documento confidencial</span>
    <span>${ativos.length} ativo(s) · ${carimbo}</span>
  </footer>
  <script>window.addEventListener('load', function () { setTimeout(function () { window.focus(); window.print(); }, 250); });<\/script>
</body>
</html>`

    const w = window.open('', '_blank', 'width=900,height=1000')
    if (!w) {
      alert('Não foi possível abrir o relatório. Habilite os pop-ups para este site e tente novamente.')
      return
    }
    w.document.write(html)
    w.document.close()
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96">
        <div className="animate-spin w-10 h-10 border-2 border-[#c5a059] border-t-transparent rounded-full mb-4"></div>
        <span className="text-white/40 uppercase tracking-[0.2em] text-[10px] font-black">{t('common.loading')}</span>
      </div>
    )
  }
  
  return (
    <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-1000">
      {/* Welcome & Stats Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div 
          className="lg:col-span-2 relative border border-white/5 p-12 rounded-sm overflow-hidden flex flex-col justify-between min-h-[350px] shadow-2xl"
          style={{ background: 'radial-gradient(circle at top right, #021a3d 0%, #010c20 100%)' }}
        >
          {/* Decorative glow */}
          <div className="absolute top-0 right-0 w-80 h-80 bg-[#c5a059]/5 blur-[120px] rounded-full pointer-events-none"></div>
          
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
               <div className="w-8 h-px bg-[#c5a059]"></div>
               <span className="text-[10px] font-black uppercase tracking-[0.4em] text-[#c5a059]">{t('auth.personal_security')}</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-serif font-bold text-white mb-6 tracking-tight leading-tight">
              {t('common.marina_hub')} <br />
              <span className="italic text-[#c5a059]">Fleet Excellence.</span>
            </h1>
            <p className="text-white/40 text-lg max-w-md leading-relaxed font-light">
              {t('lp.mission_tagline')}
            </p>
          </div>

          <div className="relative z-10 flex flex-wrap gap-6 mt-12">
            <button 
              onClick={() => navigate('/app/ativos', { state: { openForm: true } })}
              className="bg-[#c5a059] hover:bg-[#b38f4d] text-[#010c20] px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3 shadow-xl shadow-[#c5a059]/10"
            >
              <Plus size={16} />
              {t('common.add_asset')}
            </button>
            <button
              onClick={generateReport}
              className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-10 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-3"
            >
              <Download size={16} />
              Report
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {[
            { label: t('common.total_assets'), value: stats.total, icon: Ship, color: '#c5a059' },
            { label: t('common.generated_dossiers'), value: stats.dossiers, icon: Download, color: '#c5a059' },
            { label: t('common.total_revenue'), value: `$${stats.revenue}`, icon: TrendingUp, color: '#c5a059' }
          ].map((stat, i) => (
            <div key={i} className="bg-white/[0.02] border border-white/5 p-8 rounded-sm flex items-center gap-8 group hover:border-[#c5a059]/30 transition-all shadow-lg">
              <div className="w-16 h-16 bg-[#c5a059]/5 border border-[#c5a059]/10 rounded-sm flex items-center justify-center text-[#c5a059] group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                <stat.icon size={28} strokeWidth={1.5} />
              </div>
              <div>
                <p className="text-white/30 text-[10px] uppercase tracking-[0.3em] font-black mb-2">{stat.label}</p>
                <p className="text-4xl font-serif font-bold text-white tracking-tight">{stat.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Categorias Técnicas — Canvas Principal */}
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-serif font-bold text-white tracking-tight flex items-center gap-4">
              <Wrench size={22} className="text-[#c5a059]" />
              Painel Técnico
            </h2>
            <p className="text-[10px] text-white/30 uppercase tracking-[0.4em] font-black mt-2">Acesso rápido às categorias de inspeção</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-5">
          {[
            { id: 'documentacao', label: 'Documentação', desc: 'Legal & Conformidade', icon: FileText },
            { id: 'motor', label: 'Motor', desc: 'Propulsão & Mecânica', icon: Zap },
            { id: 'eletrica', label: 'Elétrica', desc: 'Eletrônica & Navegação', icon: Cpu },
            { id: 'seguranca', label: 'Segurança', desc: 'Salvatagem & Proteção', icon: Shield },
            { id: 'manutencao', label: 'Manutenção', desc: 'Serviços & Revisões', icon: Wrench },
            { id: 'pintura', label: 'Pintura', desc: 'Estética & Superfície', icon: Paintbrush },
            { id: 'interior', label: 'Interior', desc: 'Acomodações & Conforto', icon: Armchair },
            { id: 'dossie', label: 'Dossiê', desc: 'Integridade Certificada', icon: FileCheck },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => navigate('/app/ativos', { state: { openCategory: cat.id } })}
              className="group relative bg-[#0a2540] border border-white/5 rounded-sm p-6 text-left hover:border-[#c5a059]/40 transition-all duration-500 hover:-translate-y-1 shadow-lg overflow-hidden"
            >
              {/* Glow sutil no hover */}
              <div className="absolute top-0 right-0 w-24 h-24 bg-[#c5a059]/5 blur-[40px] rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>

              <div className="relative z-10">
                <div className="w-11 h-11 bg-[#c5a059]/10 border border-[#c5a059]/20 rounded-sm flex items-center justify-center text-[#c5a059] mb-4 group-hover:bg-[#c5a059] group-hover:text-[#010c20] transition-all duration-500">
                  <cat.icon size={22} strokeWidth={1.5} />
                </div>
                <p className="text-white font-bold text-sm tracking-wide group-hover:text-[#c5a059] transition-colors">{cat.label}</p>
                <p className="text-[9px] text-white/30 uppercase tracking-[0.2em] font-black mt-1.5">{cat.desc}</p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Assets Section */}
      <div>
        <div className="flex items-center justify-between mb-12 border-b border-white/5 pb-8">
          <h2 className="text-2xl font-serif font-bold text-white flex items-center gap-4 tracking-tight">
            <Anchor size={24} className="text-[#c5a059]" />
            {t('common.your_assets')}
          </h2>
          <div className="flex gap-4">
            <div className="flex bg-white/5 border border-white/10 rounded-sm p-1 shadow-inner">
               <button className="px-6 py-1.5 text-[9px] font-black uppercase tracking-widest bg-[#c5a059] text-[#010c20] rounded-sm transition-all">Grid</button>
               <button className="px-6 py-1.5 text-[9px] font-black uppercase tracking-widest text-white/40 hover:text-white transition-all">List</button>
            </div>
          </div>
        </div>
        
        {ativos.length === 0 ? (
          <div className="bg-white/[0.02] border border-white/5 border-dashed rounded-sm text-center py-32 group hover:border-[#c5a059]/30 transition-all shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-[#c5a059]/2 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            <div className="relative z-10">
              <div className="w-24 h-24 bg-white/5 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-8 text-white/10 group-hover:text-[#c5a059] group-hover:scale-110 transition-all duration-700">
                 <Ship size={48} strokeWidth={1} />
              </div>
              <h3 className="text-2xl font-serif font-bold text-white mb-4 uppercase tracking-widest">{t('common.no_assets')}</h3>
              <p className="text-white/30 max-w-sm mx-auto mb-10 text-sm font-light leading-relaxed">
                {t('common.start_adding')}
              </p>
              <button 
                onClick={() => navigate('/app/ativos', { state: { openForm: true } })}
                className="bg-transparent border border-[#c5a059] text-[#c5a059] hover:bg-[#c5a059] hover:text-[#010c20] px-12 py-4 rounded-sm text-[10px] font-black uppercase tracking-[0.3em] transition-all shadow-xl"
              >
                {t('common.add_asset')}
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            {ativos.map((ativo) => (
              <div 
                key={ativo.id} 
                className="group bg-white/[0.02] border border-white/5 rounded-sm overflow-hidden hover:border-[#c5a059]/40 transition-all duration-700 hover:-translate-y-2 shadow-2xl relative"
              >
                {/* Visual Header */}
                <div className="h-56 bg-[#010c20] relative overflow-hidden">
                   <div className="absolute inset-0 bg-gradient-to-t from-[#010c20] via-transparent to-transparent z-10"></div>
                   <div className="absolute top-5 left-5 z-20">
                      <span className={`px-4 py-1.5 rounded-sm text-[9px] font-black uppercase tracking-[0.3em] border shadow-2xl ${
                        ativo.porte_categoria === 'superyacht' ? 'bg-[#c5a059] border-[#c5a059] text-[#010c20]' : 
                        ativo.porte_categoria === 'executive' ? 'bg-white/90 border-white text-[#010c20]' : 
                        'bg-white/10 border-white/20 text-white'
                      }`}>
                        {t(`common.${ativo.porte_categoria}`)}
                      </span>
                   </div>
                   
                   {/* Abstract background icon */}
                   <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] group-hover:opacity-[0.08] group-hover:scale-125 transition-all duration-1000">
                      <Ship size={200} strokeWidth={0.5} />
                   </div>

                   <div className="absolute bottom-6 left-8 z-20">
                      <h3 className="text-2xl font-serif font-bold text-white tracking-tight group-hover:text-[#c5a059] transition-all">
                        {ativo.nome_reg || `${ativo.marca} ${ativo.modelo}`}
                      </h3>
                      <p className="text-[10px] text-white/30 uppercase tracking-[0.4em] font-black mt-2">
                        {ativo.ano_fabricacao} <span className="mx-2 text-[#c5a059]">•</span> {ativo.tipo}
                      </p>
                   </div>
                </div>
                
                {/* Details */}
                <div className="p-8 pt-4">
                  <div className="mb-8">
                    <div className="flex justify-between items-end mb-3">
                      <span className="text-[10px] uppercase tracking-[0.3em] font-black text-white/30">{t('common.progress')}</span>
                      <span className="text-lg font-serif font-bold text-[#c5a059]">{ativo.progresso}%</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden shadow-inner">
                      <div 
                        className="h-full bg-gradient-to-r from-[#c5a059] to-[#E5D5B7] rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(197,160,89,0.3)]"
                        style={{ width: `${ativo.progresso}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                     <div className="flex gap-2">
                        {[1, 2, 3].map(level => (
                          <div 
                            key={level}
                            className={`w-12 h-1 rounded-sm transition-all duration-700 ${
                              ativo.progresso >= (level * 33.3) ? 'bg-[#c5a059]' : 'bg-white/5'
                            }`}
                          />
                        ))}
                     </div>
                     <button className="text-[10px] uppercase tracking-[0.3em] font-black text-white/30 hover:text-[#c5a059] transition-all">
                        {t('common.explore')} →
                     </button>
                  </div>
                </div>

                <div className="px-8 py-5 bg-white/[0.01] border-t border-white/5 flex items-center justify-between text-[9px] uppercase tracking-[0.3em] font-black text-white/20 group-hover:bg-[#c5a059]/5 transition-all">
                   <div className="flex items-center gap-3">
                      {ativo.progresso === 100 ? (
                        <CheckCircle size={16} className="text-[#c5a059]" />
                      ) : (
                        <AlertCircle size={16} className="text-[#c5a059]/40" />
                      )}
                      <span className={ativo.progresso === 100 ? 'text-[#c5a059]' : ''}>
                        {ativo.progresso === 100 ? t('common.cert_complete') : t('common.complete_docs')}
                      </span>
                   </div>
                   <span className="opacity-50">ID: #{ativo.id.slice(0, 4)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
