import { useState, useEffect } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  LayoutDashboard, Users, GraduationCap, CalendarCheck,
  ClipboardList, LogOut, Menu, X, ChevronDown, User, ScanFace, Activity,
} from 'lucide-react'

function useNavItems() {
  const { user } = useAuth()
  const isAdmin = user?.rol === 'ADMIN'
  const isStudent = user?.rol === 'ESTUDIANTE'
  return [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    ...(isAdmin ? [{ to: '/usuarios', label: 'Usuarios', icon: Users }] : []),
    { to: '/perfil', label: 'Mi Perfil', icon: User },
    ...(isAdmin ? [{ to: '/monitoring', label: 'Monitoreo', icon: Activity }] : []),
    ...(isAdmin || user?.rol === 'DOCENTE' ? [{
      to: '/academico', label: 'Académico', icon: GraduationCap, children: [
        { to: '/academico/carreras', label: 'Carreras' },
        { to: '/academico/ciclos', label: 'Ciclos' },
        { to: '/academico/materias', label: 'Materias' },
        { to: '/academico/horarios', label: 'Horarios' },
        { to: '/academico/matriculas', label: 'Matrículas' },
      ]
    }] : []),
    ...(isStudent ? [
      { to: '/asistencia/hoy', label: 'Asistencia Hoy', icon: CalendarCheck },
      { to: '/registro-rostro', label: 'Registrar Rostro', icon: ScanFace },
    ] : [
      { to: '/asistencia', label: 'Asistencia', icon: CalendarCheck },
    ]),
    { to: '/reportes', label: 'Reportes', icon: ClipboardList },
  ]
}

function SidebarItem({ item, onClose }) {
  const location = useLocation()
  const hasChildren = item.children
  const childActive = hasChildren && item.children.some((c) => location.pathname === c.to)
  const isActive = hasChildren ? childActive : location.pathname === item.to
  const [open, setOpen] = useState(childActive)

  useEffect(() => {
    if (childActive) setOpen(true)
  }, [childActive])

  if (hasChildren) {
    return (
      <div>
        <button
          onClick={() => setOpen(!open)}
          className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all duration-200 ${
            isActive
              ? 'bg-unl-red/15 text-white'
              : 'text-gray-400 hover:bg-white/5 hover:text-white'
          }`}
        >
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
            isActive ? 'bg-unl-red text-white' : 'bg-white/5 text-gray-400'
          }`}>
            <item.icon size={16} />
          </div>
          <span className="flex-1 text-left font-medium">{item.label}</span>
          <ChevronDown size={14} className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
        </button>
        <div className={`overflow-hidden transition-all duration-200 ${open ? 'max-h-60 opacity-100 mt-1' : 'max-h-0 opacity-0'}`}>
          <div className="ml-4 pl-4 border-l border-white/10 space-y-0.5">
            {item.children.map((child) => (
              <NavLink
                key={child.to}
                to={child.to}
                onClick={onClose}
                className={({ isActive }) =>
                  `block px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-unl-green/20 text-unl-green font-medium'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`
                }
              >
                {child.label}
              </NavLink>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <NavLink
      to={item.to}
      onClick={onClose}
      className={({ isActive }) =>
        `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all duration-200 ${
          isActive
            ? 'bg-unl-red text-white font-medium shadow-lg shadow-unl-red/20'
            : 'text-gray-400 hover:bg-white/5 hover:text-white'
        }`
      }
    >
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
        isActive ? 'bg-white/20' : 'bg-white/5'
      }`}>
        <item.icon size={16} />
      </div>
      <span className="font-medium">{item.label}</span>
    </NavLink>
  )
}

function SidebarContent({ onClose }) {
  const { user, logout } = useAuth()
  const navItems = useNavItems()
  return (
    <>
      <div className="flex items-center gap-3 px-5 h-16 border-b border-white/5 shrink-0">
        <div className="w-9 h-9 bg-gradient-to-br from-unl-red to-unl-red-dark rounded-xl flex items-center justify-center shadow-lg shadow-unl-red/20">
          <img src="/unl-logo.png" alt="UNL" className="h-6 w-6 object-contain brightness-0 invert" />
        </div>
        <div className="leading-tight">
          <span className="font-bold text-sm text-white block">SACARF</span>
          <span className="text-[10px] text-gray-500 tracking-wide">UNL - Asistencia Facial</span>
        </div>
        {onClose && (
          <button onClick={onClose} className="ml-auto text-gray-400 hover:text-white md:hidden p-1">
            <X size={18} />
          </button>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {navItems.map((item) => (
          <SidebarItem key={item.to} item={item} onClose={onClose} />
        ))}
      </nav>

      <div className="p-3 border-t border-white/5 shrink-0">
        {user && (
          <div className="flex items-center gap-3 px-3 py-2 mb-2 rounded-lg bg-white/5">
            <div className="w-9 h-9 bg-gradient-to-br from-unl-red to-unl-green rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-md shrink-0">
              {user.first_name?.charAt(0) || user.username?.charAt(0) || 'U'}
            </div>
            <div className="text-xs text-gray-400 truncate min-w-0">
              <p className="text-white text-sm font-medium truncate">{user.first_name} {user.last_name}</p>
            </div>
          </div>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-400 hover:bg-white/5 hover:text-red-400 rounded-lg transition-colors w-full group"
        >
          <LogOut size={16} className="group-hover:text-red-400" />
          <span className="font-medium">Cerrar Sesión</span>
        </button>
      </div>
    </>
  )
}

export default function Layout() {
  const { user } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()
  const navItems = useNavItems()

  const pageTitle = navItems
    .flatMap((i) => (i.children ? [i, ...i.children] : i))
    .find((i) => i.to === location.pathname)?.label || 'Dashboard'

  return (
    <div className="flex h-screen bg-unl-white">
      <aside className="w-64 bg-unl-black text-white flex-col transition-all duration-300 hidden md:flex">
        <SidebarContent />
      </aside>

      <div
        className={`fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden transition-opacity duration-300 ${sidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`fixed top-0 left-0 h-full w-64 bg-unl-black text-white z-50 transform transition-transform duration-300 md:hidden ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <SidebarContent onClose={() => setSidebarOpen(false)} />
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 h-16 flex items-center gap-4 px-4 md:px-6 shrink-0">
          <button
            className="md:hidden w-9 h-9 flex items-center justify-center text-gray-500 hover:text-unl-red hover:bg-unl-red/5 rounded-lg transition-colors"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-unl-green animate-pulse" />
            <h1 className="text-lg font-bold text-unl-black">{pageTitle}</h1>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-sm text-gray-500 hidden sm:block">
              {user?.first_name} {user?.last_name}
            </span>
            <div className="w-9 h-9 bg-gradient-to-br from-unl-red to-unl-green rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-md shrink-0">
              {user?.first_name?.charAt(0) || 'U'}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
