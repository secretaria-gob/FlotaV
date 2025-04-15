# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('database_standalone.py', '.'),
        ('auth.py', '.'),
        ('send_message.py', '.'),
        ('config.yaml', '.'),
        ('standalone_assets/config.yaml', 'standalone_assets'),
        ('.streamlit', '.streamlit')
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'sqlite3',
        'yaml',
        'sqlalchemy',
        'importlib_metadata',
        'streamlit.runtime',  # Nueva l�nea
        'streamlit.web',      # Nueva l�nea  # Nueva l�nea
        'streamlit_authenticator'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Gestion_Flota_Vehicular',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Gestion_Flota_Vehicular',
)
