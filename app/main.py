from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.solicitudes import router
from app.config import get_database_path
from app.core.errors import ErrorDeDominio
from app.repositories.solicitudes import RepositorioSQLite
from app.services.solicitudes import ServicioSolicitudes


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

    @app.get("/health", tags=["Sistema"])
    def health() -> dict:
        return {"estado": "ok"}

    app.include_router(router)
    return app


app = create_app()
