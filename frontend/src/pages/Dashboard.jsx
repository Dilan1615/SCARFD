import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../contexts/AuthContext'
import { Users, GraduationCap, BookOpen, CalendarCheck, TrendingUp, Clock, Shield } from 'lucide-react'

function StatCard({ icon: Icon, label, value, color, delay }) {
  return (
    <div
      className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5 hover:shadow-md transition-all duration-300 hover:-translate-y-1 opacity-0 animate-fade-up"
      style={{ animationDelay: `${delay}s`, animationFillMode: 'forwards' }}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm text-gray-500 font-medium truncate">{label}</p>
          <p className="text-2xl font-bold text-unl-black mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-2xl ${color} shadow-sm shrink-0`}>
          <Icon size={22} className="text-white" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/academico/carreras/').catch(() => ({ data: [] })),
      api.get('/academico/materias/').catch(() => ({ data: [] })),
      api.get('/usuario/usuarios/').catch(() => ({ data: [] })),
      api.get('/asistencia/asistencias/').catch(() => ({ data: [] })),
    ]).then(([carreras, materias, usuarios, asistencias]) => {
      setStats({
        carreras: carreras.data.length || carreras.data.results?.length || 0,
        materias: materias.data.length || materias.data.results?.length || 0,
        usuarios: usuarios.data.length || usuarios.data.results?.length || 0,
        asistencias: asistencias.data.length || asistencias.data.results?.length || 0,
      })
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-2 border-unl-red border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const quickActions = [
    { path: '/academico/carreras', label: 'Carreras', desc: 'Administrar carreras', icon: GraduationCap },
    { path: '/academico/materias', label: 'Materias', desc: 'Gestionar materias', icon: BookOpen },
    { path: '/asistencia', label: 'Asistencia', desc: 'Registrar asistencias', icon: CalendarCheck },
    { path: '/reportes', label: 'Reportes', desc: 'Generar reportes', icon: TrendingUp },
  ]

  const userInfo = [
    { label: 'Nombres', value: `${user?.first_name || ''} ${user?.last_name || ''}`.trim() || '-' },
    { label: 'Usuario', value: user?.username || '-' },
    { label: 'Email', value: user?.email || '-' },
    { label: 'Cédula', value: user?.cedula || '-' },
  ]

  return (
    <div className="space-y-5">
      <div className="bg-gradient-to-r from-unl-black to-[#3C231E] rounded-2xl p-6 text-white shadow-lg">
        <div className="flex items-center gap-4">
          <div className="shrink-0 hidden sm:block">
            {user?.foto_referencia_url ? (
              <img src={user.foto_referencia_url} alt="" className="w-14 h-14 rounded-2xl object-cover border-2 border-white/20" />
            ) : (
              <div className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center">
                <Shield size={22} className="text-unl-green" />
              </div>
            )}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-0.5">Panel de Control</p>
            <h2 className="text-xl sm:text-2xl font-bold truncate">
              Bienvenido, {user?.first_name || user?.username || 'Usuario'}
            </h2>
            <p className="text-gray-400 text-sm mt-0.5 truncate">
              Universidad Nacional de Loja — Sistema de Asistencia Facial
            </p>
          </div>
          <div className="shrink-0">
            <span className="block text-xs text-gray-500 text-right mb-1">Rol</span>
            <span className="inline-block px-3 py-1.5 bg-unl-red/20 text-red-300 text-xs font-bold rounded-xl uppercase tracking-wider">
              {user?.rol || '-'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard icon={GraduationCap} label="Carreras" value={stats?.carreras || 0} color="bg-unl-red" delay={0.1} />
        <StatCard icon={BookOpen} label="Materias" value={stats?.materias || 0} color="bg-unl-green" delay={0.2} />
        <StatCard icon={Users} label="Usuarios" value={stats?.usuarios || 0} color="bg-gray-800" delay={0.3} />
        <StatCard icon={CalendarCheck} label="Asistencias" value={stats?.asistencias || 0} color="bg-gradient-to-br from-unl-red to-unl-green" delay={0.4} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 opacity-0 animate-fade-up" style={{ animationDelay: '0.5s', animationFillMode: 'forwards' }}>
          <h3 className="text-base font-bold text-unl-black mb-4 flex items-center gap-2">
            <Clock size={18} className="text-unl-red" />
            Información del Usuario
          </h3>
          <div className="space-y-0">
            {userInfo.map((item, i) => (
              <div key={item.label} className={`flex items-center justify-between py-2.5 ${i < userInfo.length - 1 ? 'border-b border-gray-100' : ''}`}>
                <span className="text-sm text-gray-500 shrink-0">{item.label}</span>
                <span className="text-sm font-medium text-unl-black text-right ml-4 truncate max-w-[55%]">{item.value}</span>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2.5">
              <span className="text-sm text-gray-500">Rol</span>
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-unl-red/10 text-unl-red uppercase tracking-wider">
                {user?.rol || '-'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 opacity-0 animate-fade-up" style={{ animationDelay: '0.6s', animationFillMode: 'forwards' }}>
          <h3 className="text-base font-bold text-unl-black mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-unl-green" />
            Acciones Rápidas
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {quickActions.map((action) => (
              <button
                key={action.path}
                onClick={() => navigate(action.path)}
                className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl bg-gray-50 hover:bg-gray-100 border border-gray-100 hover:border-gray-200 transition-all text-center group"
              >
                <div className="w-10 h-10 rounded-xl bg-white shadow-sm border border-gray-100 flex items-center justify-center group-hover:border-unl-red/20 group-hover:shadow-md transition-all">
                  <action.icon size={20} className="text-gray-400 group-hover:text-unl-red transition-colors" />
                </div>
                <div>
                  <p className="font-semibold text-gray-700 text-sm">{action.label}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{action.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="text-center text-xs text-gray-400 pt-4 border-t border-gray-200">
        Universidad Nacional de Loja
      </div>
    </div>
  )
}
