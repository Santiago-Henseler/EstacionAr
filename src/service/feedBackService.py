from repository.feedBackRepository import insert, averages
from repository.predictRepository import setAdjustments, horaActual
from service.predictSrevice import _ruledStreet

# Confidence => indica que tan buena fue la estimación de la respuesta [0:5]
# Proba => indica la probabilidad dada por el modelo
# si la confidence es 5 => la proba se guarda directo
# si la confidence esta entre 4 y 2 => si la proba es menor a 0,5 se debe aumentar en 0,2
#                                   => si la proba es mayor o igual a 0,5 se debe disminuir en 0,2
# si la confidence esta entre 2 y 0 => si la proba es menor a 0,5 se debe aumentar en 0,3
#                                   => si la proba es mayor o igual a 0,5 se debe disminuir en 0,3
def saveFeedBack(street_name: str, level: int, confidence: int, proba: float, hour: int | None = None) -> bool:
    section = _ruledStreet(street_name, level)
    if section is None:
        return False

    # TODO: mejorar calculo: ej si confidence es 1 y proba es 0.4, la proba sube a 0.7?
    # preguntar si se encontro mas o menos lugar del que deberia?
    if confidence == 5:
        delta = 0
    elif confidence >= 2:
        delta = 0.2
    else:
        delta = 0.3

    new_proba = proba - delta if proba >= 0.5 else proba + delta
    new_proba = min(max(new_proba, 0.0), 1.0)

    insert(
        street_name.strip().upper(),
        section['aInit'],
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