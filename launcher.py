import os
import sys
import sqlite3
import traceback
import webbrowser
import time
from pathlib import Path

def main():
    try:
        print("Iniciando aplicación de Gestión de Flota Vehicular...")
        
        # Configurar el entorno para modo standalone
        port = "8501"
        os.environ['STREAMLIT_SERVER_PORT'] = port
        os.environ['STREAMLIT_SERVER_HEADLESS'] = "false"
        os.environ['STREAMLIT_SERVER_ADDRESS'] = "localhost"
        
        # Crear directorio de datos si no existe
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        print(f"Directorio de datos creado en: {data_dir}")
        
        # Ruta a la base de datos SQLite
        db_path = os.path.join(data_dir, "flota_vehicular.db")
        os.environ['DATABASE_FILE'] = db_path
        print(f"Base de datos configurada en: {db_path}")
        
        # Copiar config.yaml si no existe
        config_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(config_dir, "config.yaml")
        
        if not os.path.exists(config_path):
            assets_config = os.path.join(config_dir, "standalone_assets", "config.yaml")
            if os.path.exists(assets_config):
                import shutil
                shutil.copy(assets_config, config_path)
                print(f"Archivo de configuración copiado de: {assets_config} a {config_path}")
            else:
                print(f"ADVERTENCIA: No se encontró el archivo de configuración en: {assets_config}")
        
        # Obtener la ruta al script app.py
        app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
        if not os.path.exists(app_path):
            print(f"ERROR: No se encontró el archivo app.py en: {app_path}")
            input("Presione Enter para salir...")
            return
        
        print(f"Usando archivo de aplicación: {app_path}")
        
        # Abrir el navegador automáticamente después de un breve retraso
        url = f"http://localhost:{port}"
        print(f"Abriendo navegador en: {url}")
        
        def open_browser():
            time.sleep(3)  # Esperar 3 segundos para que Streamlit se inicie
            webbrowser.open(url)
        
        import threading
        threading.Thread(target=open_browser).start()
        
        # Iniciar Streamlit
        print("Iniciando servidor Streamlit...")
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", app_path]
        stcli.main()
        
    except Exception as e:
        print(f"\nERROR: Se produjo un error al iniciar la aplicación:")
        print(f"{str(e)}")
        print("\nDetalles del error:")
        traceback.print_exc()
        print("\nPor favor, tome una captura de pantalla de este error y envíela al soporte técnico.")
        input("\nPresione Enter para salir...")

if __name__ == "__main__":
    main()
    # Si el programa llega aquí, es porque Streamlit ha terminado o ha ocurrido un error
    input("\nLa aplicación ha terminado. Presione Enter para salir...")
