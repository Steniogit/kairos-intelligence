/* ============================================================
   Sidebar — Navegação lateral do Dashboard Kairós
   ============================================================ */

import { NavLink, useLocation } from 'react-router-dom'
import {
  Building2,
  FlaskConical,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
} from 'lucide-react'
import './Sidebar.css'

const NAV_ITEMS = [
  {
    label: 'Clínicas',
    icon: Building2,
    path: '/clinicas',
    description: 'Gestão de Clínicas',
  },
  {
    label: 'Laboratório',
    icon: FlaskConical,
    path: '/laboratorio',
    description: 'Assistente Prometheus',
  },
  {
    label: 'Analytics',
    icon: BarChart3,
    path: '/analytics',
    description: 'Dados e Relatórios',
  },
  {
    label: 'Configurações',
    icon: Settings,
    path: '/configuracoes',
    description: 'Sistema',
  },
]

export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()

  return (
    <aside className={`k-sidebar ${collapsed ? 'k-sidebar--collapsed' : ''}`}>
      {/* Logo */}
      <div className="k-sidebar-logo">
        <div className="k-sidebar-logo-icon">
          <Zap size={22} />
        </div>
        {!collapsed && (
          <div className="k-sidebar-logo-text">
            <span className="k-sidebar-brand">Kairós</span>
            <span className="k-sidebar-version">Intelligence</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="k-sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname.startsWith(item.path)
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={`k-sidebar-item ${isActive ? 'k-sidebar-item--active' : ''}`}
              title={collapsed ? item.label : undefined}
            >
              <div className="k-sidebar-item-icon">
                <Icon size={20} />
              </div>
              {!collapsed && (
                <div className="k-sidebar-item-text">
                  <span className="k-sidebar-item-label">{item.label}</span>
                  <span className="k-sidebar-item-desc">{item.description}</span>
                </div>
              )}
              {isActive && <div className="k-sidebar-item-indicator" />}
            </NavLink>
          )
        })}
      </nav>

      {/* Collapse Toggle */}
      <button className="k-sidebar-toggle" onClick={onToggle}>
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        {!collapsed && <span>Recolher</span>}
      </button>
    </aside>
  )
}
