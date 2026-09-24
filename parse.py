def parseReglas():
    with open("dataSets/estacionamiento_via_publica.csv") as e:
        with open("dataSets/estacionamiento_parsed.csv","w") as a:
            i = 0
            for line in e.readlines():
                if i == 0:
                    a.write("x0,y0,x1,y1,mano,regla,hInicio,hFin\n")
                    i += 1
                else:
                    xyxy = line.split(";")[0].replace('"MULTILINESTRING','').replace("((",'').replace('))"', '').split(",")
                    x0 = xyxy[0].split(" ")[1]
                    y0 = xyxy[0].split(" ")[2]
                    x1 = xyxy[1].split(" ")[0]
                    y1 = xyxy[1].split(" ")[1]

                    # Desde (x0,y0) hasta (x1,y1) funciona esta norma
                    row = x0 + "," + y0 + "," + x1 + "," + y1
    
                    # En que mano se cumple la norma
                    row = row + "," + line.split(";")[7] 

                    ruleLine = line.split(";")[15].replace(" Y DETENERSE", "").replace(" A 45Â°", "").replace(" A 90Â°", "")
                    timeLine = line.split(";")[17]

                    rule = line.split(";")[11] if ruleLine == "" else ruleLine
                    time = line.split(";")[13] if ruleLine == "" else timeLine

                    if time == "24 HORAS":
                        a.write(row + "," + rule + "," + "0,24\n")
                    else:
                        a.write(row + "," + rule + "," + "7,21\n") 


def parseConteo():
    with open("dataSets/conteo_Vehicular_detalle_semanal.csv") as e:
        for line in e.readlines():
            print(line.split(",")[14])


if __name__ == "__main__":
    #parseReglas()
    parseConteo()