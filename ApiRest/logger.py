import logging
import sys
from pathlib import Path
from pythonjsonlogger import jsonlogger
from datetime import datetime

# Crear el directorio de logs si no existe
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurar el logger principal
logger = logging.getLogger("api")
logger.setLevel(logging.INFO)

# Handler para archivos JSON
json_handler = logging.FileHandler(filename=log_dir / f"api_{datetime.now().strftime('%Y%m%d')}.json")
json_handler.setFormatter(
    jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
)

# Handler para consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
)

logger.addHandler(json_handler)
logger.addHandler(console_handler)