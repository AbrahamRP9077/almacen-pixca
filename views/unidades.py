import streamlit as st
import pandas as pd
from database import get_session
from models import UnidadMedida, Articulo


def show():
    st.title("📏 Unidades de Medida")

    session = get_session()

    try:
        # Tabs
        tab1, tab2 = st.tabs(["➕ Nueva Unidad", "✏️ Editar/Eliminar"])

        with tab1:
            st.subheader("Crear Nueva Unidad de Medida")

            with st.form("nueva_unidad"):
                col1, col2 = st.columns(2)

                with col1:
                    nombre = st.text_input("Nombre *", placeholder="Ej: Kilogramo")
                    abreviatura = st.text_input("Abreviatura", placeholder="Ej: kg")

                with col2:
                    descripcion = st.text_input("Descripción", placeholder="Ej: Unidad de peso")

                submitted = st.form_submit_button("💾 Guardar Unidad", use_container_width=True)

                if submitted:
                    if not nombre:
                        st.error("El nombre es obligatorio")
                    else:
                        # Verificar si ya existe
                        existente = session.query(UnidadMedida).filter_by(nombre=nombre).first()
                        if existente:
                            st.error(f"Ya existe una unidad con el nombre '{nombre}'")
                        else:
                            nueva_unidad = UnidadMedida(
                                nombre=nombre,
                                abreviatura=abreviatura,
                                descripcion=descripcion
                            )
                            session.add(nueva_unidad)
                            session.commit()
                            st.success("✅ Unidad creada exitosamente!")
                            st.rerun()

        with tab2:
            st.subheader("Unidades Existentes")

            unidades = session.query(UnidadMedida).all()

            if unidades:
                # Estadísticas
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total unidades", len(unidades))
                with col2:
                    con_abreviatura = len([u for u in unidades if u.abreviatura])
                    st.metric("Con abreviatura", con_abreviatura)
                with col3:
                    # Unidades en uso
                    en_uso = 0
                    for u in unidades:
                        if session.query(Articulo).filter_by(unidad_medida_id=u.id).count() > 0:
                            en_uso += 1
                    st.metric("En uso", en_uso)

                # Buscador
                busqueda = st.text_input("🔍 Buscar unidad", placeholder="Nombre o abreviatura...")

                # Filtrar
                unidades_filtradas = unidades
                if busqueda:
                    unidades_filtradas = [
                        u for u in unidades
                        if busqueda.lower() in u.nombre.lower() or
                           (u.abreviatura and busqueda.lower() in u.abreviatura.lower())
                    ]

                # Mostrar en tabla
                data = []
                for u in unidades_filtradas:
                    cantidad_articulos = session.query(Articulo).filter_by(unidad_medida_id=u.id).count()
                    data.append({
                        'ID': u.id,
                        'Nombre': u.nombre,
                        'Abreviatura': u.abreviatura or '-',
                        'Descripción': u.descripcion or '-',
                        'Artículos': cantidad_articulos,
                        'En uso': '✅' if cantidad_articulos > 0 else '❌'
                    })

                df = pd.DataFrame(data)

                # Selector para editar
                unidad_seleccionada = st.selectbox(
                    "Seleccionar unidad para editar",
                    options=df['ID'].tolist(),
                    format_func=lambda x: df[df['ID'] == x]['Nombre'].iloc[0]
                )

                if unidad_seleccionada:
                    unidad = session.query(UnidadMedida).get(unidad_seleccionada)

                    if unidad:
                        with st.form("editar_unidad"):
                            col1, col2 = st.columns(2)

                            with col1:
                                nuevo_nombre = st.text_input("Nombre", value=unidad.nombre)
                                nueva_abreviatura = st.text_input("Abreviatura", value=unidad.abreviatura or "")

                            with col2:
                                nueva_descripcion = st.text_input("Descripción", value=unidad.descripcion or "")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                actualizar = st.form_submit_button("🔄 Actualizar", use_container_width=True)
                            with col2:
                                eliminar = st.form_submit_button("🗑️ Eliminar", use_container_width=True)
                            with col3:
                                cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)

                            if actualizar:
                                if not nuevo_nombre:
                                    st.error("El nombre es obligatorio")
                                else:
                                    # Verificar nombre único
                                    if nuevo_nombre != unidad.nombre:
                                        existente = session.query(UnidadMedida).filter_by(nombre=nuevo_nombre).first()
                                        if existente:
                                            st.error(f"Ya existe otra unidad con el nombre '{nuevo_nombre}'")
                                            return

                                    unidad.nombre = nuevo_nombre
                                    unidad.abreviatura = nueva_abreviatura or None
                                    unidad.descripcion = nueva_descripcion or None

                                    session.commit()
                                    st.success("✅ Unidad actualizada!")
                                    st.rerun()

                            if eliminar:
                                # Verificar si tiene artículos asociados
                                articulos_asociados = session.query(Articulo).filter_by(
                                    unidad_medida_id=unidad.id).count()
                                if articulos_asociados > 0:
                                    st.error(
                                        f"No se puede eliminar porque tiene {articulos_asociados} artículo(s) asociado(s)")
                                else:
                                    session.delete(unidad)
                                    session.commit()
                                    st.success("✅ Unidad eliminada!")
                                    st.rerun()

                # Mostrar tabla
                st.subheader("Listado de Unidades")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Artículos": st.column_config.NumberColumn("Artículos"),
                        "En uso": st.column_config.TextColumn("En uso", width="small")
                    }
                )
            else:
                st.info("No hay unidades de medida registradas")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        session.rollback()
    finally:
        session.close()