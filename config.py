import os
from datetime import timedelta
from urllib.parse import quote_plus

class Config:
    # Database - conexión con parámetros adicionales para evitar timeouts
    DB_HOST = os.getenv('STOCKDB_MYSQL_HOST', 'stockdb-mysql.hpr-4a53b146.svc')
    DB_PORT = os.getenv('STOCKDB_MYSQL_PORT', '3306')
    DB_NAME = os.getenv('STOCKDB_MYSQL_DATABASE', 'hpr-4a53b146-stockdb')
    DB_USER = os.getenv('STOCKDB_MYSQL_USER', 'hpr-4a53b146-stockdb')
    DB_PASSWORD = os.getenv('STOCKDB_MYSQL_PASSWORD', 't109skbRw55uHruY')
    
    # Construir URL con parámetros de conexión
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?connect_timeout=60"           # Tiempo máximo de conexión
        "&read_timeout=60"              # Timeout de lectura
        "&write_timeout=60"              # Timeout de escritura
        "&charset=utf8mb4"               # Juego de caracteres
        "&pool_pre_ping=True"             # Verifica conexión antes de usarla
        "&pool_recycle=300"               # Recicla conexiones cada 5 minutos
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,                  # Tamaño del pool de conexiones
        'pool_pre_ping': True,             # Verifica la conexión antes de usarla
        'pool_recycle': 300,                # Recicla después de 5 minutos
    }

    # JWT para sesiones
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'janet-te-amo-mucho')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
