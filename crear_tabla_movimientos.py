import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from config import Config
from database import engine


def crear_tabla_movimientos():
    """Crea la tabla movimientos_stock si no existe"""

    print("🔧 Verificando/Creando tabla movimientos_stock...")

    inspector = inspect(engine)

    # Verificar si la tabla ya existe
    if 'movimientos_stock' not in inspector.get_table_names():
        with engine.connect() as conn:
            # Crear la tabla movimientos_stock
            conn.execute(text("""
                CREATE TABLE movimientos_stock (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    articulo_id INT NOT NULL,
                    usuario_id INT,
                    tipo ENUM('INGRESO', 'EGRESO', 'AJUSTE') NOT NULL,
                    cantidad FLOAT NOT NULL,
                    cantidad_anterior FLOAT,
                    cantidad_nueva FLOAT,
                    observacion TEXT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (articulo_id) REFERENCES articulos(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )
            """))
            conn.commit()
            print("✅ Tabla 'movimientos_stock' creada exitosamente!")
    else:
        print("ℹ️ La tabla 'movimientos_stock' ya existe")

    print("\n✅ Proceso completado!")


if __name__ == "__main__":
    crear_tabla_movimientos()