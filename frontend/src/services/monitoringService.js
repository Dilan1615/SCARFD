// Reutiliza la instancia de Axios ya configurada del proyecto
// (timeout 5s + interceptor JWT + baseURL apuntando al gateway).
import api from "/src/api/axios.js";

const BASE = "/monitoring";

export const monitoringService = {

    /** Estado de cada microservicio: activo/caído + tiempo de respuesta. */
    getEstadoServicios: () =>
        api.get(`${BASE}/salud/`)
            .then((r) => r.data),

    /** CPU, RAM, disco y contenedores Docker. */
    getInfraestructura: () =>
        api.get(`${BASE}/infraestructura/`)
            .then((r) => r.data),

    /** Peticiones/min, tiempo de respuesta, errores 4xx/5xx, por microservicio. */
    getBackend: (rangoMinutos = 30) =>
        api.get(`${BASE}/backend/`, {
            params: {
                rango_minutos: rangoMinutos
            }
        }).then((r) => r.data),

    /** Conexiones activas, consultas/seg y almacenamiento de PostgreSQL. */
    getBaseDatos: () =>
        api.get(`${BASE}/base-datos/`)
            .then((r) => r.data),

    /** Indicadores de negocio SACARF. */
    getNegocio: () =>
        api.get(`${BASE}/negocio/`)
            .then((r) => r.data),

    /** Todo el dashboard en una sola petición. */
    getResumen: () =>
        api.get(`${BASE}/resumen/`)
            .then((r) => r.data),

    /**
     * Logs de auditoría paginados.
     * filtros puede incluir:
     * usuario, accion, servicio, modelo,
     * fecha_desde, fecha_hasta, buscar, page, page_size
     */
    getAuditoria: (filtros = {}) =>
        api.get(`${BASE}/auditoria/`, {
            params: filtros
        }).then((r) => r.data),

    /** Conteos de las últimas 24h por acción y servicio. */
    getAuditoriaResumen: () =>
        api.get(`${BASE}/auditoria/resumen/`)
            .then((r) => r.data)
};

export default monitoringService;