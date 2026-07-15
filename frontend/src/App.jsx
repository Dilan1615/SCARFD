import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import { ToastProvider } from './contexts/ToastContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import RecuperarPassword from './pages/RecuperarPassword'
import Dashboard from './pages/Dashboard'
import UsuariosList from './pages/usuarios/UsuariosList'
import MiPerfil from './pages/usuarios/MiPerfil'
import CarrerasList from './pages/academico/CarrerasList'
import CiclosList from './pages/academico/CiclosList'
import MateriasList from './pages/academico/MateriasList'
import HorariosList from './pages/academico/HorariosList'
import MatriculasList from './pages/academico/MatriculasList'
import AsistenciaList from './pages/asistencia/AsistenciaList'
import AsistenciaHoy from './pages/asistencia/AsistenciaHoy'
import RegistroRostro from './pages/asistencia/RegistroRostro'
import ReportesList from './pages/reportes/ReportesList'
import DashboardMonitoring from './pages/monitoring/DashboardMonitoring'
import LogsActividad from './pages/monitoring/LogsActividad'

function PrivateRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen"><div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" /></div>
  return user ? children : <Navigate to="/login" />
}

export default function App() {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen"><div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <ToastProvider>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" /> : <Login />} />
        <Route path="/recuperar-password" element={user ? <Navigate to="/" /> : <RecuperarPassword />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="usuarios" element={<UsuariosList />} />
          <Route path="perfil" element={<MiPerfil />} />
          <Route path="academico/carreras" element={<CarrerasList />} />
          <Route path="academico/ciclos" element={<CiclosList />} />
          <Route path="academico/materias" element={<MateriasList />} />
          <Route path="academico/horarios" element={<HorariosList />} />
          <Route path="academico/matriculas" element={<MatriculasList />} />
          <Route path="asistencia" element={<AsistenciaList />} />
          <Route path="asistencia/hoy" element={<AsistenciaHoy />} />
          <Route path="registro-rostro" element={<RegistroRostro />} />
          <Route path="reportes" element={<ReportesList />} />
          <Route path="monitoring" element={<DashboardMonitoring />} />
          <Route path="/monitoreo"element={<DashboardMonitoring />}/>
          <Route path="/monitoreo/logs"element={<LogsActividad />}/>
        </Route>
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </ToastProvider>
  )
}
