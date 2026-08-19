import ee
from flask import Flask

proyectid = "bubbly-axiom-455219-a8"

app = Flask(__name__)

ee.Initialize(project=proyectid)  # iniciar Google Earth
print("Earth Engine inicializado correctamente")


def calcularVigorVegetativo(latitud, longitud, fechaInicio, fechaFin):
    earthengineValue = ee.Geometry.Point([longitud, latitud])
    boundedValue = earthengineValue.buffer(250).bounds()
    imageCollection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

    filteredCollection = imageCollection.filterBounds(boundedValue).filterDate(fechaInicio, fechaFin).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).sort("CLOUDY_PIXEL_PERCENTAGE")

    try:
        image = filteredCollection.first()
        vigorVegetativo = image.normalizedDifference(["B8", "B4"])
        return vigorVegetativo.reduceRegion(reducer=ee.Reducer.mean(), geometry=boundedValue, scale=10, maxPixels=1e9).get("nd").getInfo()
    except Exception as e:
        return None


def calcularHumedad(latitud, longitud, fechaInicio, fechaFin):
    earthengineValue = ee.Geometry.Point([longitud, latitud])
    boundedValue = earthengineValue.buffer(250).bounds()
    imageCollection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

    filteredCollection = imageCollection.filterBounds(boundedValue).filterDate(fechaInicio, fechaFin).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).sort("CLOUDY_PIXEL_PERCENTAGE")

    try:
        image = filteredCollection.first()
        humedad = image.normalizedDifference(["B8", "B11"])
        return humedad.reduceRegion(reducer=ee.Reducer.mean(), geometry=boundedValue, scale=10, maxPixels=1e9).get("nd").getInfo()
    except Exception as e:
        return None


@app.route("/")
def backend():
    latitud = -32.40
    longitud = -62.10

    # Los 6 meses a consultar, con su primer y ultimo dia
    meses = [
        ("2024-01-01", "2024-02-01", "Enero"),
        ("2024-02-01", "2024-03-01", "Febrero"),
        ("2024-03-01", "2024-04-01", "Marzo"),
        ("2024-04-01", "2024-05-01", "Abril"),
        ("2024-05-01", "2024-06-01", "Mayo"),
        ("2024-06-01", "2024-07-01", "Junio"),
    ]

    filas = ""

    for fechaInicio, fechaFin, nombreMes in meses:
        ndvi = calcularVigorVegetativo(latitud, longitud, fechaInicio, fechaFin)
        ndmi = calcularHumedad(latitud, longitud, fechaInicio, fechaFin)

        # Si alguno vino None (sin imagen disponible), lo mostramos como texto
        ndvi_texto = f"{ndvi:.3f}" if ndvi is not None else "Sin datos"
        ndmi_texto = f"{ndmi:.3f}" if ndmi is not None else "Sin datos"

        filas += f"<tr><td>{nombreMes}</td><td>{ndvi_texto}</td><td>{ndmi_texto}</td></tr>"

    return f"""
    <h1>NDVI y NDMI por mes (2024)</h1>
    <table border="1" cellpadding="8">
        <tr><th>Mes</th><th>NDVI</th><th>NDMI</th></tr>
        {filas}
    </table>
    """


app.run(debug=True)