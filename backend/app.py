import random
import ee
import flask
from flask import Flask
from datetime import datetime, timedelta

proyectid = "bubbly-axiom-455219-a8"

app = Flask(__name__)



ee.Initialize(project=proyectid) #iniciar Google Earth

print("Earth Engine inicializado correctamente") #Avisamos que se incio correctamente





def normalizar(valor, minimo, maximo):

    resultado = (valor - minimo) / (maximo - minimo)

    if(resultado < 0):
        resultado = 0
    elif(resultado > 1):
        resultado = 1

    return resultado

def clasificar(valorNormalizado):

    if(valorNormalizado < 0.25):
        return "Muy Bajo"
    elif(valorNormalizado < 0.5):
        return "Moderado"
    elif(valorNormalizado < 0.75):
        return "Bueno"
    else:
        return "Excelente"
    
def calcular_porcentaje_fertilidad(ndvi, ndmi, temperatura, precipitacion, imagen_url):
   
   ndvi_normalizado = normalizar(ndvi, 0, 0.75)
   ndmi_normalizado = normalizar(ndmi, -0.75, 0.75)
   precipitacion_normalizada = normalizar(precipitacion, 0, 40)
   temperatura_normalizada = normalizar(temperatura, 5, 30)

   fertilidad_porcentaje = ((ndvi_normalizado * 0.40) + (ndmi_normalizado * 0.30) + (temperatura_normalizada * 0.15) + (precipitacion_normalizada * 0.15)) * 100
    
   estado_ndvi = clasificar(ndvi_normalizado)
   estado_ndmi = clasificar(ndmi_normalizado)
   estado_temperatura = clasificar(temperatura_normalizada)
   estado_precipitacion = clasificar(precipitacion_normalizada)
   return f"""
        <h1>Fertilidad estimada — {fertilidad_porcentaje:.2f}%</h1>
        <img src="{imagen_url}" width="400">
        <p>Vigor Vegetativo: {estado_ndvi}: {ndvi}</p>
        <p>Humedad en la parcela: {estado_ndmi}: {ndmi}</p>
        <p>Temperatura: {estado_temperatura}: {temperatura}</p>
        <p>Precipitación: {estado_precipitacion}: {precipitacion}</p>
        """

def fertilidad_actual(latitud, longitud, anio, dia_del_anio):

    fecha = datetime(anio, 1, 1) + timedelta(days=dia_del_anio - 1) # pasar fecha en forma de numero a en forma de calendario
    fechaInicio = datetime(anio, 1, 1) + timedelta(days=dia_del_anio - 30) # pasar fecha en forma de numero a en forma de calendario

    earthengineValue = ee.Geometry.Point([longitud, latitud]) #Buscamos el punto en google earth con las coordenadas

    boundedValue = earthengineValue.buffer(300).bounds() #Lo transformamos en un cuadrado

    imageCollection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") #Le pedimos a Google su coleccion de imagenes satelitales 

    filteredCollection = imageCollection.filterBounds(boundedValue).filterDate(fechaInicio, fecha).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).sort("system:time_start", False)
    #Filtramos por las imagenes que nos sirven, es decir, pocas nubes, en nuestra zona agricola, y el periodo que nos interesa, y las ordenamos de la mas reciente a la mas antigua

    Selected_image = filteredCollection.first() #tomamos la primer imagen de la coleccion filtrada, que es la mas reciente

    ndvi = Selected_image.normalizedDifference(["B8", "B4"]).reduceRegion(reducer = ee.Reducer.mean(), geometry = boundedValue, scale = 10, maxPixels = 1e9).get("nd").getInfo()
    ndmi = Selected_image.normalizedDifference(["B8", "B11"]).reduceRegion(reducer = ee.Reducer.mean(), geometry = boundedValue, scale = 10, maxPixels = 1e9).get("nd").getInfo()

    fechaImagen = Selected_image.date()
    fechaImagenSiguiente = fechaImagen.advance(1, "day")
    

    clima = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterDate(fechaImagen, fechaImagenSiguiente)
    .filterBounds(boundedValue)
    .first()
    )
    climaStats = clima.select(["temperature_2m", "total_precipitation_sum"]).reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=boundedValue,
    scale=1000,
    maxPixels=1e9 #Lo que nos interesa (presipitacion y temperatura)
    )
    vis = {
    "min": 0,
    "max": 2500,
    "bands": ["B4", "B3", "B2"]  # color real
    }

    urlImagen = Selected_image.getThumbURL({
    "region": boundedValue,
    "dimensions": 512,
    "format": "png",
    **vis
    })

    temperaturaKelvin = climaStats.get("temperature_2m").getInfo()
    temperaturaCelsius = temperaturaKelvin - 273.15 #lo pasamos a nuestra unidad de medida (celsius)

    precipitacionMetros = climaStats.get("total_precipitation_sum").getInfo()
    precipitacionMilimetros = precipitacionMetros * 1000 #lo pasamos a nuestra unidad de medida (milimetros)
    
    resultado = calcular_porcentaje_fertilidad(ndvi, ndmi, temperaturaCelsius, precipitacionMilimetros, urlImagen) #Calculamos el % de fertilidad y el estado de cada parametro

    return resultado

@app.route("/")
def index():
   return fertilidad_actual(-35.12, -57.52, 2022, 60) #Ejemplo de uso de la funcion
   #return fertilidad_actual(-36.12, -57.52, 2025, 25)
app.run()

    
