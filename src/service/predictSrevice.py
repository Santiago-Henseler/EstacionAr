from model.predictModel import PredictedStreet
from repository.predictRepository import getValue

def predictStreet(street: str, level: int) -> list[PredictedStreet]:
    # Primero buscar las N calles cercanas a la ubicación

    values = getValue(street)

    ruledStreet = None
    for aInit in values["streets"].keys():
        if (level > int(aInit) or level > int(aInit) - 5) and level < int(values["streets"][aInit]["aFin"]):
            if ruledStreet == None:
                ruledStreet = values["streets"][aInit]
                continue
            elif ruledStreet["aFin"] > int(values["streets"][aInit]["aFin"]):
                ruledStreet = values["streets"][aInit] 

    print(ruledStreet)

    # Chequear que se pueda estacionar en ellas
    # Si se puede preguntar al modelo la probabilidad

    return [PredictedStreet(name = street, WKT = [1.1], probability = 0.4), PredictedStreet(name = "a", WKT = [1.1], probability = 0.4)]