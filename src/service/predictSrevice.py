from model.predictModel import PredictedStreet

def predictStreet(street: str) -> list[PredictedStreet]:
    # Primero buscar las N calles cercanas a la ubicación
    # Chequear que se pueda estacionar en ellas
    # Si se puede preguntar al modelo la probabilidad

    # TODO: respuesta fija hasta que este el modelo (3.5)
    return [PredictedStreet(name = street, WKT = [1.1], probability = 0.4), PredictedStreet(name = "a", WKT = [1.1], probability = 0.4)]