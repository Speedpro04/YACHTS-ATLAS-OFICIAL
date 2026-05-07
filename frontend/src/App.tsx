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
import PagamentoDossie from './pages/PagamentoDossie'
import LoginArmador from './pages/LoginArmador'
import PortalArmador from './pages/PortalArmador'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/frota" element={<Frota />} />
        <Route path="/seguranca" element={<Seguranca />} />
        <Route path="/login" element={<Login />} />
        <Route path="/acesso-armador" element={<LoginArmador />} />
        <Route path="/portal-armador" element={<PortalArmador />} />
        <Route path="/registro-marina" element={<RegistroMarina />} />
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