import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.solicitudes import router
from app.config import get_database_path
from app.core.errors import CODIGOS_HTTP, MENSAJE_ERROR_INTERNO, ErrorDeDominio, respuesta_uniforme
from app.repositories.solicitudes import RepositorioSQLite
from app.services.solicitudes import ServicioSolicitudes

logger = logging.getLogger("novedades")


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """Crea la aplicación. Recibir la ruta de la base permite aislar las pruebas."""
    ruta = db_path or get_database_path()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # La base se abre al iniciar la aplicación, no al importar el módulo.
        app.state.servicio = ServicioSolicitudes(RepositorioSQLite(ruta))
        yield

    app = FastAPI(
        title="API de novedades de inventario",
        version="1.0.0",
        description="Registro y consulta de novedades de inventario reportadas por tiendas.",
        lifespan=lifespan,
    )
    app.state.db_path = ruta

    @app.exception_handler(ErrorDeDominio)
    async def manejar_error_de_dominio(_: Request, error: ErrorDeDominio) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content=error.como_respuesta())

    @app.exception_handler(StarletteHTTPException)
    async def manejar_error_http(_: Request, error: StarletteHTTPException) -> JSONResponse:
        codigo, mensaje = CODIGOS_HTTP.get(error.status_code, ("ERROR_HTTP", str(error.detail)))
        return JSONResponse(
            status_code=error.status_code,
            content=respuesta_uniforme(codigo, mensaje),
            headers=getattr(error, "headers", None),
        )

    @app.exception_handler(Exception)
    async def manejar_error_inesperado(_: Request, error: Exception) -> JSONResponse:
        # Se registra el detalle en el log del servidor; al cliente nunca se le expone.
        logger.exception("Error no controlado", exc_info=error)
        return JSONResponse(status_code=500, content=respuesta_uniforme("ERROR_INTERNO", MENSAJE_ERROR_INTERNO))

    @app.get("/health", tags=["Sistema"])
    def health() -> dict:
        return {"estado": "ok"}

    app.include_router(router)
    return app


app = create_app()
