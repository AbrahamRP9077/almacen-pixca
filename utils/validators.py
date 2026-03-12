import re
from typing import Optional, Tuple, List
from database import get_session
from models import Articulo, Proveedor, UnidadMedida, Usuario


class Validators:

    @staticmethod
    def validar_codigo_articulo(codigo: str, articulo_id: Optional[int] = None) -> Tuple[bool, str]:
        """Valida que el código de artículo sea único"""
        if not codigo:
            return True, ""  # Código opcional

        session = get_session()
        try:
            query = session.query(Articulo).filter(Articulo.codigo == codigo)
            if articulo_id:
                query = query.filter(Articulo.id != articulo_id)

            existe = query.first()
            if existe:
                return False, f"Ya existe un artículo con el código '{codigo}'"
            return True, ""
        finally:
            session.close()

    @staticmethod
    def validar_nombre_proveedor(nombre: str, proveedor_id: Optional[int] = None) -> Tuple[bool, str]:
        """Valida que el nombre del proveedor sea único"""
        if not nombre:
            return False, "El nombre es obligatorio"

        session = get_session()
        try:
            query = session.query(Proveedor).filter(Proveedor.nombre == nombre)
            if proveedor_id:
                query = query.filter(Proveedor.id != proveedor_id)

            existe = query.first()
            if existe:
                return False, f"Ya existe un proveedor con el nombre '{nombre}'"
            return True, ""
        finally:
            session.close()

    @staticmethod
    def validar_ruc_proveedor(ruc: str, proveedor_id: Optional[int] = None) -> Tuple[bool, str]:
        """Valida el formato y unicidad del RUC"""
        if not ruc:
            return True, ""  # RUC opcional

        # Validar formato básico de RUC (ejemplo para Paraguay)
        if not re.match(r'^\d{6,8}-\d$', ruc):
            return False, "Formato de RUC inválido. Debe ser: 123456-0"

        session = get_session()
        try:
            query = session.query(Proveedor).filter(Proveedor.ruc == ruc)
            if proveedor_id:
                query = query.filter(Proveedor.id != proveedor_id)

            existe = query.first()
            if existe:
                return False, f"Ya existe un proveedor con el RUC '{ruc}'"
            return True, ""
        finally:
            session.close()

    @staticmethod
    def validar_email(email: str) -> Tuple[bool, str]:
        """Valida formato de email"""
        if not email:
            return True, ""  # Email opcional

        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(patron, email):
            return False, "Formato de email inválido"
        return True, ""

    @staticmethod
    def validar_telefono(telefono: str) -> Tuple[bool, str]:
        """Valida formato de teléfono"""
        if not telefono:
            return True, ""  # Teléfono opcional

        # Acepta varios formatos: (021) 123456, 021 123456, 0981 123456
        patron = r'^[\d\s\(\)\-+]{6,20}$'
        if not re.match(patron, telefono):
            return False, "Formato de teléfono inválido"
        return True, ""

    @staticmethod
    def validar_unidad_medida(nombre: str, unidad_id: Optional[int] = None) -> Tuple[bool, str]:
        """Valida que el nombre de la unidad sea único"""
        session = get_session()
        try:
            query = session.query(UnidadMedida).filter(UnidadMedida.nombre == nombre)
            if unidad_id:
                query = query.filter(UnidadMedida.id != unidad_id)

            existe = query.first()
            if existe:
                return False, f"Ya existe una unidad de medida con el nombre '{nombre}'"
            return True, ""
        finally:
            session.close()

    @staticmethod
    def validar_username(username: str, usuario_id: Optional[int] = None) -> Tuple[bool, str]:
        """Valida que el username sea único"""
        session = get_session()
        try:
            query = session.query(Usuario).filter(Usuario.username == username)
            if usuario_id:
                query = query.filter(Usuario.id != usuario_id)

            existe = query.first()
            if existe:
                return False, f"Ya existe un usuario con el username '{username}'"
            return True, ""
        finally:
            session.close()

    @staticmethod
    def validar_password(password: str) -> Tuple[bool, str]:
        """Valida la fortaleza de la contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"

        if not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una mayúscula"

        if not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una minúscula"

        if not re.search(r'\d', password):
            return False, "La contraseña debe contener al menos un número"

        return True, ""

    @staticmethod
    def validar_articulo_para_eliminar(articulo_id: int) -> Tuple[bool, str, List[str]]:
        """Verifica si un artículo puede ser eliminado"""
        session = get_session()
        try:
            articulo = session.query(Articulo).get(articulo_id)
            if not articulo:
                return False, "Artículo no encontrado", []

            advertencias = []

            # Verificar si tiene movimientos
            if articulo.movimientos:
                advertencias.append(f"Tiene {len(articulo.movimientos)} movimiento(s) de stock")

            # Verificar si tiene proveedores
            if articulo.proveedores:
                advertencias.append(f"Está asociado a {len(articulo.proveedores)} proveedor(es)")

            # Verificar si tiene stock
            if articulo.cantidad > 0:
                advertencias.append(f"Tiene {articulo.cantidad} unidades en stock")

            return True, "Puede ser eliminado", advertencias
        finally:
            session.close()

    @staticmethod
    def validar_proveedor_para_eliminar(proveedor_id: int) -> Tuple[bool, str, List[str]]:
        """Verifica si un proveedor puede ser eliminado"""
        session = get_session()
        try:
            proveedor = session.query(Proveedor).get(proveedor_id)
            if not proveedor:
                return False, "Proveedor no encontrado", []

            advertencias = []

            # Verificar si tiene artículos asociados
            if proveedor.articulos:
                advertencias.append(f"Está asociado a {len(proveedor.articulos)} artículo(s)")

            return True, "Puede ser eliminado", advertencias
        finally:
            session.close()