"""Modelos de ranking de noticias reconstruidos por ingeniería inversa.

Cada función recibe una `Noticia` y devuelve un `Resultado` con la puntuación
final y el desglose de cada factor, para ver por qué una pieza sube o baja.

Nivel de evidencia de cada constante:
  [CÓDIGO]   publicado por la empresa (X 2023, Reddit, Hacker News).
  [FILTRADO] documento interno filtrado y reportado por prensa.
  [OFICIAL]  la empresa lo describe pero sin números; el valor es estimado.
  [ESTIMADO] inferido de pruebas externas; ajústalo con tus propios datos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Noticia:
    titulo: str
    fuente: str = ""
    horas: float = 1.0                # antigüedad de la publicación
    # Probabilidades que el modelo de cada red predice para un usuario (0-1)
    p_like: float = 0.0
    p_respuesta: float = 0.0          # responder / comentar
    p_repost: float = 0.0             # retuitear / compartir
    p_click: float = 0.0              # abrir la nota o el video
    p_click_perfil: float = 0.0
    p_autor_responde: float = 0.0     # el autor contesta el comentario
    p_negativo: float = 0.0           # "no me interesa", ocultar, silenciar
    p_reporte: float = 0.0
    p_reaccion: float = 0.0           # reacciones distintas a "me gusta" (Meta)
    # Video
    es_video: bool = False
    duracion_seg: float = 0.0
    vista_esperada_seg: float = 0.0   # tiempo de visualización esperado
    satisfaccion: float = 0.5         # encuestas "¿te gustó?" (0-1)
    # Señales de contenido y fuente
    autoridad_fuente: float = 0.5     # 0-1 reputación / E-E-A-T
    relevancia_tema: float = 0.5      # coincidencia con intereses o búsqueda
    prominencia: float = 0.0          # 0-1 cuántos medios cubren la historia
    originalidad: float = 0.5         # 1 = reportaje original, 0 = refrito
    clickbait: float = 0.0            # 0-1 probabilidad de ser clickbait
    desmentida: bool = False          # marcada por verificadores
    enlace_externo: bool = False
    en_red: bool = True               # el usuario sigue al autor
    autor_verificado: bool = False    # suscripción de pago (X Premium)
    afinidad: float = 0.5             # cercanía usuario-autor (0-1)
    ubicacion_coincide: bool = False
    clicks_buenos: float = 0.0        # clicks largos (NavBoost)
    clicks_malos: float = 0.0         # regreso rápido a resultados
    # Votos (agregadores)
    votos_arriba: int = 0
    votos_abajo: int = 0


@dataclass
class Resultado:
    plataforma: str
    puntuacion: float
    desglose: dict = field(default_factory=dict)


# --------------------------------------------------------------------------
# X / Twitter  [CÓDIGO] github.com/twitter/the-algorithm-ml (marzo 2023)
# El "heavy ranker" predice ~10 acciones y las suma con estos pesos.
# --------------------------------------------------------------------------
PESOS_X = {
    "like": 0.5,
    "repost": 1.0,
    "respuesta": 13.5,
    "click_perfil": 12.0,       # click al perfil seguido de interacción
    "click": 11.0,              # abrir conversación y quedarse
    "video_50": 0.005,          # ver 50 % del video
    "autor_responde": 75.0,     # respuesta que el autor contesta
    "negativo": -74.0,          # mostrar menos, silenciar, bloquear
    "reporte": -369.0,
}
X_FACTOR_FUERA_DE_RED = 0.75     # [CÓDIGO, puede haber cambiado]
X_FACTOR_VERIFICADO = {True: 4.0, False: 2.0}  # en red / fuera de red [CÓDIGO 2023]
X_FACTOR_ENLACE = 0.5            # [ESTIMADO] Musk confirmó castigo a enlaces


def ranking_x(n: Noticia) -> Resultado:
    p_video50 = 0.0
    if n.es_video and n.duracion_seg > 0:
        p_video50 = min(1.0, n.vista_esperada_seg / (0.5 * n.duracion_seg))
    acciones = {
        "like": n.p_like, "repost": n.p_repost, "respuesta": n.p_respuesta,
        "click_perfil": n.p_click_perfil, "click": n.p_click,
        "video_50": p_video50, "autor_responde": n.p_autor_responde,
        "negativo": n.p_negativo, "reporte": n.p_reporte,
    }
    desglose = {k: PESOS_X[k] * v for k, v in acciones.items()}
    base = sum(desglose.values())
    mult = 1.0
    if not n.en_red:
        mult *= X_FACTOR_FUERA_DE_RED
    if n.autor_verificado:
        mult *= X_FACTOR_VERIFICADO[n.en_red]
    if n.enlace_externo:
        mult *= X_FACTOR_ENLACE
    desglose["multiplicador"] = mult
    return Resultado("X", base * mult, desglose)


def diversidad_autores_x(puntuaciones: list[float], decaimiento=0.5, piso=0.25):
    """[CÓDIGO] Cada post extra del mismo autor vale menos: 1, .5, .25, .25…"""
    salida = []
    for i, s in enumerate(sorted(puntuaciones, reverse=True)):
        factor = max(piso, decaimiento ** i)
        salida.append(s * factor)
    return salida


# --------------------------------------------------------------------------
# Meta (Facebook / Instagram)
# [FILTRADO] "Facebook Files", WSJ 2021: puntos de "Meaningful Social
# Interactions" (2018): like 1, reacción o compartir sin texto 5,
# comentario significativo o compartir con texto 30. Desde 2020 el
# "me enoja" vale 0.  [OFICIAL] Meta Transparency Center: suma ponderada de
# predicciones × degradaciones de integridad. Noticias reducidas desde 2023.
# --------------------------------------------------------------------------
PESOS_META = {"like": 1.0, "reaccion": 5.0, "repost": 5.0, "respuesta": 30.0,
              "click": 2.0}
META_DEGRADACION = {
    "desmentida": 0.2,          # [OFICIAL "reduce mucho"] valor estimado
    "clickbait": 0.5,           # se aplica en proporción a la probabilidad
    "enlace_externo": 0.7,      # [ESTIMADO] Meta prefiere contenido nativo
}
META_FACTOR_NOTICIAS = 0.6       # [ESTIMADO] menor peso a noticias desde 2023


def ranking_meta(n: Noticia) -> Resultado:
    acciones = {"like": n.p_like, "reaccion": n.p_reaccion, "repost": n.p_repost,
                "respuesta": n.p_respuesta, "click": n.p_click}
    desglose = {k: PESOS_META[k] * v for k, v in acciones.items()}
    valor = sum(desglose.values())
    # Afinidad: amigos y grupos pesan más que páginas (cambio de 2018).
    afinidad = 0.5 + n.afinidad
    mult = afinidad * META_FACTOR_NOTICIAS
    if n.desmentida:
        mult *= META_DEGRADACION["desmentida"]
    mult *= 1 - n.clickbait * (1 - META_DEGRADACION["clickbait"])
    if n.enlace_externo:
        mult *= META_DEGRADACION["enlace_externo"]
    mult *= 1 - min(1.0, 10 * n.p_negativo)   # ocultar publicación
    desglose["multiplicador"] = mult
    return Resultado("Meta", valor * mult, desglose)


# --------------------------------------------------------------------------
# TikTok  [FILTRADO] documento "TikTok Algo 101", NYT 2021:
#   Plike×Vlike + Pcomment×Vcomment + Eplaytime×Vplaytime + Pplay×Vplay
# Los valores V no se publicaron; los de abajo son [ESTIMADO]. La
# retención (tiempo visto / duración) es la señal dominante.
# --------------------------------------------------------------------------
PESOS_TIKTOK = {"like": 1.0, "comentario": 2.0, "tiempo": 0.1, "play": 1.0,
                "compartir": 3.0}


def ranking_tiktok(n: Noticia) -> Resultado:
    if not n.es_video:
        return Resultado("TikTok", 0.0, {"nota": "solo video"})
    retencion = n.vista_esperada_seg / n.duracion_seg if n.duracion_seg else 0
    desglose = {
        "like": PESOS_TIKTOK["like"] * n.p_like,
        "comentario": PESOS_TIKTOK["comentario"] * n.p_respuesta,
        "tiempo": PESOS_TIKTOK["tiempo"] * n.vista_esperada_seg,
        "play": PESOS_TIKTOK["play"] * n.p_click,
        "compartir": PESOS_TIKTOK["compartir"] * n.p_repost,
    }
    base = sum(desglose.values())
    # Videos vistos completos (o repetidos) reciben un empuje extra.
    mult = 0.5 + min(retencion, 1.5)
    mult *= 1 - min(1.0, 10 * n.p_negativo)
    desglose["retencion"] = retencion
    desglose["multiplicador"] = mult
    return Resultado("TikTok", base * mult, desglose)


# --------------------------------------------------------------------------
# YouTube  [CÓDIGO/PAPER] Covington et al. 2016 (tiempo de visualización
# esperado), Zhao et al. 2019 (multiobjetivo: interacción + satisfacción).
# [OFICIAL] En noticias, YouTube "eleva fuentes autorizadas".
# --------------------------------------------------------------------------
def ranking_youtube(n: Noticia) -> Resultado:
    tiempo_esperado = n.p_click * n.vista_esperada_seg
    satisfaccion = 0.5 + n.satisfaccion          # 0.5 a 1.5
    autoridad = 0.5 + n.autoridad_fuente         # sesgo a fuentes autorizadas
    clickbait = 1 - 0.7 * n.clickbait            # click sin vista = castigo
    desglose = {"tiempo_esperado": tiempo_esperado, "satisfaccion": satisfaccion,
                "autoridad": autoridad, "clickbait": clickbait}
    score = tiempo_esperado * satisfaccion * autoridad * clickbait
    if n.desmentida:
        score *= 0.1
    return Resultado("YouTube", score, desglose)


# --------------------------------------------------------------------------
# Google News / Discover
# [OFICIAL] Factores: relevancia, prominencia, autoridad, frescura,
# ubicación; desde 2019 premia el reportaje original.
# [FILTRADO] Content Warehouse API (mayo 2024): siteAuthority, NavBoost
# (goodClicks, badClicks, lastLongestClicks), señales de frescura.
# Pesos [ESTIMADO].
# --------------------------------------------------------------------------
GOOGLE_VIDA_MEDIA_HORAS = 12.0
PESOS_GOOGLE = {"relevancia": 0.30, "autoridad": 0.25, "prominencia": 0.15,
                "originalidad": 0.15, "navboost": 0.15}


def ranking_google_news(n: Noticia) -> Resultado:
    frescura = 0.5 ** (n.horas / GOOGLE_VIDA_MEDIA_HORAS)
    total_clicks = n.clicks_buenos + n.clicks_malos
    navboost = n.clicks_buenos / total_clicks if total_clicks else 0.5
    senales = {"relevancia": n.relevancia_tema, "autoridad": n.autoridad_fuente,
               "prominencia": n.prominencia, "originalidad": n.originalidad,
               "navboost": navboost}
    desglose = {k: PESOS_GOOGLE[k] * v for k, v in senales.items()}
    calidad = sum(desglose.values())
    mult = frescura * (1.2 if n.ubicacion_coincide else 1.0)
    mult *= 1 - 0.6 * n.clickbait
    if n.desmentida:
        mult *= 0.1
    desglose["frescura"] = frescura
    desglose["multiplicador"] = mult
    return Resultado("Google News", calidad * mult, desglose)


# --------------------------------------------------------------------------
# Reddit "hot"  [CÓDIGO] reddit/r2/lib/db/_sorts.pyx (código abierto)
# --------------------------------------------------------------------------
REDDIT_EPOCA = 1134028003  # 8 dic 2005


def ranking_reddit(n: Noticia, ahora_epoch: float = 1_790_000_000) -> Resultado:
    s = n.votos_arriba - n.votos_abajo
    orden = math.log10(max(abs(s), 1))
    signo = 1 if s > 0 else -1 if s < 0 else 0
    segundos = ahora_epoch - n.horas * 3600 - REDDIT_EPOCA
    score = round(signo * orden + segundos / 45000, 7)
    # 45000 s = 12.5 h: un post 12.5 h más nuevo equivale a 10× más votos.
    return Resultado("Reddit", score, {"orden": orden, "signo": signo,
                                       "tiempo": segundos / 45000})


# --------------------------------------------------------------------------
# Hacker News  [CÓDIGO público, Paul Graham / Arc]
#   score = (votos - 1) / (horas + 2) ^ 1.8   × penalizaciones
# --------------------------------------------------------------------------
def ranking_hackernews(n: Noticia, gravedad: float = 1.8) -> Resultado:
    votos = n.votos_arriba
    pen = 1.0
    if n.clickbait > 0.5:
        pen *= 0.4          # penalización manual/automática a títulos cebo
    score = (max(votos - 1, 0) / (n.horas + 2) ** gravedad) * pen
    return Resultado("Hacker News", score, {"votos": votos, "penalizacion": pen})


PLATAFORMAS = {
    "X": ranking_x,
    "Meta": ranking_meta,
    "TikTok": ranking_tiktok,
    "YouTube": ranking_youtube,
    "Google News": ranking_google_news,
    "Reddit": ranking_reddit,
    "Hacker News": ranking_hackernews,
}


def rankear(noticias: list[Noticia], plataforma: str) -> list[tuple[Noticia, Resultado]]:
    fn = PLATAFORMAS[plataforma]
    pares = [(n, fn(n)) for n in noticias]
    return sorted(pares, key=lambda p: p[1].puntuacion, reverse=True)
