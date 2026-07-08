# SACARF - Modulo Usuario

Documentacion focalizada unicamente en el modulo `usuario`y `academico` para facilitar el versionado y evitar referencias a otros servicios del proyecto.

## Alcance

Este repositorio documenta el servicio de usuarios, autenticacion y recuperacion de contrasena. Asi como la creacion de carreras, materias, matriculas y horarios.
## Arquitectura
```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx Gateway                        │
│                      (puerto 8000)                          │
│  /api/usuario/*     → upstream usuario    :8001             │
│  /api/academico/*   → upstream academico  :8002             │
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

┌────────────────┐                                          ┌────────────────┐
│  usuario-svc   │                                          │  academico-svc │
│  Django :8001  │                                          │  Django :8002  │
│                │                                          │                │
│  /api/usuario/ │                                          │ /api/academico/│
└───────┬────────┘                                          └───────┬────────┘
        │                                                           │
        └───────────────────────────────────────────────────────────┘
                                    │
                          ┌─────────▼──────────┐
                          │   PostgreSQL 15     │
                          │   (db :5432)        │
                          └────────────────────┘
```

## Servicio usuario

| Propiedad | Valor |
|-----------|-------|
| Puerto | 8001 |
| Settings | `services/usuario/usuario/settings.py` |
| URLConf | `services/usuario/usuario/urls.py` |

## Endpoints

- `POST /api/usuario/token/` - Login JWT
- `POST /api/usuario/token/refresh/` - Refrescar token
- `GET /api/usuario/usuarios/` - Listar usuarios
- `POST /api/usuario/usuarios/` - Crear usuario
- `GET /api/usuario/usuarios/me/` - Perfil del usuario autenticado
- `PUT/PATCH /api/usuario/usuarios/perfil/` - Actualizar perfil propio
- `POST /api/usuario/usuarios/register/` - Registro publico
- `POST /api/usuario/usuarios/cambiar-password/` - Cambiar contrasena
- `POST /api/usuario/usuarios/solicitar-restablecimiento/` - Solicitar restablecimiento
- `POST /api/usuario/usuarios/restablecer-password/` - Restablecer contrasena

## Responsabilidad

Gestion de usuarios, autenticacion JWT, actualizacion de perfil, carga de foto de referencia, control de intentos fallidos de login y recuperacion de contrasena por correo.

## Ejecucion local

```bash
cd sacarf
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python services/usuario/manage.py runserver 8001
```

## Estructura relacionada

- `services/usuario/` - Proyecto Django del modulo usuario
- `sacarf/apps/usuario/` - App principal de usuarios
- `shared/` - Utilidades compartidas usadas por el servicio


## academico-service

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

## Versionado

Esta documentacion queda acotada al modulo `usuario` y `academico` para trabajar cambios, historial y revisiones sin arrastrar la descripcion de otros modulos.

