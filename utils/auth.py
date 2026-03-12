import bcrypt
import streamlit as st
from models import Usuario
from database import get_session


class AuthService:
    @staticmethod
    def hash_password(password):
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def check_password(hashed_password, password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def authenticate(username, password):
        session = get_session()
        try:
            # Versión compatible: no usamos el campo 'activo'
            usuario = session.query(Usuario).filter_by(username=username).first()
            if usuario and AuthService.check_password(usuario.password, password):
                return usuario
            return None
        finally:
            session.close()

    @staticmethod
    def create_user(username, password, nombre=None, role='USER'):
        session = get_session()
        try:
            # Verificar si ya existe
            existente = session.query(Usuario).filter_by(username=username).first()
            if existente:
                raise ValueError(f"Ya existe un usuario con el username '{username}'")

            hashed_password = AuthService.hash_password(password)
            usuario = Usuario(
                username=username,
                password=hashed_password,
                nombre=nombre,
                role=role
            )
            session.add(usuario)
            session.commit()
            return usuario
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()