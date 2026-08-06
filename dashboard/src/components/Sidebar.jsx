import { NavLink, useLocation } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Zap, Stethoscope } from 'lucide-react'
import './Sidebar.css'
const NAV_ITEMS = [
  { label: 'Módulo Clínico', icon: Stethoscope, path: '/clinico', description: 'Consultas & Documentos' },
]
export default function Sidebar({ collapsed, onToggle }) {
  const location = useLocation()
  return (
    <aside className={`k-sidebar ${collapsed ? 'k-sidebar--collapsed' : ''}`}>
      <div className="k-sidebar-logo"><div className="k-sidebar-logo-icon"><Zap size={22} /></div>{!collapsed && (<div className="k-sidebar-logo-text"><span className="k-sidebar-brand">Kairós</span><span className="k-sidebar-version">Intelligence</span></div>)}</div>
      <nav className="k-sidebar-nav">{NAV_ITEMS.map((item) => { const Icon = item.icon; const isActive = location.pathname.startsWith(item.path); return (<NavLink key={item.path} to={item.path} className={`k-sidebar-item ${isActive ? 'k-sidebar-item--active' : ''}`} title={collapsed ? item.label : undefined}><div className="k-sidebar-item-icon"><Icon size={20} /></div>{!collapsed && (<div className="k-sidebar-item-text"><span className="k-sidebar-item-label">{item.label}</span><span className="k-sidebar-item-desc">{item.description}</span></div>)}{isActive && <div className="k-sidebar-item-indicator" />}</NavLink>)})}</nav>
      <button className="k-sidebar-toggle" onClick={onToggle}>{collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}{!collapsed && <span>Recolher</span>}</button>
    </aside>
  )
}
