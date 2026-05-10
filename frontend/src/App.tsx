import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Ativos from './pages/Ativos'
import Documentos from './pages/Documentos'
import Login from './pages/Login'
import Layout from './components/Layout'

import LandingPage from './pages/LandingPage'
import Frota from './pages/Frota'
import Seguranca from './pages/Seguranca'
import RegistroMarina from './pages/RegistroMarina'
import MarinaParceira from './pages/MarinaParceira'
import PagamentoDossie from './pages/PagamentoDossie'
import Parceiros from './pages/Parceiros'
import LoginProprietario from './pages/LoginProprietario'
import PortalProprietario from './pages/PortalProprietario'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/frota" element={<Frota />} />
        <Route path="/seguranca" element={<Seguranca />} />
        <Route path="/login" element={<Login />} />
        <Route path="/acesso-proprietario" element={<LoginProprietario />} />
        <Route path="/portal-proprietario" element={<PortalProprietario />} />
        <Route path="/registro-marina" element={<RegistroMarina />} />
        <Route path="/marina-parceira" element={<MarinaParceira />} />
        <Route path="/app" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="ativos" element={<Ativos />} />
          <Route path="documentos" element={<Documentos />} />
          <Route path="parceiros" element={<Parceiros />} />
          <Route path="pagamento-dossie" element={<PagamentoDossie />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App