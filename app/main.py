from typing import Optional

from fastapi import FastAPI

from app.config import get_database_path


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """Crea la aplicación. Recibir la ruta de la base permite aislar las pruebas."""
    app = FastAPI(
        title="API de novedades de inventario",
        version="1.0.0",
        description="Registro y consulta de novedades de inventario reportadas por tiendas.",
    )
    app.state.db_path = db_path or get_database_path()

    @app.get("/health", tags=["Sistema"])
    def health() -> dict:
        return {"estado": "ok"}

    return app


app = create_app()
