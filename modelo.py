import random
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import ast

#from pymongo import MongoClient

def parseReglas():
    with open("dataSets/estacionamiento_via_publica.csv") as e:
        with open("dataSets/estacionamiento_parsed.csv","w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("calle,x0,y0,x1,y1,mano,aInicio,aFin,regla,hInicio,hFin\n")
                    i += 1
                else:
                    splited = line.split(";")

                    # Nombre de la calle
                    row = splited[2].replace('"', "").replace(",", "")

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

                    if time == "24 HORAS":
                        a.write(row + "," + rule + "," + "0,24\n")
                    else:
                        a.write(row + ",PERMITIDO ESTACIONAR,22,6\n")
                        a.write(row + "," + rule + "," + "7,21\n") 


def parseConteo1():
    with open("dataSets/conteo_vehicular_2024.csv") as e:
        with open("dataSets/conteo_vehicular_parsed.csv", "w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("calle,x0,y0,hora,cantidad\n")
                    i += 1
                else:
                    splited = line.split(",")

                    # Nombre de la calle
                    row = ''.join(c for c in splited[6].replace('"', "") if not c.isdigit())

                    # x,y
                    row = row + "," + splited[7].replace('"', "") + "," + splited[8].replace('"', "")

                    # Horario
                    horario = splited[3].replace('"', "") if splited[3].replace('"', "") != "0" else "24"

                    row = row + "," + horario 

                    # Cantidad de autos
                    row = row + ","+ splited.pop(len(splited)-1).replace("\n", "").replace('"', "")

                    a.write(row + "\n")


def parseConteo2():
    with open("dataSets/conteo_vehicular_2025.csv") as e:
        with open("dataSets/conteo_vehicular_parsed.csv", "a") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    i += 1
                else:

                    #calle,x0,y0,hora,cantidad
                    splited = line.split(",")

                    # Nombre de la calle (sin altura)
                    row = ''.join(c for c in splited[4].replace('"', "") if not c.isdigit())

                    # x,y
                    row = row + "," + splited[5].replace('"', "") + "," + splited[6].replace('"', "")

                    # Horario
                    horario = str(random.randint(10, 18))

                    row = row + "," + horario 

                    # Cantidad de autos
                    row = row + ","+ splited[12].replace('"', "") 
                    
                    a.write(row)


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


def mergeDatasets():
    conteo = pd.read_csv("dataSets/conteo_vehicular_parsed.csv")
    reglas = pd.read_csv("dataSets/estacionamiento_parsed.csv")
    
    conteoGroup = conteo.groupby(["calle", "x0", "y0", "hora"])["cantidad"].sum().reset_index()

    conteoGroup['calle'] = conteoGroup['calle'].str.strip().str.upper()
    reglas['calle'] = reglas['calle'].str.strip().str.upper()

    merged = pd.merge(reglas, conteoGroup, on="calle", how='left')
    merged = merged[((merged['hora'] >= merged['hInicio']) & (merged['hora'] <= merged['hFin'])) | (merged['hora'].isna())]
    merged = merged.drop(columns=["x0_y","y0_y"])

    merged["cantidad"] = merged["cantidad"].fillna(0)

    merged["estacionamientos"] = 0
    merged.loc[merged["regla"] == "PERMITIDO ESTACIONAR" , "estacionamientos"] = 10
    merged.loc[(merged["regla"] == "PERMITIDO ESTACIONAR") & (merged['calle'].str.contains("AV.", na=False, regex=False)) , "estacionamientos"] = 15

    merged = merged.drop(columns=["regla", "mano"])

    maxCant = max(merged["cantidad"])
    merged.loc[(merged["estacionamientos"] > 0) & (merged["cantidad"] > 0), "estacionamientos"] = merged["estacionamientos"] - (2 + ((merged["cantidad"] - 1) * (merged["estacionamientos"] -1)) // (maxCant - 1))

    merged["hora"] = merged["hora"].apply(lambda x: np.random.randint(0,24) if pd.isna(x) else x).astype(int)

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

    #CONNECTION_STRING = "mongodb://root:secretpassword@localhost:27017"
    #client = MongoClient(CONNECTION_STRING)
    #dbConection = client['db']['streets']

    #dbConection.create_index([("street", 1), ("aInit", 1)])

    def insertInMongo(x):
        
        rules = {}
        for i in range(len(x)):
            vecinos = {}
            v = ast.literal_eval(x[i][6])
            for j in range(len(v)):
                vecinos[v[j][0]] = {
                    "aInit": v[j][1],
                    "aFin": v[j][2]
                }

            rules[x[i][1]] = {
                "rule": 1 if x[i][0] == 'PERMITIDO ESTACIONAR' else -1,
                "aFin": x[i][2],
                "hInit": x[i][3],
                "hFin": x[i][4],
                "mano": x[i][5],
                "neighbors": vecinos
            }

        #dbConection.insert_one({
        #    "_id": {"street": x["calle"]},
        #    "rules": [],
        #    "neighbors": vecinos
        #})

    df.groupby("calle")[["regla", "aInicio", "aFin", "hInicio", "hFin", "mano", "calles_cercanas"]].apply(lambda x: x.values).apply(lambda x: insertInMongo(x))

if __name__ == "__main__":
    #parseReglas()
    #parseConteo1()
    #parseConteo2()
    #parseoCalles()
    #mergeDatasets()    
    loadMongoData()