from repository.feedBackRepository import insert, averages
from repository.predictRepository import setAdjustments, horaActual, predict
from service.predictSrevice import _ruledStreet

# Confidence => indica que tan buena fue la estimación de la respuesta (-5 a 5)
#               si es positivo => se encontraron mas lugares de los esperados (subir la probabilidad)
#               si es negativo => se encontraron menos lugares de los esperados (bajar la probabilidad)
#               si es 0 => la estimación fue correcta (no se cambia la probabilidad)
# Proba => probabilidad dada por el modelo

MAX_STEP = 0.6 # cuanto cambia la probabilidad como maximo (si el feedback es 5 o -5)

def saveFeedBack(street_name: str, level: int, error: int, hour: int | None = None) -> bool:
    section = _ruledStreet(street_name, level)
    if section is None:
        return False

    hour = hour if hour is not None else horaActual()

    step = MAX_STEP * abs(error) / 5

    proba = predict(street_name, section["aInit"], section["aFin"], hour)

    if error > 0:
        new_proba = proba + (1 - proba) * step
    elif error < 0:
        new_proba = proba - proba * step
    else:
        new_proba = proba

    insert(
        street_name.strip().upper(),
        section["aInit"],
        hour if hour is not None else horaActual(),
        new_proba
    )
    return True

def updateProbabilities() -> int:
    nuevos = {}
    for street, aInit, hora, avg, n in averages():
        nuevos[(street, aInit, hora)] = (avg, n)
    setAdjustments(nuevos)
    return len(nuevos)