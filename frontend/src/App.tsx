import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Ativos from './pages/Ativos'
import Documentos from './pages/Documentos'
import Login from './pages/Login'
import Layout from './components/Layout'

import LandingPage from './pages/LandingPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/app" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="ativos" element={<Ativos />} />
          <Route path="documentos" element={<Documentos />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App