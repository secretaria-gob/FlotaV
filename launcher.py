import os
import sys
import sqlite3
import streamlit.web.cli as stcli
from pathlib import Path

def main():
    # Configurar el entorno para modo standalone
    os.environ['STREAMLIT_SERVER_PORT'] = "8501"
    os.environ['STREAMLIT_SERVER_HEADLESS'] = "false"
    os.environ['STREAMLIT_SERVER_ADDRESS'] = "localhost"
    
    # Crear directorio de datos si no existe
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Ruta a la base de datos SQLite
    db_path = os.path.join(data_dir, "flota_vehicular.db")
    os.environ['DATABASE_FILE'] = db_path
    
    # Copiar config.yaml si no existe
    config_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(config_dir, "config.yaml")
    
    if not os.path.exists(config_path):
        assets_config = os.path.join(config_dir, "standalone_assets", "config.yaml")
        if os.path.exists(assets_config):
            import shutil
            shutil.copy(assets_config, config_path)
    
    # Obtener la ruta al script app.py
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
    
    # Iniciar Streamlit
    sys.argv = ["streamlit", "run", app_path]
    stcli.main()

if __name__ == "__main__":
    main()
