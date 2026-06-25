# SACARF — Sistema de Asistencia con Reconocimiento Facial

**Universidad Nacional de Loja**

Sistema web para el registro de asistencia de estudiantes mediante reconocimiento facial, gestión académica (carreras, ciclos, materias, horarios) y generación de reportes.

---

## Arquitectura

```
┌─────────────────────┐     ┌──────────────────────┐
│   React + Vite      │◄───►│   Django REST API    │
│   (frontend:5173)   │     │   (backend:8000)      │
└─────────────────────┘     └───────┬──────────────┘
                                    │
                           ┌────────▼────────┐
                           │   PostgreSQL    │
                           │   (db:5432)     │
                           └─────────────────┘
```

- **Frontend**: React 18 + Vite + Tailwind CSS + React Router
- **Backend**: Django 5 + Django REST Framework + SimpleJWT
- **Base de datos**: PostgreSQL
- **Contenedores**: Docker / docker-compose
- **Reconocimiento facial**: AWS Rekognition (S3 + Rekognition)
- **Correo**: Brevo API (envío de enlaces de recuperación)

---

## Estructura del proyecto

```
sacarf/
├── sacarf/                        # Configuración principal de Django
│   ├── settings.py                # Configuración global (DB, JWT, CORS, etc.)
│   └── urls.py                    # Ruteo principal (/api/usuario/, /api/academico/, etc.)
├── apps/
│   ├── usuario/                   # Gestión de usuarios y autenticación
│   │   ├── models.py              # Usuario, PasswordResetToken
│   │   ├── views.py               # UsuarioViewSet (CRUD, registro, perfil, recuperación)
│   │   ├── serializers.py         # Validación de datos (contraseña fuerte, etc.)
│   │   ├── authentication.py      # JWT + autenticación por usuario o email
│   │   ├── permissions.py         # IsAdminForMutation (solo admin crea/edita/elimina)
│   │   ├── email_service.py       # Envío de correos vía Brevo API
│   │   └── urls.py                # Rutas: token/, usuarios/, restablecimiento
│   ├── academico/                 # Gestión académica
│   │   ├── models.py              # Carrera, Ciclo, Materia, Horario
│   │   ├── views.py               # ViewSets con IsAdminForMutation
│   │   ├── serializers.py         # Validaciones de fechas y horas
│   │   └── urls.py                # Rutas: carreras/, ciclos/, materias/, horarios/
│   ├── asistencia/                # Registro de asistencia facial
│   │   ├── models.py              # Asistencia, Justificacion, Reconocimiento, RegistroFacial
│   │   ├── views.py               # AsistenciaViewSet, JustificacionViewSet, etc.
│   │   ├── serializers.py         # Validación de horarios, duplicados, etc.
│   │   ├── services.py            # Integración con AWS Rekognition
│   │   └── urls.py                # Rutas: asistencias/, justificaciones/, etc.
│   └── reportes/                  # Generación de reportes
│       ├── models.py              # Reporte (PDF/Excel/Dashboard)
│       └── views.py               # ReporteViewSet
├── Dockerfile
├── manage.py
└── requirements.txt

frontend/
├── src/
│   ├── pages/
│   │   ├── Login.jsx              # Inicio de sesión (usuario o email + contraseña)
│   │   ├── Dashboard.jsx          # Panel principal con estadísticas
│   │   ├── RecuperarPassword.jsx  # Recuperación de contraseña por enlace
│   │   ├── usuarios/
│   │   │   ├── UsuariosList.jsx   # CRUD de usuarios (solo admin)
│   │   │   └── MiPerfil.jsx       # Edición de perfil personal
│   │   ├── academico/
│   │   │   ├── CarrerasList.jsx   # CRUD carreras (solo admin)
│   │   │   ├── CiclosList.jsx     # CRUD ciclos (solo admin)
│   │   │   ├── MateriasList.jsx   # CRUD materias (solo admin)
│   │   │   └── HorariosList.jsx   # CRUD horarios (solo admin)
│   │   ├── asistencia/
│   │   │   └── AsistenciaList.jsx # Registro y consulta de asistencias
│   │   └── reportes/
│   │       └── ReportesList.jsx   # Generación de reportes
│   ├── components/
│   │   ├── Layout.jsx             # Layout principal con sidebar
│   │   ├── DataTable.jsx          # Tabla genérica con búsqueda y paginación
│   │   └── FormModal.jsx          # Modal genérico para formularios
│   ├── contexts/
│   │   ├── AuthContext.jsx        # Contexto de autenticación (login, logout, refresh)
│   │   └── ToastContext.jsx       # Sistema de notificaciones toast
│   └── api/
│       └── axios.js               # Cliente axios con interceptor JWT
├── Dockerfile
└── package.json

docker-compose.yml                 # Orquestación de contenedores
```

---

## Modelos de datos y relaciones

### App `usuario`

| Modelo | Campos | Descripción |
|--------|--------|-------------|
| **Usuario** | `username`, `email`, `password`, `first_name`, `last_name`, `cedula`, `telefono`, `rol` (ADMIN/DOCENTE/ESTUDIANTE), `foto_referencia_url`, `is_active` | Usuario del sistema, hereda de `AbstractUser`. El campo `is_active` se usa para desactivar (no eliminar) usuarios. |
| **PasswordResetToken** | `email`, `token`, `created_at`, `is_used` | Token de un solo uso para restablecer contraseña. Expira según `PASSWORD_RESET_TIMEOUT` (30s por defecto). |

### App `academico`

| Modelo | Campos | Relaciones |
|--------|--------|------------|
| **Carrera** | `codigo` (unique), `nombre`, `descripcion`, `duracion` (semestres), `modalidad` (VIRTUAL/PRESENCIAL/HIBRIDA) | — |
| **Ciclo** | `num`, `fecha_inicio`, `fecha_fin`, `estado` (ACTIVO/FINALIZADO) | FK → `Carrera` (unique_together: `num` + `carrera`) |
| **Materia** | `codigo` (unique), `nombre`, `descripcion`, `creditos`, `horas_semanales` | FK → `Carrera`, FK → `Ciclo`, FK → `Usuario` (docente, con `limit_choices_to={'rol': 'DOCENTE'}`) |
| **Horario** | `dia_semana`, `hora_inicio`, `hora_fin`, `minutos_tolerancia`, `aula` | FK → `Materia`. Validación: `hora_fin > hora_inicio` y sin solapamientos. |

**Jerarquía**: `Carrera` → `Ciclo` → `Materia` → `Horario`

### App `asistencia`

| Modelo | Campos | Relaciones |
|--------|--------|------------|
| **RegistroFacial** | `face_id`, `collection_id`, `fecha_registro`, `estado` | OneToOne → `Usuario` (estudiante). Almacena el ID del rostro en AWS Rekognition. |
| **Reconocimiento** | `fecha_hora`, `resultado`, `confianza`, `ubicacion`, `imagen_url` | FK → `Usuario` (estudiante), FK → `RegistroFacial`. Cada intento de reconocimiento facial. |
| **Asistencia** | `fecha`, `hora_registro`, `estado` (PRESENTE/AUSENTE/TARDE/JUSTIFICADO), `confianza` | FK → `Usuario` (estudiante), FK → `Horario`, OneToOne → `Reconocimiento`. Unique: `(estudiante, horario, fecha)`. |
| **Justificacion** | `motivo`, `fecha_solicitud`, `documento_url`, `estado` (PENDIENTE/APROBADA/RECHAZADA), `comentario_docente` | OneToOne → `Asistencia`, FK → `Usuario` (estudiante), FK → `Usuario` (docente_aprueba). |

**Flujo de asistencia**:
1. Estudiante se registra facialmente (guarda rostro en AWS Rekognition) → `RegistroFacial`
2. En hora de clase, envía selfie → se busca en Rekognition → se crea `Reconocimiento`
3. Si confianza ≥ 85% y coincide con el estudiante → se crea `Asistencia` (PRESENTE o TARDE según tolerancia)
4. Si falta, puede justificar → se crea `Justificacion` (PENDIENTE), docente aprueba/rechaza

### App `reportes`

| Modelo | Campos | Descripción |
|--------|--------|-------------|
| **Reporte** | `tipo` (POR_ESTUDIANTE/POR_MATERIA/POR_CICLO/GENERAL), `parametros` (JSON), `formato` (PDF/EXCEL/DASHBOARD), `archivo_url` | Reportes generados, asociados al usuario que los generó. |

---

## Permisos

| Rol | Usuarios | Académico | Asistencia | Perfil propio |
|-----|----------|-----------|------------|---------------|
| **ADMIN** | CRUD completo (desactivar) | CRUD completo | Lectura | Edición |
| **DOCENTE** | Solo lectura propia | Solo lectura | Gestión de justificaciones + ver asistencias de sus materias | Edición |
| **ESTUDIANTE** | Solo lectura propia | Solo lectura | Registrar asistencia + justificar | Edición |

El permiso `IsAdminForMutation` (en `usuario/permissions.py`) restringe las acciones `create`, `update`, `partial_update` y `destroy` solo a usuarios con `rol == 'ADMIN'`; el resto solo pueden leer (`list`, `retrieve`).

---

## Autenticación

- **JWT** via `rest_framework_simplejwt` (access token: 8h, refresh: 1d)
- **Login** con username **o** email gracias al backend `EmailOrUsernameModelBackend`
- **Recuperación de contraseña**:
  1. Usuario ingresa email → se genera token de 30s
  2. Se envía enlace por Brevo API → usuario hace clic
  3. Ingresa nueva contraseña (mín. 8 chars, 1 mayúscula, 1 número, 1 símbolo)
- **CustomJWTAuthentication**: captura tokens expirados y retorna `None` (anónimo) en lugar de 401, permitiendo que los permisos decidan

---

## Cómo correr el proyecto

### Requisitos

- Docker y Docker Compose
- Node.js 18+ (para desarrollo local del frontend)
- Python 3.10+ (para desarrollo local del backend)

### Con Docker (recomendado)

```bash
# 1. Clonar y entrar
git clone <repo>
cd sacarf

# 2. Configurar variables de entorno
#    Editar .env con los valores correctos (DB, Brevo API key, etc.)

# 3. Construir y levantar
docker-compose up -d --build

# 4. Ejecutar migraciones
docker-compose exec web python manage.py migrate

# 5. Crear superusuario (opcional)
docker-compose exec web python manage.py createsuperuser

# 6. Acceder
#    Frontend: http://localhost:5173
#    Backend:  http://localhost:8000
#    Admin:    http://localhost:8000/admin/
```

### Desarrollo local (sin Docker)

**Backend:**

```bash
cd sacarf
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar PostgreSQL y crear la base de datos
# Editar .env con DB_HOST=localhost

python manage.py migrate
python manage.py runserver 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Variables de entorno (`.env`)

```
# Base de datos
DB_NAME=sacarf_db
DB_USER=sacarf_user
DB_PASSWORD=sacarf_2026
DB_HOST=db
DB_PORT=5432

# Django
SECRET_KEY=tu-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Brevo (email)
BREVO_API_KEY=xkeysib-...
BREVO_FROM_EMAIL=no-reply@ejemplo.com
BREVO_FROM_NAME=SACARF

# Frontend
FRONTEND_URL=http://localhost:5173

# AWS (reconocimiento facial)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
AWS_S3_BUCKET=sacarf-facial
```

---

## API Endpoints principales

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/usuario/token/` | Obtener JWT (username o email + password) |
| POST | `/api/usuario/token/refresh/` | Refrescar JWT |
| POST | `/api/usuario/usuarios/register/` | Registro de usuario |
| POST | `/api/usuario/usuarios/solicitar-restablecimiento/` | Solicitar enlace de recuperación |
| POST | `/api/usuario/usuarios/restablecer-password/` | Restablecer contraseña con token |

### Usuarios
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/usuario/usuarios/` | Listar usuarios (admin: todos; otros: solo propio) |
| GET | `/api/usuario/usuarios/me/` | Datos del usuario actual |
| PATCH | `/api/usuario/usuarios/perfil/` | Actualizar perfil propio (nombres, cédula, teléfono, foto) |
| POST | `/api/usuario/usuarios/cambiar-password/` | Cambiar contraseña |
| DELETE | `/api/usuario/usuarios/:id/` | Desactivar usuario (soft delete, solo admin) |

### Académico
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/api/academico/carreras/` | CRUD carreras (solo admin para POST/PUT/DELETE) |
| GET/POST | `/api/academico/ciclos/` | CRUD ciclos |
| GET/POST | `/api/academico/materias/` | CRUD materias |
| GET/POST | `/api/academico/horarios/` | CRUD horarios |

### Asistencia
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/asistencia/asistencias/registrar/` | Registrar asistencia con foto |
| GET | `/api/asistencia/asistencias/` | Listar asistencias |
| POST | `/api/asistencia/justificaciones/` | Crear justificación |
| POST | `/api/asistencia/justificaciones/aprobar/` | Aprobar/rechazar justificación (docente) |
| POST | `/api/asistencia/registro-facial/registrar-rostro/` | Registrar rostro en AWS Rekognition |

---

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios |
| Backend | Django 5, Django REST Framework, SimpleJWT, django-filter, drf-yasg |
| Base de datos | PostgreSQL |
| Reconocimiento facial | AWS Rekognition + S3 |
| Correo | Brevo API (transactional email) |
| Contenedores | Docker, docker-compose |
