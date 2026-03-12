import streamlit as st
import pandas as pd
from database import get_session
from models import Articulo, UnidadMedida, Proveedor, ArticuloProveedor, MovimientoStock, TipoMovimiento
from utils.validators import Validators
from sqlalchemy.exc import IntegrityError
from datetime import datetime


def show():
    st.title("📝 Administrar Artículos")

    # Verificar permisos
    if st.session_state.usuario.role.value not in ['ADMIN', 'SUPER_ADMIN']:
        st.error("⛔ No tienes permisos para acceder a esta página")
        return

    session = get_session()

    try:
        # Tabs para diferentes operaciones
        tab1, tab2, tab3 = st.tabs(["➕ Nuevo Artículo", "✏️ Editar/Eliminar", "📊 Movimientos"])

        # ========== TAB 1: NUEVO ARTÍCULO ==========
        with tab1:
            st.subheader("Crear Nuevo Artículo")

            with st.form("nuevo_articulo"):
                col1, col2 = st.columns(2)

                with col1:
                    codigo = st.text_input("Código", placeholder="Ej: ART-001",
                                           help="Código único del artículo (opcional)")

                    # Validar código en tiempo real
                    if codigo:
                        valido, msg = Validators.validar_codigo_articulo(codigo)
                        if not valido:
                            st.warning(msg)

                    descripcion = st.text_input("Descripción *", placeholder="Ej: Martillo 16oz")
                    cantidad = st.number_input("Cantidad Inicial", min_value=0.0, value=0.0, step=0.5)

                with col2:
                    # Unidades de medida
                    unidades = session.query(UnidadMedida).all()
                    if not unidades:
                        st.warning("⚠️ Debe crear unidades de medida primero")

                    unidad_opciones = {f"{u.nombre} ({u.abreviatura or 'N/A'})": u.id for u in unidades}
                    unidad_seleccionada = st.selectbox(
                        "Unidad de Medida *",
                        options=list(unidad_opciones.keys()) if unidad_opciones else ["Sin unidades"],
                        disabled=not unidades
                    )

                    es_fiscal = st.checkbox("Es Fiscal", value=False)

                    # Stock mínimo y máximo
                    col_min, col_max = st.columns(2)
                    with col_min:
                        stock_minimo = st.number_input("Stock Mínimo", min_value=0.0, value=0.0, step=1.0)
                    with col_max:
                        stock_maximo = st.number_input("Stock Máximo", min_value=0.0, value=999999.0, step=1.0)

                # Proveedores
                st.subheader("Proveedores")
                proveedores = session.query(Proveedor).all()
                if proveedores:
                    proveedores_seleccionados = st.multiselect(
                        "Seleccionar proveedores",
                        options=[(p.id, p.nombre) for p in proveedores],
                        format_func=lambda x: x[1]
                    )
                else:
                    st.info("No hay proveedores disponibles")
                    proveedores_seleccionados = []

                # Botón de submit del formulario
                submitted = st.form_submit_button("💾 Guardar Artículo", use_container_width=True)

                if submitted:
                    errores = []

                    # Validaciones
                    if not descripcion:
                        errores.append("La descripción es obligatoria")

                    if not unidades:
                        errores.append("Debe crear unidades de medida primero")

                    if codigo:
                        valido, msg = Validators.validar_codigo_articulo(codigo)
                        if not valido:
                            errores.append(msg)

                    if stock_minimo > stock_maximo:
                        errores.append("El stock mínimo no puede ser mayor al stock máximo")

                    if errores:
                        for error in errores:
                            st.error(error)
                    else:
                        try:
                            # Crear artículo
                            nuevo_articulo = Articulo(
                                codigo=codigo if codigo else None,
                                descripcion=descripcion,
                                cantidad=cantidad,
                                es_fiscal=es_fiscal,
                                stock_minimo=stock_minimo,
                                stock_maximo=stock_maximo,
                                unidad_medida_id=unidad_opciones[unidad_seleccionada] if unidades else None
                            )
                            session.add(nuevo_articulo)
                            session.flush()

                            # Agregar relaciones con proveedores
                            for proveedor_id, _ in proveedores_seleccionados:
                                # Verificar si ya existe la relación
                                existente = session.query(ArticuloProveedor).filter_by(
                                    articulo_id=nuevo_articulo.id,
                                    proveedor_id=proveedor_id
                                ).first()

                                if not existente:
                                    articulo_proveedor = ArticuloProveedor(
                                        articulo_id=nuevo_articulo.id,
                                        proveedor_id=proveedor_id
                                    )
                                    session.add(articulo_proveedor)

                            # Registrar movimiento inicial si hay cantidad
                            if cantidad > 0:
                                movimiento = MovimientoStock(
                                    articulo_id=nuevo_articulo.id,
                                    usuario_id=st.session_state.usuario.id,
                                    tipo=TipoMovimiento.INGRESO,
                                    cantidad=cantidad,
                                    cantidad_anterior=0,
                                    cantidad_nueva=cantidad,
                                    observacion="Stock inicial"
                                )
                                session.add(movimiento)

                            session.commit()
                            st.success("✅ Artículo creado exitosamente!")
                            st.rerun()

                        except IntegrityError as e:
                            session.rollback()
                            if "Duplicate entry" in str(e):
                                st.error("Error: Ya existe un artículo con ese código")
                            else:
                                st.error(f"Error de integridad: {str(e)}")
                        except Exception as e:
                            session.rollback()
                            st.error(f"Error al crear artículo: {str(e)}")

        # ========== TAB 2: EDITAR/ELIMINAR ==========
        with tab2:
            st.subheader("Artículos Existentes")

            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filtro_stock = st.selectbox("Filtrar por stock", ["Todos", "Stock bajo", "Sin stock", "Con stock"])
            with col2:
                busqueda = st.text_input("🔍 Buscar", placeholder="Código o descripción...")

            # Query base
            articulos = session.query(Articulo).all()

            if articulos:
                # Aplicar filtros
                articulos_filtrados = articulos

                if filtro_stock == "Stock bajo":
                    articulos_filtrados = [a for a in articulos_filtrados if a.cantidad <= (a.stock_minimo or 5)]
                elif filtro_stock == "Sin stock":
                    articulos_filtrados = [a for a in articulos_filtrados if a.cantidad == 0]
                elif filtro_stock == "Con stock":
                    articulos_filtrados = [a for a in articulos_filtrados if a.cantidad > 0]

                if busqueda:
                    articulos_filtrados = [
                        a for a in articulos_filtrados
                        if (a.codigo and busqueda.lower() in a.codigo.lower()) or
                           busqueda.lower() in a.descripcion.lower()
                    ]

                # Selector de artículo
                articulo_opciones = {
                    f"{a.codigo or 'S/C'} - {a.descripcion}": a.id
                    for a in articulos_filtrados
                }

                if articulo_opciones:
                    articulo_seleccionado = st.selectbox(
                        "Seleccionar artículo",
                        options=list(articulo_opciones.keys())
                    )

                    if articulo_seleccionado:
                        articulo_id = articulo_opciones[articulo_seleccionado]
                        articulo = session.query(Articulo).get(articulo_id)

                        if articulo:
                            # PRIMER FORMULARIO: Editar artículo
                            with st.form("editar_articulo"):
                                st.write(f"**ID:** {articulo.id}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    nuevo_codigo = st.text_input("Código", value=articulo.codigo or "")

                                    # Validar código en tiempo real
                                    if nuevo_codigo and nuevo_codigo != articulo.codigo:
                                        valido, msg = Validators.validar_codigo_articulo(nuevo_codigo, articulo.id)
                                        if not valido:
                                            st.warning(msg)

                                    nueva_descripcion = st.text_input("Descripción", value=articulo.descripcion)
                                    nueva_cantidad = st.number_input("Cantidad", value=float(articulo.cantidad),
                                                                     min_value=0.0, step=0.5)

                                with col2:
                                    # Unidades
                                    unidades = session.query(UnidadMedida).all()
                                    unidad_opciones = {u.id: f"{u.nombre} ({u.abreviatura or 'N/A'})" for u in unidades}
                                    nueva_unidad = st.selectbox(
                                        "Unidad de Medida",
                                        options=list(unidad_opciones.keys()),
                                        format_func=lambda x: unidad_opciones[x],
                                        index=list(unidad_opciones.keys()).index(
                                            articulo.unidad_medida_id) if articulo.unidad_medida_id and articulo.unidad_medida_id in unidad_opciones else 0
                                    )

                                    nuevo_fiscal = st.checkbox("Es Fiscal", value=articulo.es_fiscal)

                                    col_min, col_max = st.columns(2)
                                    with col_min:
                                        nuevo_stock_min = st.number_input("Stock Mínimo",
                                                                          value=float(articulo.stock_minimo or 0),
                                                                          min_value=0.0, step=1.0)
                                    with col_max:
                                        nuevo_stock_max = st.number_input("Stock Máximo",
                                                                          value=float(articulo.stock_maximo or 999999),
                                                                          min_value=0.0, step=1.0)

                                # Gestión de proveedores
                                st.subheader("Proveedores")

                                # Obtener proveedores actuales
                                relaciones_actuales = session.query(ArticuloProveedor).filter_by(
                                    articulo_id=articulo.id).all()
                                proveedores_actuales_ids = [r.proveedor_id for r in relaciones_actuales]

                                proveedores_disponibles = session.query(Proveedor).all()

                                if proveedores_disponibles:
                                    # Crear opciones para el multiselect
                                    opciones_proveedores = [(p.id, p.nombre) for p in proveedores_disponibles]

                                    # Valores por defecto (los actuales)
                                    default_values = [(p.id, p.nombre) for p in proveedores_disponibles if
                                                      p.id in proveedores_actuales_ids]

                                    nuevos_proveedores_widget = st.multiselect(
                                        "Seleccionar proveedores",
                                        options=opciones_proveedores,
                                        default=default_values,
                                        format_func=lambda x: x[1]
                                    )

                                    # Extraer IDs de los seleccionados
                                    nuevos_ids = [p[0] for p in nuevos_proveedores_widget]
                                else:
                                    st.info("No hay proveedores disponibles")
                                    nuevos_ids = []

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

                                    if not nueva_descripcion:
                                        errores.append("La descripción es obligatoria")

                                    if nuevo_codigo and nuevo_codigo != articulo.codigo:
                                        valido, msg = Validators.validar_codigo_articulo(nuevo_codigo, articulo.id)
                                        if not valido:
                                            errores.append(msg)

                                    if nuevo_stock_min > nuevo_stock_max:
                                        errores.append("El stock mínimo no puede ser mayor al stock máximo")

                                    if errores:
                                        for error in errores:
                                            st.error(error)
                                    else:
                                        try:
                                            # Registrar cambio de cantidad si es necesario
                                            if nueva_cantidad != articulo.cantidad:
                                                movimiento = MovimientoStock(
                                                    articulo_id=articulo.id,
                                                    usuario_id=st.session_state.usuario.id,
                                                    tipo=TipoMovimiento.AJUSTE,
                                                    cantidad=nueva_cantidad - articulo.cantidad,
                                                    cantidad_anterior=articulo.cantidad,
                                                    cantidad_nueva=nueva_cantidad,
                                                    observacion="Ajuste manual desde edición"
                                                )
                                                session.add(movimiento)

                                            # Actualizar artículo
                                            articulo.codigo = nuevo_codigo or None
                                            articulo.descripcion = nueva_descripcion
                                            articulo.cantidad = nueva_cantidad
                                            articulo.es_fiscal = nuevo_fiscal
                                            articulo.stock_minimo = nuevo_stock_min
                                            articulo.stock_maximo = nuevo_stock_max
                                            articulo.unidad_medida_id = nueva_unidad

                                            # --- GESTIÓN DE PROVEEDORES CORREGIDA PARA TU BD ---
                                            # 1. Eliminar relaciones que ya no existen
                                            ids_a_eliminar = set(proveedores_actuales_ids) - set(nuevos_ids)
                                            for proveedor_id in ids_a_eliminar:
                                                relacion = session.query(ArticuloProveedor).filter_by(
                                                    articulo_id=articulo.id,
                                                    proveedor_id=proveedor_id
                                                ).first()
                                                if relacion:
                                                    session.delete(relacion)

                                            # 2. Agregar nuevas relaciones
                                            ids_a_agregar = set(nuevos_ids) - set(proveedores_actuales_ids)
                                            for proveedor_id in ids_a_agregar:
                                                nueva_relacion = ArticuloProveedor(
                                                    articulo_id=articulo.id,
                                                    proveedor_id=proveedor_id,
                                                    es_preferente=False
                                                )
                                                session.add(nueva_relacion)
                                            # --- FIN DE LA CORRECCIÓN ---

                                            session.commit()
                                            st.success("✅ Artículo actualizado!")
                                            st.rerun()

                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"Error al actualizar: {str(e)}")

                                if eliminar:
                                    # Marcar para eliminar en la siguiente iteración
                                    st.session_state['articulo_a_eliminar'] = articulo.id
                                    st.session_state['mostrar_confirmacion'] = True
                                    st.rerun()

                            # SEGUNDA PARTE: Confirmación de eliminación (fuera del formulario)
                            if st.session_state.get('mostrar_confirmacion', False) and st.session_state.get(
                                    'articulo_a_eliminar') == articulo.id:
                                st.warning("⚠️ ¿Estás seguro de que deseas eliminar este artículo?")

                                # Verificar si tiene movimientos
                                movimientos_count = session.query(MovimientoStock).filter_by(
                                    articulo_id=articulo.id).count()
                                if movimientos_count > 0:
                                    st.info(
                                        f"Este artículo tiene {movimientos_count} movimiento(s) de stock que también se eliminarán.")

                                # Verificar relaciones con proveedores
                                relaciones_count = session.query(ArticuloProveedor).filter_by(
                                    articulo_id=articulo.id).count()
                                if relaciones_count > 0:
                                    st.info(f"Este artículo tiene {relaciones_count} proveedor(es) asociado(s).")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Sí, eliminar", key=f"confirm_si_{articulo.id}"):
                                        try:
                                            # IMPORTANTE: Como NO hay CASCADE en la BD, debemos eliminar manualmente
                                            # Primero eliminar relaciones con proveedores
                                            session.query(ArticuloProveedor).filter_by(articulo_id=articulo.id).delete()

                                            # Luego eliminar movimientos de stock
                                            session.query(MovimientoStock).filter_by(articulo_id=articulo.id).delete()

                                            # Finalmente eliminar el artículo
                                            session.delete(articulo)

                                            session.commit()
                                            st.session_state['mostrar_confirmacion'] = False
                                            st.session_state['articulo_a_eliminar'] = None
                                            st.success("✅ Artículo eliminado permanentemente!")
                                            st.rerun()
                                        except Exception as e:
                                            session.rollback()
                                            st.error(f"Error al eliminar: {str(e)}")

                                with col2:
                                    if st.button("❌ No, cancelar", key=f"confirm_no_{articulo.id}"):
                                        st.session_state['mostrar_confirmacion'] = False
                                        st.session_state['articulo_a_eliminar'] = None
                                        st.rerun()
                else:
                    st.info("No hay artículos que coincidan con los filtros")
            else:
                st.info("No hay artículos registrados")

        # ========== TAB 3: MOVIMIENTOS ==========
        with tab3:
            st.subheader("Movimientos de Stock")

            # Selector de artículo para ver movimientos
            articulos = session.query(Articulo).all()
            if articulos:
                articulo_opciones = {f"{a.codigo or 'S/C'} - {a.descripcion}": a.id for a in articulos}
                articulo_seleccionado = st.selectbox(
                    "Seleccionar artículo",
                    options=list(articulo_opciones.keys()),
                    key="mov_selector"
                )

                if articulo_seleccionado:
                    articulo_id = articulo_opciones[articulo_seleccionado]
                    movimientos = session.query(MovimientoStock).filter_by(articulo_id=articulo_id).order_by(
                        MovimientoStock.fecha.desc()).all()

                    if movimientos:
                        data = []
                        for m in movimientos:
                            data.append({
                                'Fecha': m.fecha.strftime('%d/%m/%Y %H:%M') if m.fecha else 'N/A',
                                'Tipo': m.tipo.value if m.tipo else 'N/A',
                                'Cantidad': m.cantidad,
                                'Stock Anterior': m.cantidad_anterior,
                                'Stock Nuevo': m.cantidad_nueva,
                                'Usuario': m.usuario.nombre if m.usuario else 'Sistema',
                                'Observación': m.observacion or ''
                            })

                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Estadísticas de movimientos
                        st.subheader("Resumen")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total movimientos", len(movimientos))
                        with col2:
                            ingresos = sum(1 for m in movimientos if m.tipo and m.tipo.value == 'INGRESO')
                            st.metric("Ingresos", ingresos)
                        with col3:
                            egresos = sum(1 for m in movimientos if m.tipo and m.tipo.value == 'EGRESO')
                            st.metric("Egresos", egresos)
                    else:
                        st.info("No hay movimientos para este artículo")
            else:
                st.info("No hay artículos registrados")

    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()