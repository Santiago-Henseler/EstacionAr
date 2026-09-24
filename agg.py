import pandas as pd


if __name__ == "__main__":
    conteo = pd.read_csv("dataSets/conteo_vehicular_parsed.csv")

    print(conteo.groupby(["calle", "x0", "y0", "hora"])["cantidad"].sum().reset_index())

