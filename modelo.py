import os
import sys
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree

import ast
from pymongo import MongoClient, GEOSPHERE

# Semilla fija para que el dataset simulado sea reproducible
SEMILLA = 42

# Un conteo se asocia a las cuadras que estan a menos de 3 cuadras (~100 m cada una)
RADIO_ASOCIACION_M = 300
RADIO_TIERRA_M = 6371000

# Supuesto de la simulacion: una calle tiene un 30% del flujo de una avenida
FACTOR_FLUJO_CALLE = 0.3

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://root:secretpassword@localhost:27017")

def parseReglas():
    with open("dataSets/estacionamiento_via_publica.csv") as e:
        with open("dataSets/estacionamiento_parsed.csv","w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("id,calle,x0,y0,x1,y1,mano,aInicio,aFin,regla,hInicio,hFin\n")
                    i += 1
                else:
                    splited = line.split(";")

                    # Id del tramo y nombre de la calle
                    row = splited[1] + "," + splited[2].replace('"', "").replace(",", "")

                    xyxy = splited[0].replace('"MULTILINESTRING','').replace("((",'').replace('))"', '').split(",")

                    x0 = xyxy[0].split(" ")[1]
                    y0 = xyxy[0].split(" ")[2]

                    x1 = xyxy[len(xyxy) -1].split(" ")[0]
                    y1 = xyxy[len(xyxy) -1].split(" ")[1]

                    # Desde (x0,y0) hasta (x1,y1) funciona esta norma
                    row = row + "," + x0 + "," + y0 + "," + x1 + "," + y1

                    # En que mano se cumple la norma
                    row = row + "," + splited[7]

                    # Altura de la norma
                    alturas = splited[8].split("-")

                    if len(alturas) == 1:
                        row = row + ",0,0"
                    else:
                        row = row + "," + alturas[0].replace(" ", "") + "," + alturas[1].replace(" ", "")

                    ruleLine = splited[15].replace(" Y DETENERSE", "").replace(" A 45Â°", "").replace(" A 90Â°", "").replace(" PARALELO A CICLOVIA", "")
                    timeLine = splited[17]

                    rule = splited[11] if ruleLine == "" else ruleLine
                    time = splited[13] if ruleLine == "" else timeLine

                    # La franja va de hInicio (incluida) a hFin (excluida), si hInicio > hFin cruza la medianoche
                    if time == "24 HORAS":
                        a.write(row + "," + rule + "," + "0,24\n")
                    else:
                        a.write(row + ",PERMITIDO ESTACIONAR,21,7\n")
                        a.write(row + "," + rule + "," + "7,21\n")


def parseConteo1():
    with open("dataSets/conteo_vehicular_2024.csv") as e:
        with open("dataSets/conteo_vehicular_parsed.csv", "w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("calle,x0,y0,fecha,hora,cantidad\n")
                    i += 1
                else:
                    splited = line.split(",")

                    # Nombre de la calle
                    row = ''.join(c for c in splited[6].replace('"', "") if not c.isdigit())

                    # x,y
                    row = row + "," + splited[7].replace('"', "") + "," + splited[8].replace('"', "")

                    # Fecha y horario
                    row = row + "," + splited[0].replace('"', "") + "," + splited[3].replace('"', "")

                    # Cantidad de autos
                    row = row + ","+ splited.pop(len(splited)-1).replace("\n", "").replace('"', "")

                    a.write(row + "\n")


def parseConteo2():
    # El conteo de 2025 trae totales diarios, se reparten en las 24 horas con una
    # distribucion normal con la media y el desvio del perfil horario de 2024
    conteo = pd.read_csv("dataSets/conteo_vehicular_parsed.csv")
    perfil = conteo.groupby("hora")["cantidad"].sum()
    perfil = perfil / perfil.sum()

    media = (perfil * perfil.index).sum()
    desvio = np.sqrt((perfil * (perfil.index - media) ** 2).sum())

    horas = np.arange(24)
    pesos = np.exp(-0.5 * ((horas - media) / desvio) ** 2)
    pesos = pesos / pesos.sum()

    with open("dataSets/conteo_vehicular_2025.csv") as e:
        with open("dataSets/conteo_vehicular_parsed.csv", "a") as a:
            for line in e.readlines():
                splited = line.split(",")

                # Hay filas sin conteo
                if splited[12].strip() == "":
                    continue

                # Nombre de la calle (sin altura)
                row = ''.join(c for c in splited[4].replace('"', "") if not c.isdigit())

                # x,y y fecha
                row = row + "," + splited[5].replace('"', "") + "," + splited[6].replace('"', "") + "," + splited[0]

                # Cantidad de autos en cada hora
                total = float(splited[12])
                for hora in horas:
                    a.write(row + "," + str(hora) + "," + str(round(total * pesos[hora], 1)) + "\n")


def parseoCalles():
    with open("dataSets/callejero.csv") as e:
        with open("dataSets/calles_parsed.csv", "w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("calle,aInicio,aFin,WKT\n")
                    i += 1
                else:
                    splited = line.split(",")

                    maxAlt = max(splited[4], splited[6])
                    minAlt = min(splited[3], splited[5])

                    a.write(splited[2] + ","+ minAlt + "," + maxAlt + "," + splited[22])


def horasDeRegla(hInicio, hFin):
    if hInicio < hFin:
        return list(range(hInicio, hFin))
    return list(range(hInicio, 24)) + list(range(0, hFin))


def cargarTramos():
    reglas = pd.read_csv("dataSets/estacionamiento_parsed.csv")
    reglas["calle"] = reglas["calle"].str.strip().str.upper()
    reglas["lon"] = (reglas["x0"] + reglas["x1"]) / 2
    reglas["lat"] = (reglas["y0"] + reglas["y1"]) / 2
    return reglas


def flujoPorHora():
    conteo = pd.read_csv("dataSets/conteo_vehicular_parsed.csv")
    conteo["calle"] = conteo["calle"].str.strip().str.upper()

    # Total por punto, fecha y hora (todos los vehiculos y cuartos de hora) y despues el promedio entre fechas
    porFecha = conteo.groupby(["calle", "x0", "y0", "fecha", "hora"])["cantidad"].sum().reset_index()
    flujo = porFecha.groupby(["calle", "x0", "y0", "hora"])["cantidad"].mean().reset_index()

    puntos = flujo[["calle", "x0", "y0"]].drop_duplicates().reset_index(drop=True)
    puntos["punto"] = puntos.index
    flujo = flujo.merge(puntos, on=["calle", "x0", "y0"])[["punto", "hora", "cantidad"]]

    return puntos, flujo


def asignarPuntos(tramos, puntos):
    # Primero el conteo mas cercano a menos de 3 cuadras
    tree = BallTree(np.radians(puntos[["y0", "x0"]].to_numpy()), metric="haversine")
    distancias, indices = tree.query(np.radians(tramos[["lat", "lon"]].to_numpy()), k=1)

    tramos["punto"] = -1
    tramos["origen_flujo"] = "simulado"

    cercano = distancias[:, 0] * RADIO_TIERRA_M <= RADIO_ASOCIACION_M
    tramos.loc[cercano, "punto"] = puntos["punto"].to_numpy()[indices[cercano, 0]]
    tramos.loc[cercano, "origen_flujo"] = "cercano"

    # Si no hay ninguno, el conteo mas cercano sobre la misma calle
    for calle, puntosCalle in puntos.groupby("calle"):
        mismaCalle = (tramos["origen_flujo"] == "simulado") & (tramos["calle"] == calle)
        if not mismaCalle.any():
            continue

        treeCalle = BallTree(np.radians(puntosCalle[["y0", "x0"]].to_numpy()), metric="haversine")
        _, indicesCalle = treeCalle.query(np.radians(tramos.loc[mismaCalle, ["lat", "lon"]].to_numpy()), k=1)

        tramos.loc[mismaCalle, "punto"] = puntosCalle["punto"].to_numpy()[indicesCalle[:, 0]]
        tramos.loc[mismaCalle, "origen_flujo"] = "misma_calle"

    return tramos


def mergeDatasets():
    rng = np.random.default_rng(SEMILLA)

    reglas = cargarTramos()
    puntos, flujo = flujoPorHora()

    tramos = reglas.drop_duplicates("id")[["id", "calle", "lon", "lat"]].copy()
    tramos = asignarPuntos(tramos, puntos)

    # Cada tramo tiene un ruido propio para que los simulados no sean todos iguales
    tramos["ruido"] = rng.lognormal(0, 0.3, len(tramos))

    # Una fila por tramo y hora, con la regla que aplica en esa hora
    reglas["hora"] = [horasDeRegla(i, f) for i, f in zip(reglas["hInicio"], reglas["hFin"])]
    merged = reglas.explode("hora").astype({"hora": int})

    # Hay tramos repetidos en el dataset de la ciudad, si las reglas se pisan gana la prohibicion
    merged = merged.sort_values("regla", ascending=False).drop_duplicates(["id", "hora"])
    merged = merged.merge(tramos[["id", "punto", "origen_flujo", "ruido"]], on="id")
    merged = merged.merge(flujo, on=["punto", "hora"], how="left")

    # Flujo simulado: perfil horario promedio de los conteos, escalado por tipo de calle
    perfil = flujo.groupby("hora")["cantidad"].mean()
    esAvenida = merged["calle"].str.contains("AV.", na=False, regex=False)
    simulado = merged["hora"].map(perfil) * np.where(esAvenida, 1, FACTOR_FLUJO_CALLE) * merged["ruido"]

    sinFlujo = merged["cantidad"].isna()
    merged.loc[sinFlujo, "origen_flujo"] = "simulado"
    merged["cantidad"] = merged["cantidad"].fillna(simulado).round(1)

    merged["estacionamientos"] = 0
    merged.loc[merged["regla"] == "PERMITIDO ESTACIONAR" , "estacionamientos"] = 10
    merged.loc[(merged["regla"] == "PERMITIDO ESTACIONAR") & esAvenida , "estacionamientos"] = 15

    # Se normaliza con el percentil 95 y no con el maximo para que unos pocos picos no aplasten al resto
    maxCant = merged["cantidad"].quantile(0.95)
    cantidad = merged["cantidad"].clip(upper=maxCant)
    conFlujo = (merged["estacionamientos"] > 0) & (merged["cantidad"] > 0)
    merged.loc[conFlujo, "estacionamientos"] = (merged["estacionamientos"] - (2 + ((cantidad - 1) * (merged["estacionamientos"] -1)) // (maxCant - 1))).clip(lower=0)

    merged = merged[["id", "calle", "x0", "y0", "x1", "y1", "aInicio", "aFin", "hora", "cantidad", "origen_flujo", "estacionamientos"]]
    merged = merged.sort_values(["id", "hora"])

    merged.to_csv("merged.csv", index=False)


def loadMongoData():
    df = pd.read_csv("dataSets/estacionamiento_parsed.csv")

    df["lon"] = (df["x0"] + df["x1"]) / 2
    df["lat"] = (df["y0"] + df["y1"]) / 2
    coords = np.radians(df[["lat", "lon"]].to_numpy())

    tree = BallTree(coords, metric="haversine")
    distances, indices = tree.query(coords, k=6)

    distances = distances[:, 1:] * 6371000
    indices = indices[:, 1:]

    result = pd.DataFrame({"id_calle": np.repeat(df.index.to_numpy(), 5), "id_vecina": indices.flatten(), "distancia_m": distances.flatten()})

    result = result.merge(
        df.reset_index().rename(columns={
            "index": "id_vecina",
            "calle": "calle_vecina",
            "mano": "mano_vecina",
            "regla": "regla_vecina",
            "aInicio": "aInicio_vecina",
            "aFin": "aFin_vecina"
        }),
        on="id_vecina"
    )

    result = result.merge(df[["calle", "mano", "aInicio", "aFin"]].reset_index()
        .rename(columns={
            "index": "id_calle",
            "calle": "calle_original",
            "mano": "mano_original",
            "aInicio": "aInicio_original",
            "aFin": "aFin_original"
        }),
        on="id_calle"
    )

    calles_cercanas = result.sort_values("distancia_m").drop_duplicates(subset=["id_calle", "calle_vecina"]).groupby("id_calle")[["calle_vecina", "aInicio_vecina", "aFin_vecina"]].apply(lambda x: str(x.head(5).values.tolist())).reset_index(name="calles_cercanas")
    df = df.reset_index(names="id_calle").merge(calles_cercanas, on="id_calle", how="left").drop(columns=["lon", "lat"])

    CONNECTION_STRING = "mongodb://root:secretpassword@localhost:27017"
    client = MongoClient(CONNECTION_STRING)
    dbConection = client['db']['streets']

    dbConection.create_index([("street", 1)])

    def insertInMongo(x, street):
        rules = {}
        for i in range(len(x)):
            vecinos = {}
            v = ast.literal_eval(x[i][6])
            for j in range(len(v)):
                vecinos[v[j][0]] = {
                    "aInit": v[j][1],
                    "aFin": v[j][2]
                }

            rules[str(x[i][1])] = {
                "rule": 1 if x[i][0] == 'PERMITIDO ESTACIONAR' else -1,
                "aFin": x[i][2],
                "hInit": x[i][3],
                "hFin": x[i][4],
                "mano": x[i][5],
                "neighbors": vecinos
            }

        dbConection.insert_one({
            "_id": str(street),
            "streets": rules 
        })

    df.groupby("calle")[["regla", "aInicio", "aFin", "hInicio", "hFin", "mano", "calles_cercanas"]].apply(lambda x: insertInMongo(x.values, x.name))


if __name__ == "__main__":
    parseReglas()
    parseConteo1()
    parseConteo2()
    parseoCalles()
    mergeDatasets()

    # Requiere el mongo levantado: docker compose up -d mongodb
    if "--mongo" in sys.argv:
        loadMongoData()
