"""VIALIS sencillo: muestra incidentes viales de demostración y las zonas con más riesgo.

Este archivo hace todo el trabajo:
1. Lee los datos del archivo data.csv.
2. Agrupa los incidentes en zonas pequeñas.
3. Muestra dos páginas: Resumen e Incidentes.
"""
import csv
from pathlib import Path

from flask import Flask, render_template
from jinja2 import DictLoader

# Las plantillas (páginas HTML) están guardadas dentro de este mismo archivo, al final.
app = Flask(__name__)

ARCHIVO_DATOS = Path(__file__).resolve().parent / "data.csv"
TAMANO_ZONA = 0.005  # en grados: aproximadamente 500 metros
GRAVEDAD = {"Leve": 1, "Moderada": 2, "Grave": 3, "Fatal": 4}


def leer_incidentes():
    """Lee data.csv y devuelve una lista de incidentes."""
    with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
        incidentes = list(csv.DictReader(archivo))
    for incidente in incidentes:
        incidente["latitud"] = float(incidente["latitud"])
        incidente["longitud"] = float(incidente["longitud"])
        incidente["gravedad"] = GRAVEDAD.get(incidente["severidad"], 1)
    return incidentes


def nivel_de(puntaje):
    """Convierte el puntaje de una zona en un nivel de riesgo (provisional)."""
    if puntaje >= 12:
        return "critico", "Crítico"
    if puntaje >= 8:
        return "alto", "Alto"
    if puntaje >= 4:
        return "moderado", "Moderado"
    return "bajo", "Bajo"


def calcular_zonas(incidentes):
    """Agrupa los incidentes por zona y suma la gravedad de cada zona."""
    zonas = {}
    for incidente in incidentes:
        i = round(incidente["latitud"] / TAMANO_ZONA)
        j = round(incidente["longitud"] / TAMANO_ZONA)
        clave = (i, j)
        if clave not in zonas:
            zonas[clave] = {
                "lat": round(i * TAMANO_ZONA, 4),
                "lng": round(j * TAMANO_ZONA, 4),
                "incidentes": 0,
                "puntaje": 0,
            }
        zonas[clave]["incidentes"] += 1
        zonas[clave]["puntaje"] += incidente["gravedad"]

    lista = sorted(zonas.values(), key=lambda z: z["puntaje"], reverse=True)
    for numero, zona in enumerate(lista, start=1):
        zona["nombre"] = f"Zona {numero}"
        zona["clase"], zona["nivel"] = nivel_de(zona["puntaje"])
    return lista


@app.route("/")
def inicio():
    incidentes = leer_incidentes()
    return render_template(
        "inicio.html",
        titulo="Resumen",
        total=len(incidentes),
        zonas=calcular_zonas(incidentes),
    )


@app.route("/incidentes")
def lista_incidentes():
    incidentes = sorted(leer_incidentes(), key=lambda i: (i["fecha"], i["hora"]), reverse=True)
    return render_template("incidentes.html", titulo="Incidentes", incidentes=incidentes)


# ---------------------------------------------------------------------------
# Plantillas (páginas HTML). Jinja las usa para rellenar los datos.
# ---------------------------------------------------------------------------

BASE = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VIALIS - {{ titulo }}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f1f5f9; color: #0f172a; }
    header { background: #0f172a; color: white; padding: 14px 24px; }
    header a { color: #93c5fd; margin-left: 16px; text-decoration: none; }
    main { max-width: 1000px; margin: 24px auto; padding: 0 16px; }
    .tarjeta { background: white; border-radius: 10px; padding: 16px 20px; margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 8px; border-bottom: 1px solid #e2e8f0; }
    .nivel { color: white; padding: 3px 10px; border-radius: 99px; font-weight: bold; }
    .critico { background: #b91c1c; }
    .alto { background: #ea580c; }
    .moderado { background: #2563eb; }
    .bajo { background: #16a34a; }
    .nota { color: #64748b; font-size: 14px; }
  </style>
</head>
<body>
  <header>
    <b>VIALIS</b>
    <a href="/">Resumen</a>
    <a href="/incidentes">Incidentes</a>
  </header>
  <main>
    {% block contenido %}{% endblock %}
    <p class="nota">Puntuación provisional y no oficial. Los datos son de demostración (SIMULADO).</p>
  </main>
</body>
</html>
"""

INICIO = """{% extends "base.html" %}
{% block contenido %}
<div class="tarjeta">
  <h1>Resumen</h1>
  <p>Incidentes de demostración: <b>{{ total }}</b></p>
  <p>Zonas (cuadros de unos 500 metros): <b>{{ zonas|length }}</b></p>
</div>

<div class="tarjeta">
  <h2>Zonas con más riesgo</h2>
  <table>
    <tr><th>Zona</th><th>Incidentes</th><th>Puntaje</th><th>Nivel</th><th>Mapa</th></tr>
    {% for zona in zonas[:10] %}
    <tr>
      <td>{{ zona.nombre }}</td>
      <td>{{ zona.incidentes }}</td>
      <td>{{ zona.puntaje }}</td>
      <td><span class="nivel {{ zona.clase }}">{{ zona.nivel }}</span></td>
      <td><a href="https://www.openstreetmap.org/?mlat={{ zona.lat }}&mlon={{ zona.lng }}&zoom=16" target="_blank">Abrir mapa</a></td>
    </tr>
    {% endfor %}
  </table>
  <p class="nota">
    Puntaje = suma de la gravedad de los incidentes de la zona
    (leve 1, moderada 2, grave 3, fatal 4).
  </p>
</div>
{% endblock %}
"""

INCIDENTES = """{% extends "base.html" %}
{% block contenido %}
<div class="tarjeta">
  <h1>Incidentes</h1>
  <table>
    <tr><th>Fecha</th><th>Hora</th><th>Categoría</th><th>Descripción</th><th>Severidad</th></tr>
    {% for incidente in incidentes %}
    <tr>
      <td>{{ incidente.fecha }}</td>
      <td>{{ incidente.hora }}</td>
      <td>{{ incidente.categoria }}</td>
      <td>{{ incidente.descripcion }}</td>
      <td>{{ incidente.severidad }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
"""

app.jinja_loader = DictLoader({
    "base.html": BASE,
    "inicio.html": INICIO,
    "incidentes.html": INCIDENTES,
})


if __name__ == "__main__":
    app.run(debug=True)
