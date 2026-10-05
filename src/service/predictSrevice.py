from model.predictModel import PredictedStreet
from repository.predictRepository import getValue

def predictStreet(street: str) -> list[PredictedStreet]:
    # Primero buscar las N calles cercanas a la ubicación

    getValue()


    # Chequear que se pueda estacionar en ellas
    # Si se puede preguntar al modelo la probabilidad

    return [PredictedStreet(name = street, WKT = [1.1], probability = 0.4), PredictedStreet(name = "a", WKT = [1.1], probability = 0.4)]