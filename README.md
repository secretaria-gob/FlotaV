# Gestión de Flota Vehicular - Versión Standalone

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
