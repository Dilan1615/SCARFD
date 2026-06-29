import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Link } from 'react-router-dom'
import { Eye, EyeOff, LogIn, AlertCircle, Mail, Lock } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [intentos, setIntentos] = useState(null)
  const [showContent, setShowContent] = useState(false)

  useEffect(() => {
    setTimeout(() => setShowContent(true), 100)
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIntentos(null)
    setLoading(true)
    try {
      await login(email, password)
      window.location.href = '/'
    } catch (err) {
      const data = err.response?.data || {}
      setError(data.detail || 'Credenciales inválidas. Intente nuevamente.')
      if (data.intentos_restantes !== undefined) {
        setIntentos(data.intentos_restantes)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-unl-black via-[#2C1A16] to-unl-black flex items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(191,8,17,0.08)_0%,_transparent_70%)]" />
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-unl-red/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-unl-green/5 rounded-full blur-3xl" />

      <div className={`relative w-full max-w-6xl flex flex-col lg:flex-row items-center gap-8 lg:gap-16 transition-all duration-700 ${showContent ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
        <div className="flex-1 text-center lg:text-left animate-fade-up max-w-xl">
          <div className="inline-flex items-center gap-2.5 mb-6 px-4 py-2 bg-white/5 backdrop-blur-sm rounded-full border border-white/10">
            <span className="w-2 h-2 rounded-full bg-unl-green animate-pulse" />
            <span className="text-xs text-gray-400 font-medium tracking-widest uppercase">Sistema de Asistencia Facial</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-black text-white leading-none mb-4">
            Universidad
            <br />
            Nacional
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-unl-red via-red-400 to-unl-red">de Loja</span>
          </h1>

          <p className="text-gray-400 text-base sm:text-lg max-w-md mx-auto lg:mx-0 leading-relaxed">
            Sistema de Asistencia con Reconocimiento Facial
          </p>

          <div className="hidden lg:flex items-center gap-6 mt-10 text-xs text-gray-600">
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-unl-red" />
              Excelencia
            </span>
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-unl-green" />
              Innovación
            </span>
            <span className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-gray-600" />
              Transformación
            </span>
          </div>
        </div>

        <div className="w-full max-w-[390px] animate-fade-up">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
            <div className="p-7">
              <div className="text-center mb-6">
                <div className="w-14 h-14 bg-gradient-to-br from-unl-red to-unl-red-dark rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-unl-red/20">
                  <img src="/unl-logo.png" alt="UNL" className="h-8 w-8 object-contain brightness-0 invert" />
                </div>
                <h2 className="text-xl font-bold text-unl-black">Bienvenido</h2>
                <p className="text-gray-400 text-sm mt-1">Inicia sesión para continuar</p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm mb-4">
                  <div className="flex items-center gap-2.5">
                    <AlertCircle size={16} className="shrink-0" />
                    {error}
                  </div>
                  {intentos !== null && intentos > 0 && (
                    <div className="mt-2 flex items-center gap-2 text-amber-700 text-xs">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0" />
                      Intentos restantes: {intentos}
                    </div>
                  )}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Correo</label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full h-11 pl-10 pr-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 placeholder-gray-400 bg-gray-50 focus:bg-white"
                      placeholder="Ingrese su correo"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Contraseña</label>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                      type={showPass ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full h-11 pl-10 pr-11 border border-gray-200 rounded-xl focus:ring-2 focus:ring-unl-red/20 focus:border-unl-red outline-none transition-all text-gray-900 placeholder-gray-400 bg-gray-50 focus:bg-white"
                      placeholder="Ingrese su contraseña"
                      required
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

                <div className="flex items-center justify-end">
                  <Link to="/recuperar-password" className="text-xs text-unl-red hover:text-red-700 hover:underline transition-colors font-medium">
                    ¿Olvidaste tu contraseña?
                  </Link>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full h-11 bg-gradient-to-r from-unl-red to-red-700 hover:from-red-700 hover:to-unl-red text-white font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 shadow-md hover:shadow-lg text-sm"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <><LogIn size={15} /> Ingresar al Sistema</>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
