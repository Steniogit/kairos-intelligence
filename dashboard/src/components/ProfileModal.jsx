/* ============================================================
   ProfileModal.jsx — Meu Perfil (Avatar Upload)
   Modal flutuante para visualizar e alterar dados e foto do médico.
   ============================================================ */

import { useState, useRef } from 'react'
import { X, Upload, Camera, Loader2, User, Building, Phone } from 'lucide-react'
import { uploadAvatar } from '../services/api'
import './ProfileModal.css'

export default function ProfileModal({ doctor, onClose, onUpdateAvatar }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setLoading(true)
    setError(null)
    try {
      // Faz o upload no paperclip
      const data = await uploadAvatar(doctor.crm, file)
      // Chama callback do Topbar para atualizar a interface imediatamente
      onUpdateAvatar(data.avatar_url)
    } catch (err) {
      setError('Erro ao enviar imagem. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }

  // Fallback de Iniciais
  const getInitials = (name) => {
    if (!name) return '?'
    const parts = name.replace(/^(Dr\.?|Dra\.?)\s*/i, '').trim().split(/\s+/)
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    return parts[0]?.[0]?.toUpperCase() || '?'
  }

  const avatarSrc = doctor?.avatarUrl || doctor?.avatar_url
  const hasAvatar = !!avatarSrc

  return (
    <div className="profile-modal-overlay">
      <div className="profile-modal-content">
        <button className="profile-modal-close" onClick={onClose}>
          <X size={20} />
        </button>

        <h2 className="profile-modal-title">Meu Perfil</h2>

        <div className="profile-modal-body">
          {/* Sessão Avatar */}
          <div className="profile-avatar-section">
            <div className="profile-avatar-wrapper">
              {hasAvatar ? (
                <img src={avatarSrc} alt="Avatar" className="profile-avatar-image" />
              ) : (
                <div className="profile-avatar-fallback">
                  {getInitials(doctor?.name)}
                </div>
              )}
              
              <button 
                className="profile-avatar-edit-btn" 
                onClick={() => fileInputRef.current?.click()}
                disabled={loading}
              >
                {loading ? <Loader2 size={16} className="k-animate-spin" /> : <Camera size={16} />}
              </button>
            </div>
            
            <input 
              type="file" 
              accept="image/*" 
              ref={fileInputRef} 
              style={{ display: 'none' }} 
              onChange={handleFileChange}
            />
            
            {error && <p className="profile-error">{error}</p>}
            <p className="profile-avatar-hint">Clique no ícone da câmera para alterar sua foto.</p>
          </div>

          {/* Informações do Médico */}
          <div className="profile-info-section">
            <div className="profile-info-item">
              <User size={16} className="profile-info-icon" />
              <div>
                <span className="profile-info-label">Nome Completo</span>
                <span className="profile-info-value">{doctor?.name}</span>
              </div>
            </div>
            
            <div className="profile-info-item">
              <Phone size={16} className="profile-info-icon" />
              <div>
                <span className="profile-info-label">CRM</span>
                <span className="profile-info-value">{doctor?.crm}</span>
              </div>
            </div>

            <div className="profile-info-item">
              <Building size={16} className="profile-info-icon" />
              <div>
                <span className="profile-info-label">Clínica Vinculada</span>
                <span className="profile-info-value">{doctor?.tenantName || doctor?.tenant_slug}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="profile-modal-footer">
          <button className="k-btn k-btn-primary" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  )
}
