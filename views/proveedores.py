import streamlit as st
import pandas as pd
from database import get_session
from models import Proveedor, ArticuloProveedor, Articulo
from utils.validators import Validators
from sqlalchemy.exc import IntegrityError


def show():
    st.title("🏢 Gestión de Proveedores")

    # Verificar permisos
    if st.session_state.usuario.role.value not in ['ADMIN', 'SUPER_ADMIN']:
        st.error("⛔ No tienes permisos para acceder a esta página")
        return

    session = get_session()

    try:
        # Tabs
        tab1, tab2 = st.tabs(["➕ Nuevo Proveedor", "✏️ Editar/Eliminar"])

        # ========== TAB 1: NUEVO PROVEEDOR ==========
        with tab1:
            st.subheader("Crear Nuevo Proveedor")

            with st.form("nuevo_proveedor"):
                col1, col2 = st.columns(2)

                with col1:
                    nombre = st.text_input("Nombre *", placeholder="Ej: Distribuidora ABC")

                    # Validar nombre en tiempo real
                    if nombre:
                        valido, msg = Validators.validar_nombre_proveedor(nombre)
                        if not valido:
                            st.warning(msg)

                    ruc = st.text_input("RUC", placeholder="Ej: 1234567-0",
                                        help="Formato: 1234567-0")

                    # Validar RUC en tiempo real
                    if ruc:
                        valido, msg = Validators.validar_ruc_proveedor(ruc)
                        if not valido:
                            st.warning(msg)

                    telefono = st.text_input("Teléfono", placeholder="Ej: 021 123456")

                    # Validar teléfono
                    if telefono:
                        valido, msg = Validators.validar_telefono(telefono)
                        if not valido:
                            st.warning(msg)

                with col2:
                    email = st.text_input("Email", placeholder="Ej: contacto@abc.com")

                    # Validar email
                    if email:
                        valido, msg = Validators.validar_email(email)
                        if not valido:
                            st.warning(msg)

                    direccion = st.text_input("Dirección", placeholder="Ej: Av. Principal 123")
                    contacto = st.text_input("Persona de Contacto", placeholder="Ej: Juan Pérez")
                    observaciones = st.text_area("Observaciones", placeholder="Notas adicionales...")

                submitted = st.form_submit_button("💾 Guardar Proveedor", use_container_width=True)

                if submitted:
                    errores = []

                    # Validaciones
                    if not nombre:
                        errores.append("El nombre es obligatorio")
                    else:
                        valido, msg = Validators.validar_nombre_proveedor(nombre)
                        if not valido:
                            errores.append(msg)

                    if ruc:
                        valido, msg = Validators.validar_ruc_proveedor(ruc)
                        if not valido:
                            errores.append(msg)

                    if email:
                        valido, msg = Validators.validar_email(email)
                        if not valido:
                            errores.append(msg)

                    if telefono:
                        valido, msg = Validators.validar_telefono(telefono)
                        if not valido:
                            errores.append(msg)

                    if errores:
                        for error in errores:
                            st.error(error)
                    else:
                        try:
                            nuevo_proveedor = Proveedor(
                                nombre=nombre,
                                ruc=ruc or None,
                                telefono=telefono or None,
                                email=email or None,
                                direccion=direccion or None,
                                contacto=contacto or None,
                                observaciones=observaciones or None
                            )
                            session.add(nuevo_proveedor)
                            session.commit()
                            st.success("✅ Proveedor creado exitosamente!")
                            st.rerun()

                        except IntegrityError as e:
                            session.rollback()
                            if "Duplicate entry" in str(e):
                                if "ruc" in str(e).lower():
                                    st.error(f"Error: Ya existe un proveedor con ese RUC")
                                elif "nombre" in str(e).lower():
                                    st.error(f"Error: Ya existe un proveedor con ese nombre")
                                else:
                                    st.error(f"Error: El proveedor ya existe (duplicado)")
                            else:
                                st.error(f"Error de integridad: {str(e)}")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error al crear proveedor: {str(e)}")

        # ========== TAB 2: EDITAR/ELIMINAR ==========
        with tab2:
            st.subheader("Proveedores Existentes")

            # Filtros
            busqueda = st.text_input("🔍 Buscar proveedor", placeholder="Nombre o RUC...")

            # Query base
            proveedores = session.query(Proveedor).all()

            if proveedores:
                # Aplicar filtro de búsqueda
                proveedores_filtrados = proveedores
                if busqueda:
                    proveedores_filtrados = [
                        p for p in proveedores
                        if busqueda.lower() in p.nombre.lower() or
                           (p.ruc and busqueda in p.ruc)
                    ]

                # Mostrar estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total proveedores", len(proveedores_filtrados))
                with col2:
                    con_articulos = 0
                    for p in proveedores_filtrados:
                        if session.query(ArticuloProveedor).filter_by(proveedor_id=p.id).count() > 0:
                            con_articulos += 1
                    st.metric("Con artículos", con_articulos)
                with col3:
                    with_ruc = len([p for p in proveedores_filtrados if p.ruc])
                    st.metric("Con RUC", with_ruc)

                # Mostrar en tabla
                data = []
                for p in proveedores_filtrados:
                    cantidad_articulos = session.query(ArticuloProveedor).filter_by(proveedor_id=p.id).count()
                    data.append({
                        'ID': p.id,
                        'Nombre': p.nombre,
                        'RUC': p.ruc or '-',
                        'Teléfono': p.telefono or '-',
                        'Email': p.email or '-',
                        'Contacto': p.contacto or '-',
                        'Artículos': cantidad_articulos
                    })

                df = pd.DataFrame(data)

                # Selector de proveedor para editar
                proveedor_seleccionado = st.selectbox(
                    "Seleccionar proveedor para editar",
                    options=df['ID'].tolist(),
                    format_func=lambda x: f"{df[df['ID'] == x]['Nombre'].iloc[0]}"
                )

                if proveedor_seleccionado:
                    proveedor = session.query(Proveedor).get(proveedor_seleccionado)

                    if proveedor:
                        # PRIMER FORMULARIO: Editar proveedor
                        with st.form("editar_proveedor"):
                            col1, col2 = st.columns(2)

                            with col1:
                                nuevo_nombre = st.text_input("Nombre", value=proveedor.nombre)

                                # Validar nombre en tiempo real
                                if nuevo_nombre and nuevo_nombre != proveedor.nombre:
                                    valido, msg = Validators.validar_nombre_proveedor(nuevo_nombre, proveedor.id)
                                    if not valido:
                                        st.warning(msg)

                                nuevo_ruc = st.text_input("RUC", value=proveedor.ruc or "")

                                # Validar RUC
                                if nuevo_ruc and nuevo_ruc != proveedor.ruc:
                                    valido, msg = Validators.validar_ruc_proveedor(nuevo_ruc, proveedor.id)
                                    if not valido:
                                        st.warning(msg)

                                nuevo_telefono = st.text_input("Teléfono", value=proveedor.telefono or "")
                                if nuevo_telefono and nuevo_telefono != proveedor.telefono:
                                    valido, msg = Validators.validar_telefono(nuevo_telefono)
                                    if not valido:
                                        st.warning(msg)

                            with col2:
                                nuevo_email = st.text_input("Email", value=proveedor.email or "")
                                if nuevo_email and nuevo_email != proveedor.email:
                                    valido, msg = Validators.validar_email(nuevo_email)
                                    if not valido:
                                        st.warning(msg)

                                nueva_direccion = st.text_input("Dirección", value=proveedor.direccion or "")
                                nuevo_contacto = st.text_input("Contacto", value=proveedor.contacto or "")
                                nuevas_observaciones = st.text_area("Observaciones",
                                                                    value=proveedor.observaciones or "")

                            # Mostrar artículos asociados
                            if proveedor.articulos:
                                st.subheader("Artículos que provee")
                                articulos_data = []
                                for ap in proveedor.articulos:
                                    articulo = session.query(Articulo).get(ap.articulo_id)
                                    if articulo:
                                        articulos_data.append({
                                            'Código': articulo.codigo or '-',
                                            'Descripción': articulo.descripcion,
                                            'Preferente': '✅' if ap.es_preferente else '❌'
                                        })
                                if articulos_data:
                                    st.dataframe(pd.DataFrame(articulos_data), hide_index=True)

                            # Botones del formulario
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                actualizar = st.form_submit_button("🔄 Actualizar", use_container_width=True)
                            with col2:
                                eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                            with col3:
                                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                            if actualizar:
                                errores = []

                                if not nuevo_nombre:
                                    errores.append("El nombre es obligatorio")
                                else:
                                    valido, msg = Validators.validar_nombre_proveedor(nuevo_nombre, proveedor.id)
                                    if not valido:
                                        errores.append(msg)

                                if nuevo_ruc and nuevo_ruc != proveedor.ruc:
                                    valido, msg = Validators.validar_ruc_proveedor(nuevo_ruc, proveedor.id)
                                    if not valido:
                                        errores.append(msg)

                                if nuevo_email:
                                    valido, msg = Validators.validar_email(nuevo_email)
                                    if not valido:
                                        errores.append(msg)

                                if nuevo_telefono:
                                    valido, msg = Validators.validar_telefono(nuevo_telefono)
                                    if not valido:
                                        errores.append(msg)

                                if errores:
                                    for error in errores:
                                        st.error(error)
                                else:
                                    try:
                                        proveedor.nombre = nuevo_nombre
                                        proveedor.ruc = nuevo_ruc or None
                                        proveedor.telefono = nuevo_telefono or None
                                        proveedor.email = nuevo_email or None
                                        proveedor.direccion = nueva_direccion or None
                                        proveedor.contacto = nuevo_contacto or None
                                        proveedor.observaciones = nuevas_observaciones or None

                                        session.commit()
                                        st.success("✅ Proveedor actualizado!")
                                        st.rerun()

                                    except IntegrityError as e:
                                        session.rollback()
                                        if "Duplicate entry" in str(e):
                                            if "ruc" in str(e).lower():
                                                st.error("Error: Ya existe otro proveedor con ese RUC")
                                            elif "nombre" in str(e).lower():
                                                st.error("Error: Ya existe otro proveedor con ese nombre")
                                            else:
                                                st.error("Error: El proveedor ya existe (duplicado)")
                                        else:
                                            st.error(f"Error de integridad: {str(e)}")
                                    except Exception as e:
                                        session.rollback()
                                        st.error(f"Error al actualizar: {str(e)}")

                            if eliminar:
                                # Marcar para eliminar en la siguiente iteración
                                st.session_state['proveedor_a_eliminar'] = proveedor.id
                                st.session_state['mostrar_confirmacion_proveedor'] = True
                                st.rerun()

                        # SEGUNDA PARTE: Confirmación de eliminación (fuera del formulario)
                        if st.session_state.get('mostrar_confirmacion_proveedor', False) and st.session_state.get(
                                'proveedor_a_eliminar') == proveedor.id:
                            st.warning("⚠️ ¿Estás seguro de que deseas eliminar este proveedor?")

                            # Verificar si tiene artículos asociados
                            articulos_asociados = session.query(ArticuloProveedor).filter_by(
                                proveedor_id=proveedor.id).count()

                            if articulos_asociados > 0:
                                st.error(
                                    f"❌ No se puede eliminar porque tiene {articulos_asociados} artículo(s) asociado(s).")
                                st.info("Primero debe eliminar las relaciones del proveedor con los artículos.")

                                if st.button("🔙 Volver", key="volver_proveedor"):
                                    st.session_state['mostrar_confirmacion_proveedor'] = False
                                    st.session_state['proveedor_a_eliminar'] = None
                                    st.rerun()
                            else:
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Sí, eliminar", key=f"confirm_si_prov_{proveedor.id}"):
                                        try:
                                            session.delete(proveedor)
                                            session.commit()
                                            st.session_state['mostrar_confirmacion_proveedor'] = False
                                            st.session_state['proveedor_a_eliminar'] = None
                                            st.success("✅ Proveedor eliminado!")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"Error al eliminar: {str(e)}")

                                with col2:
                                    if st.button("❌ No, cancelar", key=f"confirm_no_prov_{proveedor.id}"):
                                        st.session_state['mostrar_confirmacion_proveedor'] = False
                                        st.session_state['proveedor_a_eliminar'] = None
                                        st.rerun()

                # Mostrar tabla completa
                st.subheader("Listado de Proveedores")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Artículos": st.column_config.NumberColumn("Artículos", help="Cantidad de artículos que provee")
                    }
                )
            else:
                st.info("No hay proveedores registrados")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()