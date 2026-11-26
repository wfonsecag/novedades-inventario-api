import os

DEFAULT_DATABASE_PATH = "novedades.db"


def get_database_path() -> str:
    """Ruta del archivo SQLite; se configura con la variable de entorno DATABASE_PATH."""
    return os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH)
