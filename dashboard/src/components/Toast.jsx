/* ============================================================
   Toast — Sistema de notificações premium
   Uso: const { addToast } = useToast()
        addToast('Clínica salva com sucesso!', 'success')
   ============================================================ */

import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import './Toast.css'

const ToastContext = createContext(null)

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const DURATION = 4000

function ToastItem({ toast, onRemove }) {
  const [exiting, setExiting] = useState(false)
  const timerRef = useRef(null)

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      setExiting(true)
      setTimeout(() => onRemove(toast.id), 300)
    }, DURATION)

    return () => clearTimeout(timerRef.current)
  }, [toast.id, onRemove])

  function handleClose() {
    clearTimeout(timerRef.current)
    setExiting(true)
    setTimeout(() => onRemove(toast.id), 300)
  }

  const Icon = ICONS[toast.type] || Info

  return (
    <div className={`k-toast k-toast-${toast.type} ${exiting ? 'k-toast-exit' : ''}`}>
      <Icon size={18} className="k-toast-icon" />
      <span className="k-toast-message">{toast.message}</span>
      <button className="k-toast-close" onClick={handleClose}>
        <X size={14} />
      </button>
      <div className="k-toast-progress" style={{ animationDuration: `${DURATION}ms` }} />
    </div>
  )
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random()
    setToasts(prev => [...prev, { id, message, type }])
  }, [])

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="k-toast-container">
        {toasts.map(toast => (
          <ToastItem key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
