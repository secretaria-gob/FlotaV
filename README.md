# Gesti�n de Flota Vehicular - Versi�n Standalone

Esta es la versi�n standalone (sin conexi�n) de la aplicaci�n de Gesti�n de Flota Vehicular.

## Instrucciones de uso

1. Ejecute el archivo "iniciar_aplicacion.bat" para iniciar la aplicaci�n.
2. La aplicaci�n se abrir� en su navegador web predeterminado.
3. Utilice las siguientes credenciales para ingresar:
   - Usuario administrador: admin / admin123
   - Usuario regular: user / user123

## Empaquetado para distribuci�n

Para crear un paquete ejecutable que puede distribuirse a otros equipos:

1. Aseg�rese de tener instalado Python 3.9 o superior
2. Ejecute el archivo "build_exe.py" con Python
3. Espere a que finalice el proceso de empaquetado
4. El ejecutable y los archivos necesarios se crear�n en la carpeta "dist/Gestion_Flota_Vehicular"
5. Copie toda la carpeta "Gestion_Flota_Vehicular" para distribuir la aplicaci�n

## Datos de la aplicaci�n

Todos los datos se almacenan localmente en una base de datos SQLite ubicada en la carpeta "data"
dentro del directorio de la aplicaci�n.

Para realizar copias de seguridad, simplemente copie el archivo "flota_vehicular.db" de la carpeta "data".
