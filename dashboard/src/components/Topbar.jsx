/* ============================================================
   Topbar — Barra superior com informações do sistema
   ============================================================ */

import { Bell, Search, User, Activity } from 'lucide-react'
import { useState, useEffect } from 'react'
import { healthCheck } from '../services/api'
import './Topbar.css'

export default function Topbar() {
  const [health, setHealth] = useState(null)
  const [searchOpen, setSearchOpen] = useState(false)

  useEffect(() => {
    healthCheck()
      .then(setHealth)
      .catch(() => setHealth(null))
  }, [])

  return (
    <header className="k-topbar">
      <div className="k-topbar-left">
        <h1 className="k-topbar-title">Painel de Comando</h1>
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
          onClick={() => setSearchOpen(!searchOpen)}
          title="Pesquisar"
          id="btn-search"
        >
          <Search size={18} />
        </button>

        {/* Notificações */}
        <button className="k-btn k-btn-ghost k-btn-icon k-topbar-notif" title="Notificações" id="btn-notifications">
          <Bell size={18} />
          <span className="k-topbar-notif-dot" />
        </button>

        {/* Perfil */}
        <div className="k-topbar-profile" id="profile-menu">
          <div className="k-topbar-avatar">
            <User size={18} />
          </div>
          <div className="k-topbar-user">
            <span className="k-topbar-user-name">CEO Kairós</span>
            <span className="k-topbar-user-role">Administrador</span>
          </div>
        </div>
      </div>
    </header>
  )
}
