import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_session
from models import Articulo


def show():
    st.title("📦 Stock Actual")

    session = get_session()
    try:
        articulos = session.query(Articulo).all()

        if articulos:
            # Convertir a DataFrame
            data = []
            for art in articulos:
                data.append({
                    'ID': art.id,
                    'Código': art.codigo or '-',
                    'Descripción': art.descripcion,
                    'Cantidad': art.cantidad,
                    'Unidad': art.unidad_medida.nombre if art.unidad_medida else 'N/A',
                    'Tipo': 'Fiscal' if art.es_fiscal else 'No Fiscal',
                    'Stock Bajo': art.cantidad < 5,
                    'Proveedores': len(art.proveedores)
                })

            df = pd.DataFrame(data)

            # Filtros
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                busqueda = st.text_input("🔍 Buscar", placeholder="Descripción o código...")
            with col2:
                tipo_filtro = st.selectbox("Tipo", ["Todos", "Fiscal", "No Fiscal"])
            with col3:
                proveedores_filtro = st.selectbox("Proveedores", ["Todos", "Con proveedores", "Sin proveedores"])
            with col4:
                stock_filtro = st.selectbox("Stock", ["Todos", "Stock bajo (<5)"])

            # Aplicar filtros
            df_filtrado = df.copy()

            if busqueda:
                df_filtrado = df_filtrado[
                    df_filtrado['Descripción'].str.contains(busqueda, case=False) |
                    df_filtrado['Código'].str.contains(busqueda, case=False)
                    ]

            if tipo_filtro == "Fiscal":
                df_filtrado = df_filtrado[df_filtrado['Tipo'] == "Fiscal"]
            elif tipo_filtro == "No Fiscal":
                df_filtrado = df_filtrado[df_filtrado['Tipo'] == "No Fiscal"]

            if proveedores_filtro == "Con proveedores":
                df_filtrado = df_filtrado[df_filtrado['Proveedores'] > 0]
            elif proveedores_filtro == "Sin proveedores":
                df_filtrado = df_filtrado[df_filtrado['Proveedores'] == 0]

            if stock_filtro == "Stock bajo (<5)":
                df_filtrado = df_filtrado[df_filtrado['Stock Bajo'] == True]

            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total artículos", len(df_filtrado))
            with col2:
                st.metric("Stock bajo", len(df_filtrado[df_filtrado['Stock Bajo']]))
            with col3:
                st.metric("Fiscales", len(df_filtrado[df_filtrado['Tipo'] == 'Fiscal']))
            with col4:
                st.metric("Con proveedores", len(df_filtrado[df_filtrado['Proveedores'] > 0]))

            # Gráfico
            if len(df_filtrado[df_filtrado['Stock Bajo']]) > 0:
                st.warning(f"⚠️ Hay {len(df_filtrado[df_filtrado['Stock Bajo']])} artículos con stock bajo")

                fig = px.bar(
                    df_filtrado[df_filtrado['Stock Bajo']].sort_values('Cantidad'),
                    x='Descripción',
                    y='Cantidad',
                    title="Artículos con Stock Bajo",
                    color='Tipo',
                    text='Cantidad'
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

            # Tabla
            st.dataframe(
                df_filtrado.drop(columns=['ID', 'Stock Bajo', 'Proveedores']),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Cantidad": st.column_config.NumberColumn("Cantidad", format="%d"),
                    "Unidad": st.column_config.TextColumn("Unidad"),
                    "Tipo": st.column_config.TextColumn("Tipo")
                }
            )

        else:
            st.info("No hay artículos en el stock")

    finally:
        session.close()