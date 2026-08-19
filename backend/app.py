import ee
from flask import Flask, jsonify, render_template
from datetime import datetime, timedelta

proyectid = "bubbly-axiom-455219-a8"

app = Flask(__name__)

ee.Initialize(project=proyectid)
print("Earth Engine inicializado correctamente")

def normalizar(valor, minimo, maximo):
    resultado = (valor - minimo) / (maximo - minimo)
    if(resultado < 0): return 0
    elif(resultado > 1): return 1
    return resultado

def clasificar(valorNormalizado):
    if(valorNormalizado < 0.25): return "Muy Bajo"
    elif(valorNormalizado < 0.5): return "Moderado"
    elif(valorNormalizado < 0.75): return "Bueno"
    else: return "Excelente"
    
def calcular_porcentaje_fertilidad(ndvi, ndmi, temperatura, precipitacion, imagen_url, lat, lng):
   ndvi_normalizado = normalizar(ndvi, 0, 0.75)
   ndmi_normalizado = normalizar(ndmi, -0.75, 0.75)
   precipitacion_normalizada = normalizar(precipitacion, 0, 40)
   temperatura_normalizada = normalizar(temperatura, 5, 30)

   fertilidad_porcentaje = ((ndvi_normalizado * 0.40) + (ndmi_normalizado * 0.30) + (temperatura_normalizada * 0.15) + (precipitacion_normalizada * 0.15)) * 100
    
   # AHORA DEVOLVEMOS UN DICCIONARIO, NO UN STRING DE HTML
   return {
       "ok": True,
       "lat": round(lat, 5),
       "lng": round(lng, 5),
       "url": imagen_url,
       "fertilidad": round(fertilidad_porcentaje, 2),
       "ndvi": round(ndvi, 3),
       "estado_ndvi": clasificar(ndvi_normalizado),
       "ndmi": round(ndmi, 3),
       "estado_ndmi": clasificar(ndmi_normalizado),
       "temperatura": round(temperatura, 1),
       "estado_temperatura": clasificar(temperatura_normalizada),
       "precipitacion": round(precipitacion, 1),
       "estado_precipitacion": clasificar(precipitacion_normalizada)
   }

def fertilidad_actual(latitud, longitud, anio, dia_del_anio):
    try:
        fecha = datetime(anio, 1, 1) + timedelta(days=dia_del_anio - 1)
        fechaInicio = datetime(anio, 1, 1) + timedelta(days=dia_del_anio - 30)

        earthengineValue = ee.Geometry.Point([longitud, latitud])
        boundedValue = earthengineValue.buffer(300).bounds()

        imageCollection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        filteredCollection = imageCollection.filterBounds(boundedValue).filterDate(fechaInicio, fecha).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).sort("system:time_start", False)

        Selected_image = filteredCollection.first()

        ndvi = Selected_image.normalizedDifference(["B8", "B4"]).reduceRegion(reducer = ee.Reducer.mean(), geometry = boundedValue, scale = 10, maxPixels = 1e9).get("nd").getInfo()
        ndmi = Selected_image.normalizedDifference(["B8", "B11"]).reduceRegion(reducer = ee.Reducer.mean(), geometry = boundedValue, scale = 10, maxPixels = 1e9).get("nd").getInfo()

        fechaImagen = Selected_image.date()
        fechaImagenSiguiente = fechaImagen.advance(1, "day")
        
        clima = (ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
                .filterDate(fechaImagen, fechaImagenSiguiente)
                .filterBounds(boundedValue)
                .first())
        
        climaStats = clima.select(["temperature_2m", "total_precipitation_sum"]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=boundedValue, scale=1000, maxPixels=1e9)
        
        vis = {"min": 0, "max": 2500, "bands": ["B4", "B3", "B2"]}

        urlImagen = Selected_image.getThumbURL({
            "region": boundedValue, "dimensions": 512, "format": "png", **vis
        })

        temperaturaCelsius = climaStats.get("temperature_2m").getInfo() - 273.15
        precipitacionMilimetros = climaStats.get("total_precipitation_sum").getInfo() * 1000
        
        # Pasamos lat y lng a la funcion para que las guarde en el diccionario
        return calcular_porcentaje_fertilidad(ndvi, ndmi, temperaturaCelsius, precipitacionMilimetros, urlImagen, latitud, longitud)
    except Exception as e:
        return {"ok": False, "error": str(e), "lat": latitud, "lng": longitud}

# SERVIDOR WEB: ENVIAR AL FRONTEND LA INTERFAZ GRAFICA Y LOS DATOS DE FERTILIDAD
#----------- COMUNICACION CON EL FRONTEND (LEVIN) -----------

@app.route("/")
def index():
    # Devuelve la interfaz gráfica
    return render_template("index.html")

@app.route("/api/hectareas")
def obtener_hectareas():
    lat_base = -35.12
    lng_base = -57.52
    resultados = []
    
    for i in range(10):
        lng_actual = lng_base + (i * 0.001)
        datos = fertilidad_actual(lat_base, lng_actual, 2022, 300)
        resultados.append(datos)
        
    return jsonify(resultados)

if __name__ == "__main__":
    app.run(debug=True)