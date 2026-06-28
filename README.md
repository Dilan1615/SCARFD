# SACARF — Sistema de Asistencia con Reconocimiento Facial

**Universidad Nacional de Loja**

Sistema web para el registro de asistencia de estudiantes mediante reconocimiento facial, gestión académica (carreras, ciclos, materias, horarios, matrículas) y generación de reportes.

---

## Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Características](#características)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Modelos de Datos y Relaciones](#modelos-de-datos-y-relaciones)
- [Permisos y Roles](#permisos-y-roles)
- [Autenticación](#autenticación)
- [Frontend: Componentes y Rutas](#frontend-componentes-y-rutas)
- [API Endpoints](#api-endpoints)
- [Flujo de Reconocimiento Facial](#flujo-de-reconocimiento-facial)
- [Flujo de Recuperación de Contraseña](#flujo-de-recuperación-de-contraseña)
- [Cómo Correr el Proyecto](#cómo-correr-el-proyecto)
- [Variables de Entorno](#variables-de-entorno)
- [Documentación de la API](#documentación-de-la-api)

---

## Arquitectura

```
┌──────────────────────┐     ┌──────────────────────────┐
│   React + Vite       │◄───►│   Django REST API        │
│   (frontend :5173)    │     │   (backend :8000)        │
│                      │     │                          │
│   Proxy Vite:        │     │   JWT (SimpleJWT)        │
│   /api → :8000       │     │   CORS abierto           │
└──────────────────────┘     └───────┬──────────────────┘
                                      │
                            ┌─────────▼──────────┐
                            │   PostgreSQL 15     │
                            │   (db :5432)        │
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

- **Frontend**: React 19 + Vite 8 + Tailwind CSS 4 + React Router 7 + Axios + Lucide React + Recharts
- **Backend**: Django 4.2 + Django REST Framework 3.17 + SimpleJWT 5.3 + django-filter 23.5
- **Base de datos**: PostgreSQL 15 (SQLite en desarrollo local sin Docker)
- **Reconocimiento facial**: AWS Rekognition (`IndexFaces` + `SearchFacesByImage`) + S3 para almacenamiento de imágenes
- **Correo**: Brevo API (envío de enlaces de recuperación de contraseña)
- **Contenedores**: Docker + docker-compose
- **Documentación API**: Swagger (drf-yasg) en `/swagger/` y Redoc en `/redoc/`

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
| Base de datos | PostgreSQL | 15 |
| Infraestructura | Docker / docker-compose | — |
| Facial | AWS Rekognition | — |
| Email | Brevo API | — |

---

## Características

### Gestión de Usuarios
- **Tres roles**: ADMIN, DOCENTE, ESTUDIANTE
- **Autenticación JWT** (access token: 8h, refresh: 1d)
- **Login por email o username** indistintamente
- **Registro de usuarios** con foto de perfil opcional
- **Recuperación de contraseña** mediante enlace enviado por correo (token con expiración de 30 min)
- **Soft delete**: los administradores desactivan usuarios (`is_active = False`) en lugar de eliminarlos
- **Bloqueo por intentos fallidos**: 5 intentos fallidos → bloqueo de 30 minutos

### Gestión Académica
- **Carreras**: código único, nombre, descripción, duración (semestres), modalidad (VIRTUAL/PRESENCIAL/HÍBRIDA)
- **Ciclos**: asociados a una carrera, con fecha de inicio/fin y estado (ACTIVO/FINALIZADO)
- **Materias**: asociadas a carrera + ciclo + docente, con créditos y horas semanales
- **Horarios**: por materia, día de la semana, hora inicio/fin, aula y minutos de tolerancia
- **Matrículas**: vinculan estudiante + carrera + ciclo, con estado ACTIVA/FINALIZADA

### Registro de Asistencia Facial
- **Registro facial único**: el estudiante se toma una selfie que se indexa en AWS Rekognition
- **Marcado de asistencia**: selfie → `SearchFacesByImage` → si confianza ≥ 85% y coincide con el `ExternalImageId` del estudiante, se registra
- **Cálculo automático de estado**: PRESENTE (dentro de la tolerancia), TARDE (después de la tolerancia), AUSENTE (fuera del tiempo máximo)
- **Justificaciones**: estudiantes pueden justificar inasistencias; docentes aprueban/rechazan

### Reportes
- **Tipos**: por estudiante, por materia, por ciclo, general
- **Formatos**: PDF (ReportLab) y Excel (openpyxl)
- **Filtros**: por fechas, estudiante, materia, ciclo

---

## Estructura del Proyecto

```
sacarf/
├── sacarf/                          # Configuración principal de Django
│   ├── settings.py                  # Configuración global (DB, JWT, CORS, AWS, email)
│   ├── urls.py                      # Ruteo principal (/api/usuario/, /api/academico/, etc.)
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── usuario/                     # Gestión de usuarios y autenticación
│   │   ├── models.py                # Usuario (AbstractUser sin username), PasswordResetToken
│   │   ├── views.py                 # UsuarioViewSet (CRUD, register, me, perfil, cambiar_password)
│   │   ├── serializers.py           # Validación de datos (contraseña fuerte, etc.)
│   │   ├── authentication.py        # EmailOrUsernameModelBackend + CustomJWTAuthentication
│   │   ├── permissions.py           # IsAdminForMutation (solo admin crea/edita/elimina)
│   │   ├── email_service.py         # Envío de correos vía Brevo API
│   │   ├── login_view.py            # Vista personalizada de login con control de intentos fallidos
│   │   └── urls.py                  # Rutas: token/, usuarios/, restablecimiento/
│   │
│   ├── academico/                   # Gestión académica
│   │   ├── models.py                # Carrera, Ciclo, Materia, Horario, Matricula
│   │   ├── views.py                 # ViewSets con IsAdminForMutation + mis_materias
│   │   ├── serializers.py           # Validaciones de fechas y horas
│   │   └── urls.py                  # CRUD carreras/, ciclos/, materias/, horarios/, matriculas/
│   │
│   ├── asistencia/                  # Registro de asistencia facial
│   │   ├── models.py                # Asistencia, Justificacion, Reconocimiento, RegistroFacial
│   │   ├── views.py                 # AsistenciaViewSet, JustificacionViewSet, etc.
│   │   ├── serializers.py           # Validación de horarios, duplicados, días, etc.
│   │   ├── services.py              # AwsRekognitionService (Rekognition + S3)
│   │   └── urls.py                  # Rutas: asistencias/, justificaciones/, registro-facial/
│   │
│   └── reportes/                    # Generación de reportes
│       ├── models.py                # Reporte (PDF/Excel/Dashboard)
│       ├── views.py                 # ReporteViewSet (generar, descargar)
│       ├── serializers.py           # Serializers para generación de reportes
│       ├── services.py              # ReporteService (PDF con ReportLab, Excel con openpyxl)
│       └── urls.py                  # Rutas: reportes/
│
├── media/
│   └── fotos/                       # Imágenes subidas por usuarios (local, no Docker)
│
├── Dockerfile
├── manage.py
└── requirements.txt

frontend/
├── src/
│   ├── main.jsx                     # Entry point con BrowserRouter
│   ├── App.jsx                      # Definición de rutas
│   ├── App.css / index.css          # Estilos globales + Tailwind
│   │
│   ├── api/
│   │   └── axios.js                 # Cliente Axios con interceptor JWT (refresh automático)
│   │
│   ├── contexts/
│   │   ├── AuthContext.jsx          # Contexto de autenticación (login, logout, refresh, usuario actual)
│   │   └── ToastContext.jsx         # Sistema de notificaciones toast
│   │
│   ├── components/
│   │   ├── Layout.jsx               # Layout principal con sidebar responsivo (role-based)
│   │   ├── DataTable.jsx            # Tabla genérica con búsqueda, filtros y paginación
│   │   └── FormModal.jsx            # Modal genérico para formularios CRUD
│   │
│   ├── pages/                       # Páginas (vistas completas)
│   │   ├── Login.jsx                # Inicio de sesión (email + contraseña)
│   │   ├── Dashboard.jsx            # Panel principal con tarjetas de resumen y gráficos (Recharts)
│   │   ├── RecuperarPassword.jsx    # Formulario de recuperación de contraseña
│   │   │
│   │   ├── usuarios/
│   │   │   ├── UsuariosList.jsx     # CRUD de usuarios (solo admin)
│   │   │   └── MiPerfil.jsx         # Edición de perfil personal (foto, datos)
│   │   │
│   │   ├── academico/
│   │   │   ├── CarrerasList.jsx     # CRUD carreras
│   │   │   ├── CiclosList.jsx       # CRUD ciclos
│   │   │   ├── MateriasList.jsx     # CRUD materias
│   │   │   ├── HorariosList.jsx     # CRUD horarios
│   │   │   └── MatriculasList.jsx   # CRUD matrículas
│   │   │
│   │   ├── asistencia/
│   │   │   ├── AsistenciaHoy.jsx    # Asistencia del día con cámara (estudiante)
│   │   │   ├── AsistenciaList.jsx   # Historial de asistencias (admin/docente)
│   │   │   └── RegistroRostro.jsx   # Registro facial inicial (estudiante, una vez)
│   │   │
│   │   └── reportes/
│   │       └── ReportesList.jsx     # Generación y descarga de reportes
│   │
│   ├── assets/                      # Imágenes estáticas
│   └── public/
│       ├── favicon.svg
│       ├── icons.svg
│       └── unl-logo.png
│
├── index.html
├── vite.config.js                   # Proxy /api → localhost:8000, Tailwind plugin
├── package.json
├── .oxlintrc.json
└── Dockerfile

docker-compose.yml                   # Orquestación: db (PostgreSQL) + web (Django)
entrypoint.sh                        # Script de inicio: migraciones + superusuario por defecto
```

---

## Modelos de Datos y Relaciones

### App `usuario` — Usuarios y Autenticación

| Modelo | Campos | Detalles |
|--------|--------|----------|
| **Usuario** | `email` (unique, login field) | Hereda de `AbstractUser`. `username = None`. Manager personalizado (`UsuarioManager`) que no requiere username. |
| | `cedula` (unique, max 10) | Cédula de identidad |
| | `telefono` (max 15, opcional) | Número de contacto |
| | `rol` (ADMIN/DOCENTE/ESTUDIANTE) | Control de permisos |
| | `foto_referencia_url` (URL, opcional) | Foto de perfil |
| | `intentos_fallidos` (int, default 0) | Contador para bloqueo por fuerza bruta |
| | `bloqueado_hasta` (datetime, nullable) | Fin del bloqueo temporal |
| | `is_active` (bool) | Soft delete: admin desactiva, no elimina |
| **PasswordResetToken** | `email` | Email del usuario que solicita restablecimiento |
| | `token` (unique, max 64) | Token generado con `secrets.token_urlsafe(32)` |
| | `created_at` (auto) | Fecha de creación |
| | `is_used` (bool, default False) | Marca de un solo uso |

**Relaciones**: `Usuario` → OneToOne `registro_facial` (asistencia), FK `asistencias`, FK `reconocimientos`, FK `matriculas`, FK `materias_dictadas` (docente).

### App `academico` — Gestión Académica

| Modelo | Campos | Relaciones |
|--------|--------|------------|
| **Carrera** | `codigo` (unique, max 20), `nombre` (max 100), `descripcion` (text), `duracion` (semestres), `modalidad` (VIRTUAL/PRESENCIAL/HIBRIDA) | — |
| **Ciclo** | `num` (int), `fecha_inicio`, `fecha_fin`, `estado` (ACTIVO/FINALIZADO) | FK → `Carrera`. Unique: `(num, carrera)` |
| **Materia** | `codigo` (unique, max 20), `nombre` (max 100), `descripcion` (text), `creditos`, `horas_semanales` | FK → `Carrera`, FK → `Ciclo`, FK → `Usuario` (docente, `rol=DOCENTE`) |
| **Horario** | `dia_semana` (LUNES–VIERNES), `hora_inicio`, `hora_fin`, `minutos_tolerancia` (default 10), `aula` (max 50) | FK → `Materia`. Validación: `hora_inicio < hora_fin` y sin solapamientos |
| **Matricula** | `fecha_matricula` (auto), `estado` (ACTIVA/FINALIZADA) | FK → `Usuario` (estudiante, `rol=ESTUDIANTE`), FK → `Carrera`, FK → `Ciclo`. Unique: `(estudiante, ciclo)` |

**Jerarquía**: `Carrera` → `Ciclo` → `Materia` → `Horario`

### App `asistencia` — Asistencia Facial

| Modelo | Campos | Relaciones |
|--------|--------|------------|
| **RegistroFacial** | `face_id` (unique, max 100, ID de Rekognition), `collection_id` (default: `sacarf_faces`), `fecha_registro` (auto), `estado` (ACTIVO/INACTIVO) | OneToOne → `Usuario` (estudiante) |
| **Reconocimiento** | `fecha_hora` (auto), `resultado` (bool), `confianza` (float), `ubicacion` (max 100), `imagen_url` (URL, nullable) | FK → `Usuario` (estudiante), FK → `RegistroFacial` (nullable) |
| **Asistencia** | `fecha` (auto), `hora_registro` (auto), `estado` (PRESENTE/AUSENTE/TARDE/JUSTIFICADO), `confianza` (float) | FK → `Usuario` (estudiante), FK → `Horario`, OneToOne → `Reconocimiento`. Unique: `(estudiante, horario, fecha)` |
| **Justificacion** | `motivo` (text), `fecha_solicitud` (auto), `documento_url` (URL, nullable), `estado` (PENDIENTE/APROBADA/RECHAZADA), `comentario_docente` (text) | OneToOne → `Asistencia`, FK → `Usuario` (estudiante), FK → `Usuario` (docente_aprueba, nullable) |

### App `reportes` — Reportes

| Modelo | Campos | Descripción |
|--------|--------|-------------|
| **Reporte** | `tipo` (POR_ESTUDIANTE/POR_MATERIA/POR_CICLO/GENERAL), `formato` (PDF/EXCEL/DASHBOARD), `parametros` (JSON), `archivo_url` (URL, nullable), `nombre` (max 200), `fecha_generacion` (auto) | Asociado al usuario que lo generó (`generado_por`, FK → `Usuario`) |

---

## Permisos y Roles

| Rol | Usuarios | Académico | Asistencia | Reportes |
|-----|----------|-----------|------------|----------|
| **ADMIN** | CRUD completo + desactivar (soft delete) | CRUD completo (carreras, ciclos, materias, horarios, matrículas) | Lectura total + gestión de justificaciones | Generar y descargar todos |
| **DOCENTE** | Solo lectura propia (vía `get_queryset`) | Solo lectura | Gestión de justificaciones de sus materias + ver asistencias de sus clases | Generar y descargar reportes de sus materias |
| **ESTUDIANTE** | Solo lectura propia | Solo lectura (vía endpoint `mis_materias`) | Registrar asistencia facial + justificar propias inasistencias | Sin acceso |

### Permiso `IsAdminForMutation`
- Archivo: `usuario/permissions.py`
- Las acciones `create`, `update`, `partial_update`, `destroy` requieren `rol == 'ADMIN'`
- `list`, `retrieve` disponibles para cualquier usuario autenticado

---

## Autenticación

### JWT con SimpleJWT
- **Access token**: 8 horas de duración
- **Refresh token**: 1 día de duración
- **Header**: `Authorization: Bearer <token>`

### Login con Email o Username
- `authentication.py` → `EmailOrUsernameModelBackend`
- Intenta autenticar primero por email (campo `USERNAME_FIELD`), luego por email explícito
- El frontend envía `email` + `password` indistintamente

### CustomJWTAuthentication
- Captura tokens expirados y retorna `None` en lugar de lanzar 401
- Permite que los permisos decidan cómo manejar usuarios anónimos

### Control de Intentos Fallidos
- `login_view.py`: después de 5 intentos fallidos de login, el usuario se bloquea por 30 minutos
- Se verifica con `usuario.esta_bloqueado()` antes de procesar la autenticación

### Flujo de Login
```
1. Usuario ingresa email + contraseña
2. POST /api/usuario/token/
3. Backend verifica bloqueo → autentica → genera JWT
4. Frontend almacena tokens en localStorage (access_token, refresh_token)
5. Axios interceptor: si 401, intenta refresh; si falla refresh, redirige a login
```

---

## Frontend: Componentes y Rutas

### Configuración de Vite
- Archivo: `frontend/vite.config.js`
- Proxy automático: `/api` → `http://localhost:8000`
- Plugins: `@vitejs/plugin-react` + `@tailwindcss/vite`

### Sistema de Rutas (React Router 7)
```
/login                  → Login.jsx
/recuperar-password     → RecuperarPassword.jsx
/                       → Layout + Dashboard.jsx
/usuarios               → Layout + UsuariosList.jsx (admin)
/mi-perfil              → Layout + MiPerfil.jsx
/carreras               → Layout + CarrerasList.jsx (admin)
/ciclos                 → Layout + CiclosList.jsx (admin)
/materias               → Layout + MateriasList.jsx (admin)
/horarios               → Layout + HorariosList.jsx (admin)
/matriculas             → Layout + MatriculasList.jsx (admin)
/asistencia/hoy         → Layout + AsistenciaHoy.jsx (estudiante)
/asistencia             → Layout + AsistenciaList.jsx (admin/docente)
/registro-rostro        → Layout + RegistroRostro.jsx (estudiante)
/reportes               → Layout + ReportesList.jsx (admin/docente)
```

### Componentes Compartidos

| Componente | Descripción |
|-----------|-------------|
| **Layout.jsx** | Sidebar responsivo con menú según rol. Admin/docente ven panel completo; estudiante ve solo asistencia, perfil y registro facial |
| **DataTable.jsx** | Tabla genérica con búsqueda, paginación, filtros por columna, ordenamiento |
| **FormModal.jsx** | Modal genérico para formularios CRUD con validación |

### Contextos

| Contexto | Descripción |
|----------|-------------|
| **AuthContext.jsx** | Provee `user`, `login()`, `logout()`, `loading`. Persiste sesión en localStorage. Refresca token automáticamente |
| **ToastContext.jsx** | Sistema de notificaciones con `showToast(message, type)` donde type = success/error/info |

### API Client (`api/axios.js`)
- Instancia de Axios con `baseURL` configurada
- Interceptor de request: agrega `Authorization: Bearer <token>`
- Interceptor de response: en 401 intenta refresh automático (usa el refresh token almacenado)
- Si el refresh falla, limpia sesión y redirige a login

---

## API Endpoints

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/usuario/token/` | Obtener JWT (email + password). Controla intentos fallidos y bloqueo |
| POST | `/api/usuario/token/refresh/` | Refrescar JWT |
| POST | `/api/usuario/usuarios/register/` | Registro de usuario (AllowAny) |
| POST | `/api/usuario/usuarios/solicitar-restablecimiento/` | Solicitar enlace de recuperación (AllowAny) |
| POST | `/api/usuario/usuarios/restablecer-password/` | Restablecer contraseña con token (AllowAny) |

### Usuarios
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/usuario/usuarios/` | Listar usuarios (admin: todos; docentes/estudiantes: solo propio) |
| GET | `/api/usuario/usuarios/me/` | Datos del usuario actual |
| PATCH | `/api/usuario/usuarios/perfil/` | Actualizar perfil propio (nombres, cédula, teléfono, foto) |
| POST | `/api/usuario/usuarios/cambiar-password/` | Cambiar contraseña (requiere contraseña actual) |
| DELETE | `/api/usuario/usuarios/:id/` | Desactivar usuario (soft delete, solo admin) |

### Académico
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/api/academico/carreras/` | CRUD carreras (solo admin para POST/PUT/DELETE) |
| GET/POST | `/api/academico/ciclos/` | CRUD ciclos |
| GET/POST | `/api/academico/materias/` | CRUD materias |
| GET/POST | `/api/academico/horarios/` | CRUD horarios |
| GET/POST | `/api/academico/matriculas/` | CRUD matrículas (solo admin) |
| GET | `/api/academico/matriculas/mis_materias/` | **Materias del día del estudiante autenticado** con horarios, estado de asistencia y `tiene_registro_facial` |

### Asistencia
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/asistencia/asistencias/` | Listar asistencias (filtrado por rol) |
| POST | `/api/asistencia/asistencias/registrar/` | Registrar asistencia con foto (Rekognition SearchFacesByImage) |
| GET | `/api/asistencia/asistencias/por_estudiante/` | Asistencias por estudiante |
| GET | `/api/asistencia/asistencias/por_materia/` | Asistencias por materia |
| POST | `/api/asistencia/justificaciones/` | Crear justificación |
| POST | `/api/asistencia/justificaciones/aprobar/` | Aprobar/rechazar justificación (docente) |
| POST | `/api/asistencia/registro-facial/registrar_rostro/` | Indexar rostro en AWS Rekognition (IndexFaces) — una sola vez por estudiante |

### Reportes
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/reportes/reportes/` | Listar reportes generados |
| POST | `/api/reportes/reportes/generar/` | Generar nuevo reporte (admin/docente) |
| GET | `/api/reportes/reportes/:id/descargar/` | Descargar reporte |
| GET | `/api/reportes/reportes/tipos/` | Listar tipos y formatos disponibles |

### Documentación
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/swagger/` | Interfaz Swagger UI |
| GET | `/redoc/` | Interfaz Redoc |
| GET | `/admin/` | Admin de Django |

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
  4. Por cada horario, verifica si ya existe Asistencia (ya_registro, estado_asistencia)
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

## Flujo de Recuperación de Contraseña

```
1. Usuario ingresa email en /recuperar-password
2. POST /api/usuario/usuarios/solicitar-restablecimiento/ { email }
3. Backend:
   a. Genera token con secrets.token_urlsafe(32)
   b. Crea PasswordResetToken(email, token)
   c. Envía email vía Brevo API con enlace:
      {FRONTEND_URL}/recuperar-password?token={token}
   d. El token expira en PASSWORD_RESET_TIMEOUT (30 min por defecto)
4. Usuario hace clic en el enlace → frontend lee token de query params
5. Usuario ingresa nueva contraseña (mín. 8 chars, 1 mayúscula, 1 número, 1 símbolo)
6. POST /api/usuario/usuarios/restablecer-password/ { token, password }
7. Backend:
   a. Verifica token existe, no usado, no expirado
   b. Actualiza contraseña del usuario
   c. Marca token como usado (is_used = True)
```

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

# 3. Construir y levantar
docker-compose up -d --build

# 4. Verificar que los servicios están corriendo
docker-compose ps

# 5. Acceder
#    Frontend: http://localhost:5173
#    Backend:  http://localhost:8000
#    Admin:    http://localhost:8000/admin/
#    Swagger:  http://localhost:8000/swagger/
```

> **Nota**: El `entrypoint.sh` ejecuta migraciones automáticamente y crea un superusuario por defecto:
> - **Email**: admin@sacarf.com
> - **Password**: admin123

### Desarrollo Local (sin Docker)

**Backend:**

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
#    Opción A: PostgreSQL (requiere PostgreSQL instalado)
#      - Crear base de datos: createdb sacarf_db
#      - Editar .env: DB_HOST=localhost, DB_ENGINE=django.db.backends.postgresql
#    Opción B: SQLite (más simple para desarrollo)
#      - Editar .env: DB_ENGINE=django.db.backends.sqlite3
#      - Comentar DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# 4. Ejecutar migraciones
cd sacarf
python manage.py makemigrations
python manage.py migrate

# 5. Crear superusuario
python manage.py shell -c "
from apps.usuario.models import Usuario
Usuario.objects.create_superuser(email='admin@sacarf.com', password='admin123', cedula='0000000000', rol='ADMIN')
"

# 6. Iniciar servidor
python manage.py runserver 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

El frontend estará en `http://localhost:5173` con proxy automático al backend en `http://localhost:8000`.

### Comandos Útiles

```bash
# Backend: ejecutar pruebas
cd sacarf && python manage.py test apps/usuario apps/academico apps/asistencia apps/reportes

# Frontend: linter
cd frontend && npm run lint

# Frontend: build de producción
cd frontend && npm run build

# Docker: ver logs
docker-compose logs -f web

# Docker: ejecutar comando en el contenedor web
docker-compose exec web python manage.py createsuperuser
```

---

## Variables de Entorno

Archivo `.env` en la raíz del proyecto:

```env
# ─── Base de Datos ──────────────────────────────────────
DB_NAME=sacarf_db                     # Nombre de la base de datos
DB_USER=sacarf_user                   # Usuario de la base de datos
DB_PASSWORD=                          # Contraseña de la base de datos
DB_HOST=db                            # Host (db cuando usa Docker, localhost en local)
DB_PORT=5432                          # Puerto de PostgreSQL

# Django
SECRET_KEY=                           # Clave secreta de Django (generar una única)
DEBUG=True                            # True en desarrollo, False en producción
ALLOWED_HOSTS=localhost,127.0.0.1     # Hosts permitidos

# ─── AWS Rekognition + S3 ───────────────────────────────
AWS_ACCESS_KEY_ID=                    # Access Key de AWS
AWS_SECRET_ACCESS_KEY=                # Secret Access Key de AWS
AWS_REGION=us-east-1                  # Región de AWS
AWS_S3_BUCKET=sacarf-images           # Bucket S3 para imágenes
REKOGNITION_COLLECTION_ID=sacarf_faces # Colección de Rekognition

# ─── Brevo (Correo) ─────────────────────────────────────
BREVO_API_KEY=                        # API Key de Brevo
BREVO_FROM_EMAIL=                     # Email remitente
BREVO_FROM_NAME=SACARF                # Nombre del remitente
DEFAULT_FROM_EMAIL=                   # Email por defecto (coincide con BREVO_FROM_EMAIL)
PASSWORD_RESET_TIMEOUT=1800           # Tiempo de expiración del token (1800s = 30 min)

# ─── Frontend ───────────────────────────────────────────
FRONTEND_URL=http://localhost:5173    # URL del frontend (para enlaces en correos)

# ─── Gmail SMTP (alternativa a Brevo) ───────────────────
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=tu-email@gmail.com
# EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
```

### Configuración de AWS

Para que el reconocimiento facial funcione, necesitas:

1. **Crear un bucket S3** (ej: `sacarf-images`) en la región `us-east-1`
2. **Crear una colección en Rekognition** (se crea automáticamente la primera vez que se indexa un rostro)
3. **Crear un usuario IAM** con la siguiente política:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:IndexFaces",
        "rekognition:SearchFacesByImage",
        "rekognition:CreateCollection",
        "rekognition:ListCollections"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::sacarf-images/*"
    }
  ]
}
```

---

## Documentación de la API

La API está documentada automáticamente con `drf-yasg`:

- **Swagger UI**: `http://localhost:8000/swagger/`
- **Redoc**: `http://localhost:8000/redoc/`

La documentación incluye todos los endpoints, parámetros, modelos de request/response y esquemas de autenticación JWT.

---

## Desarrollo

### Estructura de Commits

Este proyecto sigue commits descriptivos en español. Ejemplos:
- `feat: agregar registro facial con AWS Rekognition`
- `fix: validar solapamiento de horarios`
- `refactor: extraer AwsRekognitionService a módulo separado`

### Scripts del Frontend

```bash
npm run dev      # Iniciar servidor de desarrollo
npm run build    # Build de producción
npm run preview  # Preview del build
npm run lint     # Ejecutar oxlint
```

### Pruebas

```bash
# Backend (Django)
cd sacarf
python manage.py test apps/usuario/tests
python manage.py test apps/academico/tests
python manage.py test apps/asistencia/tests
python manage.py test apps/reportes/tests

# Frontend (oxlint ya incluido como linter)
cd frontend
npm run lint
```
