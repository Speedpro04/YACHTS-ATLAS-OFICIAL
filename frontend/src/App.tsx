import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Ativos from './pages/Ativos'
import Documentos from './pages/Documentos'
import Login from './pages/Login'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'

import LandingPage from './pages/LandingPage'
import Sobre from './pages/Sobre'
import Frota from './pages/Frota'
import Seguranca from './pages/Seguranca'
import RegistroMarina from './pages/RegistroMarina'
import MarinaParceira from './pages/MarinaParceira'
import SejaParceiro from './pages/SejaParceiro'
import SolicitarDossie from './pages/SolicitarDossie'
import SolicitacoesDossie from './pages/SolicitacoesDossie'
import PagamentoDossie from './pages/PagamentoDossie'
import LoginProprietario from './pages/LoginProprietario'
import RedefinirSenha from './pages/RedefinirSenha'
import PortalProprietario from './pages/PortalProprietario'
import SuccessDossie from './pages/SuccessDossie'
import SuccessOnboarding from './pages/SuccessOnboarding'
import Registros from './pages/Registros'
import NormasTecnicas from './pages/NormasTecnicas'
import SeoMeta from './components/SeoMeta'
import TermosFundadores from './pages/TermosFundadores'
import VerificacaoManual from './pages/VerificacaoManual'
import ConferirDocumento from './pages/ConferirDocumento'
import Privacidade from './pages/Privacidade'
import Verificacao from './pages/Verificacao'

function App() {
  return (
    <BrowserRouter>
      <SeoMeta />
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
    </BrowserRouter>
  )
}

export default App
