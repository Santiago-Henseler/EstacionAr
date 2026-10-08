from model.predictModel import PredictResponse, PredictedStreet
from repository.predictRepository import getRuledStreet, getAllStreets

def _ruledStreet(street_name: str, level: int):
    ruledStreets = getRuledStreet(street_name)
    if ruledStreets is None:
        return None  # la calle no existe

    # para hacer que level caiga en el rango de las alturas (comienzan en ***1 o ***2)
    levelInRange = level
    if levelInRange % 10 == 0:
        levelInRange += 2

    ruledStreet = None
    for aInit, section in ruledStreets["streets"].items():
        a0 = int(aInit)
        # dentro del rango y de la misma paridad
        (f"Comparando {a0} <= {levelInRange} <= {int(section['aFin'])} y {levelInRange}% 2 == {a0}% 2")
        if a0 <= levelInRange <= int(section["aFin"]) and levelInRange % 2 == a0 % 2:
            ruledStreet = section
            ruledStreet["aInit"] = a0

    return ruledStreet

def getNeighbors(street: dict) -> list[PredictedStreet]:
    neighbors = []
    for sName in street["neighbors"].keys():
        aInit = street["neighbors"][sName]["aInit"]
        s = _ruledStreet(sName, aInit)
        if s is None:
            continue
        s["name"] = sName
        s["aInit"] = aInit
        neighbors.append(PredictedStreet(
            name = sName,
            WKT = [1.1],
            probability = 0.4,
            level = aInit,
            rule = s["rule"],
            hInit = s["hInit"],
            hFin = s["hFin"],
            aInit = s["aInit"],
            aFin = s["aFin"]
        ))
    return neighbors



def predictStreet(street_name: str, level: int) -> PredictResponse:

    street = _ruledStreet(street_name, level)
    if street is None:
        return None  # la calle no existe

    # Busco las N calles cercanas a la ubicación
    neighbors = getNeighbors(street)

    # Model.predict(s) 
    
    # TODO: respuesta fija hasta que este el modelo (3.5)
    return {
        "street": PredictedStreet(
            name = street_name,
            WKT = [1.1],
            probability = 0.4,
            level = level,
            rule = street["rule"],
            hInit = street["hInit"],
            hFin = street["hFin"],
            aInit = street["aInit"],
            aFin = street["aFin"]
        ),
        "neighbors": neighbors
    }

def getStreets() -> dict[str]:
    return {"streets": getAllStreets()}