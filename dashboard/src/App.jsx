/* ============================================================
   App.jsx — Componente raiz do Dashboard Kairós
   Routing + Layout (Sidebar + Topbar + Content)
   ============================================================ */

import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'

import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'

import ClinicasPage from './pages/clinicas/ClinicasPage'
import ClinicaForm from './pages/clinicas/ClinicaForm'
import LaboratorioPage from './pages/laboratorio/LaboratorioPage'
import AnalyticsPage from './pages/analytics/AnalyticsPage'
import ConfiguracoesPage from './pages/configuracoes/ConfiguracoesPage'

import './App.css'

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className={`k-app ${sidebarCollapsed ? 'k-app--collapsed' : ''}`}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div className="k-main-wrapper">
        <Topbar />

        <main className="k-main">
          <Routes>
            {/* Redireciona raiz para clínicas */}
            <Route path="/" element={<Navigate to="/clinicas" replace />} />

            {/* Gestão de Clínicas */}
            <Route path="/clinicas" element={<ClinicasPage />} />
            <Route path="/clinicas/nova" element={<ClinicaForm />} />
            <Route path="/clinicas/:id" element={<ClinicaForm />} />
            <Route path="/clinicas/:id/editar" element={<ClinicaForm />} />

            {/* Laboratório Kairós (Prometheus) */}
            <Route path="/laboratorio" element={<LaboratorioPage />} />

            {/* Analytics */}
            <Route path="/analytics" element={<AnalyticsPage />} />

            {/* Command Center */}
            <Route path="/configuracoes" element={<ConfiguracoesPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
