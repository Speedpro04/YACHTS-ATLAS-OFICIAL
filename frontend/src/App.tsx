import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Suspense, lazy } from 'react'
import SeoMeta from './components/SeoMeta'

// ============================================================================
// CARREGAMENTO POR ROTA
// ============================================================================
// Até 31/08/2026 as 29 rotas eram importadas de forma estática, e o build saía
// como UM arquivo de 853 KB. Quem abria a home baixava o painel da marina, o
// `@supabase/supabase-js` e a biblioteca de ícones inteira antes de ver a
// primeira letra — e a landing não usa nenhum dos três.
//
// Quem visita a home é a marina AVALIANDO o produto. Ela paga o custo da
// aplicação inteira para ler uma página de venda, e foi o que o fundador
// sentiu como "a página está um pouco lenta".
//
// A LANDING FICA ESTÁTICA, DE PROPÓSITO
// -------------------------------------
// É a rota de entrada e a mais visitada. Deixá-la em `lazy` trocaria o
// problema de peso por um round-trip extra ANTES do primeiro pixel: o
// navegador baixaria o esqueleto, descobriria que precisa de outro arquivo e
// só então mostraria algo. Para a rota de entrada, isso é pior.
//
// Todo o resto carrega quando alguém realmente vai lá.
// ============================================================================
import LandingPage from './pages/LandingPage'

// ── Institucional: quem está avaliando o produto ────────────────────────────
const Sobre = lazy(() => import('./pages/Sobre'))
const Frota = lazy(() => import('./pages/Frota'))
const Seguranca = lazy(() => import('./pages/Seguranca'))
const RegistroMarina = lazy(() => import('./pages/RegistroMarina'))
const MarinaParceira = lazy(() => import('./pages/MarinaParceira'))
const SejaParceiro = lazy(() => import('./pages/SejaParceiro'))
const SolicitarDossie = lazy(() => import('./pages/SolicitarDossie'))
const TermosFundadores = lazy(() => import('./pages/TermosFundadores'))
const Privacidade = lazy(() => import('./pages/Privacidade'))
const SuccessOnboarding = lazy(() => import('./pages/SuccessOnboarding'))

// ── Verificação pública: destino do QR impresso no dossiê ───────────────────
// Quem chega aqui está com um documento na mão, muitas vezes no celular, em
// rede de marina. É o caminho que MAIS se beneficia de não arrastar o painel
// junto — e o que menos pode falhar.
const VerificacaoManual = lazy(() => import('./pages/VerificacaoManual'))
const ConferirDocumento = lazy(() => import('./pages/ConferirDocumento'))
const Verificacao = lazy(() => import('./pages/Verificacao'))

// ── Autenticação ────────────────────────────────────────────────────────────
const Login = lazy(() => import('./pages/Login'))
const LoginProprietario = lazy(() => import('./pages/LoginProprietario'))
const RedefinirSenha = lazy(() => import('./pages/RedefinirSenha'))
const PortalProprietario = lazy(() => import('./pages/PortalProprietario'))

// ── Painel da marina: só depois do login ────────────────────────────────────
// É a parte mais pesada do sistema, e a que menos gente vê: uma marina paga,
// autenticada, algumas vezes por dia. Não tem por que estar no caminho de
// quem só quer ler a página de venda ou conferir um QR.
const Layout = lazy(() => import('./components/Layout'))
const PrivateRoute = lazy(() => import('./components/PrivateRoute'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Ativos = lazy(() => import('./pages/Ativos'))
const Documentos = lazy(() => import('./pages/Documentos'))
const NormasTecnicas = lazy(() => import('./pages/NormasTecnicas'))
const SolicitacoesDossie = lazy(() => import('./pages/SolicitacoesDossie'))
const PagamentoDossie = lazy(() => import('./pages/PagamentoDossie'))
const SuccessDossie = lazy(() => import('./pages/SuccessDossie'))
const Registros = lazy(() => import('./pages/Registros'))

// Fallback do Suspense: fundo do produto e nada mais.
//
// Sem spinner de propósito. A troca de rota é rápida o bastante para o
// spinner só piscar, e pisca-pisca em transição rápida é percebido como
// travamento, não como carregamento. O fundo na cor da marca faz a espera
// parecer parte da página, não uma tela em branco.
function Carregando() {
  return <div className="min-h-screen bg-[#010c20]" aria-busy="true" />
}

function App() {
  return (
    <BrowserRouter>
      <SeoMeta />
      <Suspense fallback={<Carregando />}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/sobre" element={<Sobre />} />
          <Route path="/frota" element={<Frota />} />
          <Route path="/seguranca" element={<Seguranca />} />
          <Route path="/login" element={<Login />} />
          <Route path="/acesso-proprietario" element={<LoginProprietario />} />
          <Route path="/redefinir-senha" element={<RedefinirSenha />} />
          <Route path="/portal-proprietario" element={<PortalProprietario />} />
          <Route path="/registro-marina" element={<RegistroMarina />} />
          <Route path="/marina-parceira" element={<MarinaParceira />} />
          <Route path="/seja-parceiro" element={<SejaParceiro />} />
          <Route path="/solicitar-dossie" element={<SolicitarDossie />} />
          <Route path="/termos-fundadores" element={<TermosFundadores />} />
          <Route path="/privacidade" element={<Privacidade />} />
          {/* Pública, sem login: destino do QR impresso no dossiê. */}
          {/* Sem protocolo: entrada manual. O dossie impresso manda "acesse o
              endereco e informe protocolo, codigo e data" — ate agora esse
              endereco nao existia, e quem nao conseguisse ler o QR ficava sem
              saida. Precisa vir ANTES da rota com parametro. */}
          <Route path="/verificar" element={<VerificacaoManual />} />
          {/* Contra-prova: sobe o PDF e confere se ele foi alterado depois da
              emissao. O arquivo NAO sai do navegador — so o SHA-256 e enviado. */}
          <Route path="/conferir" element={<ConferirDocumento />} />
          <Route path="/verificar/:protocolo" element={<Verificacao />} />
          <Route path="/success" element={<SuccessOnboarding />} />
          <Route element={<PrivateRoute />}>
            <Route path="/app" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="ativos" element={<Ativos />} />
              <Route path="documentos" element={<Documentos />} />
              <Route path="normas" element={<NormasTecnicas />} />
              <Route path="solicitacoes-dossie" element={<SolicitacoesDossie />} />
              <Route path="pagamento-dossie" element={<PagamentoDossie />} />
              <Route path="dossie-sucesso" element={<SuccessDossie />} />
              <Route path="registros/:ativoId" element={<Registros />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
