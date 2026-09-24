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
                    row = line.split(";")[2].replace('"', "")

                    xyxy = line.split(";")[0].replace('"MULTILINESTRING','').replace("((",'').replace('))"', '').split(",")
                    x0 = xyxy[0].split(" ")[1]
                    y0 = xyxy[0].split(" ")[2]
                    x1 = xyxy[1].split(" ")[0]
                    y1 = xyxy[1].split(" ")[1]

                    # Desde (x0,y0) hasta (x1,y1) funciona esta norma
                    row = row + x0 + "," + y0 + "," + x1 + "," + y1
    
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


def parseConteo():
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
                    row = splited[6]

                    # x,y
                    row = row + "," + splited[7] + "," + splited[8]

                    # Horario
                    row = row + "," + splited[3].replace('"', "")

                    # Cantidad de autos
                    row = row + ","+ splited.pop(len(splited)-1).replace("\n", "").replace('"', "")

                    a.write(row + "\n")
                    



if __name__ == "__main__":
    #parseReglas()
    parseConteo()