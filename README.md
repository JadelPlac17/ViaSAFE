# VIALIS sencillo

Una versión básica de VIALIS para aprender y mostrar. Tiene dos páginas:

- **Resumen**: cuántos incidentes hay, cuántos son de noche, las zonas con más riesgo y el conteo por categoría.
- **Incidentes**: la lista de incidentes, con botones para filtrar por categoría y una columna que indica si fue de día o de noche.
- **Fuentes**: qué datos públicos existen en datos.gob.do (publicador, cobertura, actualización, licencia y advertencias). Describe las fuentes; no contiene los datos de los archivos.

Los datos son de demostración (SIMULADO). El puntaje es provisional y no es oficial.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `app.py` | El programa. Lee los datos y muestra las páginas. |
| `data.csv` | Los incidentes de demostración. Puedes abrirlo con Excel. |
| `requirements.txt` | Las librerías que necesita el programa. |
| `README.md` | Estas instrucciones. |

## Probarlo en tu computadora

1. Instala Python 3 desde python.org.
2. Abre una terminal dentro de esta carpeta.
3. Instala las librerías:
   ```
   py -m pip install -r requirements.txt
   ```
   (En Mac o Linux usa `python3` en lugar de `py`.)
4. Arranca el programa:
   ```
   py app.py
   ```
5. Abre el navegador en **http://127.0.0.1:5000**.

Para detenerlo, vuelve a la terminal y pulsa `Ctrl + C`.

## Subirlo a GitHub

1. Crea un repositorio nuevo en github.com (por ejemplo, `vialis-sencillo`). No marques ninguna opción extra.
2. Pulsa **uploading an existing file**.
3. Arrastra **los cuatro archivos** (`app.py`, `data.csv`, `requirements.txt`, `README.md`). No arrastres una carpeta.
4. Pulsa **Commit changes**.

## Publicarlo en Render

1. Entra en render.com con tu cuenta de GitHub.
2. Pulsa **New +** y elige **Web Service** (no Blueprint).
3. Elige el repositorio nuevo.
4. Completa:
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type:** Free
5. Pulsa **Deploy Web Service** y espera a que diga **Live**.
6. Abre la dirección que termina en `.onrender.com`.

Si algo falla, copia el texto rojo de la pestaña **Logs** y compártelo.

## Qué se dejó fuera (para más adelante)

Para mantenerlo simple no tiene: inicio de sesión, base de datos, mapa interactivo, importar archivos ni el modelo de cinco factores de la versión completa.
