import random
import pandas as pd

def parseReglas():
    with open("dataSets/estacionamiento_via_publica.csv") as e:
        with open("dataSets/estacionamiento_parsed.csv","w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("calle,x0,y0,x1,y1,mano,regla,hInicio,hFin\n")
                    i += 1
                else:
                    # Nombre de la calle
                    row = line.split(";")[2].replace('"', "").replace(",", "")

                    xyxy = line.split(";")[0].replace('"MULTILINESTRING','').replace("((",'').replace('))"', '').split(",")
                    x0 = xyxy[0].split(" ")[1]
                    y0 = xyxy[0].split(" ")[2]
                    x1 = xyxy[1].split(" ")[0]
                    y1 = xyxy[1].split(" ")[1]

                    # Desde (x0,y0) hasta (x1,y1) funciona esta norma
                    row = row + "," + x0 + "," + y0 + "," + x1 + "," + y1
    
                    # En que mano se cumple la norma
                    row = row + "," + line.split(";")[7] 

                    ruleLine = line.split(";")[15].replace(" Y DETENERSE", "").replace(" A 45Â°", "").replace(" A 90Â°", "").replace(" PARALELO A CICLOVIA", "")
                    timeLine = line.split(";")[17]

                    rule = line.split(";")[11] if ruleLine == "" else ruleLine
                    time = line.split(";")[13] if ruleLine == "" else timeLine

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
                    
if __name__ == "__main__":
    #parseReglas()
    #parseConteo1()
    #parseConteo2()

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

    # hacer calculo para sacar estimacion
    maxCant = max(merged["cantidad"])
    merged.loc[(merged["estacionamientos"] > 0) & (merged["cantidad"] > 0), "estacionamientos"] = 1 - (max - merged["cantidad"])

    merged.to_csv("a", index=False)

    print(merged)
