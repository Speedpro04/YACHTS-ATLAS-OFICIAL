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
import PagamentoDossie from './pages/PagamentoDossie'
import Parceiros from './pages/Parceiros'
import LoginProprietario from './pages/LoginProprietario'
import PortalProprietario from './pages/PortalProprietario'
import SuccessDossie from './pages/SuccessDossie'
import SuccessOnboarding from './pages/SuccessOnboarding'
import Registros from './pages/Registros'
import SeoMeta from './components/SeoMeta'
import TermosFundadores from './pages/TermosFundadores'

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
        <Route path="/portal-proprietario" element={<PortalProprietario />} />
        <Route path="/registro-marina" element={<RegistroMarina />} />
        <Route path="/marina-parceira" element={<MarinaParceira />} />
        <Route path="/termos-fundadores" element={<TermosFundadores />} />
        <Route path="/success" element={<SuccessOnboarding />} />
        <Route element={<PrivateRoute />}>
          <Route path="/app" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="ativos" element={<Ativos />} />
            <Route path="documentos" element={<Documentos />} />
            <Route path="parceiros" element={<Parceiros />} />
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
