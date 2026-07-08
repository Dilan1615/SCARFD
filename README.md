# SACARF - Modulo Usuario

Documentacion focalizada unicamente en el modulo `usuario` para facilitar el versionado y evitar referencias a otros servicios del proyecto.

## Alcance

Este repositorio documenta el servicio de usuarios, autenticacion y recuperacion de contrasena. Todo lo demas queda fuera de esta version.

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

## Versionado

Esta documentacion queda acotada al modulo `usuario` para trabajar cambios, historial y revisiones sin arrastrar la descripcion de otros modulos.
