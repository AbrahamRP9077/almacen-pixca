from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Enum, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum
from datetime import datetime

Base = declarative_base()


class Role(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    SUPER_ADMIN = "SUPER_ADMIN"


class TipoMovimiento(enum.Enum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"
    AJUSTE = "AJUSTE"


class Usuario(Base):
    __tablename__ = 'usuarios'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    nombre = Column(String(100))
    role = Column(Enum(Role), default=Role.USER)

    # Nota: No incluimos 'activo', 'fecha_creacion', 'ultimo_acceso' para mantener compatibilidad
    # con la BD existente

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nombre': self.nombre,
            'role': self.role.value if self.role else None
        }


class UnidadMedida(Base):
    __tablename__ = 'unidades_medida'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    abreviatura = Column(String(10))
    descripcion = Column(String(200))

    articulos = relationship('Articulo', back_populates='unidad_medida')


class Proveedor(Base):
    __tablename__ = 'proveedores'

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    ruc = Column(String(20), unique=True)  # Agregamos unique=True para validación
    telefono = Column(String(20))
    email = Column(String(100))
    direccion = Column(String(200))
    contacto = Column(String(100))
    observaciones = Column(Text)

    # Nota: No incluimos 'activo', 'fecha_registro' para mantener compatibilidad

    articulos = relationship('ArticuloProveedor', back_populates='proveedor')


class Articulo(Base):
    __tablename__ = 'articulos'

    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True)  # Agregamos unique=True para validación
    descripcion = Column(String(200), nullable=False)
    cantidad = Column(Float, default=0)
    stock_minimo = Column(Integer, default=0)
    stock_maximo = Column(Integer, default=999999)
    es_fiscal = Column(Boolean, default=False)
    unidad_medida_id = Column(Integer, ForeignKey('unidades_medida.id'))

    # Nota: No incluimos 'activo', 'fecha_creacion', 'ultima_actualizacion' para mantener compatibilidad

    unidad_medida = relationship('UnidadMedida', back_populates='articulos')
    proveedores = relationship('ArticuloProveedor', back_populates='articulo')


class ArticuloProveedor(Base):
    __tablename__ = 'articulos_proveedores'

    id = Column(Integer, primary_key=True)
    articulo_id = Column(Integer, ForeignKey('articulos.id'), nullable=False) # Asegurar nullable=False
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'), nullable=False) # Asegurar nullable=False
    es_preferente = Column(Boolean, default=False)

    # Relaciones: SOLO para navegación, SIN cascade adicional.
    # El cascade real se maneja en la BD o explícitamente como arriba.
    articulo = relationship('Articulo', back_populates='proveedores')
    proveedor = relationship('Proveedor', back_populates='articulos')


class MovimientoStock(Base):
    __tablename__ = 'movimientos_stock'

    id = Column(Integer, primary_key=True)
    articulo_id = Column(Integer, ForeignKey('articulos.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    tipo = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Float, nullable=False)
    cantidad_anterior = Column(Float)
    cantidad_nueva = Column(Float)
    observacion = Column(Text)
    fecha = Column(DateTime, default=datetime.now)

    # Relaciones
    articulo = relationship('Articulo')
    usuario = relationship('Usuario')