import random
import ee
import flask
from flask import Flask

proyectid = "bubbly-axiom-455219-a8"

app = Flask(__name__)



ee.Initialize(project=proyectid) #iniciar Google Earth

print("Earth Engine inicializado correctamente") #Avisamos que se incio correctamente





def calcularVigorVegetativo(latitud, longitud, fechaInicio, fechaFin):

    earthengineValue = ee.Geometry.Point([longitud, latitud]) #Buscamos el punto en google earth con las coordenadas

    boundedValue = earthengineValue.buffer(250).bounds() #Lo transformamos en un cuadrado de 500x500 metros

    imageCollection = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") #Le pedimos a Google su coleccion de imagenes satelitales 

    filteredCollection = imageCollection.filterBounds(boundedValue).filterDate(fechaInicio, fechaFin).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20)).sort("CLOUDY_PIXEL_PERCENTAGE")
    #Filtramos por las imagenes que nos sirven, es decir, pocas nubes, en nuestra zona agricola, y el año que nos interesa (2022-2023)

    image = filteredCollection.first() #tomamos la primer imagen de la coleccion filtrada, que es la que tiene menos nubes

    vigor = image.normalizedDifference(["B8", "B4"]) #Calculamos el vigor vegetativo (NDVI), (Esto todavia es una imagen)

    vigorEnNumeros = vigor.reduceRegion(reducer = ee.Reducer.mean(), geometry = boundedValue, scale = 10, maxPixels = 1e9).get("nd").getInfo() #Transformamos la imagen en un numero, que es el promedio del vigor vegetativo en toda la zona agricola

    return vigorEnNumeros #Devolvemos el numero que representa el vigor vegetativo

@app.route("/")
def backend():
    latitud = -32.40
    longitud = -62.10
    return str(calcularVigorVegetativo(latitud, longitud, "2024-01-01", "2024-02-03"))
app.run()