import streamlit as st
import pandas as pd
from database import get_session
from models import Usuario, Role
from utils.auth import AuthService
from utils.validators import Validators
from sqlalchemy.exc import IntegrityError
import random
import string


def generar_password_temporal():
    """Genera una contraseña temporal segura"""
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(caracteres) for _ in range(10))


def show():
    st.title("👥 Gestión de Usuarios")

    # Verificar que sea SUPER_ADMIN
    if st.session_state.usuario.role.value != 'SUPER_ADMIN':
        st.error("No tienes permisos para acceder a esta página")
        return

    session = get_session()

    try:
        # Tabs
        tab1, tab2 = st.tabs(["➕ Nuevo Usuario", "✏️ Editar/Eliminar"])

        # ========== TAB 1: NUEVO USUARIO ==========
        with tab1:
            st.subheader("Crear Nuevo Usuario")

            with st.form("nuevo_usuario"):
                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input("Nombre de usuario *", placeholder="Ej: jperez")

                    # Validar username en tiempo real
                    if username:
                        valido, msg = Validators.validar_username(username)
                        if not valido:
                            st.warning(msg)

                    nombre = st.text_input("Nombre completo *", placeholder="Ej: Juan Pérez")

                with col2:
                    role = st.selectbox(
                        "Rol *",
                        options=[r.value for r in Role],
                        format_func=lambda x: {
                            'SUPER_ADMIN': '👑 Super Administrador',
                            'ADMIN': '🛡️ Administrador',
                            'USER': '👤 Usuario'
                        }.get(x, x)
                    )

                    # Opción para generar contraseña automática
                    generar_pass = st.checkbox("Generar contraseña automática", value=True)

                    if generar_pass:
                        password_temp = generar_password_temporal()
                        st.info(f"Contraseña generada: `{password_temp}`")
                        st.caption("Guarde esta contraseña para entregarla al usuario")
                    else:
                        password = st.text_input("Contraseña *", type="password", placeholder="Mínimo 8 caracteres")
                        password_confirm = st.text_input("Confirmar contraseña *", type="password")

                submitted = st.form_submit_button("💾 Crear Usuario", use_container_width=True)

                if submitted:
                    errores = []

                    if not username:
                        errores.append("El nombre de usuario es obligatorio")
                    else:
                        valido, msg = Validators.validar_username(username)
                        if not valido:
                            errores.append(msg)

                    if not nombre:
                        errores.append("El nombre completo es obligatorio")

                    if generar_pass:
                        password_final = password_temp
                    else:
                        if not password:
                            errores.append("La contraseña es obligatoria")
                        elif password != password_confirm:
                            errores.append("Las contraseñas no coinciden")
                        else:
                            valido, msg = Validators.validar_password(password)
                            if not valido:
                                errores.append(msg)
                            else:
                                password_final = password

                    if errores:
                        for error in errores:
                            st.error(error)
                    else:
                        try:
                            AuthService.create_user(
                                username=username,
                                password=password_final,
                                nombre=nombre,
                                role=role
                            )
                            st.success("✅ Usuario creado exitosamente!")
                            if generar_pass:
                                st.info(f"⚠️ Contraseña del usuario: `{password_temp}`")
                            st.rerun()

                        except IntegrityError as e:
                            if "Duplicate entry" in str(e):
                                st.error(f"Error: Ya existe un usuario con el username '{username}'")
                            else:
                                st.error(f"Error de integridad: {str(e)}")
                        except Exception as e:
                            st.error(f"Error al crear usuario: {str(e)}")

        # ========== TAB 2: EDITAR/ELIMINAR ==========
        with tab2:
            st.subheader("Usuarios Existentes")

            # Filtros
            busqueda = st.text_input("🔍 Buscar usuario", placeholder="Username o nombre...")

            # Query base - Sin filtro de activo
            usuarios = session.query(Usuario).all()

            if usuarios:
                # Aplicar filtro de búsqueda
                usuarios_filtrados = usuarios
                if busqueda:
                    usuarios_filtrados = [
                        u for u in usuarios
                        if busqueda.lower() in u.username.lower() or
                           (u.nombre and busqueda.lower() in u.nombre.lower())
                    ]

                # Estadísticas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total usuarios", len(usuarios_filtrados))
                with col2:
                    super_admins = len([u for u in usuarios_filtrados if u.role.value == 'SUPER_ADMIN'])
                    st.metric("Super Admins", super_admins)
                with col3:
                    admins = len([u for u in usuarios_filtrados if u.role.value == 'ADMIN'])
                    st.metric("Admins", admins)
                with col4:
                    users = len([u for u in usuarios_filtrados if u.role.value == 'USER'])
                    st.metric("Usuarios", users)

                # Mostrar en tabla
                data = []
                for u in usuarios_filtrados:
                    data.append({
                        'ID': u.id,
                        'Username': u.username,
                        'Nombre': u.nombre or '-',
                        'Rol': u.role.value,
                        'Es actual': '✅' if u.id == st.session_state.usuario.id else ''
                    })

                df = pd.DataFrame(data)

                # Selector para editar
                usuario_seleccionado = st.selectbox(
                    "Seleccionar usuario para editar",
                    options=df['ID'].tolist(),
                    format_func=lambda
                        x: f"{df[df['ID'] == x]['Username'].iloc[0]} - {df[df['ID'] == x]['Nombre'].iloc[0]}"
                )

                if usuario_seleccionado:
                    usuario = session.query(Usuario).get(usuario_seleccionado)

                    if usuario:
                        # PRIMER FORMULARIO: Editar usuario
                        with st.form("editar_usuario"):
                            st.write(f"**ID:** {usuario.id}")
                            st.write(f"**Username:** {usuario.username}")

                            col1, col2 = st.columns(2)

                            with col1:
                                nuevo_nombre = st.text_input("Nombre completo", value=usuario.nombre or "")

                                # Cambiar contraseña
                                cambiar_pass = st.checkbox("Cambiar contraseña")
                                if cambiar_pass:
                                    nueva_password = st.text_input("Nueva contraseña", type="password")
                                    confirmar_password = st.text_input("Confirmar nueva contraseña", type="password")

                            with col2:
                                nuevo_rol = st.selectbox(
                                    "Rol",
                                    options=[r.value for r in Role],
                                    index=[r.value for r in Role].index(usuario.role.value),
                                    format_func=lambda x: {
                                        'SUPER_ADMIN': '👑 Super Administrador',
                                        'ADMIN': '🛡️ Administrador',
                                        'USER': '👤 Usuario'
                                    }.get(x, x)
                                )

                            # Advertencias
                            if usuario.id == 1:
                                st.warning("⚠️ Este es el superadministrador principal. Ten cuidado al modificarlo.")

                            if usuario.id == st.session_state.usuario.id:
                                st.info("ℹ️ Estás editando tu propio usuario")

                            # Botones del formulario
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                actualizar = st.form_submit_button("🔄 Actualizar", use_container_width=True)
                            with col2:
                                eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                            with col3:
                                reset_pass = st.form_submit_button("🔑 Resetear Password", use_container_width=True)
                            with col4:
                                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                            if actualizar:
                                errores = []

                                if not nuevo_nombre:
                                    errores.append("El nombre es obligatorio")

                                if cambiar_pass:
                                    if not nueva_password:
                                        errores.append("Debe ingresar la nueva contraseña")
                                    elif nueva_password != confirmar_password:
                                        errores.append("Las contraseñas no coinciden")
                                    else:
                                        valido, msg = Validators.validar_password(nueva_password)
                                        if not valido:
                                            errores.append(msg)

                                if errores:
                                    for error in errores:
                                        st.error(error)
                                else:
                                    try:
                                        usuario.nombre = nuevo_nombre
                                        usuario.role = nuevo_rol

                                        if cambiar_pass and nueva_password:
                                            usuario.password = AuthService.hash_password(nueva_password)

                                        session.commit()
                                        st.success("✅ Usuario actualizado!")

                                        # Si el usuario actual se cambió a sí mismo, actualizar sesión
                                        if usuario.id == st.session_state.usuario.id:
                                            st.session_state.usuario = usuario

                                        st.rerun()

                                    except Exception as e:
                                        session.rollback()
                                        st.error(f"Error al actualizar: {str(e)}")

                            if eliminar:
                                # Marcar para eliminar en la siguiente iteración
                                st.session_state['usuario_a_eliminar'] = usuario.id
                                st.session_state['mostrar_confirmacion_usuario'] = True
                                st.rerun()

                            if reset_pass:
                                nueva_pass = generar_password_temporal()
                                usuario.password = AuthService.hash_password(nueva_pass)
                                session.commit()
                                st.success(f"✅ Contraseña reseteada exitosamente!")
                                st.info(f"⚠️ Nueva contraseña: `{nueva_pass}`")

                        # SEGUNDA PARTE: Confirmación de eliminación (fuera del formulario)
                        if st.session_state.get('mostrar_confirmacion_usuario', False) and st.session_state.get(
                                'usuario_a_eliminar') == usuario.id:
                            st.warning("⚠️ ¿Estás seguro de que deseas eliminar este usuario?")

                            if usuario.id == 1:
                                st.error("❌ No se puede eliminar al superadministrador principal")
                                if st.button("🔙 Volver", key="volver_usuario"):
                                    st.session_state['mostrar_confirmacion_usuario'] = False
                                    st.session_state['usuario_a_eliminar'] = None
                                    st.rerun()
                            elif usuario.id == st.session_state.usuario.id:
                                st.error("❌ No puedes eliminarte a ti mismo")
                                if st.button("🔙 Volver", key="volver_usuario_mismo"):
                                    st.session_state['mostrar_confirmacion_usuario'] = False
                                    st.session_state['usuario_a_eliminar'] = None
                                    st.rerun()
                            else:
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Sí, eliminar", key=f"confirm_si_usr_{usuario.id}"):
                                        try:
                                            session.delete(usuario)
                                            session.commit()
                                            st.session_state['mostrar_confirmacion_usuario'] = False
                                            st.session_state['usuario_a_eliminar'] = None
                                            st.success("✅ Usuario eliminado!")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"Error al eliminar: {str(e)}")

                                with col2:
                                    if st.button("❌ No, cancelar", key=f"confirm_no_usr_{usuario.id}"):
                                        st.session_state['mostrar_confirmacion_usuario'] = False
                                        st.session_state['usuario_a_eliminar'] = None
                                        st.rerun()

                # Mostrar tabla
                st.subheader("Listado de Usuarios")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Es actual": st.column_config.TextColumn("Actual", width="small")
                    }
                )
            else:
                st.info("No hay usuarios registrados")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()