import streamlit as st
from utils.auth import AuthService
from utils.components import mostrar_estadisticas

# Configuración de la página
st.set_page_config(
    page_title="Control de Stock",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar estado de la sesión
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'pagina_actual' not in st.session_state:
    st.session_state.pagina_actual = 'login'


# Página de Login
def login_page():
    # Centrar el contenido
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        # Logo y título
        st.markdown("""
        <div style='text-align: center; padding: 2rem;'>
            <h1 style='font-size: 4rem; margin-bottom: 0;'>📦</h1>
            <h1>Control de Stock</h1>
            <p style='color: gray;'>Sistema de Gestión de Inventario</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("🔐 Contraseña", type="password", placeholder="Ingresa tu contraseña")

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                submit = st.form_submit_button("🚀 Iniciar Sesión", use_container_width=True)

            if submit:
                if not username or not password:
                    st.error("Por favor completa todos los campos")
                else:
                    usuario = AuthService.authenticate(username, password)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.session_state.pagina_actual = 'stock'
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")


# Barra lateral
def render_sidebar():
    with st.sidebar:
        # Información del usuario
        st.markdown(f"""
        <div style='padding: 1rem; background: #f0f2f6; border-radius: 10px; margin-bottom: 1rem;'>
            <p style='margin: 0; color: gray;'><strong>👤 {st.session_state.usuario.nombre}</strong></p>
            <p style='margin: 0; color: gray; font-size: 0.9rem;'>Rol: {st.session_state.usuario.role.value}</p>
        </div>
        """, unsafe_allow_html=True)

        # Estadísticas
        mostrar_estadisticas()

        st.markdown("---")

        # Navegación
        st.markdown("### 📋 Menú")

        # Definir páginas según rol
        pages = {
            "📦 Ver Stock": "stock",
            "📝 Administrar Artículos": "articulos",
            "🏢 Proveedores": "proveedores",
            "📏 Unidades de Medida": "unidades",
        }

        # Solo SUPER_ADMIN puede ver usuarios
        if st.session_state.usuario.role.value == 'SUPER_ADMIN':
            pages["👥 Usuarios"] = "usuarios"

        # Botones de navegación
        for page_name, page_key in pages.items():
            if st.button(
                    page_name,
                    key=f"nav_{page_key}",
                    use_container_width=True,
                    type="primary" if st.session_state.pagina_actual == page_key else "secondary"
            ):
                st.session_state.pagina_actual = page_key
                st.rerun()

        st.markdown("---")

        # Botón de cierre de sesión
        if st.button("🚪 Cerrar Sesión", use_container_width=True, type="primary"):
            st.session_state.usuario = None
            st.session_state.pagina_actual = 'login'
            st.rerun()


# Página principal
def main_page():
    render_sidebar()

    # Renderizar la página según la selección
    try:
        if st.session_state.pagina_actual == 'stock':
            from views.stock import show
            show()
        elif st.session_state.pagina_actual == 'articulos':
            if st.session_state.usuario.role.value in ['ADMIN', 'SUPER_ADMIN']:
                from views.articulos import show
                show()
            else:
                st.error("⛔ No tienes permisos para acceder a esta página")
        elif st.session_state.pagina_actual == 'proveedores':
            if st.session_state.usuario.role.value in ['ADMIN', 'SUPER_ADMIN']:
                from views.proveedores import show
                show()
            else:
                st.error("⛔ No tienes permisos para acceder a esta página")
        elif st.session_state.pagina_actual == 'unidades':
            if st.session_state.usuario.role.value in ['ADMIN', 'SUPER_ADMIN']:
                from views.unidades import show
                show()
            else:
                st.error("⛔ No tienes permisos para acceder a esta página")
        elif st.session_state.pagina_actual == 'usuarios':
            if st.session_state.usuario.role.value == 'SUPER_ADMIN':
                from views.usuarios import show
                show()
            else:
                st.error("⛔ No tienes permisos para acceder a esta página")
    except Exception as e:
        st.error(f"Error al cargar la página: {str(e)}")
        import traceback
        traceback.print_exc()


# Controlador principal
if st.session_state.usuario is None:
    login_page()
else:
    main_page()