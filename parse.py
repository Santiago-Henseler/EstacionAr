import random

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
    with open("dataSets/conteo_Vehicular_detalle_semanal.csv") as e:
        with open("dataSets/conteo_vehicular_parsed.csv", "w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("calle,x0,y0,hora,cantidad\n")
                    i += 1
                else:
                    splited = line.split(",")

                    # Nombre de la calle
                    row = splited[6].replace('"', "")

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

                    # Nombre de la calle 
                    row = splited[5].replace('"', "")

                    # x,y
                    row = row + "," + splited[6].replace('"', "") + "," + splited[7].replace('"', "")

                    # Horario
                    horario = str(random.randint(10, 18))

                    row = row + "," + horario 

                    # Cantidad de autos
                    row = row + ","+ splited[12].replace('"', "") 

                    print(row) # Problema con las avenida que tienen por ej ALBERDI, JUAN BAUTISTA AV. 890

                    #a.write(row + "\n")
                    
if __name__ == "__main__":
    parseReglas()
    parseConteo1()
    parseConteo2()