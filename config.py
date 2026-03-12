import os
from datetime import timedelta

class Config:
    # Database - conexión directa a Hostim
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://hpr-4a53b146-stockdb:t109skbRw55uHruY@"
        "stockdb-mysql.hpr-4a53b146.svc:3306/hpr-4a53b146-stockdb"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT para sesiones
    JWT_SECRET_KEY = "janet-te-amo-mucho"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)