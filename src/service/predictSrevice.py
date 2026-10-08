from model.predictModel import PredictedStreet
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

def predictStreet(street_name: str, level: int) -> list[PredictedStreet]:
    # Primero busco las N calles cercanas a la ubicación
    nearStreet = []

    street = _ruledStreet(street_name, level)
    if street is None:
        return None  # la calle no existe
    street["name"] = street_name
    # street["aInit"] = level
    nearStreet.append(street)
    
    for sName in street["neighbors"].keys():
        aInit = street["neighbors"][sName]["aInit"]
        s = _ruledStreet(sName, aInit)
        if s is None:
            continue
        s["name"] = sName
        s["aInit"] = aInit
        nearStreet.append(s)

    # Model.predict(s) 

    # TODO: respuesta fija hasta que este el modelo (3.5)
    return [
        PredictedStreet(
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
        PredictedStreet(
            name = "placeholder",
            WKT = [1.1],
            probability = 0.4,
            level = level,
            rule = 1,
            hInit = 0,
            hFin = 24,
            aInit = 0,
            aFin = 100
        )
    ]

def getStreets() -> dict[str]:
    return {"streets": getAllStreets()}