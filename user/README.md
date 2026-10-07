# Users API

Microservicio de usuarios de EstacionAr: registro, login con email y contraseña, refresh tokens y login con Google. Construido con FastAPI + PostgreSQL.

## Stack

| Tecnología | Uso |
|---|---|
| FastAPI | Framework web |
| PostgreSQL 17 | Base de datos |
| SQLAlchemy 2.0 | ORM |
| Pydantic v2 | Validación de datos |
| PyJWT | Tokens JWT |
| pwdlib (Argon2) | Hash de contraseñas |
| httpx | Cliente HTTP (Google OAuth) |
| slowapi | Rate limiting del login |
| pytest | Testing |

## Estructura

```
user/
├── app/
│   ├── main.py              # Punto de entrada
│   ├── config.py            # Variables de configuración
│   ├── database.py          # Configuración SQLAlchemy
│   ├── dependencies.py      # Usuario actual a partir del JWT
│   ├── limiter.py
│   ├── models/              # user, refresh_token
│   ├── repositories/        # user, refresh_token
│   ├── routers/             # auth, user, health
│   ├── schemas/             # auth, user
│   └── services/            # auth, google_auth, user
├── test/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── example_env.txt
```

## Puesta en marcha

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp example_env.txt .env      # completar con valores reales
docker compose up -d         # levanta PostgreSQL
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` y Swagger en `http://localhost:8000/docs`.

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | — | URL de conexión PostgreSQL |
| `TEST_DATABASE_URL` | — | URL de BD para tests |
| `SECRET_KEY` | — | Clave para firmar los JWT |
| `ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Expiración del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Expiración del refresh token |
| `RATE_LIMIT_LOGIN` | `10/minute` | Límite de intentos de login por IP |
| `GOOGLE_CLIENT_ID` | — | Client ID de Google OAuth |
| `GOOGLE_CLIENT_SECRET` | — | Client secret de Google OAuth |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/auth/google/callback` | Callback de Google |

## Endpoints

| Método | Path | Auth | Descripción |
|---|---|---|---|
| POST | `/users` | No | Registrar usuario |
| GET | `/users/me` | Bearer | Ver el usuario autenticado |
| PATCH | `/users/me` | Bearer | Cambiar el nombre |
| POST | `/auth/login` | No | Login con email y contraseña |
| POST | `/auth/refresh` | No | Rotar refresh token y obtener nuevo access token |
| GET | `/auth/google` | No | Redirige al login de Google |
| GET | `/auth/google/callback` | No | Callback de Google; devuelve los tokens |
| GET | `/livez` | No | Liveness |
| GET | `/readyz` | No | Readiness (chequea la BD) |

Los endpoints autenticados esperan el header `Authorization: Bearer <access_token>`.

## Autenticación

- **Access token**: JWT firmado con `SECRET_KEY`, con `sub` = id del usuario.
- **Refresh token**: string aleatorio; en la BD se guarda solo su hash SHA-256. Cada uso lo revoca y emite uno nuevo (rotación).

### Login con Google

1. El cliente abre `GET /auth/google`: el servicio genera un `state` aleatorio, lo guarda en una cookie (10 min) y redirige a Google.
2. Google redirige a `/auth/google/callback?code=...&state=...`. Si el `state` no coincide con la cookie se responde 400 (protección CSRF).
3. El servicio canjea el código y obtiene email y `sub` de Google. Si Google no verificó el email, responde 400.
4. Busca al usuario por `google_id`; si no existe, por email (y lo vincula); si tampoco existe, lo crea.
5. Responde `{access_token, refresh_token, token_type}`.

#### Credenciales de Google

En [Google Cloud Console](https://console.cloud.google.com), dentro del proyecto:

1. **Google Auth Platform → Branding**: nombre de la app y email de soporte.
2. **Audience**: tipo *External*; mientras esté en *Testing*, agregar los emails que van a poder loguearse en *Test users*.
3. **Clients → Create client** → *Web application*, con redirect URI `http://localhost:8000/auth/google/callback` (debe coincidir exactamente con `GOOGLE_REDIRECT_URI`).
4. Copiar el Client ID y el Client secret a `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en el `.env`.

## Validaciones

Contraseña al registrarse: entre 8 y 128 caracteres, con al menos una mayúscula, una minúscula, un número y un carácter especial (`@$!%*?&._-#`). Nombre: entre 4 y 100 caracteres.

## Tests

```bash
pytest
```

Necesitan `TEST_DATABASE_URL` apuntando a una base PostgreSQL existente (la recrean en cada test).
