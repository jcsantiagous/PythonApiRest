import time
from datetime import timedelta

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import settings
from crud import get_user_by_email, create_user, get_user_by_username
from database import db_manager
from logger import logger
from models import UserModel
from schemas import UserCreate, UserResponse, Token
from security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
    security
)

app = FastAPI(
    title="API REST Segura",
    description=("\n"
                 "    API REST segura con las siguientes características:\n"
                 "    * Autenticación JWT\n"
                 "    * Soporte para múltiples bases de datos\n"
                 "    * Seguridad OWASP\n"
                 "    * Sistema de logging\n"
                 "    * Documentación completa\n"
                 "    "),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log de la solicitud entrante
    logger.info(
        "Solicitud entrante",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
    )

    response = await call_next(request)

    # Log de la respuesta
    process_time = time.time() - start_time
    logger.info(
        "Respuesta enviada",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "process_time": f"{process_time:.4f}s"
        }
    )

    return response


# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de seguridad OWASP
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security),
        db: Session = Depends(db_manager.get_db)
) -> UserModel:
    """
    Obtiene el usuario actual basado en el token JWT.

    Args:
        credentials: Credenciales de autenticación Bearer
        db: Sesión de base de datos

    Returns:
        UserModel: Usuario autenticado

    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        user = get_user_by_email(db, payload.get("sub"))
        if user is None:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return user
    except Exception as ex:
        logger.error(f"Error en autenticación: {str(ex)}")
        raise


# Rutas de la API
@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["usuarios"],
    summary="Registrar un nuevo usuario",
    description="Crea un nuevo usuario en el sistema con email y contraseña"
)
def register_user(user: UserCreate, db: Session = Depends(db_manager.get_db)):
    try:
        logger.info(f"Intento de registro para el email: {user.email}")

        db_user = get_user_by_email(db, user.email.__str__())
        if db_user:
            logger.warning(f"Intento de registro con email duplicado: {user.email}")
            raise HTTPException(status_code=400, detail="Email ya registrado")

        db_user_by_username = get_user_by_username(db, user.username)
        if db_user_by_username:
            logger.warning(f"Intento de registro con username duplicado: {user.username}")
            raise HTTPException(status_code=400, detail="Nombre de usuario ya registrado")

        hashed_password = get_password_hash(user.password)
        user_data = {
            "email": user.email,
            "username": user.username,
            "hashed_password": hashed_password,
            "is_active": True
        }
        new_user = create_user(db, user_data)
        logger.info(f"Usuario registrado exitosamente: {user.email}")
        return new_user
    except Exception as ex:
        logger.error(f"Error en registro de usuario: {str(ex)}")
        raise


@app.post(
    "/login",
    response_model=Token,
    tags=["autenticación"],
    summary="Iniciar sesión",
    description="Obtiene un token JWT para autenticación"
)
def login(user_credentials: UserCreate, db: Session = Depends(db_manager.get_db)):
    try:
        logger.info(f"Intento de login para el email: {user_credentials.email}")

        user = get_user_by_email(db, user_credentials.email.__str__())
        if not user or not verify_password(user_credentials.password, user.hashed_password):
            logger.warning(f"Intento de login fallido para el email: {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info(f"Login exitoso para el email: {user_credentials.email}")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as ex:
        logger.error(f"Error en login: {str(ex)}")
        raise


@app.get(
    "/users/me",
    response_model=UserResponse,
    tags=["usuarios"],
    summary="Obtener usuario actual",
    description="Obtiene la información del usuario autenticado"
)
def read_users_me(current_user: UserModel = Depends(get_current_user)):
    try:
        logger.info(f"Consulta de perfil para el usuario: {current_user.email}")
        return current_user
    except Exception as ex:
        logger.error(f"Error al obtener perfil de usuario: {str(ex)}")
        raise


# Personalización del esquema OpenAPI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="API REST Segura",
        version="1.0.0",
        description="""
        API REST segura con características avanzadas:

        * **Autenticación**: Sistema JWT para gestión segura de sesiones
        * **Base de datos**: Soporte para MySQL, MSSQL, Oracle y SQLite
        * **Seguridad**: Implementación de recomendaciones OWASP
        * **Logging**: Sistema completo de registro de eventos
        * **Documentación**: API completamente documentada

        Para usar la API:
        1. Registra un nuevo usuario en `/register`
        2. Obtén un token JWT en `/login`
        3. Usa el token en el header `Authorization: Bearer <token>`
        """,
        routes=app.routes,
    )

    # Personalizar los tags
    openapi_schema["tags"] = [
        {
            "name": "usuarios",
            "description": "Operaciones con usuarios"
        },
        {
            "name": "autenticación",
            "description": "Operaciones de autenticación y autorización"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    # Configuración inicial de la aplicación
    logger.info("Iniciando aplicación...")

    # Crear las tablas en la base de datos
    try:
        db_manager.Base.metadata.create_all(bind=db_manager.engine)
        logger.info("Tablas de base de datos creadas exitosamente")
    except Exception as e:
        logger.error(f"Error al crear tablas en la base de datos: {str(e)}")
        raise

    # Iniciar el servidor
    logger.info("Iniciando servidor...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)