import os
import shutil
import sys
import streamlit as st

def setup_standalone_files():
    """
    Prepara los archivos necesarios para el empaquetado de la aplicación
    en modo standalone (sin conexión a PostgreSQL).
    """
    print("Configurando archivos para versión standalone...")
    
    # Crear directorio para la versión standalone si no existe
    standalone_dir = "standalone_app"
    os.makedirs(standalone_dir, exist_ok=True)
    
    # Copiar archivos necesarios al directorio standalone
    files_to_copy = [
        "app.py", 
        "auth.py", 
        "config.yaml",
        "build_exe.py",
        "send_message.py"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(standalone_dir, file))
            print(f"Copiado: {file}")
        else:
            print(f"Advertencia: No se encontró {file}")
    
    # Copiar el archivo database_standalone.py desde build_exe.py
    if os.path.exists("build_exe.py"):
        print("Creando archivo de base de datos para versión standalone...")
        
        # Ya se ha creado en build_exe.py, así que solo lo copiamos
        with open("database_standalone.py", "r") as source_file:
            database_content = source_file.read()
        
        with open(os.path.join(standalone_dir, "database.py"), "w") as target_file:
            target_file.write(database_content)
            print("Archivo database.py creado para modo standalone (SQLite)")
    
    # Crear directorio .streamlit si no existe
    streamlit_dir = os.path.join(standalone_dir, ".streamlit")
    os.makedirs(streamlit_dir, exist_ok=True)
    
    # Crear archivo de configuración de Streamlit
    config_content = """[server]
headless = false
port = 8501
address = "localhost"

[theme]
primaryColor = "#3872E0"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"""
    
    with open(os.path.join(streamlit_dir, "config.toml"), "w") as f:
        f.write(config_content)
        print("Archivo de configuración .streamlit/config.toml creado")
    
    # Crear un script de inicio simple para usuarios
    startup_bat = """@echo off
echo Iniciando Gestión de Flota Vehicular...
start "" "Gestion_Flota_Vehicular\\Gestion_Flota_Vehicular.exe"
"""
    
    with open(os.path.join(standalone_dir, "iniciar_aplicacion.bat"), "w") as f:
        f.write(startup_bat)
        print("Script de inicio iniciar_aplicacion.bat creado")
    
    # Crear un archivo README para instrucciones
    readme_content = """# Gestión de Flota Vehicular - Versión Standalone

Esta es la versión standalone (sin conexión) de la aplicación de Gestión de Flota Vehicular.

## Instrucciones de uso

1. Ejecute el archivo "iniciar_aplicacion.bat" para iniciar la aplicación.
2. La aplicación se abrirá en su navegador web predeterminado.
3. Utilice las siguientes credenciales para ingresar:
   - Usuario administrador: admin / admin123
   - Usuario regular: user / user123

## Empaquetado para distribución

Para crear un paquete ejecutable que puede distribuirse a otros equipos:

1. Asegúrese de tener instalado Python 3.9 o superior
2. Ejecute el archivo "build_exe.py" con Python
3. Espere a que finalice el proceso de empaquetado
4. El ejecutable y los archivos necesarios se crearán en la carpeta "dist/Gestion_Flota_Vehicular"
5. Copie toda la carpeta "Gestion_Flota_Vehicular" para distribuir la aplicación

## Datos de la aplicación

Todos los datos se almacenan localmente en una base de datos SQLite ubicada en la carpeta "data"
dentro del directorio de la aplicación.

Para realizar copias de seguridad, simplemente copie el archivo "flota_vehicular.db" de la carpeta "data".
"""
    
    with open(os.path.join(standalone_dir, "README.md"), "w") as f:
        f.write(readme_content)
        print("Archivo README.md creado con instrucciones")
    
    print("\nConfiguración completada con éxito!")
    print(f"Todos los archivos están en el directorio: {standalone_dir}")
    print("Para empaquetar la aplicación, vaya al directorio standalone_app y ejecute 'python build_exe.py'")

if __name__ == "__main__":
    setup_standalone_files()