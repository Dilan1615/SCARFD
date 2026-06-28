import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../api/axios'
import { useAuth } from '../../contexts/AuthContext'
import { useToast } from '../../contexts/ToastContext'
import MaintenanceBanner from '../../components/MaintenanceBanner'
import { Camera, CheckCircle2, Clock, MapPin, X, AlertCircle, Loader2 } from 'lucide-react'

const estadoColors = {
  PRESENTE: 'bg-green-100 text-green-700 border-green-200',
  AUSENTE: 'bg-red-100 text-red-700 border-red-200',
  TARDE: 'bg-amber-100 text-amber-700 border-amber-200',
  JUSTIFICADO: 'bg-blue-100 text-blue-700 border-blue-200',
}

const estadoIcons = {
  PRESENTE: CheckCircle2,
  AUSENTE: X,
  TARDE: AlertCircle,
  JUSTIFICADO: CheckCircle2,
}

function CameraModal({ open, onClose, horario, materiaNombre, onSubmit }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const [stream, setStream] = useState(null)
  const [captured, setCaptured] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) {
      if (stream) {
        stream.getTracks().forEach(t => t.stop())
        setStream(null)
      }
      setCaptured(null)
      setError('')
      return
    }
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 640, height: 480 } })
      .then(s => {
        setStream(s)
        if (videoRef.current) videoRef.current.srcObject = s
      })
      .catch(() => setError('No se pudo acceder a la cámara'))
  }, [open])

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
      await onSubmit(captured, horario)
      onClose()
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || 'Error al registrar asistencia')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-scale-in">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <h3 className="text-lg font-bold text-unl-black">Registrar Asistencia</h3>
            <p className="text-sm text-gray-500">{materiaNombre}</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-unl-red rounded-xl transition-colors">
            <X size={18} />
          </button>
        </div>

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
                  {submitting ? 'Registrando...' : 'Confirmar Asistencia'}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AsistenciaHoy() {
  const { user } = useAuth()
  const { addToast } = useToast()
  const navigate = useNavigate()
  const [matriculas, setMatriculas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [camera, setCamera] = useState(null)
  const [academicoDown, setAcademicoDown] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    setAcademicoDown(false)
    api.get('/academico/matriculas/mis_materias/')
      .then(({ data }) => {
        if (data.tiene_registro_facial === false) {
          navigate('/registro-rostro')
          return
        }
        setMatriculas(Array.isArray(data.matriculas) ? data.matriculas : [])
      })
      .catch(err => {
        if (!err.response || err.response.status >= 500) {
          setAcademicoDown(true)
        } else if (err.response?.status === 404) {
          setError('No tienes una matrícula activa')
        } else {
          setError('Error al cargar tus materias')
        }
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const handleRegistrar = async (imagenBase64, horario) => {
    const base64Data = imagenBase64.includes(',') ? imagenBase64.split(',')[1] : imagenBase64
    await api.post('/asistencia/asistencias/registrar/', {
      estudiante_id: user.id,
      horario_id: horario.id,
      imagen_base64: base64Data,
    })
    addToast(`Asistencia registrada: ${horario.hora_inicio.substring(0, 5)} - ${horario.materia_nombre || ''}`)
    load()
  }

  const getCurrentTimeStatus = (horario) => {
    const now = new Date()
    const [h, m] = horario.hora_inicio.split(':')
    const start = new Date()
    start.setHours(Number(h), Number(m), 0)
    const diff = (now - start) / 60000
    if (diff < 0) return { label: 'No iniciada', color: 'text-gray-400' }
    if (diff <= horario.minutos_tolerancia) return { label: 'A tiempo', color: 'text-green-600' }
    if (diff <= horario.minutos_tolerancia * 2) return { label: 'Tarde', color: 'text-amber-600' }
    return { label: 'Cerrado', color: 'text-red-600' }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-unl-red border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (academicoDown) {
    return <MaintenanceBanner service="academico" />
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <AlertCircle size={40} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500 font-medium">{error}</p>
      </div>
    )
  }

  if (matriculas.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <Clock size={40} className="mx-auto text-gray-300 mb-3" />
        <p className="text-gray-500 font-medium">No tienes clases programadas para hoy</p>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {matriculas.map((mat) => (
        <div key={mat.matricula_id}>
          <div className="mb-3">
            <h3 className="text-lg font-bold text-unl-black">{mat.carrera}</h3>
            <p className="text-sm text-gray-500">{mat.ciclo}</p>
          </div>

          {mat.materias.length === 0 ? (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 text-center">
              <Clock size={32} className="mx-auto text-gray-300 mb-2" />
              <p className="text-gray-500 font-medium">No hay clases programadas para hoy</p>
              <p className="text-xs text-gray-400 mt-1">Hoy es {new Date().toLocaleDateString('es-EC', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
            </div>
          ) : (
            <div className="space-y-3">
            {mat.materias.map((materia) => (
              <div key={materia.id} className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="px-5 py-3.5 bg-gray-50 border-b border-gray-100">
                  <h4 className="font-bold text-unl-black">{materia.nombre}</h4>
                  <p className="text-xs text-gray-500">{materia.codigo} {materia.docente_nombre ? `— ${materia.docente_nombre}` : ''}</p>
                </div>
                <div className="divide-y divide-gray-50">
                  {materia.horarios_hoy.map((horario) => {
                    const timeStatus = getCurrentTimeStatus(horario)
                    const EstIcon = horario.estado_asistencia ? estadoIcons[horario.estado_asistencia] || CheckCircle2 : null
                    return (
                      <div key={horario.id} className="px-5 py-3.5 flex items-center justify-between gap-4">
                        <div className="flex items-center gap-4 min-w-0 flex-1">
                          <div className="w-10 h-10 rounded-xl bg-unl-red/5 flex items-center justify-center shrink-0">
                            <Clock size={18} className="text-unl-red" />
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-sm text-unl-black">
                                {horario.hora_inicio.substring(0, 5)} — {horario.hora_fin.substring(0, 5)}
                              </span>
                              <span className={`text-xs font-medium ${timeStatus.color}`}>
                                {timeStatus.label}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
                              {horario.aula && <span className="flex items-center gap-1"><MapPin size={12} /> {horario.aula}</span>}
                              <span>Tolerancia: {horario.minutos_tolerancia} min</span>
                            </div>
                          </div>
                        </div>

                        {horario.ya_registro && horario.estado_asistencia ? (
                          <span className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border ${estadoColors[horario.estado_asistencia] || 'bg-gray-100 text-gray-600'}`}>
                            {EstIcon && <EstIcon size={14} />}
                            {horario.estado_asistencia === 'PRESENTE' && 'Presente'}
                            {horario.estado_asistencia === 'TARDE' && 'Tarde'}
                            {horario.estado_asistencia === 'AUSENTE' && 'Ausente'}
                            {horario.estado_asistencia === 'JUSTIFICADO' && 'Justificado'}
                          </span>
                        ) : timeStatus.label === 'Cerrado' ? (
                          <span className="shrink-0 text-xs text-red-500 font-medium px-3 py-1.5">Fuera de tiempo</span>
                        ) : (
                          <button
                            onClick={() => setCamera({ horario, materiaNombre: materia.nombre })}
                            className="shrink-0 flex items-center gap-2 bg-unl-red hover:bg-unl-red-dark text-white px-4 py-2 rounded-xl text-sm font-medium transition-all shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0"
                          >
                            <Camera size={16} /> Marcar
                          </button>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
            </div>
          )}
        </div>
      ))}

      <CameraModal
        open={!!camera}
        onClose={() => setCamera(null)}
        horario={camera?.horario}
        materiaNombre={camera?.materiaNombre}
        onSubmit={handleRegistrar}
      />
    </div>
  )
}
