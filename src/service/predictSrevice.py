from model.predictModel import PredictResponse, PredictedStreet
from repository.predictRepository import getRuledStreet, getAllStreets, predict

MAX_DEPTH = 6

def _ruledStreet(street_name: str, level: int, cache: dict | None = None):
    # cache: evita repetir la consulta a Mongo para una misma calle dentro de un request
    if cache is not None and street_name in cache:
        doc = cache[street_name]
    else:
        doc = getRuledStreet(street_name)
        if cache is not None:
            cache[street_name] = doc

    if doc is None:
        return None  # la calle no existe

    # para hacer que level caiga en el rango de las alturas (comienzan en ***1 o ***2)
    levelInRange = level
    if levelInRange % 10 == 0:
        levelInRange += 2

    ruledStreet = None
    for aInit, section in doc["streets"].items():
        a0 = int(aInit)
        # dentro del rango y de la misma paridad
        if a0 <= levelInRange <= int(section["aFin"]) and levelInRange % 2 == a0 % 2:
            # copia, para no modificar el documento cacheado
            ruledStreet = {**section, "aInit": a0}

    return ruledStreet


def _buildNode(name: str, level: int, depth: int, cache: dict, ancestors: frozenset):
    section = _ruledStreet(name, level, cache)
    if section is None:
        return None

    key = (name, section["aInit"])
    if key in ancestors:
        return None

    neighbors = []
    if depth > 0:
        nextAncestors = ancestors | {key}
        for nName, nInfo in section.get("neighbors", {}).items():
            child = _buildNode(nName, nInfo["aInit"], depth - 1, cache, nextAncestors)
            if child is not None:
                neighbors.append(child)

    return {
        "street": PredictedStreet(
            name = name,
            probability = predict(name, section["aInit"], section["aFin"]),
            level = level,
            rule = section["rule"],
            hInit = section["hInit"],
            hFin = section["hFin"],
            aInit = section["aInit"],
            aFin = section["aFin"],
            latitudeInit = section["latitudeInit"],
            longitudeInit = section["longitudeInit"],
            latitudeEnd = section["latitudeEnd"],
            longitudeEnd = section["longitudeEnd"]
        ),
        "neighbors": neighbors
    }


def predictStreet(street_name: str, level: int, depth: int = 1) -> PredictResponse:
    depth = max(0, min(depth, MAX_DEPTH))
    return _buildNode(street_name, level, depth, cache={}, ancestors=frozenset())


def getStreets() -> dict[str]:
    return {"streets": getAllStreets()}