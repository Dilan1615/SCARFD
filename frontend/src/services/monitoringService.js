// Reutiliza la instancia de Axios ya configurada del proyecto
// (timeout 5s + interceptor JWT + baseURL apuntando al gateway).
import api from '../api/axios'

const BASE = '/monitoring'

export const monitoringService = {
  /** Estado de cada microservicio: activo/caído + tiempo de respuesta. */
  getEstadoServicios: () => api.get(`${BASE}/salud/`).then((r) => r.data),

  /** CPU, RAM, disco y contenedores Docker. */
  getInfraestructura: () => api.get(`${BASE}/infraestructura/`).then((r) => r.data),

  /** Peticiones/min, tiempo de respuesta, errores 4xx/5xx, por microservicio. */
  getBackend: (rangoMinutos = 30) =>
    api.get(`${BASE}/backend/`, { params: { rango_minutos: rangoMinutos } }).then((r) => r.data),

  /** Conexiones activas, consultas/seg y almacenamiento de PostgreSQL. */
  getBaseDatos: () => api.get(`${BASE}/base-datos/`).then((r) => r.data),

  /** Indicadores de negocio SACARF. */
  getNegocio: () => api.get(`${BASE}/negocio/`).then((r) => r.data),

  /** Todo el dashboard en una sola petición (usado en el primer render). */
  getResumen: () => api.get(`${BASE}/resumen/`).then((r) => r.data),
}

export default monitoringService
