import os
import shutil
import subprocess
import sys

def build_executable():
    print("🚗 Iniciando empaquetado de la aplicación...")
    
    # Limpiar builds anteriores
    for dir in ["dist", "build"]:
        if os.path.exists(dir):
            shutil.rmtree(dir)
            print(f"🗑️ Directorio {dir} eliminado")

    # Configuración básica
    os.makedirs("standalone_assets", exist_ok=True)
    
    # 1. Crear archivo de configuración de autenticación
    with open("standalone_assets/config.yaml", "w") as f:
        f.write("""credentials:
  usernames:
    admin:
      name: Administrador
      password: $2b$12$Pb0ZxrCHNTPQoLsdBR1UGe6O.3n7ECVIcqiPXHH7qn.zpb2NnLoGK
      role: admin
    user:
      name: Usuario Básico
      password: $2b$12$lQOXx1.mfQz5GD9DJM.8SeWP1tCJ.2F/hPrtrrm85w7e6ATUlwglu
      role: user
cookie:
  expiry_days: 30
  key: flota_vehicular_app
  name: flota_cookie
""")

    # 2. Generar launcher optimizado
    with open("launcher.py", "w") as f:
        f.write("""import os
import sys
import streamlit.web.cli as stcli

def main():
    # Configuración del entorno
    os.environ.update({
        'STREAMLIT_SERVER_PORT': '8501',
        'STREAMLIT_SERVER_HEADLESS': 'false',
        'STREAMLIT_SERVER_ADDRESS': 'localhost'
    })
    
    # Configurar base de datos
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    os.environ['DATABASE_FILE'] = os.path.join(data_dir, "flota_vehicular.db")
    
    # Iniciar aplicación
    sys.argv = ["streamlit", "run", "app.py"]
    stcli.main()

if __name__ == "__main__":
    main()
""")

    # 3. Crear archivo .spec optimizado
    spec_content = """# -*- mode: python -*-
block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('database.py', '.'),  
        ('auth.py', '.'),
        ('config.yaml', '.'),
        ('standalone_assets/config.yaml', 'standalone_assets'),
        ('.streamlit', '.streamlit')
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'sqlalchemy',
        'sqlite3',
        'streamlit.runtime',
        'importlib.metadata'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], name='Gestion_Flota_Vehicular', debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='Gestion_Flota_Vehicular')"""
    
    with open("gestflota.spec", "w") as f:
        f.write(spec_content)

    # 4. Ejecutar PyInstaller
    print("🔨 Ejecutando PyInstaller...")
    result = subprocess.call(["pyinstaller", "gestflota.spec", "--noconfirm"])
    
    if result == 0:
        print("\n✅ ¡Empaquetado exitoso!")
        print("📦 Ejecutable generado en: dist/Gestion_Flota_Vehicular")
    else:
        print("\n❌ Error en el proceso. Revise los logs.")

if __name__ == "__main__":
    build_executable()