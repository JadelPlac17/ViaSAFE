"""VIALIS sencillo: muestra incidentes viales de demostración y las zonas con más riesgo.

Este archivo hace todo el trabajo:
1. Lee los datos del archivo data.csv.
2. Agrupa los incidentes en zonas pequeñas y cuenta por categoría.
3. Muestra dos páginas: Resumen e Incidentes (con filtro por categoría).
"""
import csv
from pathlib import Path

from flask import Flask, render_template, request
from jinja2 import DictLoader

# Las plantillas (páginas HTML) están guardadas dentro de este mismo archivo, al final.
app = Flask(__name__)

ARCHIVO_DATOS = Path(__file__).resolve().parent / "data.csv"
TAMANO_ZONA = 0.005  # en grados: aproximadamente 500 metros
GRAVEDAD = {"Leve": 1, "Moderada": 2, "Grave": 3, "Fatal": 4}


def es_de_noche(hora):
    """Devuelve True si la hora está entre las 18:00 y las 06:00."""
    hora_numero = int(hora.split(":")[0])
    return hora_numero >= 18 or hora_numero < 6


def leer_incidentes():
    """Lee data.csv y devuelve una lista de incidentes."""
    with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
        incidentes = list(csv.DictReader(archivo))
    for incidente in incidentes:
        incidente["latitud"] = float(incidente["latitud"])
        incidente["longitud"] = float(incidente["longitud"])
        incidente["gravedad"] = GRAVEDAD.get(incidente["severidad"], 1)
        incidente["de_noche"] = es_de_noche(incidente["hora"])
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
    maximo = lista[0]["puntaje"] if lista else 1  # para dibujar la barra de cada zona
    for numero, zona in enumerate(lista, start=1):
        zona["nombre"] = f"Zona {numero}"
        zona["porcentaje"] = round(zona["puntaje"] * 100 / maximo)
        zona["clase"], zona["nivel"] = nivel_de(zona["puntaje"])
    return lista


def contar_por_categoria(incidentes):
    """Cuenta cuántos incidentes hay de cada categoría, del que más tiene al que menos."""
    cuentas = {}
    for incidente in incidentes:
        categoria = incidente["categoria"]
        cuentas[categoria] = cuentas.get(categoria, 0) + 1
    return sorted(cuentas.items(), key=lambda par: par[1], reverse=True)


@app.route("/")
def inicio():
    incidentes = leer_incidentes()
    return render_template(
        "inicio.html",
        titulo="Resumen",
        pagina="inicio",
        total=len(incidentes),
        graves=sum(1 for i in incidentes if i["gravedad"] >= 3),
        de_noche=sum(1 for i in incidentes if i["de_noche"]),
        zonas=calcular_zonas(incidentes),
        por_categoria=contar_por_categoria(incidentes),
    )


@app.route("/incidentes")
def lista_incidentes():
    # Si la dirección trae ?categoria=..., mostramos solo esa categoría.
    categoria = request.args.get("categoria", "")

    todos = leer_incidentes()
    categorias = sorted({incidente["categoria"] for incidente in todos})

    incidentes = todos
    if categoria:
        incidentes = [i for i in todos if i["categoria"] == categoria]
    incidentes = sorted(incidentes, key=lambda i: (i["fecha"], i["hora"]), reverse=True)

    return render_template(
        "incidentes.html",
        titulo="Incidentes",
        pagina="incidentes",
        incidentes=incidentes,
        categorias=categorias,
        categoria=categoria,
    )


# Fuentes de datos: solo la información que aparece en la documentación de cada página
# de datos.gob.do (revisada el 28 de noviembre de 2026). No son los archivos de datos.
FUENTES = [
    {
        "nombre": "Asistencia y Protección Vial, 2020-2026",
        "publicador": "Ministerio de Obras Públicas y Comunicaciones (MOPC)",
        "cobertura": "Desde octubre de 2020 hasta octubre de 2026",
        "actualizacion": "2 de noviembre de 2026",
        "licencia": "ODbL",
        "formatos": "CSV, ODS, XLSX",
        "para_que": "Accidentes, lesionados, fallecidos y estado de las vías, por mes.",
        "advertencia": "La página dice 'quincenal' y 'trimestral' a la vez.",
        "enlace": "https://datos.gob.do/dataset/asistenciavial",
    },
    {
        "nombre": "Infraestructura Vial y Estado de Carreteras 2026",
        "publicador": "Ministerio de Obras Públicas y Comunicaciones (MOPC)",
        "cobertura": "República Dominicana, por municipio, provincia y sector",
        "actualizacion": "12 de octubre de 2026",
        "licencia": "ODbL",
        "formatos": "CSV, ODS, XLSX",
        "para_que": "Estado de las carreteras, longitud y último mantenimiento. No trae coordenadas.",
        "advertencia": "Las fechas de la descripción no coinciden con los nombres de los archivos.",
        "enlace": "https://datos.gob.do/dataset/infraestructura-vial-y-estado-de-carreteras-2026-2028",
    },
    {
        "nombre": "Asistencias Viales de Tránsito, 2018-2026",
        "publicador": "Dirección General de Seguridad de Tránsito (DIGESETT)",
        "cobertura": "2018 a 2026",
        "actualizacion": "26 de noviembre de 2026",
        "licencia": "ODbL",
        "formatos": "CSV, ODS, XLSX",
        "para_que": "Auxilio a vehículos: averías, combustible y neumáticos.",
        "advertencia": "No mide choques, solo auxilio en la vía.",
        "enlace": "https://datos.gob.do/dataset/asistencias-viales-de-transito-2018-2026",
    },
]

# Otros datasets de la búsqueda "seguridad". Solo se revisó el título y el publicador.
FUENTES_RELACIONADAS = [
    {
        "nombre": "Fallecimientos en Accidentes de Tránsito, 2016-2025",
        "publicador": "DIGESETT",
        "enlace": "https://datos.gob.do/dataset/estadistica-de-fallecimientos-por-accidentes-de-transito",
    },
    {
        "nombre": "Infracciones de Tránsito, 2010-2026",
        "publicador": "DIGESETT",
        "enlace": "https://datos.gob.do/dataset/estadisticas-de-infracciones-de-transito",
    },
    {
        "nombre": "Llamadas de Emergencias Sistema 9-1-1 (2026)",
        "publicador": "Sistema Nacional de Atención a Emergencias y Seguridad 911",
        "enlace": "https://datos.gob.do/dataset/llamadas-de-emergencias-del-sistema-9-1-1",
    },
]


@app.route("/fuentes")
def fuentes():
    return render_template(
        "fuentes.html",
        titulo="Fuentes",
        pagina="fuentes",
        fuentes=FUENTES,
        relacionadas=FUENTES_RELACIONADAS,
    )


# ---------------------------------------------------------------------------
# Plantillas (páginas HTML). Jinja las usa para rellenar los datos.
# ---------------------------------------------------------------------------

BASE = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VIALIS · {{ titulo }}</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", system-ui, Arial, sans-serif;
      background: #f1f5f9;
      color: #0f172a;
    }

    /* Barra superior */
    header {
      background: linear-gradient(135deg, #0b1220, #1e3a8a);
      color: #fff;
      padding: 16px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 12px;
      box-shadow: 0 4px 14px rgba(15, 23, 42, .25);
    }
    .marca { font-size: 20px; font-weight: 800; letter-spacing: .06em; }
    .marca span { color: #fb923c; }
    nav a {
      color: #cbd5e1;
      text-decoration: none;
      font-weight: 600;
      margin-left: 8px;
      padding: 7px 14px;
      border-radius: 8px;
    }
    nav a:hover { background: rgba(255, 255, 255, .12); color: #fff; }
    nav a.activa { background: rgba(255, 255, 255, .18); color: #fff; }

    main { max-width: 1080px; margin: 28px auto; padding: 0 18px; }
    h1 { margin: 0 0 4px; font-size: 26px; }
    h2 { margin: 0 0 14px; font-size: 18px; }
    .subtitulo { color: #64748b; margin: 0 0 22px; }

    /* Tarjetas de cifras */
    .stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 16px;
      margin-bottom: 22px;
    }
    .stat {
      background: #fff;
      border-radius: 14px;
      padding: 18px 20px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, .06);
      border-left: 5px solid #1d4ed8;
    }
    .stat.naranja { border-color: #ea580c; }
    .stat.rojo { border-color: #b91c1c; }
    .stat.verde { border-color: #16a34a; }
    .stat.morado { border-color: #7c3aed; }
    .stat small {
      color: #64748b;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .05em;
      font-size: 12px;
    }
    .stat b { display: block; font-size: 30px; margin-top: 4px; }

    /* Tarjetas de contenido y tablas */
    .tarjeta {
      background: #fff;
      border-radius: 14px;
      padding: 20px 22px;
      margin-bottom: 22px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, .06);
    }
    .dos-columnas {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 22px;
      align-items: start;
    }
    .tabla-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    th {
      text-align: left;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .05em;
      color: #64748b;
      padding: 10px 12px;
      background: #f8fafc;
      border-bottom: 2px solid #e2e8f0;
    }
    td { padding: 12px; border-bottom: 1px solid #e2e8f0; vertical-align: middle; }
    tbody tr:hover td { background: #f8fafc; }

    /* Niveles de riesgo */
    .nivel {
      color: #fff;
      padding: 4px 12px;
      border-radius: 99px;
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
    }
    .critico { background: linear-gradient(90deg, #dc2626, #991b1b); }
    .alto { background: linear-gradient(90deg, #f97316, #c2410c); }
    .moderado { background: linear-gradient(90deg, #3b82f6, #1d4ed8); }
    .bajo { background: linear-gradient(90deg, #22c55e, #15803d); }

    /* Barra de puntaje */
    .puntaje { display: flex; align-items: center; gap: 10px; }
    .barra { background: #e2e8f0; border-radius: 99px; height: 8px; width: 140px; overflow: hidden; }
    .barra div {
      height: 100%;
      border-radius: 99px;
      background: linear-gradient(90deg, #3b82f6, #f97316, #dc2626);
    }

    /* Severidad y momento del día */
    .chip { padding: 3px 10px; border-radius: 99px; font-size: 13px; font-weight: 700; white-space: nowrap; }
    .sev1 { background: #dcfce7; color: #166534; }
    .sev2 { background: #fef9c3; color: #854d0e; }
    .sev3 { background: #ffedd5; color: #9a3412; }
    .sev4 { background: #b91c1c; color: #fff; }
    .noche { background: #1e3a8a; color: #fff; }
    .dia { background: #fef3c7; color: #92400e; }

    /* Filtros por categoría */
    .filtros { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
    .filtro {
      background: #e2e8f0;
      color: #334155;
      text-decoration: none;
      padding: 7px 14px;
      border-radius: 99px;
      font-size: 13px;
      font-weight: 600;
    }
    .filtro:hover { background: #cbd5e1; }
    .filtro.activo { background: #1d4ed8; color: #fff; }

    /* Aviso destacado */
    .aviso {
      background: #fef3c7;
      border-left: 5px solid #f59e0b;
      color: #78350f;
      padding: 14px 18px;
      border-radius: 10px;
      margin-bottom: 22px;
      line-height: 1.5;
    }
    .etiqueta {
      display: inline-block;
      background: #e0e7ff;
      color: #3730a3;
      padding: 2px 8px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 700;
      margin-right: 6px;
    }

    /* Botones y notas */
    .boton {
      display: inline-block;
      background: #1d4ed8;
      color: #fff;
      padding: 6px 12px;
      border-radius: 8px;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
    }
    .boton:hover { background: #1e40af; }
    .nota { color: #64748b; font-size: 13px; margin: 14px 0 0; }
    .pie { color: #64748b; font-size: 13px; text-align: center; margin: 30px 0 10px; }

    @media (max-width: 760px) {
      header { padding: 14px 16px; }
      main { margin: 18px auto; }
      .barra { width: 90px; }
      .dos-columnas { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="marca">🚦 VIALIS<span>.</span></div>
    <nav>
      <a href="/" class="{{ 'activa' if pagina == 'inicio' else '' }}">Resumen</a>
      <a href="/incidentes" class="{{ 'activa' if pagina == 'incidentes' else '' }}">Incidentes</a>
      <a href="/fuentes" class="{{ 'activa' if pagina == 'fuentes' else '' }}">Fuentes</a>
    </nav>
  </header>
  <main>
    {% block contenido %}{% endblock %}
    <p class="pie">Puntuación provisional y no oficial · Datos de demostración (SIMULADO)</p>
  </main>
</body>
</html>
"""

INICIO = """{% extends "base.html" %}
{% block contenido %}
<h1>Resumen</h1>
<p class="subtitulo">Zonas con más riesgo a partir de incidentes de demostración.</p>

<div class="stats">
  <div class="stat"><small>Incidentes</small><b>{{ total }}</b></div>
  <div class="stat morado"><small>De noche (18:00–06:00)</small><b>{{ de_noche }}</b></div>
  <div class="stat rojo"><small>Graves o fatales</small><b>{{ graves }}</b></div>
  <div class="stat verde"><small>Zona más crítica</small><b>{{ zonas[0].nombre if zonas else "—" }}</b></div>
</div>

<div class="dos-columnas">
  <div class="tarjeta">
    <h2>Ranking de zonas</h2>
    <div class="tabla-wrap">
      <table>
        <thead>
          <tr><th>Zona</th><th>Incidentes</th><th>Puntaje</th><th>Riesgo</th><th>Mapa</th></tr>
        </thead>
        <tbody>
          {% for zona in zonas[:10] %}
          <tr>
            <td><b>{{ zona.nombre }}</b></td>
            <td>{{ zona.incidentes }}</td>
            <td>
              <div class="puntaje">
                <div class="barra"><div style="width: {{ zona.porcentaje }}%"></div></div>
                <span>{{ zona.puntaje }}</span>
              </div>
            </td>
            <td><span class="nivel {{ zona.clase }}">{{ zona.nivel }}</span></td>
            <td><a class="boton" href="https://www.openstreetmap.org/?mlat={{ zona.lat }}&mlon={{ zona.lng }}&zoom=16" target="_blank">Ver mapa</a></td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    <p class="nota">
      Puntaje = suma de la gravedad de los incidentes de la zona
      (leve 1, moderada 2, grave 3, fatal 4).
    </p>
  </div>

  <div class="tarjeta">
    <h2>Por categoría</h2>
    <table>
      <thead>
        <tr><th>Categoría</th><th>Incidentes</th></tr>
      </thead>
      <tbody>
        {% for categoria, cantidad in por_categoria %}
        <tr>
          <td><a href="/incidentes?categoria={{ categoria|urlencode }}">{{ categoria }}</a></td>
          <td><b>{{ cantidad }}</b></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
"""

INCIDENTES = """{% extends "base.html" %}
{% block contenido %}
<h1>Incidentes</h1>
<p class="subtitulo">
  {% if categoria %}Mostrando solo: <b>{{ categoria }}</b>{% else %}Lista completa de incidentes de demostración{% endif %}
  · del más reciente al más antiguo.
</p>

<div class="filtros">
  <a class="filtro {{ 'activo' if not categoria else '' }}" href="/incidentes">Todas</a>
  {% for nombre in categorias %}
  <a class="filtro {{ 'activo' if categoria == nombre else '' }}" href="/incidentes?categoria={{ nombre|urlencode }}">{{ nombre }}</a>
  {% endfor %}
</div>

<div class="tarjeta">
  <div class="tabla-wrap">
    <table>
      <thead>
        <tr><th>Fecha</th><th>Hora</th><th>Momento</th><th>Categoría</th><th>Descripción</th><th>Severidad</th></tr>
      </thead>
      <tbody>
        {% for incidente in incidentes %}
        <tr>
          <td>{{ incidente.fecha }}</td>
          <td>{{ incidente.hora }}</td>
          <td>
            {% if incidente.de_noche %}
              <span class="chip noche">🌙 Noche</span>
            {% else %}
              <span class="chip dia">☀️ Día</span>
            {% endif %}
          </td>
          <td><b>{{ incidente.categoria }}</b></td>
          <td>{{ incidente.descripcion }}</td>
          <td><span class="chip sev{{ incidente.gravedad }}">{{ incidente.severidad }}</span></td>
        </tr>
        {% else %}
        <tr><td colspan="6">No hay incidentes en esta categoría.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
"""

FUENTES_HTML = """{% extends "base.html" %}
{% block contenido %}
<h1>Fuentes de datos</h1>
<p class="subtitulo">Datos públicos del Portal de Datos Abiertos (datos.gob.do) que pueden llenar vacíos de información.</p>

<div class="aviso">
  <b>Importante:</b> esta página solo describe las fuentes. Los datos todavía no están cargados en VIALIS.
  Lo que se muestra viene de la documentación de cada dataset, no de los archivos.
</div>

<div class="tarjeta">
  <h2>Fuentes principales</h2>
  <div class="tabla-wrap">
    <table>
      <thead>
        <tr><th>Dataset</th><th>Publicado por</th><th>Cobertura</th><th>Actualizado</th><th>Para qué sirve</th><th>Enlace</th></tr>
      </thead>
      <tbody>
        {% for f in fuentes %}
        <tr>
          <td>
            <b>{{ f.nombre }}</b><br>
            <span class="etiqueta">{{ f.licencia }}</span>
            <span class="nota">{{ f.formatos }}</span>
          </td>
          <td>{{ f.publicador }}</td>
          <td>{{ f.cobertura }}</td>
          <td>{{ f.actualizacion }}</td>
          <td>
            {{ f.para_que }}
            <div class="nota">⚠️ {{ f.advertencia }}</div>
          </td>
          <td><a class="boton" href="{{ f.enlace }}" target="_blank">Abrir</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<div class="tarjeta">
  <h2>Otros datasets relacionados</h2>
  <p class="nota">Encontrados con la búsqueda "seguridad". Solo se revisó el título y el publicador.</p>
  <div class="tabla-wrap">
    <table>
      <thead>
        <tr><th>Dataset</th><th>Publicado por</th><th>Enlace</th></tr>
      </thead>
      <tbody>
        {% for r in relacionadas %}
        <tr>
          <td><b>{{ r.nombre }}</b></td>
          <td>{{ r.publicador }}</td>
          <td><a class="boton" href="{{ r.enlace }}" target="_blank">Abrir</a></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<div class="tarjeta">
  <h2>Cómo usar estos datos</h2>
  <ol>
    <li>Abre el enlace y descarga el archivo <b>CSV</b>. Es el más fácil de usar, porque se abre con Excel.</li>
    <li>Anota la fecha en que lo descargaste.</li>
    <li>Cita siempre la fuente y la licencia <b>ODbL</b>.</li>
    <li>Lee la advertencia de cada fuente antes de usar un dato.</li>
  </ol>
</div>
{% endblock %}
"""

app.jinja_loader = DictLoader({
    "base.html": BASE,
    "inicio.html": INICIO,
    "incidentes.html": INCIDENTES,
    "fuentes.html": FUENTES_HTML,
})


if __name__ == "__main__":
    app.run(debug=True)
