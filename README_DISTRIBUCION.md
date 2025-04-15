# Guía para Distribuir la Aplicación de Gestión de Flota Vehicular

Esta aplicación ha sido preparada para que pueda distribuirse como un ejecutable independiente en computadoras que no comparten red. Siga las instrucciones a continuación para crear y distribuir el ejecutable.

## Requisitos 

Para poder ejecutar el empaquetado, necesitará:

- Python 3.9 o superior instalado
- Todas las dependencias del proyecto instaladas (streamlit, pandas, etc.)
- PyInstaller (se instalará automáticamente durante el proceso)

## Instrucciones Paso a Paso

### 1. Descargar el Proyecto
Asegúrese de tener todo el código fuente de la aplicación descargado en su computadora.

### 2. Empaquetar la Aplicación
Hay dos formas de empaquetar la aplicación:

#### Método 1: Usando el Script Automatizado (Recomendado)
Simplemente ejecute el script `empaquetar_aplicacion.py` desde la línea de comandos:

```
python empaquetar_aplicacion.py
```

Este script realizará automáticamente todos los pasos necesarios y le informará cuando el proceso haya finalizado.

#### Método 2: Proceso Manual
Si prefiere hacerlo manualmente:

1. Ejecute el script de preparación:
   ```
   python setup_standalone.py
   ```

2. Cambie al directorio `standalone_app`:
   ```
   cd standalone_app
   ```

3. Ejecute el script de construcción:
   ```
   python build_exe.py
   ```

### 3. Distribuir la Aplicación

Una vez completado el proceso, encontrará el ejecutable en la carpeta:
`standalone_app/dist/Gestion_Flota_Vehicular/`

Para distribuir la aplicación:

1. Copie toda la carpeta `Gestion_Flota_Vehicular` a una unidad USB o compártala por otro medio.
2. En el equipo de destino, copie la carpeta completa a cualquier ubicación (escritorio, carpeta de programas, etc.)
3. Para iniciar la aplicación, el usuario simplemente debe hacer doble clic en el archivo `iniciar_aplicacion.bat` o directamente en `Gestion_Flota_Vehicular.exe`.

## Credenciales Predeterminadas

La aplicación viene con dos usuarios predefinidos:

- **Administrador**:
  - Usuario: `admin`
  - Contraseña: `admin123`

- **Usuario Regular**:
  - Usuario: `user`
  - Contraseña: `user123`

## Información Importante

- La aplicación empaquetada utiliza una base de datos SQLite local en lugar de PostgreSQL, lo que la hace completamente independiente.
- Cada instalación tendrá su propia base de datos, lo que significa que los datos no se comparten entre instalaciones.
- La base de datos se almacena en la carpeta `data` dentro del directorio de la aplicación.
- Para hacer copias de seguridad, simplemente copie el archivo `flota_vehicular.db` de la carpeta `data`.