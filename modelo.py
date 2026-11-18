import os
import sys
import ast
import joblib
import hashlib
import pandas as pd
import numpy as np
from pymongo import MongoClient
from sklearn.neighbors import BallTree
from sklearn.metrics import accuracy_score
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

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

    merged = merged[["calle", "aInicio", "aFin", "hora", "estacionamientos"]]

    merged.to_csv("dataSets/merged.csv", index=False)


def trainModel():
    data = pd.read_csv("dataSets/merged.csv")

    dataY = data["estacionamientos"]

    data["calle"] = data["calle"].map(lambda x: int.from_bytes(hashlib.sha256(x.strip().upper().encode("utf-8")).digest()[:4], byteorder="big"))
    dataX = data.drop(columns=["estacionamientos"])

    trainX, testX, trainY, testY = train_test_split(
        dataX,
        dataY,
        test_size=0.25,
        shuffle=True,
        random_state=42
    )
    model = DecisionTreeClassifier(
        max_depth=16,
        min_samples_leaf=5,
        random_state=42
    )

    model.fit(trainX, trainY)

    y_pred = model.predict(testX)

    print("Accuracy:", accuracy_score(testY, y_pred))
    
    joblib.dump(model, "modelo_estacionar.pkl")

from scipy.spatial import cKDTree

TOL_M = 35.0                   # un extremo a <= 35 m de otro tramo => son vecinos
PASO_M = 5.0                   # solo para buscar candidatos rápido
INCLUIR_LADO_OPUESTO = False   # True = la otra vereda de la misma cuadra también cuenta como vecina
GEOM = ["calle", "mano", "aInicio", "aFin", "x0", "y0", "x1", "y1"]


def _proyectar(seg):
    lat0 = np.radians(np.concatenate([seg["y0"], seg["y1"]]).astype(float).mean())
    f = lambda lon, lat: np.column_stack([np.radians(lon.astype(float)) * np.cos(lat0) * 6371000.0,
                                          np.radians(lat.astype(float)) * 6371000.0])
    return f(seg["x0"].to_numpy(), seg["y0"].to_numpy()), f(seg["x1"].to_numpy(), seg["y1"].to_numpy())


def _dist_punto_segmento(p, a, b):
    ab = b - a
    ab2 = (ab ** 2).sum(axis=1)
    t = np.where(ab2 > 0, ((p - a) * ab).sum(axis=1) / np.where(ab2 > 0, ab2, 1.0), 0.0)
    return np.hypot(*(p - (a + np.clip(t, 0.0, 1.0)[:, None] * ab)).T)


def _pares_conectados(P0, P1, tol=TOL_M, paso=PASO_M):
    n = len(P0)
    largo = np.hypot(*(P1 - P0).T)
    tramos = np.maximum(np.ceil(largo / paso).astype(int), 1)
    n_pts = tramos + 1
    dueno = np.repeat(np.arange(n), n_pts)
    primero = np.repeat(np.cumsum(n_pts) - n_pts, n_pts)
    t = (np.arange(n_pts.sum()) - primero) / np.repeat(tramos, n_pts)
    arbol = cKDTree(P0[dueno] + t[:, None] * (P1[dueno] - P0[dueno]))

    extremos = np.vstack([P0, P1])
    de = np.concatenate([np.arange(n), np.arange(n)]).tolist()
    candidatos = arbol.query_ball_point(extremos, r=tol + paso / 2)

    pares = {}
    for e, (idx, i) in enumerate(zip(candidatos, de)):
        cand = np.unique(dueno[idx])
        cand = cand[cand != i]
        if cand.size == 0:
            continue
        d = _dist_punto_segmento(extremos[e], P0[cand], P1[cand])
        ok = d <= tol
        for j, dj in zip(cand[ok].tolist(), d[ok].tolist()):
            clave = (i, j) if i < j else (j, i)
            if dj < pares.get(clave, np.inf):
                pares[clave] = dj
    return pares


def _paralelos_y_superpuestos(i, j, P0, P1):
    vi, vj = P1[i] - P0[i], P1[j] - P0[j]
    li, lj = np.hypot(*vi), np.hypot(*vj)
    if li == 0 or lj == 0:
        return False
    ui, uj = vi / li, vj / lj
    if abs(ui @ uj) < np.cos(np.radians(20)):
        return False
    a, b = sorted([(P0[j] - P0[i]) @ ui, (P1[j] - P0[i]) @ ui])
    return (min(li, b) - max(0.0, a)) / min(li, lj) >= 0.5


def agregar_vecinos(df):
    df = df.copy()
    validas = df[["x0", "y0", "x1", "y1"]].notna().all(axis=1)
    seg = df.loc[validas, GEOM].drop_duplicates().reset_index(drop=True)
    seg.index.name = "seg_id"
    vec = [[] for _ in range(len(seg))]

    if len(seg):
        P0, P1 = _proyectar(seg)
        calle, a_ini = seg["calle"].tolist(), seg["aInicio"].tolist()
        a_fin, mano = seg["aFin"].tolist(), seg["mano"].tolist()
        for (i, j), d in _pares_conectados(P0, P1).items():
            if calle[i] != calle[j]:
                tipo = "otra_calle"
            elif _paralelos_y_superpuestos(i, j, P0, P1):
                tipo = "lado_opuesto"
            else:
                tipo = "continuacion"
            if tipo == "lado_opuesto" and not INCLUIR_LADO_OPUESTO:
                continue
            for a, b in ((i, j), (j, i)):
                vec[a].append({"calle": calle[b], "aInicio": a_ini[b], "aFin": a_fin[b],
                               "mano": mano[b], "tipo": tipo, "dist_m": round(float(d), 1)})
        for lista in vec:
            lista.sort(key=lambda v: v["dist_m"])

    df = df.merge(seg.reset_index(), on=GEOM, how="left")
    df["vecinos"] = df["seg_id"].map(lambda s: vec[int(s)] if pd.notna(s) else [])
    return df


def _vecinos_a_dict(vecinos):
    out = {}
    for v in vecinos:
        if v["calle"] not in out:
            out[v["calle"]] = {"aInit": v["aInicio"], "aFin": v["aFin"]}
    return out


def loadMongoData():
    df = pd.read_csv("dataSets/estacionamiento_parsed.csv")
    df = agregar_vecinos(df)

    CONNECTION_STRING = "mongodb://root:secretpassword@localhost:27017"
    client = MongoClient(CONNECTION_STRING)
    dbConection = client['db']['streets']
    dbConection.drop()

    docs = []
    for calle, g in df.groupby("calle", sort=False):
        rules = {}
        for r in g.itertuples(index=False):
            rules[str(r.aInicio)] = {
                "rule": 1 if r.regla == 'PERMITIDO ESTACIONAR' else -1,
                "aFin": r.aFin,
                "hInit": r.hInicio,
                "hFin": r.hFin,
                "mano": r.mano,
                "neighbors": _vecinos_a_dict(r.vecinos),
                "latitudeInit": r.y0,
                "longitudeInit": r.x0,
                "latitudeEnd": r.y1,
                "longitudeEnd": r.x1,
            }
        docs.append({"_id": str(calle), "streets": rules})
    if docs:
        dbConection.insert_many(docs)


if __name__ == "__main__":
    #parseReglas()
    #parseConteo1()
    #parseConteo2()
    #parseoCalles()
    #mergeDatasets()
    trainModel()
    #loadMongoData()
