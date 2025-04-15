import streamlit as st

def check_authentication():
    """Simple authentication method using session state."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.name = None
    
    if not st.session_state.authenticated:
        # Create a simple login form
        with st.form("login_form"):
            st.title("Acceso al Sistema")
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión")
            
            # Simple authentication - requires username and password
            if submit:
                if not username or not password:
                    st.error("Por favor ingrese usuario y contraseña")
                else:
                    # This simulates a basic authentication
                    # In a real application, you would validate against a database
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.name = username.capitalize()
                    st.rerun()  # Refresh the page after successful login
    
    # Add logout functionality to sidebar
    if st.session_state.authenticated and st.sidebar.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.name = None
        st.rerun()
    
    if st.session_state.authenticated:
        st.sidebar.write(f"Bienvenido, **{st.session_state.name}**!")
        
    return (st.session_state.authenticated, 
            st.session_state.name, 
            st.session_state.username)

def get_user_role(username):
    """Determine the user's role based on username."""
    if username == "admin":
        return "admin"
    elif username == "manager":
        return "manager"
    else:
        return "operator"
