/* MODO SOMENTE MODULO CLINICO - solicitado 2026-08-06 - reverter: bash /root/backup-kairos-2026-08-06/reverter-completo.sh */
import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import { ClinicalAuthProvider } from './components/ClinicalAuthGate'
import ClinicoDashboard from './pages/clinico/ClinicoDashboard'
import QuarentenaPage from './pages/clinico/QuarentenaPage'
import ConsultaPage from './pages/clinico/ConsultaPage'
import DocumentosPage from './pages/clinico/DocumentosPage'
import HistoricoPage from './pages/clinico/HistoricoPage'
import GrafoPage from './pages/clinico/GrafoPage'
import './App.css'
export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  return (
    <div className={`k-app ${sidebarCollapsed ? 'k-app--collapsed' : ''}`}>
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <div className="k-main-wrapper">
        <Topbar />
        <main className="k-main">
          <Routes>
            <Route path="/" element={<Navigate to="/clinico" replace />} />
            <Route path="/clinico" element={<ClinicalAuthProvider><ClinicoDashboard /></ClinicalAuthProvider>} />
            <Route path="/clinico/consulta" element={<ClinicalAuthProvider><ConsultaPage /></ClinicalAuthProvider>} />
            <Route path="/clinico/quarentena" element={<ClinicalAuthProvider><QuarentenaPage /></ClinicalAuthProvider>} />
            <Route path="/clinico/documentos" element={<ClinicalAuthProvider><DocumentosPage /></ClinicalAuthProvider>} />
            <Route path="/clinico/historico" element={<ClinicalAuthProvider><HistoricoPage /></ClinicalAuthProvider>} />
            <Route path="/clinico/grafo" element={<ClinicalAuthProvider><GrafoPage /></ClinicalAuthProvider>} />
            <Route path="*" element={<Navigate to="/clinico" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
