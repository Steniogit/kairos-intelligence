/* ============================================================
   ConfirmModal — Modal de confirmação reutilizável
   Uso: <ConfirmModal
          open={show}
          title="Desativar clínica?"
          message="Esta ação pode ser revertida."
          confirmLabel="Desativar"
          variant="danger"
          onConfirm={handleConfirm}
          onCancel={() => setShow(false)}
        />
   ============================================================ */

import { useEffect, useRef } from 'react'
import { AlertTriangle, Trash2, X } from 'lucide-react'
import './ConfirmModal.css'

const VARIANT_CONFIG = {
  danger: {
    icon: Trash2,
    btnClass: 'k-btn-danger',
    iconBg: 'var(--k-danger-bg)',
    iconColor: 'var(--k-danger)',
  },
  warning: {
    icon: AlertTriangle,
    btnClass: 'k-btn-warning',
    iconBg: 'var(--k-warning-bg)',
    iconColor: 'var(--k-warning)',
  },
}

export default function ConfirmModal({
  open,
  title = 'Confirmar ação',
  message = 'Tem certeza que deseja continuar?',
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  variant = 'danger',
  loading = false,
  onConfirm,
  onCancel,
}) {
  const overlayRef = useRef(null)

  useEffect(() => {
    if (!open) return
    function handleEsc(e) {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [open, onCancel])

  if (!open) return null

  const config = VARIANT_CONFIG[variant] || VARIANT_CONFIG.danger
  const Icon = config.icon

  function handleOverlayClick(e) {
    if (e.target === overlayRef.current) onCancel()
  }

  return (
    <div className="k-modal-overlay" ref={overlayRef} onClick={handleOverlayClick}>
      <div className="k-modal confirm-modal" role="alertdialog">
        <div className="k-modal-header">
          <div className="confirm-modal-title">
            <div
              className="confirm-modal-icon"
              style={{ background: config.iconBg, color: config.iconColor }}
            >
              <Icon size={20} />
            </div>
            <h3>{title}</h3>
          </div>
          <button className="k-btn k-btn-ghost k-btn-icon" onClick={onCancel}>
            <X size={18} />
          </button>
        </div>
        <div className="k-modal-body">
          <p className="confirm-modal-message">{message}</p>
        </div>
        <div className="k-modal-footer">
          <button className="k-btn k-btn-secondary" onClick={onCancel} disabled={loading}>
            {cancelLabel}
          </button>
          <button
            className={`k-btn ${config.btnClass}`}
            onClick={onConfirm}
            disabled={loading}
            id="btn-confirm-action"
          >
            {loading ? 'Processando...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
