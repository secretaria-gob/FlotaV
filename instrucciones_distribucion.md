# Instrucciones para Distribuir la Aplicación de Gestión de Flota Vehicular

Este documento proporciona instrucciones detalladas para convertir la aplicación web en un programa ejecutable que puede distribuirse a computadoras sin conexión de red.

## Requisitos previos

Para crear el ejecutable, necesitará:

1. Python 3.9 o superior instalado en su computadora
2. Las bibliotecas requeridas instaladas (se instalarán automáticamente al ejecutar el proceso)
3. PyInstaller (se instalará automáticamente)

## Método simplificado (Recomendado)

Para mayor facilidad, ahora puede empaquetar la aplicación con un solo comando:

1. Ejecute el siguiente comando en una terminal desde el directorio principal del proyecto:
   ```
   python empaquetar_aplicacion.py
   ```

   Este comando realizará todo el proceso automáticamente, incluyendo:
   - Preparación de archivos para la versión standalone
   - Creación del ejecutable
   - Generación de scripts auxiliares para la ejecución

2. Al finalizar, encontrará la aplicación empaquetada en el directorio `standalone_app/dist/Gestion_Flota_Vehicular`

## Método manual (Alternativo)

Si prefiere realizar el proceso paso a paso:

### Paso 1: Preparar el entorno para distribución

Para preparar la aplicación para distribución standalone:

1. Ejecute el siguiente comando en una terminal:
   ```
   python setup_standalone.py
   ```

   Este comando creará un directorio `standalone_app` con todos los archivos necesarios para el empaquetado.

### Paso 2: Crear el ejecutable

Una vez que se haya creado el directorio de la aplicación standalone:

1. Copie el archivo `gestflota.spec` al directorio `standalone_app`

2. Navegue al directorio `standalone_app`:
   ```
   cd standalone_app
   ```

3. Ejecute PyInstaller con el archivo spec:
   ```
   python -m PyInstaller gestflota.spec
   ```

   Este proceso puede tardar varios minutos en completarse. Creará un directorio `dist` que contendrá la carpeta `Gestion_Flota_Vehicular` con todos los archivos ejecutables.

## Distribución de la aplicación

Para distribuir la aplicación a otros equipos:

1. Copie toda la carpeta `standalone_app/dist/Gestion_Flota_Vehicular` a una unidad USB o compártala por cualquier otro medio.
2. En el equipo de destino, copie toda la carpeta a cualquier ubicación (por ejemplo, el escritorio o el directorio de Programas).
3. Para ejecutar la aplicación, utilice uno de los siguientes métodos:
   - Haga doble clic en el archivo `iniciar_aplicacion.bat` (recomendado para uso normal)
   - Si experimenta problemas, utilice `diagnostico.bat` para ver mensajes de error

## Credenciales predeterminadas

La aplicación viene con las siguientes credenciales predeterminadas:

- **Administrador**:
  - Usuario: `admin`
  - Contraseña: `admin123`

- **Usuario Regular**:
  - Usuario: `user`
  - Contraseña: `user123`

## Notas importantes

- Cada instalación tendrá su propia base de datos local, lo que significa que los datos no se comparten entre diferentes instalaciones.
- La base de datos se almacena en la carpeta `data` que se crea automáticamente en el directorio de la aplicación.
- Para transferir datos entre instalaciones, necesitará copiar manualmente el archivo de base de datos `flota_vehicular.db` ubicado en la carpeta `data`.
- La base de datos se crea automáticamente en la primera ejecución. No elimine la carpeta `data` una vez que haya comenzado a usar la aplicación.
- Para realizar copias de seguridad, simplemente copie el archivo `flota_vehicular.db` de la carpeta `data`.

## Solución de problemas

- **Si la aplicación no se inicia:**
  - Asegúrese de que no haya otra instancia de la aplicación en ejecución.
  - Utilice el archivo `diagnostico.bat` para ver mensajes de error detallados.
  - Verifique que todos los archivos estén presentes en la carpeta de la aplicación.

- **Si ve errores relacionados con la base de datos:**
  - Verifique que la carpeta `data` existe y tiene permisos de escritura.
  - Si la base de datos está corrupta, puede eliminar el archivo `flota_vehicular.db` y reiniciar la aplicación para crear una nueva (perderá todos los datos).

- **Si la ventana se cierra inmediatamente:**
  - Ejecute la aplicación usando `diagnostico.bat` para ver mensajes de error.
  - En algunos sistemas puede ser necesario ejecutar como administrador la primera vez.

- **Si el navegador no se abre automáticamente:**
  - Espere unos segundos y abra manualmente su navegador.
  - Visite la dirección: `http://localhost:8501`
