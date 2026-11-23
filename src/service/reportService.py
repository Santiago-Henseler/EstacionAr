from datetime import datetime, timedelta, UTC
from fastapi import HTTPException, status
from repository.reportRepository import insertReport, countReportsSince, findByUser, noSpotReportsSince
from repository.predictRepository import horaActual, TZ
from model.reportModel import ReportCreate

MAX_REPORTS_PER_DAY = 10

# Señal en vivo: reportes recientes de "no había lugar" en el tramo, a cualquier hora
LIVE_WINDOW_MIN = 60   # reportes recientes que cuentan
HALF_LIFE_MIN = 20     # cada 20 minutos el reporte pierde la mitad del peso
LIVE_MAX = 0.8         # baja maxima por la señal en vivo

# Señal historica: reportes de la misma hora en dias anteriores
HIST_DAYS = 90
HIST_MAX = 0.5         # baja maxima por la señal historica
K_HIST = 5             # con cuantos (usuario, dia) se llega a la mitad de HIST_MAX

LOW_AVAILABILITY_USERS = 2  # usuarios distintos para marcar "poca disponibilidad"


def createReport(user_id: int, data: ReportCreate) -> dict:
    # import local: predictSrevice importa este modulo para las señales
    from service.predictSrevice import _ruledStreet

    street_name = data.street_name.strip().upper()
    section = _ruledStreet(street_name, data.level)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calle no encontrada")

    if countReportsSince(user_id, datetime.now(UTC) - timedelta(hours=24)) >= MAX_REPORTS_PER_DAY:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Limite de reportes diarios alcanzado")

    description = data.description.strip() if data.description else None
    return insertReport(
        user_id=user_id,
        reason=data.reason,
        street_name=street_name,
        level=data.level,
        a_init=section["aInit"],
        hour=horaActual(),
        description=description or None,
    )


def getUserReports(user_id: int) -> list[dict]:
    return findByUser(user_id)


def reportSignals(now: datetime | None = None) -> tuple[dict, dict]:
    """
    live: {(calle, aInit): {user_id: peso}}  -> peso del reporte mas reciente de cada usuario
    hist: {(calle, aInit, hora): n}          -> cantidad de (usuario, dia) distintos
    """
    now = now or datetime.now(UTC)
    liveSince = now - timedelta(minutes=LIVE_WINDOW_MIN)

    live: dict = {}
    histPairs: dict = {}
    for user_id, street, aInit, hour, createdAt in noSpotReportsSince(now - timedelta(days=HIST_DAYS)):
        if createdAt >= liveSince:
            ageMin = max(0.0, (now - createdAt).total_seconds() / 60)
            weight = 0.5 ** (ageMin / HALF_LIFE_MIN)
            users = live.setdefault((street, aInit), {})
            users[user_id] = max(users.get(user_id, 0.0), weight)
        else:
            day = createdAt.astimezone(TZ).date()
            histPairs.setdefault((street, aInit, hour), set()).add((user_id, day))

    hist = {key: len(pairs) for key, pairs in histPairs.items()}
    return live, hist


def applyReports(proba: float, street: str, aInit: int, hour: int, signals: tuple[dict, dict]) -> tuple[float, int]:
    live, hist = signals
    key = (street.strip().upper(), aInit)

    users = live.get(key, {})
    if users:
        s = sum(users.values())
        proba *= 1 - LIVE_MAX * s / (s + 1)

    n = hist.get((*key, hour), 0)
    if n:
        proba *= 1 - HIST_MAX * n / (n + K_HIST)

    return proba, len(users)
