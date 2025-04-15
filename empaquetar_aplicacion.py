import os
import subprocess
import sys
import shutil
import time

def main():
    """
    Script principal para empaquetar la aplicación de Gestión de Flota Vehicular
    """
    print("\n" + "=" * 80)
    print("EMPAQUETADO DE APLICACIÓN DE GESTIÓN DE FLOTA VEHICULAR".center(80))
    print("=" * 80 + "\n")
    
    print("Este script preparará la aplicación para ser distribuida como ejecutable.")
    print("El proceso puede tardar varios minutos en completarse.")
    print("\nPaso 1: Verificando requisitos...\n")
    
    # Verificar si PyInstaller está instalado
    try:
        import pyinstaller
        print("✓ PyInstaller está instalado.")
    except ImportError:
        print("PyInstaller no está instalado. Intentando instalar...")
        subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    print("\nPaso 2: Preparando archivos para la versión standalone...\n")
    
    # Ejecutar script de preparación
    if os.path.exists("setup_standalone.py"):
        subprocess.call([sys.executable, "setup_standalone.py"])
    else:
        print("Error: No se encontró el archivo setup_standalone.py")
        return
    
    # Verificar si se creó el directorio standalone_app
    if not os.path.exists("standalone_app"):
        print("Error: No se pudo crear el directorio standalone_app")
        return
    
    print("\nPaso 3: Creando el ejecutable...\n")
    
    # Cambiar al directorio standalone_app
    os.chdir("standalone_app")
    
    # Crear/ejecutar directamente PyInstaller con el spec actualizado
    print("Creando y ejecutando el script de empaquetado...")
    
    # Copiar el archivo spec actualizado
    shutil.copy("../gestflota.spec", "gestflota.spec")
    
    # Ejecutar PyInstaller con el archivo spec
    try:
        print("Ejecutando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "PyInstaller", "gestflota.spec"])
        print("PyInstaller completado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar PyInstaller: {e}")
        os.chdir("..")
        return
    
    # Volver al directorio principal
    os.chdir("..")
    
    # Verificar si se creó el directorio dist
    dist_dir = os.path.join("standalone_app", "dist", "Gestion_Flota_Vehicular")
    if os.path.exists(dist_dir):
        print("\n" + "=" * 80)
        print("¡EMPAQUETADO COMPLETADO CON ÉXITO!".center(80))
        print("=" * 80 + "\n")
        
        # Copiar instrucciones al directorio dist
        instruction_file = os.path.join("standalone_app", "README.md")
        if os.path.exists(instruction_file):
            shutil.copy(instruction_file, os.path.join(dist_dir, "README.md"))
        
        # Crear BAT mejorado para iniciar la aplicación
        bat_content = """@echo off
title Gestión de Flota Vehicular - Iniciando...
echo.
echo ================================================
echo           GESTIÓN DE FLOTA VEHICULAR
echo ================================================
echo.
echo Iniciando aplicación, por favor espere...
echo.
echo Al iniciar, se abrirá automáticamente su navegador.
echo Si la aplicación no se abre después de 10 segundos, 
echo verifique que no haya otra instancia ejecutándose.
echo.
echo Presione Ctrl+C para cancelar si es necesario.
echo.
start "" "%~dp0Gestion_Flota_Vehicular.exe"
echo Aplicación iniciada correctamente.
timeout /t 5
exit
"""
        with open(os.path.join(dist_dir, "iniciar_aplicacion.bat"), "w") as f:
            f.write(bat_content)
            
        # Crear BAT para diagnóstico si hay problemas
        diag_bat_content = """@echo on
title Gestión de Flota Vehicular - Diagnóstico
echo.
echo ================================================
echo       DIAGNÓSTICO DE FLOTA VEHICULAR
echo ================================================
echo.
echo Esta ventana mostrará información de diagnóstico
echo y permanecerá abierta para ayudar a solucionar problemas.
echo.
echo Iniciando aplicación en modo diagnóstico...
echo.
cd "%~dp0"
"%~dp0Gestion_Flota_Vehicular.exe"
echo.
echo ================================================
echo La aplicación ha terminado su ejecución.
echo Si vio mensajes de error, tome una captura de pantalla
echo y envíela al soporte técnico.
echo ================================================
echo.
pause
"""
        with open(os.path.join(dist_dir, "diagnostico.bat"), "w") as f:
            f.write(diag_bat_content)
        
        print(f"La aplicación se ha empaquetado correctamente y está lista para distribución.")
        print(f"Ubicación: {os.path.abspath(dist_dir)}")
        print("\nPara distribuir la aplicación:")
        print("1. Copie toda la carpeta 'Gestion_Flota_Vehicular' a una unidad USB o compártala")
        print("2. En el equipo de destino, los usuarios pueden ejecutar 'iniciar_aplicacion.bat'")
        print("\nCredenciales predeterminadas:")
        print("- Administrador: admin / admin123")
        print("- Usuario Regular: user / user123")
    else:
        print("\nError: No se pudo crear el ejecutable correctamente.")
        print("Revise los mensajes de error anteriores para más información.")

if __name__ == "__main__":
    main()