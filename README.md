# SACARF — Sistema de Asistencia con Reconocimiento Facial

**Universidad Nacional de Loja**

Sistema web para el registro de asistencia de estudiantes mediante reconocimiento facial, gestión académica (carreras, ciclos, materias, horarios, matrículas), generación de reportes y monitoreo del sistema (CPU, RAM, disco, contenedores, base de datos, logs de auditoría).

Arquitectura de **microservicios** con Django REST Framework, gateway Nginx y frontend React.

---

## Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Microservicios](#microservicios)
  - [usuario-service](#usuario-service)
  - [academico-service](#academico-service)
  - [asistencia-service](#asistencia-service)
  - [reportes-service](#reportes-service)
  - [monitoring-service](#monitoring-service)
- [Gateway (Nginx)](#gateway-nginx)
- [Servicio init](#servicio-init)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Cómo se Dividió el Monolito](#cómo-se-dividió-el-monolito)
  - [Separación de Código](#separación-de-código)
  - [Modelos Compartidos (shared)](#modelos-compartidos-shared)
  - [Migraciones](#migraciones)
  - [Frontend y Detección de Servicio Caído](#frontend-y-detección-de-servicio-caído)
- [Cómo Correr el Proyecto](#cómo-correr-el-proyecto)
  - [Requisitos](#requisitos)
  - [Con Docker (recomendado)](#con-docker-recomendado)
  - [Desarrollo Local (sin Docker)](#desarrollo-local-sin-docker)
- [Cómo Probar los Microservicios](#cómo-probar-los-microservicios)
  - [Verificar que todos los servicios responden](#verificar-que-todos-los-servicios-responden)
  - [Probar aislamiento (servicio caído)](#probar-aislamiento-servicio-caído)
  - [Probar que el frontend detecta servicios caídos](#probar-que-el-frontend-detecta-servicios-caídos)
  - [Pruebas unitarias de Django](#pruebas-unitarias-de-django)
- [Tecnologías](#tecnologías)
- [Variables de Entorno](#variables-de-entorno)
- [API Endpoints](#api-endpoints)
- [Flujo de Reconocimiento Facial](#flujo-de-reconocimiento-facial)
- [Sistema de Auditoría](#sistema-de-auditoría)
- [Documentación de la API](#documentación-de-la-api)

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx Gateway                        │
│                      (puerto 8000)                         │
│  /api/usuario/*     → upstream usuario    :8001             │
│  /api/academico/*   → upstream academico  :8002             │
│  /api/asistencia/*  → upstream asistencia :8003             │
│  /api/reportes/*    → upstream reportes   :8004             │
│  /api/monitoring/*  → upstream monitoring :8005             │
│  /admin/            → upstream usuario    :8001             │
│  /swagger/, /redoc/ → upstream usuario    :8001             │
└──────┬──────────────────────────────────────────────────────┘
       │
       │ (puerto 8000)
       ▼
┌─────────────────────────────────────────────────────────────┐
│                    React + Vite (frontend)                   │
│                    (puerto 5173)                             │
│              Proxy Vite: /api → gateway:8000                 │
│              Timeout Axios: 5 segundos                       │
└─────────────────────────────────────────────────────────────┘

┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  usuario-svc   │  │ academico-svc  │  │ asistencia-svc │  │  reportes-svc  │  │ monitoring-svc │
│  Django :8001  │  │  Django :8002  │  │  Django :8003  │  │  Django :8004  │  │  Django :8005  │
│                │  │                │  │                │  │                │  │                │
│  /api/usuario/ │  │ /api/academico/│  │/api/asistencia/│  │ /api/reportes/ │  │/api/monitoring/│
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                   │                   │                   │
        └───────────────────┴───────────────────┴───────────────────┴───────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │   PostgreSQL 15     │
                              │   (db :5432)        │
                              └────────────────────┘
                                        │
                              ┌─────────▼──────────┐
                              │  monitoring-svc     │
                              │  ├─ psutil (CPU/RAM/disco)
                              │  ├─ Docker SDK (contenedores)
                              │  └─ psycopg2 (SQL directa)
                              └────────────────────┘

                    ☁️ AWS Cloud
            ┌─────────────────────────┐
            │  Rekognition            │
            │  ├─ IndexFaces          │
            │  └─ SearchFacesByImage  │
            │                         │
            │  S3 Bucket              │
            │  ├─ fotos/referencia/   │
            │  └─ asistencias/        │
            └─────────────────────────┘

            📧 Brevo API (correos transaccionales)
```

---

## Microservicios

Cada microservicio es un proyecto Django independiente que comparte la misma base de datos PostgreSQL y el paquete `shared/` de solo lectura.

### usuario-service

| Propiedad | Valor |
|-----------|-------|
| Puerto | 8001 |
| Settings | `services/usuario/usuario/settings.py` |
| URLConf | `services/usuario/usuario/urls.py` |

**Apps cargadas:** `usuario`

**Endpoints:**
- `POST /api/usuario/token/` — Login JWT
- `POST /api/usuario/token/refresh/` — Refrescar token
- `GET/POST /api/usuario/usuarios/` — CRUD de usuarios (solo admin para mutations)
- `GET /api/usuario/usuarios/me/` — Perfil del usuario autenticado
- `PATCH /api/usuario/usuarios/perfil/` — Actualizar perfil propio
- `POST /api/usuario/usuarios/register/` — Registro público
- `POST /api/usuario/usuarios/solicitar-restablecimiento/` — Recuperar contraseña
- `POST /api/usuario/usuarios/restablecer-password/` — Restablecer contraseña
- `POST /api/usuario/usuarios/cambiar-password/` — Cambiar contraseña
- `GET /admin/` — Admin de Django
- `GET /swagger/` — Swagger UI
- `GET /redoc/` — Redoc

**Responsabilidad:** Gestión de usuarios, autenticación JWT, subida de fotos de perfil (conversión a JPEG), control de intentos fallidos de login, recuperación de contraseña vía Brevo. Es el único servicio que expone el admin de Django y la documentación Swagger/Redoc.

### academico-service

| Propiedad | Valor |
|-----------|-------|
| Puerto | 8002 |
| Settings | `services/academico/academico/settings.py` |
| URLConf | `services/academico/academico/urls.py` |

**Apps cargadas:** `academico`, `shared`

**Endpoints:**
- `GET/POST /api/academico/carreras/` — CRUD carreras
- `GET/POST /api/academico/ciclos/` — CRUD ciclos
- `GET/POST /api/academico/materias/` — CRUD materias
- `GET/POST /api/academico/horarios/` — CRUD horarios
- `GET/POST /api/academico/matriculas/` — CRUD matrículas
- `GET /api/academico/matriculas/mis_materias/` — Materias del día para el estudiante autenticado

**Responsabilidad:** Gestión de la estructura académica: carreras, ciclos, materias, horarios y matrículas. Consulta `shared.models.Usuario` para validar docentes y estudiantes.

### asistencia-service

| Propiedad | Valor |
|-----------|-------|
| Puerto | 8003 |
| Settings | `services/asistencia/asistencia/settings.py` |
| URLConf | `services/asistencia/asistencia/urls.py` |

**Apps cargadas:** `asistencia`, `shared`

**Endpoints:**
- `GET /api/asistencia/asistencias/` — Listar asistencias (filtrado por rol)
- `POST /api/asistencia/asistencias/registrar/` — Registrar asistencia con reconocimiento facial
- `GET /api/asistencia/asistencias/por_estudiante/` — Asistencias por estudiante
- `GET /api/asistencia/asistencias/por_materia/` — Asistencias por materia
- `POST /api/asistencia/justificaciones/` — Crear justificación
- `POST /api/asistencia/justificaciones/aprobar/` — Aprobar/rechazar justificación
- `POST /api/asistencia/registro-facial/registrar_rostro/` — Indexar rostro en AWS Rekognition

**Responsabilidad:** Registro de asistencia facial mediante AWS Rekognition, gestión de justificaciones y reconocimientos. Consulta `shared.models` para validar horarios, materias y usuarios.

### reportes-service

| Propiedad | Valor |
|-----------|-------|
| Puerto | 8004 |
| Settings | `services/reportes/reportes/settings.py` |
| URLConf | `services/reportes/reportes/urls.py` |

**Apps cargadas:** `reportes`, `shared`

**Endpoints:**
- `GET /api/reportes/reportes/` — Listar reportes generados
- `POST /api/reportes/reportes/generar/` — Generar nuevo reporte (PDF/Excel)
- `GET /api/reportes/reportes/:id/descargar/` — Descargar reporte
- `GET /api/reportes/reportes/tipos/` — Tipos y formatos disponibles

**Responsabilidad:** Generación de reportes de asistencia en PDF (ReportLab) y Excel (openpyxl), filtrado por tipo, materia, estudiante o ciclo.

### monitoring-service

| Propiedad | Valor |
|-----------|-------|
| Puerto | 8005 |
| Settings | `services/monitoring/monitoring/settings.py` |
| URLConf | `services/monitoring/monitoring/urls.py` |

**Apps cargadas:** `monitoring`, `shared`

**Endpoints:**
- `GET /api/monitoring/salud/` — Estado de cada microservicio (activo/caído + tiempo de respuesta)
- `GET /api/monitoring/infraestructura/` — CPU, RAM, disco (psutil) y contenedores Docker (SDK)
- `GET /api/monitoring/backend/` — Registros de auditoría recientes por servicio y acción
- `GET /api/monitoring/base-datos/` — Conexiones activas, consultas/seg y almacenamiento PostgreSQL
- `GET /api/monitoring/negocio/` — Indicadores de negocio: usuarios, asistencias, reconocimientos, reportes
- `GET /api/monitoring/resumen/` — Todo el dashboard en una sola petición
- `GET /api/monitoring/health/` — Self-check sin autenticación
- `GET /api/monitoring/auditoria/` — Logs de actividad paginados y filtrables
- `GET /api/monitoring/auditoria/resumen/` — Conteos de las últimas 24h por acción y servicio

**Responsabilidad:** Dashboard de monitoreo centralizado. Reemplaza a prometheus + node-exporter + cadvisor + postgres-exporter con lectura directa del host:
- **CPU / RAM / disco**: `psutil` (monta `/proc`, `/sys`, `/` del host en el contenedor)
- **Contenedores Docker**: SDK oficial de Docker (monta `docker.sock`)
- **PostgreSQL**: SQL directa vía `psycopg2`
- **Salud de servicios**: HTTP ping a `/health/` de cada microservicio
- **Logs de auditoría**: Tabla `monitoring_registroauditoria` compartida vía `shared.models.RegistroAuditoriaModel` (managed=False)

Todos los microservicios escriben logs de auditoría a través de `shared.audit.registrar_auditoria()`, que inserta filas en la tabla centralizada sin necesidad de importar la app `monitoring`.

---

## Gateway (Nginx)

El gateway es un contenedor Nginx que actúa como punto de entrada único (`puerto 8000`).

**Archivo:** `gateway/nginx.conf`

**Funcionamiento:**
- Escucha en el puerto 8000
- Enruta cada prefijo `/api/<servicio>/` al upstream correspondiente
- El header `Host` se pasa como `$http_host` (preserva el puerto original) para que `build_absolute_uri` genere URLs correctas en las respuestas Django
- Si un servicio está caído, responde con `502 Bad Gateway`
- El timeout de proxy es de 60 segundos

```
/api/usuario/*     → http://usuario-service:8001/api/usuario/
/api/academico/*   → http://academico-service:8002/api/academico/
/api/asistencia/*  → http://asistencia-service:8003/api/asistencia/
/api/reportes/*    → http://reportes-service:8004/api/reportes/
/api/monitoring/*  → http://monitoring-service:8005/api/monitoring/
/admin/*           → http://usuario-service:8001/admin/
/swagger/*         → http://usuario-service:8001/swagger/
/redoc/*           → http://usuario-service:8001/redoc/
```

El frontend solo conoce el gateway (`localhost:8000`) y nunca se comunica directamente con los servicios individuales.

---

## Servicio init

El contenedor `init` es un contenedor de una sola ejecución que corre antes que los servicios. Su responsabilidad es:
1. Ejecutar `migrate` en todas las apps
2. En modo DEBUG: verificar y generar migraciones pendientes (`makemigrations --check`)
3. Crear el superusuario por defecto si no existe (`admin@sacarf.com` / `admin123`)
4. En producción: recolectar archivos estáticos (`collectstatic`)
5. Verificar que la tabla `monitoring_registroauditoria` existe
6. Una vez completado, los servicios pueden iniciar

`depends_on:` en docker-compose usa `service_completed_successfully` para garantizar que `init` termine antes de arrancar los servicios.

---

## Estructura del Proyecto

```
sacarf/
├── sacarf/                          # Configuración raíz (solo para init)
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── manage.py                    # manage.py raíz (solo para init)
│
├── apps/
│   ├── usuario/                     # App de usuarios (código fuente)
│   ├── academico/                   # App académico (código fuente)
│   ├── asistencia/                  # App asistencia (código fuente)
│   ├── reportes/                    # App reportes (código fuente)
│   └── monitoring/                  # App monitoreo (código fuente)
│
├── docs/
│   └── pruebas/                     # Plan de pruebas detallado + informes .docx
│       ├── plan-pruebas-detallado.md
│       ├── shared.docx
│       ├── usuario.docx
│       ├── academico.docx
│       ├── asistencia.docx
│       ├── reportes.docx
│       ├── monitoring.docx
│       ├── informe-global.docx
│       └── resumen-ejecutivo.docx
│
├── shared/                          # Paquete de modelos compartidos (solo lectura)
│   ├── __init__.py
│   ├── models.py                    # Modelos duplicados con managed = False
│   ├── auth.py                      # EmailOrUsernameModelBackend + CustomJWTAuthentication
│   ├── permissions.py               # IsAdminForMutation
│   ├── audit.py                     # Auditoría centralizada (AuditoriaMixin + registrar_auditoria)
│   ├── clients.py                   # Clientes HTTP entre microservicios
│   └── tests.py                     # 58 pruebas del módulo compartido
│
├── services/                        # Proyectos Django independientes (microservicios)
│   ├── usuario/
│   │   ├── manage.py                # Entry point (PYTHONPATH + settings module)
│   │   └── usuario/
│   │       ├── __init__.py
│   │       ├── settings.py          # Solo app usuario
│   │       ├── urls.py              # Solo rutas de usuario
│   │       └── wsgi.py
│   │
│   ├── academico/
│   │   ├── manage.py
│   │   └── academico/
│   │       ├── __init__.py
│   │       ├── settings.py          # Solo app academico + shared
│   │       ├── urls.py              # Solo rutas de academico
│   │       └── wsgi.py
│   │
│   ├── asistencia/
│   │   ├── manage.py
│   │   └── asistencia/
│   │       ├── __init__.py
│   │       ├── settings.py          # Solo app asistencia + shared
│   │       ├── urls.py              # Solo rutas de asistencia
│   │       └── wsgi.py
│   │
│   ├── reportes/
│   │   ├── manage.py
│   │   └── reportes/
│   │       ├── __init__.py
│   │       ├── settings.py          # Solo app reportes + shared
│   │       ├── urls.py              # Solo rutas de reportes
│   │       └── wsgi.py
│   │
│   └── monitoring/
│       ├── manage.py
│       └── monitoring/
│           ├── __init__.py
│           ├── settings.py          # Solo app monitoring + shared
│           ├── urls.py              # Rutas de monitoreo + auditoría
│           └── wsgi.py
│
├── gateway/
│   └── nginx.conf                   # Configuración del gateway Nginx
│
├── media/
│   └── fotos/                       # Imágenes subidas localmente
│
├── Dockerfile                       # Dockerfile único para todos los servicios
├── entrypoint.sh                    # Script de entrada: init o servicio según SERVICE_NAME
├── docker-compose.yml               # Orquestación: db, init, 5 servicios + gateway
├── manage.py                        # manage.py raíz (compatibilidad local)
└── requirements.txt

frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── App.css / index.css
│   ├── api/
│   │   └── axios.js                 # Axios con timeout 5s + interceptor JWT
│   ├── contexts/
│   │   ├── AuthContext.jsx
│   │   └── ToastContext.jsx
│   ├── components/
│   │   ├── Layout.jsx
│   │   ├── DataTable.jsx
│   │   ├── FormModal.jsx
│   │   ├── ServiceStatusCard.jsx    # Tarjeta de estado de servicio
│   │   ├── MetricCard.jsx           # Tarjeta de métrica con barra de progreso
│   │   ├── LineChart.jsx            # Gráfico de líneas (series temporales)
│   │   ├── BarChart.jsx             # Gráfico de barras
│   │   ├── AlertPanel.jsx           # Panel de alertas del dashboard
│   │   ├── ActivityLogTable.jsx     # Tabla de logs de actividad
│   │   └── MaintenanceBanner.jsx    # Banner "Servicio en mantenimiento"
│   ├── pages/
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx            # servicesDown[] + banners por servicio
│   │   ├── RecuperarPassword.jsx
│   │   ├── usuarios/
│   │   ├── academico/
│   │   ├── asistencia/              # AsistenciaHoy.jsx con academicoDown
│   │   ├── reportes/
│   │   └── monitoring/
│   │       ├── DashboardMonitoring.jsx  # Dashboard principal de monitoreo
│   │       └── LogsActividad.jsx        # Logs de auditoría paginados
│   └── index.html
│
├── vite.config.js
├── package.json
└── Dockerfile

docker-compose.yml
entrypoint.sh
```

---

## Cómo se Dividió el Monolito

### Separación de Código

El proyecto original era un monolito Django con 4 apps (`usuario`, `academico`, `asistencia`, `reportes`) bajo un solo `manage.py` y un solo `settings.py`. Para dividirlo en microservicios:

1. **Se creó `services/<nombre>/manage.py`** — Cada microservicio tiene su propio `manage.py` que añade `/app` y `/app/sacarf` a `sys.path`, y apunta a su propio módulo de settings.

2. **Se creó `services/<nombre>/<nombre>/settings.py`** — Cada servicio tiene su propio `settings.py` hardcodeado que solo carga su app correspondiente:
   - `usuario-service`: solo `usuario`
   - `academico-service`: `academico` + `shared`
   - `asistencia-service`: `asistencia` + `shared`
   - `reportes-service`: `reportes` + `shared`
   - `monitoring-service`: `monitoring` + `shared`

3. **Se creó `services/<nombre>/<nombre>/urls.py`** — Cada servicio expone solo su propio prefijo de API.

4. **Se creó `services/<nombre>/<nombre>/wsgi.py`** — Cada servicio tiene su propio entrypoint WSGI.

### Modelos Compartidos (shared)

Dado que los microservicios necesitan leer modelos de otras apps (ej. `academico` necesita leer `Usuario`), pero no deben tener acceso de escritura a sus tablas, se creó el paquete `shared/`:

- **`shared/models.py`** — Contiene modelos duplicados con `managed = False`, apuntando a las tablas existentes. Incluye `Usuario`, `CarreraModel`, `CicloModel`, `MateriaModel`, `HorarioModel`, `AsistenciaModel`, `JustificacionModel`, `RegistroFacialModel`, `ReporteModel`, `RegistroAuditoriaModel`.
- **`shared/auth.py`** — Contiene `EmailOrUsernameModelBackend` y `CustomJWTAuthentication`, reutilizados por todos los servicios.
- **`shared/permissions.py`** — Contiene `IsAdminForMutation`, reutilizado por todos los servicios.
- **`shared/audit.py`** — Contiene `AuditoriaMixin` (para ViewSets) y `registrar_auditoria()` (llamadas explícitas). Los 4 microservicios escriben logs de auditoría a través de este módulo.

Todas las **ForeignKey y OneToOneField** entre apps se refactorizaron a `IntegerField` para eliminar dependencias directas. Las consultas entre servicios se hacen mediante consultas directas a los modelos compartidos (misma base de datos).

### Migraciones

Cada servicio usa `MigrationModules` para que las migraciones de todas las apps sigan residiendo en `sacarf/apps/<nombre>/migrations/`, evitando duplicación. El contenedor `init` ejecuta `migrate` para todas las apps. La tabla `monitoring_registroauditoria` es dueña real de monitoring-service, pero los demás servicios la escriben vía `shared.models.RegistroAuditoriaModel` (managed=False).

### Frontend y Detección de Servicio Caído

El frontend detecta servicios caídos mediante:

1. **Timeout global de Axios**: 5 segundos (`frontend/src/api/axios.js`)
2. **Detección por página**: cada página captura errores 5xx o de red y establece un estado `serviceDown` específico para el servicio que falló
3. **MaintenanceBanner**: componente reutilizable que muestra "Servicio de <nombre> en mantenimiento" con icono de wifi apagado
4. **Dashboard**: mantiene un array `servicesDown[]` para mostrar banners de todos los servicios caídos

---

## Cómo Correr el Proyecto

### Requisitos

- Docker y Docker Compose (recomendado)
- Node.js 18+ (para desarrollo local del frontend)
- Python 3.10+ (para desarrollo local del backend)
- Cuenta AWS con Rekognition y S3 configurados
- Cuenta Brevo con API key para envío de correos

### Con Docker (recomendado)

```bash
# 1. Clonar y entrar
git clone <repo>
cd sacarf

# 2. Configurar variables de entorno
#    Copiar .env.example a .env (o editar el existente)
#    Asegurarse de tener configuradas:
#      - DB_PASSWORD
#      - AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY
#      - BREVO_API_KEY

# 3. Construir y levantar (tarda unos minutos la primera vez)
docker-compose up -d --build

# 4. Verificar que los servicios están corriendo
docker-compose ps

# 5. Acceder
#    Frontend: http://localhost:5173
#    Backend (gateway):  http://localhost:8000
#    Admin:    http://localhost:8000/admin/
#    Swagger:  http://localhost:8000/swagger/
```

> **Nota**: El `entrypoint.sh` ejecuta migraciones automáticamente, crea un superusuario por defecto:
> - **Email**: admin@sacarf.com
> - **Password**: admin123
>
> En modo DEBUG, verifica migraciones pendientes con `makemigrations --check`.
> En producción, ejecuta `collectstatic` y omite `makemigrations`.

### Desarrollo Local (sin Docker)

**Backend (servicio específico):**

```bash
# 1. Crear y activar entorno virtual
cd sacarf
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar base de datos
#    Editar .env con DB_HOST=localhost, DB_ENGINE=django.db.backends.postgresql

# 4. Ejecutar migraciones (usa el manage.py raíz)
python manage.py migrate

# 5. Iniciar un servicio específico
python services/usuario/manage.py runserver 8001
python services/academico/manage.py runserver 8002
# ...etc
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

El frontend estará en `http://localhost:5173` con proxy automático al gateway en `http://localhost:8000`.

---

## Cómo Probar los Microservicios

### Verificar que todos los servicios responden

Con Docker funcionando:

```bash
# Ver contenedores activos
docker-compose ps

# Probar cada servicio individualmente a través del gateway
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/usuario/usuarios/me/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/academico/carreras/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/asistencia/asistencias/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/reportes/reportes/
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/monitoring/health/

# Login como admin
curl -X POST http://localhost:8000/api/usuario/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sacarf.com","password":"admin123"}'

# Listar carreras (con token)
TOKEN="<access_token_del_login>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/academico/carreras/
```

### Probar aislamiento (servicio caído)

Los servicios son independientes: si uno cae, los demás siguen funcionando.

```bash
# 1. Detener el servicio académico
docker-compose stop academico-service

# 2. Verificar que el gateway responde 502 para rutas académicas
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/academico/carreras/
# → 502 Bad Gateway

# 3. Verificar que los demás servicios siguen funcionando
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/usuario/usuarios/me/
# → 200 OK

# 4. Reactivar
docker-compose start academico-service
```

### Probar que el frontend detecta servicios caídos

1. Abrir `http://localhost:5173` e iniciar sesión
2. Navegar a una página que use el servicio académico (ej. "Gestión de Carreras")
3. En otra terminal, detener el servicio: `docker-compose stop academico-service`
4. Recargar la página → debe aparecer el banner **"Servicio de academico en mantenimiento"**
5. Reactivar: `docker-compose start academico-service`
6. Recargar → el banner desaparece y los datos cargan normalmente

### Pruebas unitarias de Django

El proyecto cuenta con **339 pruebas automatizadas** distribuidas en 6 módulos, todas pasando al 100%.

**Requisito:** Las pruebas se ejecutan con `SERVICE_NAME=all` (modo monolito) y SQLite en memoria.

```bash
# Configurar entorno
cd sacarf
$env:PYTHONPATH = "C:\ruta\a\sacarf\sacarf"
$env:SERVICE_NAME = "all"
$env:DB_NAME = ":memory:"
$env:DB_ENGINE = "django.db.backends.sqlite3"
# (más variables de entorno necesarias, ver conftest.py)

# Ejecutar pruebas de un módulo
python -m pytest sacarf/apps/usuario/tests.py -v --tb=short

# Ejecutar pruebas de todos los módulos (uno por uno en Windows)
Get-ChildItem -Path sacarf/apps/*/tests.py | ForEach-Object { $_.FullName } | ForEach-Object { python -m pytest $_ -v --tb=short }

# Ejecutar también las de shared
python -m pytest shared/tests.py -v --tb=short
```

**Resultados:**

| Módulo | Archivo | Pruebas | Estado |
|--------|---------|--------:|--------|
| shared | `shared/tests.py` | 58 | ✅ 100% |
| usuario | `sacarf/apps/usuario/tests.py` | 87 | ✅ 100% |
| academico | `sacarf/apps/academico/tests.py` | 77 | ✅ 100% |
| asistencia | `sacarf/apps/asistencia/tests.py` | 55 | ✅ 100% |
| reportes | `sacarf/apps/reportes/tests.py` | 34 | ✅ 100% |
| monitoring | `sacarf/apps/monitoring/tests.py` | 28 | ✅ 100% |
| **Total** | | **339** | **✅ 100%** |

**Tecnologías de prueba:** pytest 9.1.1, pytest-django 4.12, unittest.mock, freezegun.

**Documentación detallada:** `docs/pruebas/plan-pruebas-detallado.md` — contiene el plan de pruebas completo con descripción de cada test, qué valida, y la arquitectura de pruebas.

```bash
# Frontend
cd frontend
npm run lint
npm run build
```

---

## Tecnologías

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React | 19.2.x |
| Frontend | Vite | 8.1.x |
| Frontend | Tailwind CSS | 4.3.x |
| Frontend | React Router | 7.18.x |
| Frontend | Axios | 1.18.x |
| Frontend | Lucide React (iconos) | 1.21.x |
| Frontend | Recharts (gráficos) | 3.9.x |
| Frontend | Oxlint (linter) | 1.69.x |
| Backend | Django | 4.2.11 |
| Backend | Django REST Framework | 3.17.1 |
| Backend | SimpleJWT | 5.3.0 |
| Backend | django-filter | 23.5 |
| Backend | django-cors-headers | 4.9.0 |
| Backend | boto3 (AWS SDK) | 1.43.x |
| Backend | ReportLab (PDF) | 4.0.7 |
| Backend | openpyxl (Excel) | 3.1.2 |
| Backend | Pillow (imágenes) | 10.4.0 |
| Backend | drf-yasg (Swagger) | 1.21.7 |
| Backend | psutil (métricas host) | 6.1.1 |
| Backend | docker (SDK Docker) | 7.1.0 |
| Backend | psycopg2 (SQL directa) | 2.9.9 |
| Base de datos | PostgreSQL | 15 |
| Infraestructura | Docker / docker-compose | — |
| Gateway | Nginx | latest |
| Facial | AWS Rekognition | — |
| Email | Brevo API | — |

---

## Variables de Entorno

Archivo `.env` en la raíz del proyecto:

```env
# ─── Base de Datos ──────────────────────────────────────
DB_NAME=sacarf_db
DB_USER=sacarf_user
DB_PASSWORD=
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ─── AWS Rekognition + S3 ───────────────────────────────
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=sacarf-images
REKOGNITION_COLLECTION_ID=sacarf_faces

# ─── Brevo (Correo) ─────────────────────────────────────
BREVO_API_KEY=
BREVO_FROM_EMAIL=
BREVO_FROM_NAME=SACARF
DEFAULT_FROM_EMAIL=
PASSWORD_RESET_TIMEOUT=1800

# ─── Frontend ───────────────────────────────────────────
FRONTEND_URL=http://localhost:5173

# ─── Monitoreo ─────────────────────────────────────────
MONITORING_HEALTHCHECK_TIMEOUT=3
```

---

## API Endpoints

### A través del Gateway (`http://localhost:8000`)

| Método | Ruta | Servicio |
|--------|------|----------|
| POST | `/api/usuario/token/` | usuario |
| POST | `/api/usuario/token/refresh/` | usuario |
| GET/POST | `/api/usuario/usuarios/` | usuario |
| GET | `/api/usuario/usuarios/me/` | usuario |
| PATCH | `/api/usuario/usuarios/perfil/` | usuario |
| POST | `/api/usuario/usuarios/register/` | usuario |
| POST | `/api/usuario/usuarios/cambiar-password/` | usuario |
| POST | `/api/usuario/usuarios/solicitar-restablecimiento/` | usuario |
| POST | `/api/usuario/usuarios/restablecer-password/` | usuario |
| GET/POST | `/api/academico/carreras/` | academico |
| GET/POST | `/api/academico/ciclos/` | academico |
| GET/POST | `/api/academico/materias/` | academico |
| GET/POST | `/api/academico/horarios/` | academico |
| GET/POST | `/api/academico/matriculas/` | academico |
| GET | `/api/academico/matriculas/mis_materias/` | academico |
| GET | `/api/asistencia/asistencias/` | asistencia |
| POST | `/api/asistencia/asistencias/registrar/` | asistencia |
| GET | `/api/asistencia/asistencias/por_estudiante/` | asistencia |
| GET | `/api/asistencia/asistencias/por_materia/` | asistencia |
| POST | `/api/asistencia/justificaciones/` | asistencia |
| POST | `/api/asistencia/justificaciones/aprobar/` | asistencia |
| POST | `/api/asistencia/registro-facial/registrar_rostro/` | asistencia |
| GET | `/api/reportes/reportes/` | reportes |
| POST | `/api/reportes/reportes/generar/` | reportes |
| GET | `/api/reportes/reportes/:id/descargar/` | reportes |
| GET | `/api/reportes/reportes/tipos/` | reportes |
| GET | `/api/monitoring/salud/` | monitoring |
| GET | `/api/monitoring/infraestructura/` | monitoring |
| GET | `/api/monitoring/backend/` | monitoring |
| GET | `/api/monitoring/base-datos/` | monitoring |
| GET | `/api/monitoring/negocio/` | monitoring |
| GET | `/api/monitoring/resumen/` | monitoring |
| GET | `/api/monitoring/health/` | monitoring |
| GET | `/api/monitoring/auditoria/` | monitoring |
| GET | `/api/monitoring/auditoria/resumen/` | monitoring |
| GET | `/swagger/` | usuario |
| GET | `/redoc/` | usuario |
| GET | `/admin/` | usuario |

---

## Flujo de Reconocimiento Facial

### 1. Registro Facial (una sola vez)
```
Estudiante → /registro-rostro → toma selfie → backend:
  1. Decodifica imagen base64
  2. Llama a Rekognition.IndexFaces(CollectionId, Image, ExternalImageId=user.id)
  3. Crea RegistroFacial(face_id, estudiante)
  4. Sube imagen de referencia a S3 (referencias/{user.id}/{uuid}.jpg)
  5. Actualiza foto_referencia_url del usuario
```

### 2. Ver Materias del Día
```
GET /api/academico/matriculas/mis_materias/
  1. Filtra matrículas activas del estudiante autenticado
  2. Para cada matrícula, obtiene materias del ciclo activo
  3. Filtra horarios por día de la semana actual
  4. Por cada horario, verifica si ya existe Asistencia
  5. Retorna: tiene_registro_facial + lista de materias con horarios
```

### 3. Marcar Asistencia
```
Estudiante → presiona "Marcar" → toma selfie → POST /api/asistencia/asistencias/registrar/
  1. Decodifica imagen base64
  2. Busca rostro en Rekognition: SearchFacesByImage(CollectionId, Image, Threshold=85%)
  3. Si confianza < 85% → rechaza
  4. Si ExternalImageId != estudiante.id → rechaza
  5. Sube imagen a S3 (asistencias/{anio}/{mes}/{uuid}.jpg)
  6. Calcula estado:
     - hora_actual <= hora_inicio + tolerancia → PRESENTE
     - hora_actual <= hora_inicio + 2*tolerancia → TARDE
     - después → AUSENTE (bloqueado)
  7. Crea Reconocimiento + Asistencia en transacción atómica
```

### 4. Justificación
```
Estudiante → POST /api/asistencia/justificaciones/ (motivo, asistencia_id)
Docente → POST /api/asistencia/justificaciones/aprobar/ (justificacion_id, aprobar, comentario)
  1. Si aprueba: estado JUSTIFICADO, asistencia pasa a JUSTIFICADO
  2. Si rechaza: justificación queda RECHAZADA, asistencia mantiene su estado
```

---

## Sistema de Auditoría

Todos los microservicios registran automáticamente operaciones CRUD en la tabla centralizada `monitoring_registroauditoria`. El mecanismo tiene dos partes:

### AuditoriaMixin (automático)

Cada ViewSet que hereda `AuditoriaMixin` registra automáticamente CREATE/UPDATE en `perform_create`/`perform_update`, y DELETE en `perform_destroy`:

```python
from shared.audit import AuditoriaMixin

class MateriaViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    auditoria_servicio = 'academico'
    auditoria_modelo = 'Materia'
    ...
```

### registrar_auditoria() (explícito)

Para acciones personalizadas (`@action`) que no pasan por `perform_create`/`update`/`destroy`, se llama directamente:

```python
from shared.audit import registrar_auditoria

registrar_auditoria(
    usuario_id=user.id,
    usuario_nombre=user.email,
    accion='CREATE',
    servicio='usuario',
    modelo='Usuario',
    registro_id=usuario.id,
    descripcion=f"Registro nuevo usuario {usuario.email}",
    datos_modificados={'email': usuario.email, 'rol': usuario.rol},
    ip_origen=_obtener_ip(request),
)
```

### Tabla de auditoría

Los campos de `monitoring_registroauditoria`:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| usuario_id | Integer | ID del usuario que realizó la acción |
| usuario_nombre | String | Email o nombre del usuario |
| accion | String | CREATE, UPDATE o DELETE |
| servicio | String | usuario, academico, asistencia, reportes |
| modelo | String | Nombre del modelo afectado |
| registro_id | String | PK del registro afectado |
| descripcion | String | Descripción legible de la acción |
| datos_modificados | JSON | Snapshot de cambios (antes/después) |
| ip_origen | String | IP del cliente |
| fecha_hora | DateTime | Timestamp automático |

---

## Documentación de Pruebas

El directorio `docs/pruebas/` contiene el plan detallado y los informes generados:

| Archivo | Descripción |
|---------|-------------|
| `plan-pruebas-detallado.md` | Plan de pruebas completo — 339 tests con descripción, validación y arquitectura |
| `shared.docx` | Informe del módulo compartido (58 tests) |
| `usuario.docx` | Informe del módulo usuario (87 tests) |
| `academico.docx` | Informe del módulo académico (77 tests) |
| `asistencia.docx` | Informe del módulo asistencia (55 tests) |
| `reportes.docx` | Informe del módulo reportes (34 tests) |
| `monitoring.docx` | Informe del módulo monitorización (28 tests) |
| `informe-global.docx` | Informe consolidado con todos los módulos |
| `resumen-ejecutivo.docx` | Resumen ejecutivo con resultados y tecnología |

---

## Documentación de la API

La API está documentada automáticamente con `drf-yasg`, servida por `usuario-service` a través del gateway:

- **Swagger UI**: `http://localhost:8000/swagger/`
- **Redoc**: `http://localhost:8000/redoc/`

La documentación incluye todos los endpoints, parámetros, modelos de request/response y esquemas de autenticación JWT.
