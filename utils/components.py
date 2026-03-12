import streamlit as st
import pandas as pd


def mostrar_estadisticas():
    """Muestra estadísticas rápidas en la barra lateral"""
    from database import get_session
    from models import Articulo, Proveedor, UnidadMedida

    session = get_session()
    try:
        total_articulos = session.query(Articulo).count()
        total_proveedores = session.query(Proveedor).count()
        total_unidades = session.query(UnidadMedida).count()
        stock_bajo = session.query(Articulo).filter(Articulo.cantidad < 5).count()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 Artículos", total_articulos)
            st.metric("🏢 Proveedores", total_proveedores)
        with col2:
            st.metric("📏 Unidades", total_unidades)
            st.metric("⚠️ Stock Bajo", stock_bajo, delta_color="inverse")
    finally:
        session.close()


def tarjeta_articulo(articulo):
    """Muestra una tarjeta bonita para un artículo"""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{articulo.descripcion}**")
            st.caption(f"Código: {articulo.codigo or 'S/C'}")
        with col2:
            color = "normal" if articulo.cantidad >= 5 else "inverse"
            st.metric("Stock", int(articulo.cantidad), delta_color=color)
        with col3:
            if articulo.es_fiscal:
                st.markdown("🏷️ **Fiscal**")
            else:
                st.markdown("📦 **No Fiscal**")


def confirmar_accion(mensaje):
    """Diálogo de confirmación"""
    return st.warning(mensaje) and st.button("Sí, confirmar")