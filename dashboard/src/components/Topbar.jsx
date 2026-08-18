/* ============================================================
   Topbar — Barra superior com informações do sistema
   ============================================================ */

import { Bell, Search, User, Activity } from 'lucide-react'
import { useState, useEffect } from 'react'
import { healthCheck } from '../services/api'
import ProfileModal from './ProfileModal'

import { useToast } from './Toast'
import './Topbar.css'

export default function Topbar() {
  const [health, setHealth] = useState(null)
  const [searchOpen, setSearchOpen] = useState(false)
  const [notifOpen, setNotifOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  
  // Safe read from session storage for topbar
  let userName = "Dr."
  try {
    const s = sessionStorage.getItem('k-clinical-session')
    if (s) {
      const parsed = JSON.parse(s)
      if (parsed.name) userName = parsed.name
    }
  } catch(e) {}

  
  const { addToast } = useToast()

  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  return (
    <header className="k-topbar">
      <div className="k-topbar-left" id="topbar-portal-target" style={{ display: 'flex', alignItems: 'center' }}>
      </div>

      <div className="k-topbar-right">
        {/* Status do sistema */}
        <div className="k-topbar-status">
          <Activity size={14} className={health ? 'k-status-online' : 'k-status-offline'} />
          <span className="k-text-sm">
            {health ? 'Sistema Online' : 'Verificando...'}
          </span>
        </div>

        {/* Pesquisar */}
        <button
          className="k-btn k-btn-ghost k-btn-icon"
          onClick={() => addToast('Pesquisa global em desenvolvimento.', 'info')}
          title="Pesquisar"
          id="btn-search"
        >
          <Search size={18} />
        </button>

        {/* Notificações */}
        <button 
          className="k-btn k-btn-ghost k-btn-icon k-topbar-notif" 
          title="Notificações" 
          id="btn-notifications"
          onClick={() => addToast('Você não tem novas notificações.', 'info')}
        >
          <Bell size={18} />
          <span className="k-topbar-notif-dot" />
        </button>

        {/* Perfil */}
        <div className="k-topbar-profile" id="profile-menu" onClick={() => setProfileOpen(true)} style={{cursor: "pointer"}}>
          <div className="k-topbar-avatar">
            <User size={18} />
          </div>
          <div className="k-topbar-user">
            <span className="k-topbar-user-name">{userName}</span>
            <span className="k-topbar-user-role">Administrador</span>
          </div>
        </div>
      </div>
      {profileOpen && <ProfileModal onClose={() => setProfileOpen(false)} />}
    </header>
  )
}

