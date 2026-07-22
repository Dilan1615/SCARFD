# Plan de Pruebas — SACARF

> Sistema de Control de Asistencia con Reconocimiento Facial  
> Django 4.2.11 · DRF 3.16.1 · Python 3.12 · pytest 9 · unittest.mock · freezegun  
> 339 pruebas · 100% aprobación

---

## Índice

1. [Arquitectura de Pruebas](#1-arquitectura-de-pruebas)
2. [shared — Módulo Compartido (58 tests)](#2-shared--módulo-compartido-58-tests)
3. [usuario — Módulo Usuario (87 tests)](#3-usuario--módulo-usuario-87-tests)
4. [academico — Módulo Académico (77 tests)](#4-academico--módulo-académico-77-tests)
5. [asistencia — Módulo Asistencia (55 tests)](#5-asistencia--módulo-asistencia-55-tests)
6. [reportes — Módulo Reportes (34 tests)](#6-reportes--módulo-reportes-34-tests)
7. [monitoring — Módulo Monitorización (28 tests)](#7-monitoring--módulo-monitorización-28-tests)
8. [Resumen Global](#8-resumen-global)

---

## 1. Arquitectura de Pruebas

### 1.1 Configuración

- **Fichero raíz**: `conftest.py` en la raíz del proyecto — configura variables de entorno para testing.
- **pytest.ini**: configura el módulo de settings de Django (`sacarf.settings`).
- **Base de datos**: SQLite en memoria (`:memory:`).
- **Variables de entorno**: todas las necesarias para el funcionamiento (SECRET_KEY, ENCRYPT_KEY, API keys de Brevo/Justicia Digital/Correos, credenciales de email, etc.).
- **Servicio**: `SERVICE_NAME=all` — el sistema corre como monolito.

### 1.2 Herramientas

- **pytest 9** con plugin `pytest-django 4.12` como runner.
- **`unittest.mock`** (parche con `@patch` y `MagicMock` / `PropertyMock`) para aislar:
  - Clientes HTTP internos (UsuarioServiceClient, AcademicoServiceClient, AsistenciaServiceClient).
  - AWS Rekognition (detección/registro facial).
  - ReporteService (generación de archivos).
  - Servicios de monitorización (obtener_estado_servicios, obtener_infraestructura, obtener_metricas_backend, etc.).
  - EmailService (envío de correos vía API).
  - Shared models externos (importación dinámica con `importlib`).
- **`freezegun`** para congelar el tiempo en:
  - `Asistencia.registrar_asistencia()` — verifica estados según hora.
  - Tests de bloqueo de cuenta por intentos fallidos.
  - Tests de expiración de tokens de restablecimiento de password.
- **`APITestCase`** de DRF para pruebas de integración de endpoints.
- **`TestCase`** de Django para pruebas de modelo/serializer.

### 1.3 Convenciones

- Cada módulo tiene su fichero `tests.py` dentro de `sacarf/apps/<modulo>/`.
- Las clases de prueba se agrupan por tipo: `*ModelTest`, `*SerializerTest`, `*ViewSet*Test`.
- Cada clase base `*APIBase` extiende `APITestCase` y configura:
  - Creación de usuario administrador en `setUp()`.
  - Token JWT en cabecera `HTTP_AUTHORIZATION`.
  - URL base (`self.base_url`).
- JWT tokens se crean **dentro** del contexto de `freeze_time` cuando se usa (no en setUp).
- Las pruebas de autorización verifican tanto autenticado como sin autenticar, y por rol (admin vs estudiante/docente).

### 1.4 Estructura típica de una prueba de API

```python
class XxxViewSetTest(MonitoringAPIBase):
    def test_list(self):
        r = self.client.get(f'{self.base_url}xxx/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('results', r.data)

    def test_sin_auth(self):
        self.client.credentials()  # quita token
        r = self.client.get(f'{self.base_url}xxx/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)
```

---

## 2. shared — Módulo Compartido (58 tests)

### 2.1 Descripción

Prueba las utilidades compartidas entre todos los módulos: backend de autenticación personalizado, autenticación JWT personalizada, permisos por rol, utilidades de auditoría, y clientes HTTP para comunicación entre microservicios.

### 2.2 EmailOrUsernameModelBackendTest (5 tests)

Backend de autenticación que permite login con email o username.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_authenticate_email_correcto` | Autenticar con email y password correctos | Devuelve el usuario |
| 2 | `test_authenticate_email_incorrecto` | Autenticar con email inexistente | Devuelve `None` |
| 3 | `test_authenticate_password_incorrecto` | Autenticar con email correcto pero password incorrecto | Devuelve `None` |
| 4 | `test_authenticate_sin_username` | Llamar a `authenticate()` sin `username` | Devuelve `None` |
| 5 | `test_authenticate_usuario_inactivo` | Autenticar con usuario con `is_active=False` | Devuelve `None` |

### 2.3 CustomJWTAuthenticationTest (2 tests)

Autenticación JWT personalizada.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_authenticate_sin_header` | Request sin cabecera `Authorization` | Devuelve `None` |
| 2 | `test_authenticate_token_invalido_retorna_none` | Request con token JWT inválido | Devuelve `None` |

### 2.4 IsAdminForMutationTest (10 tests)

Permiso personalizado: solo ADMIN puede crear/actualizar/eliminar; cualquier autenticado puede leer.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_admin_puede_crear` | Admin realiza mutación CREATE | `has_permission` = `True` |
| 2 | `test_admin_puede_actualizar` | Admin realiza mutación UPDATE | `has_permission` = `True` |
| 3 | `test_admin_puede_eliminar` | Admin realiza mutación DELETE | `has_permission` = `True` |
| 4 | `test_estudiante_no_puede_crear` | Estudiante intenta CREATE | `has_permission` = `False` |
| 5 | `test_estudiante_no_puede_actualizar` | Estudiante intenta UPDATE | `has_permission` = `False` |
| 6 | `test_estudiante_no_puede_eliminar` | Estudiante intenta DELETE | `has_permission` = `False` |
| 7 | `test_lectura_admin_permitido` | Admin realiza GET | `has_permission` = `True` |
| 8 | `test_lectura_autenticado_permitido` | Estudiante realiza GET | `has_permission` = `True` |
| 9 | `test_sin_autenticacion_lectura_falla` | No autenticado intenta GET | `has_permission` = `False` |
| 10 | `test_sin_autenticacion_mutacion_falla` | No autenticado intenta CREATE | `has_permission` = `False` |

### 2.5 AuditUtilsTest (12 tests)

Utilidades de serialización de datos para auditoría.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_a_serializable_none` | `None` → `None` | Retorna `None` |
| 2 | `test_a_serializable_int` | Entero → mismo entero | Retorna el entero |
| 3 | `test_a_serializable_float` | Flotante → mismo flotante | Retorna el float |
| 4 | `test_a_serializable_str` | Cadena → misma cadena | Retorna la cadena |
| 5 | `test_a_serializable_bool` | Booleano → mismo booleano | Retorna el bool |
| 6 | `test_a_serializable_list` | Lista de objetos → lista de strings | Cada elemento convertido a str |
| 7 | `test_a_serializable_dict` | Diccionario anidado → dict serializable | Valores convertidos recursivamente |
| 8 | `test_a_serializable_date` | `datetime.date` → string ISO | Formato `YYYY-MM-DD` |
| 9 | `test_a_serializable_datetime` | `datetime.datetime` → string ISO | Formato ISO con zona horaria |
| 10 | `test_a_serializable_model_instance` | Instancia de modelo Django → string | `str(instancia)` |
| 11 | `test_obtener_ip_con_xff` | Request con cabecera `X-Forwarded-For` | IP extraída de XFF |
| 12 | `test_obtener_ip_sin_xff` | Request sin XFF, solo `REMOTE_ADDR` | IP de REMOTE_ADDR |
| 13 | `test_obtener_ip_sin_headers` | Request sin cabeceras | `None` |
| 14 | `test_datos_usuario_autenticado` | Usuario autenticado → dict con id, email, nombre | Campos correctos |
| 15 | `test_datos_usuario_anonimo` | Usuario anónimo → dict con valores por defecto | `usuario_id=None`, `usuario_nombre='anonimo'` |

### 2.6 RegistrarAuditoriaTest (4 tests)

Función `registrar_auditoria()` que persiste eventos de auditoría.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_registrar_auditoria_exitoso` | Registro completo con todos los campos | Objeto creado con valores correctos |
| 2 | `test_registrar_auditoria_sin_datos_modificados` | Auditoría sin `datos_modificados` | `datos_modificados` = `None` |
| 3 | `test_registrar_auditoria_no_lanza_excepcion` | Error interno en registro | No lanza excepción (capturada con logging) |
| 4 | `test_registrar_auditoria_descripcion_truncada` | Descripción mayor a 255 caracteres | Descripción truncada |

### 2.7 AuditoriaMixinTest (2 tests)

Mixin para modelos que integran auditoría automática.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_nombre_servicio_por_auditoria_servicio` | Mixin definido con `auditoria_servicio` | `nombre_servicio()` retorna el valor |
| 2 | `test_nombre_modelo_por_auditoria_modelo` | Mixin definido con `auditoria_modelo` | `nombre_modelo()` retorna el valor |

### 2.8 UsuarioServiceClientTest (4 tests)

Cliente HTTP para comunicación con el microservicio Usuario.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_get_usuario_exitoso` | Usuario existe → response 200 | Retorna dict con datos del usuario |
| 2 | `test_get_usuario_no_encontrado` | Usuario no existe → response 404 | Retorna `None` |
| 3 | `test_get_usuario_error_conexion` | Error de conexión (timeout) | Retorna `None` (no lanza excepción) |
| 4 | `test_get_usuarios_by_role_exitoso` | Obtener usuarios por rol exitoso | Retorna lista de usuarios |
| 5 | `test_get_usuarios_by_role_error` | Error al obtener por rol | Retorna lista vacía |

### 2.9 AcademicoServiceClientTest (6 tests)

Cliente HTTP para comunicación con el microservicio Académico.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_get_materia_exitoso` | Materia existe → response 200 | Retorna dict con datos |
| 2 | `test_get_ciclo_exitoso` | Ciclo existe → response 200 | Retorna dict con datos |
| 3 | `test_get_horario_exitoso` | Horario existe → response 200 | Retorna dict con datos |
| 4 | `test_get_horario_no_encontrado` | Horario no existe → response 404 | Retorna `None` |
| 5 | `test_get_horarios_by_materia_exitoso` | Horarios por materia existen | Retorna lista |
| 6 | `test_get_horarios_by_materia_error` | Error al obtener horarios por materia | Retorna lista vacía |
| 7 | `test_get_materias_by_docente_exitoso` | Materias por docente existen | Retorna lista |

### 2.10 AsistenciaServiceClientTest (7 tests)

Cliente HTTP para comunicación con el microservicio Asistencia.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_get_asistencia_hoy_exitoso` | Asistencia hoy existe | Retorna dict |
| 2 | `test_get_asistencia_hoy_sin_match` | No hay asistencia hoy | Retorna `None` |
| 3 | `test_get_asistencias_por_estudiante_materia_exitoso` | Asistencias existen | Retorna lista |
| 4 | `test_get_asistencias_por_estudiante_materia_error` | Error en petición | Retorna lista vacía |
| 5 | `test_tiene_registro_facial_true` | Estudiante tiene registro facial | Retorna `True` |
| 6 | `test_tiene_registro_facial_false` | Estudiante no tiene registro facial | Retorna `False` |
| 7 | `test_tiene_registro_facial_error_retorna_false` | Error en petición | Retorna `False` |

---

## 3. usuario — Módulo Usuario (87 tests)

### 3.1 Descripción

Prueba la gestión completa de usuarios: modelo Usuario con email como identificador, autenticación JWT, registro, perfil, cambio/reseteo de password, login con bloqueo por intentos, permisos por rol (ADMIN, ESTUDIANTE, DOCENTE), y servicio de envío de correos.

### 3.2 UsuarioModelTest (12 tests)

Modelo `Usuario` — extiende `AbstractBaseUser`, usa `email` como `USERNAME_FIELD`.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_create_user_normaliza_email` | Crear usuario con email en mayúsculas | Email normalizado a minúsculas |
| 2 | `test_create_user_sin_email` | Crear usuario sin email | `ValueError` |
| 3 | `test_email_unique` | Crear dos usuarios con mismo email | `IntegrityError` |
| 4 | `test_cedula_unique` | Crear dos usuarios con misma cédula | `IntegrityError` |
| 5 | `test_create_superuser_correcto` | Crear superusuario con todos los permisos | `is_staff=True`, `is_superuser=True` |
| 6 | `test_create_superuser_sin_is_staff` | Superusuario sin `is_staff=True` | `ValueError` |
| 7 | `test_create_superuser_sin_is_superuser` | Superusuario sin `is_superuser=True` | `ValueError` |
| 8 | `test_str_representation` | Representación string del usuario | `str(u)` = email |
| 9 | `test_esta_bloqueado_sin_bloqueo` | Sin `bloqueado_hasta` | `False` |
| 10 | `test_esta_bloqueado_pasado` | `bloqueado_hasta` en el pasado | `False` |
| 11 | `test_esta_bloqueado_futuro` | `bloqueado_hasta` en el futuro | `True` |
| 12 | `test_esta_bloqueado_auto_por_intentos` | 5+ intentos fallidos y `bloqueado_hasta` futuro | `True` |

### 3.3 PasswordResetTokenModelTest (5 tests)

Modelo `PasswordResetToken` para gestión de tokens de reseteo.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_generar_token_es_url_safe` | Generar token automáticamente | `token` es string url-safe no vacío |
| 2 | `test_str_representation` | Representación string | Incluye email y prefijo del token |
| 3 | `test_is_valid_no_usado_y_vigente` | Token no usado y no expirado | `is_valid()` = `True` |
| 4 | `test_is_valid_token_expirado` | Token con `fecha_expiracion` pasada | `is_valid()` = `False` |
| 5 | `test_is_valid_token_usado` | Token con `usado=True` | `is_valid()` = `False` |

### 3.4 ValidarPasswordSeguraTest (4 tests)

Validador de fortaleza de contraseña.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_password_valida` | Password cumple todos los requisitos | `True` |
| 2 | `test_sin_mayuscula` | Password sin letra mayúscula | `False` |
| 3 | `test_sin_numero` | Password sin número | `False` |
| 4 | `test_sin_simbolo` | Password sin símbolo especial | `False` |

### 3.5 RegisterSerializerTest (4 tests)

Serializer de registro de nuevos usuarios.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_campos_requeridos` | Faltan campos obligatorios | Error de validación |
| 2 | `test_validate_password_debil` | Password no cumple requisitos | Error de validación |
| 3 | `test_validate_password_sin_mayuscula` | Password sin mayúscula | Error de validación |
| 4 | `test_create_crea_usuario_con_hash` | Creación exitosa | Usuario creado con password hasheado |

### 3.6 ChangePasswordSerializerTest (3 tests)

Serializer para cambio de contraseña.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_new_password_valida` | Password nueva válida | Validación pasa |
| 2 | `test_new_password_debil` | Password nueva débil | Error de validación |
| 3 | `test_new_password_sin_mayuscula` | Password nueva sin mayúscula | Error de validación |

### 3.7 SolicitarRestablecimientoSerializerTest (2 tests)

Serializer para solicitar restablecimiento de contraseña.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_email_existente` | Email registrado | Validación pasa, token creado |
| 2 | `test_email_no_existente` | Email no registrado | Error de validación |

### 3.8 RestablecerPasswordSerializerTest (4 tests)

Serializer para restablecer contraseña con token.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_token_requerido` | No se envía token | Error de validación |
| 2 | `test_passwords_no_coinciden` | `password1` ≠ `password2` | Error de validación |
| 3 | `test_passwords_coinciden` | Passwords coinciden | Validación pasa |
| 4 | `test_password_debil` | Password nueva débil | Error de validación |

### 3.9 UsuarioSerializerTest (2 tests)

Serializer general de usuario.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_serializa_campos` | Serialización de todos los campos | Campos presentes: id, email, nombre, etc. |
| 2 | `test_foto_url_none` | Usuario sin foto | `foto_url` = `None` |

### 3.10 EmailOrUsernameModelBackendTest (5 tests) — copia en shared, mismo contenido

### 3.11 CustomJWTAuthenticationTest (2 tests) — copia en shared, mismo contenido

### 3.12 IsAdminForMutationTest (6 tests) — copia parcial en shared

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_admin_puede_crear` | Admin puede crear | `True` |
| 2 | `test_admin_puede_eliminar` | Admin puede eliminar | `True` |
| 3 | `test_estudiante_no_puede_crear` | Estudiante no puede crear | `False` |
| 4 | `test_lectura_autenticado_ok` | Autenticado puede leer | `True` |
| 5 | `test_sin_autenticacion_falla` | No autenticado → permiso denegado | `False` |
| 6 | `test_admin_puede_actualizar` | Admin puede actualizar | `True` |

### 3.13 UsuarioViewSetListTest (4 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_listar_como_admin` | Admin lista todos los usuarios | 200 OK, hay resultados |
| 2 | `test_listar_como_estudiante_solo_su_registro` | Estudiante lista → solo ve su propio registro | Un solo resultado, es él mismo |
| 3 | `test_listar_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |
| 4 | `test_filtrar_por_rol_admin` | Filtrar por `?rol=ADMIN` | Solo usuarios ADMIN |

### 3.14 UsuarioViewSetCRUDTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_create_usuario_admin` | Admin crea usuario | 201 CREATED |
| 2 | `test_create_usuario_estudiante_no_puede` | Estudiante crea usuario | 403 FORBIDDEN |
| 3 | `test_retrieve_usuario_admin` | Obtener detalle de usuario | 200 OK, datos correctos |
| 4 | `test_update_usuario_admin` | Actualizar usuario | 200 OK, cambios reflejados |
| 5 | `test_destroy_usuario_admin_soft_delete` | Eliminación lógica | `is_active=False` |

### 3.15 UsuarioViewSetActionsTest (14 tests)

Acciones personalizadas del ViewSet (`me`, `perfil`, `register`, `cambiar_password`, `solicitar_restablecimiento`, `restablecer_password`).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_me_autenticado` | GET `/me/` autenticado | 200 OK, datos del usuario autenticado |
| 2 | `test_me_sin_auth` | GET `/me/` sin auth | 401 UNAUTHORIZED |
| 3 | `test_perfil_get` | GET `/perfil/` autenticado | 200 OK |
| 4 | `test_perfil_actualizar_datos` | PUT/PATCH `/perfil/` con datos | 200 OK, cambios aplicados |
| 5 | `test_perfil_sin_auth` | GET `/perfil/` sin auth | 401 UNAUTHORIZED |
| 6 | `test_register_datos_validos` | POST `/register/` con datos válidos | 201 CREATED, usuario creado |
| 7 | `test_register_email_duplicado` | POST `/register/` con email existente | 400 BAD_REQUEST |
| 8 | `test_register_password_debil` | POST `/register/` con password débil | 400 BAD_REQUEST |
| 9 | `test_cambiar_password_correcto` | POST `/cambiar-password/` correcto | 200 OK |
| 10 | `test_cambiar_password_incorrecta` | POST `/cambiar-password/` con password actual incorrecta | 400 BAD_REQUEST |
| 11 | `test_cambiar_password_sin_auth` | POST `/cambiar-password/` sin auth | 401 UNAUTHORIZED |
| 12 | `test_solicitar_restablecimiento_email_existe` | POST con email existente | 200 OK, token creado |
| 13 | `test_solicitar_restablecimiento_email_no_existe` | POST con email inexistente | 400 BAD_REQUEST |
| 14 | `test_restablecer_password_token_valido` | POST con token válido y nuevas passwords | 200 OK, password actualizada, token marcado usado |
| 15 | `test_restablecer_password_token_invalido` | POST con token inválido | 400 BAD_REQUEST |
| 16 | `test_restablecer_password_token_expirado` | POST con token expirado | 400 BAD_REQUEST |
| 17 | `test_restablecer_password_passwords_no_coinciden` | POST con passwords que no coinciden | 400 BAD_REQUEST |

### 3.16 LoginViewTest (7 tests)

View `login_view` — login con email/username + password.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_login_exitoso` | Credenciales correctas | 200 OK, tokens access + refresh |
| 2 | `test_login_incrementa_intentos` | Login fallido incrementa `intentos_fallidos` | Contador aumenta |
| 3 | `test_login_exitoso_resetea_intentos` | Login exitoso resetea contador | `intentos_fallidos` = 0 |
| 4 | `test_login_bloqueo_tras_5_intentos` | 5+ intentos fallidos | 429 TOO_MANY_REQUESTS o 403, `bloqueado_hasta` seteado |
| 5 | `test_login_cuenta_bloqueada` | Intentar login cuando bloqueado | 403 FORBIDDEN |
| 6 | `test_login_credenciales_invalidas` | Password incorrecto | 401 UNAUTHORIZED |
| 7 | `test_login_email_no_existe` | Email no registrado | 401 UNAUTHORIZED |

### 3.17 TokenRefreshViewTest (2 tests)

Refresh de token JWT.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_refresh_token_valido` | Refresh token válido | 200 OK, nuevo access token |
| 2 | `test_refresh_token_invalido` | Refresh token inválido | 401 UNAUTHORIZED |

### 3.18 EmailServiceTest (3 tests)

Servicio de envío de correos electrónicos (vía API).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_enviar_email_exitoso` | Envío exitoso | Retorna `True` |
| 2 | `test_enviar_email_sin_api_key` | API key no configurada | Retorna `False` |
| 3 | `test_enviar_email_http_error` | Error HTTP en API | Retorna `False` |

---

## 4. academico — Módulo Académico (77 tests)

### 4.1 Descripción

Prueba la gestión académica: carreras, ciclos (periodos), materias, horarios, y matrículas. Incluye validaciones de superposición de horarios, relaciones entre entidades, filtros y permisos por rol.

### 4.2 CarreraModelTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_create_carrera_correcta` | Crear carrera con datos válidos | Objeto creado, campos correctos |
| 2 | `test_str_representation` | Representación string | `str(c)` = nombre |
| 3 | `test_codigo_unique` | Código duplicado | `IntegrityError` |

### 4.3 CicloModelTest (4 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_str_representation` | Representación string | Incluye nombre y carrera |
| 2 | `test_esta_activo_true` | Fecha actual dentro del rango y estado ACTIVO | `True` |
| 3 | `test_esta_activo_false_estado_no_activo` | Estado CERRADO | `False` |
| 4 | `test_unique_together` | Misma carrera + mismo nombre | `IntegrityError` |

### 4.4 MateriaModelTest (2 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_str_representation` | Representación string | Incluye nombre y código |
| 2 | `test_codigo_unique` | Código duplicado | `IntegrityError` |

### 4.5 HorarioModelTest (6 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_str_representation` | Representación string | Incluye día, hora, materia |
| 2 | `test_es_hora_valida_true` | Hora inicio < hora fin | `True` |
| 3 | `test_es_hora_valida_false` | Hora inicio ≥ hora fin | `False` |
| 4 | `test_clean_raises_on_invalid_hours` | Hora inicio ≥ hora fin → validación | `ValidationError` |
| 5 | `test_clean_raises_on_overlapping` | Misma materia, mismo día, horario solapado | `ValidationError` |
| 6 | `test_clean_no_overlap_diff_dia` | Misma materia, diferente día → no solapamiento | Sin error |

### 4.6 MatriculaModelTest (2 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_str_representation` | Representación string | Incluye IDs |
| 2 | `test_unique_together` | Mismo estudiante + mismo ciclo | `IntegrityError` |

### 4.7 CarreraSerializerTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_serializa_campos` | Serialización de campos | `id`, `nombre`, `codigo`, `modalidad`, etc. |
| 2 | `test_id_read_only` | `id` read-only en deserialización | No se puede asignar |
| 3 | `test_modalidad_display` | `modalidad_display` en output | Muestra valor legible |

### 4.8 CicloSerializerTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_estado_display` | `estado_display` en output | Muestra valor legible |
| 2 | `test_validate_fecha_fin_valida` | `fecha_fin` > `fecha_inicio` | Válido |
| 3 | `test_validate_fecha_fin_menor_o_igual` | `fecha_fin` ≤ `fecha_inicio` | `ValidationError` |

### 4.9 MateriaSerializerTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_carrera_nombre_and_ciclo_info` | Campos anidados `carrera_nombre`, `ciclo_info` | Presentes y correctos |
| 2 | `test_docente_nombre_con_docente` | Materia con docente asignado | `docente_nombre` = nombre del docente |
| 3 | `test_docente_nombre_sin_docente` | Materia sin docente | `docente_nombre` = `None` |

### 4.10 HorarioSerializerTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_dia_display_and_materia_nombre` | Campos `dia_display` y `materia_nombre` | Presentes |
| 2 | `test_validate_hora_fin_menor_o_igual` | Hora fin ≤ hora inicio | `ValidationError` |
| 3 | `test_validate_hora_fin_valida` | Hora fin > hora inicio | Válido |

### 4.11 MatriculaSerializerTest (4 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_estudiante_nombre` | Estudiante existe | `estudiante_nombre` presente |
| 2 | `test_estudiante_nombre_no_existe` | Estudiante no existe | `estudiante_nombre` = `None` |
| 3 | `test_carrera_nombre_and_ciclo_info_and_estado_display` | Campos anidados | Presentes |
| 4 | `test_read_only_fields` | `id`, `fecha_matricula`, `estudiante_nombre` read-only | No asignables |

### 4.12 CarreraViewSetTest (11 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list_como_authenticated` | GET /carreras/ autenticado | 200 OK, lista paginada |
| 2 | `test_list_sin_auth` | GET /carreras/ sin auth | 401 UNAUTHORIZED |
| 3 | `test_retrieve` | GET /carreras/{id}/ | 200 OK, detalle |
| 4 | `test_create_admin` | POST /carreras/ admin | 201 CREATED |
| 5 | `test_create_no_admin` | POST /carreras/ estudiante | 403 FORBIDDEN |
| 6 | `test_update_admin` | PUT /carreras/{id}/ admin | 200 OK |
| 7 | `test_update_no_admin` | PUT /carreras/{id}/ estudiante | 403 FORBIDDEN |
| 8 | `test_destroy_admin` | DELETE /carreras/{id}/ admin | 204 NO CONTENT |
| 9 | `test_destroy_no_admin` | DELETE /carreras/{id}/ estudiante | 403 FORBIDDEN |
| 10 | `test_filtrar_por_modalidad` | GET /carreras/?modalidad=... | Filtrado correcto |
| 11 | `test_search_por_nombre` | GET /carreras/?search=... | Búsqueda por nombre |

### 4.13 CicloViewSetTest (7 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list` | GET /ciclos/ | 200 OK |
| 2 | `test_retrieve` | GET /ciclos/{id}/ | 200 OK |
| 3 | `test_create_admin` | POST /ciclos/ admin | 201 CREATED |
| 4 | `test_create_no_admin` | POST /ciclos/ estudiante | 403 FORBIDDEN |
| 5 | `test_update_admin` | PUT /ciclos/{id}/ admin | 200 OK |
| 6 | `test_destroy_admin` | DELETE /ciclos/{id}/ admin | 204 NO CONTENT |
| 7 | `test_filtrar_por_carrera` | GET /ciclos/?carrera_id=... | Filtrado por carrera |

### 4.14 MateriaViewSetTest (8 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list` | GET /materias/ | 200 OK |
| 2 | `test_retrieve` | GET /materias/{id}/ | 200 OK |
| 3 | `test_create_admin` | POST /materias/ admin | 201 CREATED |
| 4 | `test_create_no_admin` | POST /materias/ estudiante | 403 FORBIDDEN |
| 5 | `test_update_admin` | PUT /materias/{id}/ admin | 200 OK |
| 6 | `test_destroy_admin` | DELETE /materias/{id}/ admin | 204 NO CONTENT |
| 7 | `test_filtrar_por_docente` | GET /materias/?docente_id=... | Filtrado por docente |
| 8 | `test_search_por_codigo` | GET /materias/?search=... | Búsqueda por código |

### 4.15 HorarioViewSetTest (7 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list` | GET /horarios/ | 200 OK |
| 2 | `test_retrieve` | GET /horarios/{id}/ | 200 OK |
| 3 | `test_create_admin` | POST /horarios/ admin | 201 CREATED |
| 4 | `test_create_no_admin` | POST /horarios/ estudiante | 403 FORBIDDEN |
| 5 | `test_update_admin` | PUT /horarios/{id}/ admin | 200 OK |
| 6 | `test_destroy_admin` | DELETE /horarios/{id}/ admin | 204 NO CONTENT |
| 7 | `test_filtrar_por_dia_semana` | GET /horarios/?dia_semana=... | Filtrado por día |

### 4.16 MatriculaViewSetTest (7 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list` | GET /matriculas/ | 200 OK |
| 2 | `test_retrieve` | GET /matriculas/{id}/ | 200 OK |
| 3 | `test_create_admin` | POST /matriculas/ admin | 201 CREATED |
| 4 | `test_create_no_admin` | POST /matriculas/ estudiante | 403 FORBIDDEN |
| 5 | `test_update_admin` | PUT /matriculas/{id}/ admin | 200 OK |
| 6 | `test_destroy_admin` | DELETE /matriculas/{id}/ admin | 204 NO CONTENT |
| 7 | `test_filtrar_por_estudiante` | GET /matriculas/?estudiante_id=... | Filtrado por estudiante |

### 4.17 MisMateriasTest (5 tests)

Acción personalizada `mis_materias` — retorna las materias del estudiante/docente autenticado.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_mis_materias_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |
| 2 | `test_mis_materias_admin` | Admin → lista de todas las materias | 200 OK, lista |
| 3 | `test_mis_materias_estudiante_con_matricula` | Estudiante con matrículas activas | 200 OK, materias del estudiante |
| 4 | `test_mis_materias_estudiante_sin_matricula` | Estudiante sin matrículas | 200 OK, lista vacía |
| 5 | `test_mis_materias_con_asistencia_registrada` | Materias con indicador de asistencia hoy | Campo `asistencia_hoy` en cada materia |

---

## 5. asistencia — Módulo Asistencia (55 tests)

### 5.1 Descripción

Prueba la gestión de asistencia con reconocimiento facial: registro facial de estudiantes (AWS Rekognition), reconocimiento, marcación de asistencia con validación de tiempo y duplicados, justificaciones con flujo de aprobación/rechazo.

### 5.2 RegistroFacialModelTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_default_estado` | Nuevo registro → estado `PENDIENTE` | `estado` = `'PENDIENTE'` |
| 2 | `test_default_collection_id` | `collection_id` por defecto | `collection_id` = `'sacarf-estudiantes'` |
| 3 | `test_face_id_unique` | Mismo `face_id` duplicado | `IntegrityError` |
| 4 | `test_estudiante_id_unique` | Mismo `estudiante_id` | `IntegrityError` |
| 5 | `test_str_representation` | Representación string | Incluye `estudiante_id` y estado |

### 5.3 ReconocimientoModelTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_default_resultado_and_confianza` | Nuevo registro | `resultado='NO_COINCIDENCIA'`, `confianza=0.0` |
| 2 | `test_default_ordering_desc` | Orden descendente por `fecha_hora` | Más reciente primero |
| 3 | `test_str_representation` | Representación string | Incluye `estudiante_id` y resultado |

### 5.4 AsistenciaModelTest (7 tests)

Incluye prueba del método de clase `registrar_asistencia()` con `freezegun`.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_default_ordering_desc` | Orden descendente por `fecha` | Más reciente primero |
| 2 | `test_str_representation` | Representación string | Incluye `estudiante_id`, estado, fecha |
| 3 | `test_unique_together_estudiante_horario_fecha` | Mismo estudiante + horario + fecha | `IntegrityError` |
| 4 | `test_registrar_asistencia_presente` | Dentro de los primeros 15 min del horario | Estado `PRESENTE` |
| 5 | `test_registrar_asistencia_tarde` | Entre 15 y 60 min después del inicio | Estado `TARDE` |
| 6 | `test_registrar_asistencia_fuera_tiempo` | Fuera de la ventana de tolerancia | Estado `AUSENTE` |
| 7 | `test_registrar_asistencia_duplicada` | Ya existe asistencia para ese estudiante+horario+fecha | No se duplica, retorna existente |

### 5.5 JustificacionModelTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_str_representation` | Representación string | Incluye `estudiante_id`, estado |
| 2 | `test_aprobar` | Cambiar estado a APROBADA y setear `fecha_respuesta` | Estado `APROBADA`, fecha seteada |
| 3 | `test_rechazar` | Cambiar estado a RECHAZADA y setear `fecha_respuesta` | Estado `RECHAZADA`, fecha seteada |

### 5.6 AsistenciaViewSetListTest (3 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list_admin` | Admin lista todas las asistencias | 200 OK |
| 2 | `test_list_estudiante_solo_suyas` | Estudiante lista → solo sus asistencias | Solo las suyas |
| 3 | `test_list_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 5.7 AsistenciaViewSetCRUDTest (4 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_retrieve` | GET /asistencias/{id}/ | 200 OK |
| 2 | `test_create_admin` | POST /asistencias/ admin | 201 CREATED |
| 3 | `test_update_admin` | PUT /asistencias/{id}/ admin | 200 OK |
| 4 | `test_destroy_admin` | DELETE /asistencias/{id}/ admin | 204 NO CONTENT |

### 5.8 AsistenciaViewSetActionsTest (6 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_registrar_asistencia_exitoso` | POST `/registrar/` con ID válido y confianza > 0.9 | 200 OK, estado marcado, reconocimiento registrado |
| 2 | `test_registrar_asistencia_confianza_baja` | POST `/registrar/` con confianza ≤ 0.9 | 400 BAD_REQUEST |
| 3 | `test_registrar_asistencia_id_no_match` | POST `/registrar/` con `estudiante_id` que no coincide con el rostro detectado | 400 BAD_REQUEST |
| 4 | `test_registrar_asistencia_sin_auth` | POST `/registrar/` sin auth | 401 UNAUTHORIZED |
| 5 | `test_por_materia` | GET `/por-materia/?materia_id=X` | Lista de asistencias de esa materia |
| 6 | `test_por_materia_sin_param` | GET `/por-materia/` sin parámetro | 400 BAD_REQUEST |
| 7 | `test_por_estudiante` | GET `/por-estudiante/?estudiante_id=X` | Lista de asistencias del estudiante |
| 8 | `test_por_estudiante_sin_param` | GET `/por-estudiante/` sin parámetro | 400 BAD_REQUEST |

### 5.9 RegistroFacialViewSetTest (6 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_sin_auth` | Cualquier endpoint sin auth | 401 UNAUTHORIZED |
| 2 | `test_list_estudiante` | GET /registros-faciales/ como estudiante → solo su registro | Un resultado propietario |
| 3 | `test_create_admin` | POST /registros-faciales/ admin | 201 CREATED |
| 4 | `test_registrar_rostro_exitoso` | POST `/registrar-rostro/` | 200 OK, registro creado, Rekognition llamado |
| 5 | `test_registrar_rostro_ya_existe` | POST `/registrar-rostro/` con `estudiante_id` existente | 400 BAD_REQUEST |
| 6 | `test_registrar_rostro_no_estudiante` | POST `/registrar-rostro/` como no-estudiante | 403 FORBIDDEN |

### 5.10 ReconocimientoViewSetTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |
| 2 | `test_list_admin` | Admin lista todos | 200 OK |
| 3 | `test_list_estudiante_solo_suyos` | Estudiante lista → solo sus reconocimientos | Solo los suyos |
| 4 | `test_retrieve` | GET /reconocimientos/{id}/ | 200 OK |
| 5 | `test_create_not_allowed` | POST /reconocimientos/ no permitido | 405 METHOD_NOT_ALLOWED |

### 5.11 JustificacionViewSetTest (12 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |
| 2 | `test_list_admin` | Admin lista todas | 200 OK |
| 3 | `test_list_estudiante_solo_suyas` | Estudiante lista → solo sus justificaciones | Solo las suyas |
| 4 | `test_create_estudiante` | Estudiante crea justificación para sí mismo | 201 CREATED |
| 5 | `test_create_asistencia_ajena` | Estudiante crea justificación para otro | 404 NOT_FOUND (get_object_or_404) |
| 6 | `test_create_no_estudiante` | Admin/docente crea justificación | 403 FORBIDDEN |
| 7 | `test_create_justificacion_existente` | Ya existe justificación PENDIENTE para esa asistencia | 400 BAD_REQUEST |
| 8 | `test_create_rechazada_se_actualiza` | Justificación RECHAZADA previa → se actualiza a PENDIENTE | 200 OK, estado cambiado |
| 9 | `test_aprobar_justificacion_docente` | POST `/justificaciones/{id}/aprobar/` como docente | 200 OK, justificación APROBADA |
| 10 | `test_aprobar_justificacion_no_docente` | POST `/aprobar/` como no-docente | 403 FORBIDDEN |
| 11 | `test_aprobar_sin_auth` | POST `/aprobar/` sin auth | 401 UNAUTHORIZED |

---

## 6. reportes — Módulo Reportes (34 tests)

### 6.1 Descripción

Prueba la generación y gestión de reportes: creación, tipos disponibles, generación con filtros (general, por estudiante, por materia, por ciclo), descarga de archivos, permisos por rol.

### 6.2 ReporteModelTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_create_reporte` | Crear reporte con todos los campos | Objeto persistido correctamente |
| 2 | `test_default_formato` | Formato por defecto `PDF` | `formato` = `'PDF'` |
| 3 | `test_default_parametros` | `parametros` por defecto `{}` | Dict vacío |
| 4 | `test_ordering` | Orden descendente por `fecha_generacion` | Más reciente primero |
| 5 | `test_str_representation` | Representación string | Incluye tipo, formato, fecha |

### 6.3 ReporteSerializerTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_read_only_fields` | `id`, `fecha_generacion`, `generado_por`, `archivo` read-only | No asignables |
| 2 | `test_tipo_display` | `tipo_display` en output | Muestra valor legible |
| 3 | `test_formato_display` | `formato_display` en output | Muestra valor legible |
| 4 | `test_generado_por_nombre_con_usuario` | Reporte con `generado_por` asignado | `generado_por_nombre` = nombre del usuario |
| 5 | `test_generado_por_nombre_none` | Reporte sin `generado_por` | `generado_por_nombre` = `None` |

### 6.4 GenerarReporteSerializerTest (6 tests)

Serializer para la acción `generar`.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_valido_general` | Tipo GENERAL sin IDs adicionales | Válido |
| 2 | `test_valido_por_estudiante_con_id` | Tipo POR_ESTUDIANTE con `estudiante_id` | Válido |
| 3 | `test_invalido_por_estudiante_sin_id` | Tipo POR_ESTUDIANTE sin `estudiante_id` | Error de validación |
| 4 | `test_invalido_por_materia_sin_id` | Tipo POR_MATERIA sin `materia_id` | Error de validación |
| 5 | `test_invalido_por_ciclo_sin_id` | Tipo POR_CICLO sin `ciclo_id` | Error de validación |
| 6 | `test_default_formato` | Formato por defecto `PDF` | `formato` = `'PDF'` |

### 6.5 ReporteViewSetListTest (2 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list_admin` | Admin lista todos los reportes | 200 OK |
| 2 | `test_list_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 6.6 ReporteViewSetCRUDTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_create_admin` | Admin crea reporte | 201 CREATED |
| 2 | `test_create_estudiante_no_puede` | Estudiante crea reporte | 403 FORBIDDEN |
| 3 | `test_retrieve_admin` | GET /reportes/{id}/ admin | 200 OK |
| 4 | `test_update_admin` | PUT /reportes/{id}/ admin | 200 OK |
| 5 | `test_destroy_admin` | DELETE /reportes/{id}/ admin | 204 NO CONTENT |

### 6.7 ReporteViewSetTiposTest (1 test)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_tipos` | GET `/tipos/` | 200 OK, lista de tipos disponibles |

### 6.8 ReporteViewSetGenerarTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_generar_reporte_general_pdf` | Generar reporte GENERAL en PDF | 200 OK, ReporteService.generar llamado |
| 2 | `test_generar_reporte_excel` | Generar reporte en formato EXCEL | 200 OK |
| 3 | `test_generar_reporte_sin_datos` | Generar reporte sin datos disponibles | 200 OK con advertencia |
| 4 | `test_generar_reporte_docente_permiso` | Docente genera reporte | Permitido |
| 5 | `test_generar_reporte_estudiante_no_permiso` | Estudiante genera reporte | 403 FORBIDDEN |

### 6.9 ReporteViewSetDescargarTest (5 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_descargar_admin_con_archivo` | Admin descarga reporte con archivo | 200 OK, respuesta con archivo |
| 2 | `test_descargar_admin_sin_archivo` | Admin descarga reporte sin archivo todavía | 400 BAD_REQUEST |
| 3 | `test_descargar_estudiante_propio` | Estudiante descarga su propio reporte | 200 OK |
| 4 | `test_descargar_estudiante_ajeno` | Estudiante descarga reporte de otro | 404 NOT_FOUND |
| 5 | `test_descargar_sin_archivo_url` | Reporte sin archivo pero con `archivo_url` | Redirección a la URL |

---

## 7. monitoring — Módulo Monitorización (28 tests)

### 7.1 Descripción

Prueba el módulo de monitorización del sistema: health check, estado de servicios, infraestructura (CPU/RAM/disco), métricas de backend y base de datos, métricas de negocio, registro de auditoría con filtros y resúmenes.

### 7.2 RegistroAuditoriaModelTest (4 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_create_registro` | Crear registro con todos los campos | Objeto persistido con valores correctos |
| 2 | `test_default_usuario_nombre` | Sin `usuario_nombre` | Default `'desconocido'` |
| 3 | `test_ordering` | Orden descendente por `fecha_hora` | Más reciente primero |
| 4 | `test_str_representation` | Representación string | `[servicio] accion Modelo #id por usuario` |

### 7.3 RegistroAuditoriaSerializerTest (2 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_serializa_campos` | Serialización de todos los campos | Campos `id`, `accion`, `servicio`, etc. |
| 2 | `test_todos_read_only` | Todos los campos son read-only | No se puede asignar en deserialización |

### 7.4 HealthTest (2 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_health_sin_auth` | GET /health/ sin autenticación | 200 OK, `status: 'ok'` |
| 2 | `test_health_con_auth` | GET /health/ autenticado | 200 OK |

### 7.5 AuditoriaListTest (5 tests)

Listado paginado de registros de auditoría con filtros.

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_list_auditoria` | GET /auditoria/ | 200 OK, `results` presente |
| 2 | `test_list_auditoria_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |
| 3 | `test_filtro_por_accion` | GET /auditoria/?accion=CREATE | Solo registros CREATE |
| 4 | `test_filtro_por_servicio` | GET /auditoria/?servicio=academico | Solo registros de académico |
| 5 | `test_filtro_por_buscar` | GET /auditoria/?buscar=palabraclave | Búsqueda en descripción |

### 7.6 AuditoriaResumenTest (2 tests)

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_resumen` | GET /auditoria/resumen/ | 200 OK, incluye `total_ultimas_24h`, `por_accion`, `por_servicio` |
| 2 | `test_resumen_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 7.7 SaludTest (2 tests)

Estado de los microservicios (mockeado).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_salud` | GET /salud/ con mock de `obtener_estado_servicios` | 200 OK, lista de servicios con estado |
| 2 | `test_salud_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 7.8 InfraestructuraTest (2 tests)

Métricas de infraestructura (mockeadas, dependen de psutil/docker).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_infraestructura` | GET /infraestructura/ con mock | 200 OK, incluye `cpu`, `ram`, `disco` |
| 2 | `test_infraestructura_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 7.9 BackendMetricsTest (3 tests)

Métricas del backend Django (mockeadas).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_backend_sin_param` | GET /backend/ sin parámetros | 200 OK |
| 2 | `test_backend_con_rango` | GET /backend/?rango_minutos=60 | 200 OK, llama a servicio con `rango_minutos=60` |
| 3 | `test_backend_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 7.10 BaseDatosTest (2 tests)

Métricas de base de datos (mockeadas).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_base_datos` | GET /base-datos/ con mock | 200 OK, incluye `conexiones_activas` |
| 2 | `test_base_datos_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 7.11 NegocioTest (2 tests)

Métricas de negocio (mockeadas, cruza datos de académico+asistencia).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_negocio` | GET /negocio/ con mock | 200 OK, incluye `total_usuarios`, `asistencias_hoy`, etc. |
| 2 | `test_negocio_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

### 7.12 ResumenTest (2 tests)

Dashboard global que consolida todas las métricas (mockeadas).

| # | Test | Descripción | Valida |
|---|------|-------------|--------|
| 1 | `test_resumen` | GET /resumen/ con todos los servicios mockeados | 200 OK, incluye `servicios` |
| 2 | `test_resumen_sin_auth` | Sin autenticación | 401 UNAUTHORIZED |

---

## 8. Resumen Global

### 8.1 Resultados por Módulo

| Módulo | Totales | Exitosas | Fallidas | % |
|--------|--------:|---------:|--------:|---:|
| shared | 58 | 58 | 0 | 100% |
| usuario | 87 | 87 | 0 | 100% |
| academico | 77 | 77 | 0 | 100% |
| asistencia | 55 | 55 | 0 | 100% |
| reportes | 34 | 34 | 0 | 100% |
| monitoring | 28 | 28 | 0 | 100% |
| **TOTAL** | **339** | **339** | **0** | **100%** |

### 8.2 Distribución

| Módulo | Cantidad | Porcentaje |
|--------|--------:|-----------:|
| shared | 58 | 17.1% |
| usuario | 87 | 25.7% |
| academico | 77 | 22.7% |
| asistencia | 55 | 16.2% |
| reportes | 34 | 10.0% |
| monitoring | 28 | 8.3% |
| **TOTAL** | **339** | **100%** |

### 8.3 Cobertura por Área

- **Modelos**: validaciones de campos, constraints (unique, unique_together), propiedades calculadas (`esta_activo`, `esta_bloqueado`), métodos de clase (`registrar_asistencia`), señales, representación string.
- **Serializers**: serialización/deserialización de todos los campos, campos read-only, campos anidados, validación personalizada (`validate_*`), choices display.
- **Views/ViewSets**: CRUD completo, listado paginado, filtros (`FilterBackend`), búsqueda (`SearchFilter`), permisos por rol (`IsAdminForMutation`, `IsAuthenticated`), acciones personalizadas (`@action`).
- **Servicios**: mocking completo de dependencias externas (AWS Rekognition, clientes HTTP internos, servicio de reportes, servicio de monitoreo).
- **Autenticación**: JWT (access + refresh), backend personalizado (email/username), login con bloqueo por intentos, restablecimiento de contraseña con tokens.
- **Auditoría**: registro automático de acciones, serialización de datos modificados, filtros por acción/servicio/búsqueda, resúmenes temporales.

### 8.4 Issues Resueltos Durante el Desarrollo

1. **DRF 3.16+** no convierte automáticamente guiones bajos a guiones en URLs de acciones → usar `url_path='cambiar-password'` en `@action`.
2. **freezegun**: JWT tokens deben crearse dentro del contexto congelado, no en `setUp()`.
3. **get_object_or_404** retorna 404, no 400, cuando un estudiante intenta acceder a una justificación ajena.
4. **Archivos de prueba**: `create_estudiante` en justificaciones requiere un archivo `documento` (PNG simulado).
5. **Mock de servicios**: los servicios se importan como `from . import services` → el path del mock debe ser `apps.monitoring.views.services.obtener_*`.
6. **Clave de respuesta**: `auditoria/resumen/` devuelve `total_ultimas_24h`, no `total_24h`.

### 8.5 Tecnologías

- **Python 3.12.10**
- **Django 4.2.11**
- **Django REST Framework 3.16.1**
- **pytest 9.1.1 + pytest-django 4.12.0**
- **unittest.mock** (stdlib)
- **freezegun** (control de tiempo)
- **SQLite en memoria** (base de datos de pruebas)
- **SimpleJWT** (tokens JWT)
