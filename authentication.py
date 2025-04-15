import streamlit as st
import bcrypt

# Base de datos simulada para usuarios (puede reemplazarse con una base de datos real)
USERS_DB = {
    "admin": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()),
    "user": bcrypt.hashpw("user123".encode(), bcrypt.gensalt())
}

def check_authentication():
    """Verifica la autenticación del usuario."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.name = None

    if not st.session_state.authenticated:
        # Formulario de inicio de sesión
        with st.form("login_form"):
            st.title("Acceso al Sistema")
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión")

            if submit:
                if username in USERS_DB and bcrypt.checkpw(password.encode(), USERS_DB[username]):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.name = username.capitalize()
                    st.experimental_rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")

    # Logout en la barra lateral
    if st.session_state.authenticated and st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.name = None
        st.experimental_rerun()

    if st.session_state.authenticated:
        st.sidebar.write(f"Bienvenido, **{st.session_state.name}**!")

    return (st.session_state.authenticated, st.session_state.name, st.session_state.username)