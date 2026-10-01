# Diccionario de datos

## `merged.csv`

Dataset unificado: una fila por tramo de cuadra y hora del día. Se genera con `python modelo.py` (no se versiona por tamaño).

| Columna | Tipo | Descripción |
|---|---|---|
| `id` | int | Id del tramo en el dataset de estacionamiento de la ciudad (un tramo es un lado de una cuadra) |
| `calle` | str | Nombre de la calle |
| `x0`, `y0`, `x1`, `y1` | float | Longitud y latitud del inicio y fin del tramo |
| `aInicio`, `aFin` | int | Alturas del tramo (0 si no las tiene) |
| `hora` | int | Hora del día, de 0 a 23 |
| `cantidad` | float | Vehículos por hora que pasan por el tramo |
| `origen_flujo` | str | De dónde sale `cantidad`: `cercano` (conteo a menos de 3 cuadras), `misma_calle` (conteo más cercano sobre la misma calle) o `simulado` |
| `estacionamientos` | int | Variable objetivo: lugares libres estimados en el tramo a esa hora (0 si está prohibido estacionar) |

## Supuestos

- Los tramos sin conteo cercano usan el perfil horario promedio de los conteos de 2024; una calle tiene el 30 % del flujo de una avenida, con un ruido aleatorio por tramo (semilla fija, el dataset es reproducible).
- Capacidad de un tramo: 10 lugares (15 en avenidas), descontados según el flujo normalizado por el percentil 95.
- Las reglas "días hábiles de 7 a 21" se aplican todos los días.
