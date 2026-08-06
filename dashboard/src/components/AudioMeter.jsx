/* ============================================================
   AudioMeter — Medidor de nível de áudio em tempo real
   Usa Web Audio API (getUserMedia + AnalyserNode) para capturar
   e exibir o nível do microfone como barra horizontal animada.

   Uso:
     <AudioMeter active={isRecording} onLevelChange={setLevel} />
   ============================================================ */

import { useEffect, useRef, useState, useCallback } from 'react'
import { Mic, MicOff } from 'lucide-react'
import './AudioMeter.css'

/**
 * Converte um valor RMS normalizado (0–1) para decibéis (dBFS).
 * @param {number} rms - Valor RMS entre 0.0 e 1.0
 * @returns {number} Valor em dBFS (clamped entre -60 e 0)
 */
function rmsToDb(rms) {
  if (rms <= 0) return -60
  const db = 20 * Math.log10(rms)
  return Math.max(-60, Math.min(0, db))
}

/**
 * Retorna a classe de cor baseada no nível.
 * @param {number} level - Nível normalizado (0.0–1.0)
 * @returns {'normal' | 'moderate' | 'loud'}
 */
function getLevelCategory(level) {
  if (level > 0.75) return 'loud'
  if (level > 0.45) return 'moderate'
  return 'normal'
}

/** Dimensões internas por tamanho */
const SIZE_ICON = { sm: 14, md: 16, lg: 20 }

/**
 * @param {Object} props
 * @param {boolean} props.active - Se deve capturar áudio do microfone
 * @param {(level: number) => void} [props.onLevelChange] - Callback com nível atual (0.0–1.0)
 * @param {boolean} [props.showLabel=true] - Exibir rótulo "Nível de áudio"
 * @param {'sm'|'md'|'lg'} [props.size='md'] - Tamanho do medidor
 */
export default function AudioMeter({
  active = false,
  onLevelChange,
  showLabel = true,
  size = 'md',
}) {
  const [level, setLevel] = useState(0)
  const [db, setDb] = useState(-60)

  // Refs para recursos de áudio (não causam re-render)
  const audioCtxRef = useRef(null)
  const analyserRef = useRef(null)
  const streamRef = useRef(null)
  const rafRef = useRef(null)
  const onLevelChangeRef = useRef(onLevelChange)

  // Manter ref do callback atualizada sem re-iniciar o efeito
  useEffect(() => {
    onLevelChangeRef.current = onLevelChange
  }, [onLevelChange])

  /**
   * Loop de análise: lê os dados de frequência do AnalyserNode,
   * calcula RMS e atualiza o estado.
   */
  const tick = useCallback(() => {
    const analyser = analyserRef.current
    if (!analyser) return

    const data = new Uint8Array(analyser.fftSize)
    analyser.getByteTimeDomainData(data)

    // Calcular RMS (Root Mean Square)
    let sumSquares = 0
    for (let i = 0; i < data.length; i++) {
      const normalized = (data[i] - 128) / 128
      sumSquares += normalized * normalized
    }
    const rms = Math.sqrt(sumSquares / data.length)

    // Clampar entre 0 e 1
    const clampedLevel = Math.min(1, rms * 1.8) // leve boost para visualização
    const currentDb = rmsToDb(rms)

    setLevel(clampedLevel)
    setDb(currentDb)

    if (onLevelChangeRef.current) {
      onLevelChangeRef.current(clampedLevel)
    }

    rafRef.current = requestAnimationFrame(tick)
  }, [])

  /**
   * Efeito principal: inicializa/encerra captura de áudio
   * conforme a prop `active`.
   */
  useEffect(() => {
    if (!active) {
      // Limpar tudo quando desativado
      cleanup()
      setLevel(0)
      setDb(-60)
      return
    }

    let cancelled = false

    async function startCapture() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream

        const ctx = new (window.AudioContext || window.webkitAudioContext)()
        audioCtxRef.current = ctx

        const source = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        analyser.smoothingTimeConstant = 0.5
        source.connect(analyser)
        analyserRef.current = analyser

        // Iniciar loop de leitura
        rafRef.current = requestAnimationFrame(tick)
      } catch (err) {
        console.error('[AudioMeter] Erro ao acessar microfone:', err)
      }
    }

    startCapture()

    return () => {
      cancelled = true
      cleanup()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active])

  /** Libera todos os recursos de áudio */
  function cleanup() {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    analyserRef.current = null
  }

  const category = getLevelCategory(level)
  const dbDisplay = db <= -59 ? '-∞' : `${Math.round(db)}`
  const isClipping = level > 0.95
  const widthPercent = Math.round(level * 100)
  const IconComponent = active ? Mic : MicOff

  return (
    <div
      className={`audio-meter audio-meter--${size} ${!active ? 'audio-meter--inactive' : ''}`}
      role="meter"
      aria-valuenow={Math.round(level * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="Nível de áudio"
    >
      {showLabel && (
        <div className="audio-meter__label">
          <IconComponent size={SIZE_ICON[size]} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 4 }} />
          Nível de áudio
        </div>
      )}

      <div className="audio-meter__bar-wrapper">
        <div className="audio-meter__track">
          <div
            className={`audio-meter__fill audio-meter__fill--${category}`}
            style={{ width: active ? `${widthPercent}%` : '0%' }}
          />
        </div>
        <span className={`audio-meter__db ${isClipping ? 'audio-meter__db--clip' : ''}`}>
          {dbDisplay} dB
        </span>
      </div>
    </div>
  )
}
