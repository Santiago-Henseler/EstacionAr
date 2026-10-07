from model.predictModel import PredictedStreet
from repository.predictRepository import getRuledStreet, getAllStreets

def _ruledStreet(street: str, level: int):
    ruledStreets = getRuledStreet(street)

    ruledStreet = None
    for aInit in ruledStreets["streets"].keys():
        if (level > int(aInit) or level > int(aInit) - 5) and level < int(ruledStreets["streets"][aInit]["aFin"]):
            if ruledStreet == None:
                ruledStreet = ruledStreets["streets"][aInit]
                continue
            elif ruledStreet["aFin"] > int(ruledStreets["streets"][aInit]["aFin"]):
                ruledStreet = ruledStreets["streets"][aInit] 

    return ruledStreet

def predictStreet(street: str, level: int) -> list[PredictedStreet]:
    # Primero busco las N calles cercanas a la ubicación
    nearStreet = []

    firstStreet = _ruledStreet(street, level)
    firstStreet["name"] = street
    firstStreet["aInit"] = level
    nearStreet.append(firstStreet)
    
    for sName in firstStreet["neighbors"].keys():
        aInit = firstStreet["neighbors"][sName]["aInit"]
        s = _ruledStreet(sName, aInit)
        s["name"] = sName
        s["aInit"] = aInit
        nearStreet.append(s)

    # Model.predict(s) 

    # TODO: respuesta fija hasta que este el modelo (3.5)
    return [PredictedStreet(name = street, WKT = [1.1], probability = 0.4), PredictedStreet(name = "a", WKT = [1.1], probability = 0.4)]

def getStreets() -> list[str]:
    return getAllStreets()