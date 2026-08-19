import ee
from datetime import datetime
from sklearn.linear_model import LinearRegression

proyectid = "bubbly-axiom-455219-a8"
ee.Initialize(project=proyectid)
print("Earth Engine inicializado correctamente")

latitud = -34.05
longitud = -61.88

earthengineValue = ee.Geometry.Point([longitud, latitud])
boundedValue = earthengineValue.buffer(250).bounds()


def obtener_estacion(mes):
    if mes in [12, 1, 2]:
        return "verano"
    elif mes in [3, 4, 5]:
        return "otoño"
    elif mes in [6, 7, 8]:
        return "invierno"
    elif mes in [9, 10, 11]:
        return "primavera"

def obtener_valor_estacion(estacion):
    if estacion == "verano":
        return [1, 0, 0, 0]
    elif estacion == "otoño":
        return [0, 1, 0, 0]
    elif estacion == "invierno":
        return [0, 0, 1, 0]
    elif estacion == "primavera":
        return [0, 0, 0, 1]


def calcular_indices(imagen):
    ndvi = imagen.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndmi = imagen.normalizedDifference(["B8", "B11"]).rename("NDMI")
    indices = ndvi.addBands(ndmi)

    stats = indices.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundedValue, scale=10, maxPixels=1e9
    )

    fecha = imagen.date()
    fecha_siguiente = fecha.advance(1, "day")

    clima = (
        ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
        .filterDate(fecha, fecha_siguiente)
        .filterBounds(boundedValue)
        .first()
    )

    clima_stats = clima.select(["temperature_2m", "total_precipitation_sum"]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundedValue, scale=1000, maxPixels=1e9
    )

    return ee.Feature(None, {
        "fecha": fecha.format("YYYY-MM-dd"),
        "ndvi": stats.get("NDVI"),
        "ndmi": stats.get("NDMI"),
        "temperatura": clima_stats.get("temperature_2m"),
        "precipitacion": clima_stats.get("total_precipitation_sum")
    })


# =====================================================
# Entrenamos con datos desde 2017 hasta el 1/1/25
# =====================================================
coleccion = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(boundedValue)
    .filterDate("2017-01-01", "2025-01-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
)

coleccionConIndices = coleccion.map(calcular_indices)
resultado = coleccionConIndices.getInfo()

print(f"Se encontraron {len(resultado['features'])} pasadas satelitales")

pasadas = []
for feature in resultado["features"]:
    props = feature["properties"]
    if props["ndvi"] is None or props["ndmi"] is None or props["temperatura"] is None or props["precipitacion"] is None:
        continue
    pasadas.append({
        "fecha": datetime.strptime(props["fecha"], "%Y-%m-%d"),
        "ndvi": props["ndvi"],
        "ndmi": props["ndmi"],
        "temperatura": props["temperatura"] - 273.15,
        "precipitacion": props["precipitacion"] * 1000
    })

pasadas.sort(key=lambda p: p["fecha"])
print(f"Se usaron {len(pasadas)} pasadas validas, ordenadas por fecha")


# =====================================================
# Armamos X e y: base (pasada anterior) + clima del dia
# QUE QUEREMOS PREDECIR (no del dia base) + estacion
# =====================================================
X = []
y = []

for i in range(1, len(pasadas)):
    anterior = pasadas[i - 1]
    actual = pasadas[i]
    dias_entre_pasadas = (actual["fecha"] - anterior["fecha"]).days

    if dias_entre_pasadas > 20:
        continue

    estacion_actual = obtener_estacion(actual["fecha"].month)
    columnas_estacion = obtener_valor_estacion(estacion_actual)

    fila_x = [
        anterior["ndvi"], anterior["ndmi"], anterior["temperatura"], anterior["precipitacion"],
        dias_entre_pasadas
    ] + columnas_estacion + [
        actual["temperatura"], actual["precipitacion"]   # clima del dia a predecir
    ]

    X.append(fila_x)
    y.append([actual["ndvi"], actual["ndmi"]])

print(f"Se armaron {len(X)} pares consecutivos para entrenar")

modelo = LinearRegression()
modelo.fit(X, y)


# =====================================================
# Buscamos la ultima pasada real antes del 1/1/25
# =====================================================
fecha_objetivo = datetime(2025, 6, 1)

coleccion_reciente = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(boundedValue)
    .filterDate("2024-11-01", "2025-01-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
    .sort("system:time_start", False)
)

imagen_reciente = coleccion_reciente.first()
ndvi_reciente = imagen_reciente.normalizedDifference(["B8", "B4"]).reduceRegion(
    reducer=ee.Reducer.mean(), geometry=boundedValue, scale=10, maxPixels=1e9
).get("nd").getInfo()
ndmi_reciente = imagen_reciente.normalizedDifference(["B8", "B11"]).reduceRegion(
    reducer=ee.Reducer.mean(), geometry=boundedValue, scale=10, maxPixels=1e9
).get("nd").getInfo()

fecha_reciente_str = imagen_reciente.date().format("YYYY-MM-dd").getInfo()
fecha_reciente = datetime.strptime(fecha_reciente_str, "%Y-%m-%d")

fecha_reciente_siguiente = imagen_reciente.date().advance(1, "day")
clima_reciente = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterDate(imagen_reciente.date(), fecha_reciente_siguiente)
    .filterBounds(boundedValue)
    .first()
)
clima_reciente_stats = clima_reciente.select(["temperature_2m", "total_precipitation_sum"]).reduceRegion(
    reducer=ee.Reducer.mean(), geometry=boundedValue, scale=1000, maxPixels=1e9
).getInfo()

temp_reciente = clima_reciente_stats["temperature_2m"] - 273.15
precip_reciente = clima_reciente_stats["total_precipitation_sum"] * 1000

dias_hasta_objetivo = (fecha_objetivo - fecha_reciente).days
estacion_objetivo = obtener_estacion(fecha_objetivo.month)
columnas_estacion_objetivo = obtener_valor_estacion(estacion_objetivo)

# =====================================================
# Clima REAL del dia objetivo (1/6/25) 
# =====================================================
fecha_objetivo_ee = ee.Date("2025-06-01")
fecha_objetivo_siguiente = fecha_objetivo_ee.advance(1, "day")

clima_objetivo = (
    ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
    .filterDate(fecha_objetivo_ee, fecha_objetivo_siguiente)
    .filterBounds(boundedValue)
    .first()
)

# Validamos que haya datos climáticos, sino devolvemos error manejado
try:
    clima_objetivo_stats = clima_objetivo.select(["temperature_2m", "total_precipitation_sum"]).reduceRegion(
        reducer=ee.Reducer.mean(), geometry=boundedValue, scale=1000, maxPixels=1e9
    ).getInfo()
    temp_objetivo = clima_objetivo_stats["temperature_2m"] - 273.15
    precip_objetivo = clima_objetivo_stats["total_precipitation_sum"] * 1000
except TypeError:
    print("\nADVERTENCIA: Aún no hay datos climáticos reales (ERA5) disponibles para el 1/6/25 en Earth Engine.")
    print("Usando valores de temperatura y precipitación promedio como placeholder para completar la ejecución.")
    temp_objetivo = 15.0
    precip_objetivo = 0.0

print(f"\nÚltima pasada real conocida: {fecha_reciente_str}")
print(f"  NDVI: {ndvi_reciente:.3f} | NDMI: {ndmi_reciente:.3f}")
print(f"Días hasta el objetivo (1/6/25): {dias_hasta_objetivo}")
print(f"Clima del día objetivo: {temp_objetivo:.1f}°C, {precip_objetivo:.1f}mm")

fila_predecir = [[
    ndvi_reciente, ndmi_reciente, temp_reciente, precip_reciente, dias_hasta_objetivo
] + columnas_estacion_objetivo + [temp_objetivo, precip_objetivo]]

prediccion = modelo.predict(fila_predecir)
ndvi_predicho = prediccion[0][0]
ndmi_predicho = prediccion[0][1]


def obtener_valor_real(fecha_inicio, fecha_fin, bandas):
    coleccion_real = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(boundedValue)
        .filterDate(fecha_inicio, fecha_fin)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )
    try:
        imagen = coleccion_real.first()
        indice = imagen.normalizedDifference(bandas)
        return indice.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=boundedValue, scale=10, maxPixels=1e9
        ).get("nd").getInfo()
    except Exception:
        return None

# Ajustamos la ventana para encontrar la imagen real cercana al 1/6/25
ndvi_real = obtener_valor_real("2025-05-15", "2025-06-15", ["B8", "B4"])
ndmi_real = obtener_valor_real("2025-05-15", "2025-06-15", ["B8", "B11"])

print(f"\nPredicción para 2025-06-01:")
print(f"  NDVI predicho: {ndvi_predicho:.3f}")
print(f"  NDMI predicho: {ndmi_predicho:.3f}")

if ndvi_real is not None and ndmi_real is not None:
    diferencia_ndvi = abs(ndvi_predicho - ndvi_real)
    diferencia_ndmi = abs(ndmi_predicho - ndmi_real)
    diferencia_tonta_ndvi = abs(ndvi_reciente - ndvi_real)
    diferencia_tonta_ndmi = abs(ndmi_reciente - ndmi_real)

    print(f"\nNDVI real: {ndvi_real:.3f}")
    print(f"  Diferencia del MODELO: {diferencia_ndvi:.3f}")
    print(f"  Diferencia 'sin cambios': {diferencia_tonta_ndvi:.3f}")

    print(f"\nNDMI real: {ndmi_real:.3f}")
    print(f"  Diferencia del MODELO: {diferencia_ndmi:.3f}")
    print(f"  Diferencia 'sin cambios': {diferencia_tonta_ndmi:.3f}")
else:
    print("\nNo se encontró imagen real para esa fecha (o aún no ha ocurrido / no ha sido procesada por Sentinel-2).")