from flask import Flask, render_template, jsonify
import ee
import random

PROJECT_ID = "bubbly-axiom-455219-a8"

app = Flask(__name__)


try:
    ee.Initialize(project=PROJECT_ID)
    print("Earth Engine inicializado correctamente.")
except Exception as e:
    print("Error al inicializar Earth Engine:", e)


ZONAS_AGRICOLAS = [
    {"lat": -33.12, "lng": -61.52, "nombre": "Zona nucleo - sur de Santa Fe"},
    {"lat": -34.05, "lng": -61.88, "nombre": "Norte de Buenos Aires - Pergamino"},
    {"lat": -32.40, "lng": -62.10, "nombre": "Este de Cordoba - Marcos Juarez"},
    {"lat": -35.30, "lng": -62.72, "nombre": "Oeste de Buenos Aires - 9 de Julio"},
    {"lat": -31.65, "lng": -60.70, "nombre": "Centro de Santa Fe"},
    {"lat": -33.88, "lng": -63.25, "nombre": "Sur de Cordoba - Rio Cuarto"},
    {"lat": -36.10, "lng": -61.10, "nombre": "Bragado - Buenos Aires"},
    {"lat": -30.75, "lng": -62.10, "nombre": "Norte de Cordoba - San Francisco"},
]


def obtener_imagen_satelital(lat, lng):
    """
    Dada una coordenada, arma un cuadrado de 100x100m y pide a
    Earth Engine una imagen Sentinel-2 recortada a esa zona.
    Devuelve una URL de imagen que el navegador puede mostrar.
    """
    punto = ee.Geometry.Point([lng, lat])


    zona = punto.buffer(50).bounds()

    coleccion = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(zona)
        .filterDate("2025-10-01", "2026-06-30")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 15))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )

    imagen = coleccion.first()


    vis = {
        "min": 0,
        "max": 3000,
        "bands": ["B4", "B3", "B2"],  # R, G, B
    }

    url = imagen.getThumbURL({
        "region": zona,
        "dimensions": 512,     
        "format": "png",
        **vis
    })

    return url


@app.route("/")
def inicio():
    return render_template("index.html")



@app.route("/api/zona-aleatoria")
def zona_aleatoria():
    try:
        # Elegimos zona base al azar
        base = random.choice(ZONAS_AGRICOLAS)

        # Pequeno desplazamiento aleatorio para variar el punto exacto
        lat = base["lat"] + (random.random() - 0.5) * 0.06
        lng = base["lng"] + (random.random() - 0.5) * 0.06

        url_imagen = obtener_imagen_satelital(lat, lng)

        return jsonify({
            "ok": True,
            "url": url_imagen,
            "lat": round(lat, 5),
            "lng": round(lng, 5),
            "nombre": base["nombre"]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
