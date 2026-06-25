import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Mail, Lock, KeyRound, ArrowLeft, CheckCircle, AlertCircle, Loader2, Eye, EyeOff } from 'lucide-react'
import api from '../api/axios'

export default function RecuperarPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const tokenUrl = searchParams.get('token')
  const isResetMode = !!tokenUrl

  const [email, setEmail] = useState('')
  const [token] = useState(tokenUrl || '')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [showConfirmPass, setShowConfirmPass] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [showContent, setShowContent] = useState(false)

  useEffect(() => {
    setTimeout(() => setShowContent(true), 100)
  }, [])

  const handleRequestReset = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      await api.post('/usuario/usuarios/solicitar-restablecimiento/', { email })
      setSent(true)
      setSuccess('Revisa tu correo electrónico. El enlace expira en 30 segundos.')
    } catch (err) {
      setError(err.response?.data?.email?.[0] || err.response?.data?.error || 'Error al solicitar restablecimiento')
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }
    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }
    setLoading(true)
    try {
      const { data } = await api.post('/usuario/usuarios/restablecer-password/', { token, password, confirm_password: confirmPassword })
      setSuccess(data.mensaje)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.confirm_password?.[0] || 'Error al restablecer la contraseña')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-unl-black via-[#2C1A16] to-unl-black flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(191,8,17,0.08)_0%,_transparent_70%)]" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-unl-red/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-unl-green/5 rounded-full blur-3xl" />

      <div className={`relative w-full max-w-md transition-all duration-700 ${showContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          <div className="p-7">
            <div className="text-center mb-6">
              <div className="w-14 h-14 bg-gradient-to-br from-unl-red to-unl-red-dark rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-unl-red/20">
                <KeyRound size={24} className="text-white" />
              </div>
              <h2 className="text-xl font-bold text-unl-black">
                {isResetMode ? 'Restablecer Contraseña' : 'Recuperar Contraseña'}
              </h2>
              <p className="text-gray-400 text-sm mt-1">
                {isResetMode
                  ? 'Ingresa tu nueva contraseña'
                  : sent
                    ? 'Revisa tu bandeja de entrada'
                    : 'Ingresa tu correo electrónico'}
              </p>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm mb-4 flex items-center gap-2.5">
                <AlertCircle size={16} className="shrink-0" />
                {error}
              </div>
            )}

            {success && (
              <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl text-sm mb-4 flex items-center gap-2.5">
                <CheckCircle size={16} className="shrink-0" />
                {success}
              </div>
            )}

            {isResetMode ? (
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Nueva Contraseña
                  </label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type={showPass ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full h-11 pl-10 pr-11 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 placeholder-gray-400 bg-gray-50 focus:bg-white"
                      placeholder="Mínimo 8 caracteres"
                      required
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPass(!showPass)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Confirmar Contraseña
                  </label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type={showConfirmPass ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full h-11 pl-10 pr-11 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 placeholder-gray-400 bg-gray-50 focus:bg-white"
                      placeholder="Repite la contraseña"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPass(!showConfirmPass)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      {showConfirmPass ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-11 bg-gradient-to-r from-unl-red to-red-700 hover:from-red-700 hover:to-unl-red text-white font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 shadow-md hover:shadow-lg text-sm"
                >
                  {loading ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <>Restablecer Contraseña</>
                  )}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRequestReset} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Correo Electrónico
                  </label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full h-11 pl-10 pr-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 placeholder-gray-400 bg-gray-50 focus:bg-white"
                      placeholder="correo@ejemplo.com"
                      required
                      disabled={sent}
                    />
                  </div>
                  <p className="text-xs text-gray-400 mt-1.5">Ingresa tu correo electrónico registrado</p>
                </div>

                <button
                  type="submit"
                  disabled={loading || sent}
                  className="w-full h-11 bg-gradient-to-r from-unl-red to-red-700 hover:from-red-700 hover:to-unl-red text-white font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 shadow-md hover:shadow-lg text-sm"
                >
                  {loading ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : sent ? (
                    <>Enviado</>
                  ) : (
                    <>Enviar Enlace</>
                  )}
                </button>
              </form>
            )}

            <div className="mt-6 text-center">
              <Link
                to="/login"
                className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-unl-red transition-colors font-medium"
              >
                <ArrowLeft size={14} />
                Volver al inicio de sesión
              </Link>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-4">
          Universidad Nacional de Loja — Sistema de Asistencia Facial
        </p>
      </div>
    </div>
  )
}
