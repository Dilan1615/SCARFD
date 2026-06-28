import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/axios'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import { Camera, CheckCircle2, X, Loader2, AlertCircle, ScanFace } from 'lucide-react'

export default function RegistroRostro() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { addToast } = useToast()
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [captured, setCaptured] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [yaTieneRostro, setYaTieneRostro] = useState(false)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    api.get('/asistencia/registro-facial/')
      .then(({ data }) => {
        if (data.length > 0) {
          setYaTieneRostro(true)
        }
      })
      .catch(() => {})
      .finally(() => setChecking(false))
  }, [])

  useEffect(() => {
    if (success || yaTieneRostro || checking) return
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
      .then(s => {
        setStream(s)
        if (videoRef.current) videoRef.current.srcObject = s
      })
      .catch(() => setError('No se pudo acceder a la cámara'))
    return () => {
      if (stream) stream.getTracks().forEach(t => t.stop())
    }
  }, [success])

  const capture = () => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d').drawImage(video, 0, 0)
    setCaptured(canvas.toDataURL('image/jpeg', 0.8))
    stream?.getTracks().forEach(t => t.stop())
    setStream(null)
  }

  const retake = () => {
    setCaptured(null)
    setError('')
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
      .then(s => {
        setStream(s)
        if (videoRef.current) videoRef.current.srcObject = s
      })
      .catch(() => setError('No se pudo acceder a la cámara'))
  }

  const handleSubmit = async () => {
    if (!captured) return
    setSubmitting(true)
    setError('')
    try {
      const base64Data = captured.includes(',') ? captured.split(',')[1] : captured
      await api.post('/asistencia/registro-facial/registrar_rostro/', {
        imagen_base64: base64Data,
      })
      setSuccess(true)
      addToast('Rostro registrado exitosamente')
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || 'Error al registrar el rostro')
    } finally {
      setSubmitting(false)
    }
  }

  if (checking) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-unl-red border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (yaTieneRostro) {
    return (
      <div className="max-w-lg mx-auto">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
          <ScanFace size={48} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-xl font-bold text-unl-black mb-2">Rostro ya registrado</h2>
          <p className="text-gray-500 mb-6">Ya tienes un rostro registrado. Puedes actualizarlo si lo deseas, pero el registro excesivo puede resultar en la desactivación de tu cuenta.</p>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            <button
              onClick={() => setYaTieneRostro(false)}
              className="bg-unl-red hover:bg-unl-red-dark text-white px-6 py-2.5 rounded-xl font-medium transition-all shadow-sm hover:shadow-md"
            >
              Actualizar Rostro
            </button>
            <button
              onClick={() => navigate('/asistencia/hoy')}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-2.5 rounded-xl font-medium transition-all"
            >
              Ir a mi asistencia
            </button>
          </div>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3 mt-4">
          <AlertCircle size={18} className="text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-800">
            <strong className="block mb-1">Importante:</strong>
            Registrar el rostro repetidamente está penado. Si se detectan múltiples registros innecesarios, tu cuenta será desactivada automáticamente.
          </div>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-10 text-center max-w-md">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 size={32} className="text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-unl-black mb-2">Rostro Registrado</h2>
          <p className="text-gray-500 mb-6">Tu rostro ha sido registrado exitosamente. Ya puedes marcar tu asistencia con reconocimiento facial.</p>
          <button
            onClick={() => navigate('/asistencia/hoy')}
            className="bg-unl-red hover:bg-unl-red-dark text-white px-6 py-2.5 rounded-xl font-medium transition-all shadow-sm hover:shadow-md"
          >
            Ir a mi asistencia
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto space-y-5">
      <div className="flex items-center gap-4">
        <div className="w-10 h-10 rounded-2xl bg-unl-red/10 flex items-center justify-center">
          <ScanFace size={20} className="text-unl-red" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-unl-black">Registrar mi Rostro</h2>
          <p className="text-sm text-gray-500">Esto se hace una sola vez para habilitar la asistencia facial</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-5 space-y-4">
          <div className="bg-gray-50 rounded-xl overflow-hidden">
            <div className="aspect-[4/3] relative bg-black">
              {!captured ? (
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
              ) : (
                <img src={captured} alt="Captura" className="w-full h-full object-cover" />
              )}
              <canvas ref={canvasRef} className="hidden" />
              {error && (
                <div className="absolute bottom-0 left-0 right-0 bg-red-500/90 text-white text-xs p-2 text-center">
                  {error}
                </div>
              )}
            </div>
          </div>

          <div className="text-center text-xs text-gray-400">
            Coloca tu rostro frente a la cámara con buena iluminación
          </div>

          <div className="flex justify-center gap-3">
            {!captured ? (
              <button onClick={capture} className="flex items-center gap-2 bg-unl-red hover:bg-unl-red-dark text-white px-6 py-2.5 rounded-xl font-medium transition-all shadow-sm hover:shadow-md">
                <Camera size={18} /> Tomar Foto
              </button>
            ) : (
              <>
                <button onClick={retake} className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2.5 rounded-xl font-medium transition-all">
                  <Camera size={18} /> Repetir
                </button>
                <button onClick={handleSubmit} disabled={submitting} className="flex items-center gap-2 bg-unl-green hover:bg-green-700 text-white px-6 py-2.5 rounded-xl font-medium transition-all shadow-sm hover:shadow-md disabled:opacity-50">
                  {submitting ? <Loader2 size={18} className="animate-spin" /> : <CheckCircle2 size={18} />}
                  {submitting ? 'Registrando...' : 'Registrar Rostro'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
        <AlertCircle size={18} className="text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-800">
          <strong className="block mb-1">Recomendaciones:</strong>
          Busca un fondo claro y uniforme. Evita contraluces, sombras fuertes, gorras o mascarillas. Asegúrate de que tu rostro esté completamente visible.
        </div>
      </div>
    </div>
  )
}
