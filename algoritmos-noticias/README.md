# Ingeniería inversa de los algoritmos de noticias en redes sociales

Este estudio reconstruye cómo X, Meta, TikTok, YouTube, Google News, Reddit y Hacker News deciden qué noticia ves primero. Lo acompaña un simulador en Python que aplica esas fórmulas a un mismo conjunto de notas para ver por qué cada red las ordena distinto.

> **Qué tan confiable es cada dato.** Cada número del código (`algoritmos.py`) lleva una etiqueta:
> **[CÓDIGO]** = la empresa lo publicó · **[FILTRADO]** = documento interno reportado por prensa · **[OFICIAL]** = la empresa lo describe sin números · **[ESTIMADO]** = inferido; calíbralo con tus datos.
> Ninguna de estas empresas publica su sistema actual completo. Esto es un modelo aproximado, no una copia.

---

## 1. La arquitectura que todas comparten

Todas las redes grandes usan el mismo embudo de cuatro etapas:

```
Millones de publicaciones
   │ 1. Generación de candidatos  (de quién sigues, temas parecidos, lo viral)
   ▼ ~1,500
   │ 2. Ranking ligero             (modelo rápido descarta lo obvio)
   ▼ ~500
   │ 3. Ranking pesado             (red neuronal predice P(like), P(respuesta)…)
   ▼     puntuación = Σ peso_i × P(acción_i)
   │ 4. Filtros y reglas           (diversidad, integridad, anuncios, desmentidos)
   ▼
Tu feed
```

La idea clave: **el algoritmo no "lee" la noticia y decide si es buena**. Predice qué vas a hacer con ella (like, comentar, ver completa, ocultar, reportar) y multiplica cada predicción por un peso que la empresa elige según su negocio. Cambiar esos pesos cambia qué tipo de contenido gana.

---

## 2. Plataforma por plataforma

### X / Twitter: la mejor documentada

En marzo de 2023 X publicó su código (`twitter/the-algorithm` y `the-algorithm-ml`). El modelo pesado suma estas predicciones **[CÓDIGO]**:

| Acción predicha | Peso | Equivale a… |
|---|---:|---|
| El autor responde a tu respuesta | **+75.0** | 150 likes |
| Respuesta | **+13.5** | 27 likes |
| Click al perfil y luego interactúa | +12.0 | 24 likes |
| Abrir la conversación y quedarse | +11.0 | 22 likes |
| Repost | +1.0 | 2 likes |
| Like | +0.5 | 1 like |
| Ver 50 % de un video | +0.005 | casi nada |
| "Mostrar menos", silenciar, bloquear | **−74.0** | −148 likes |
| Reporte | **−369.0** | −738 likes |

Reglas adicionales encontradas en el código de 2023:
- **Diversidad de autores**: el segundo post del mismo autor vale 50 %, el tercero 25 % (piso 25 %).
- **Fuera de tu red** (cuentas que no sigues): multiplicador ~0.75.
- **Cuenta verificada de pago**: ×4 dentro de tu red, ×2 fuera.
- **Enlaces externos**: Musk confirmó en 2023–24 que se castigan, sin número publicado **[ESTIMADO ×0.5]**.

**Conclusión:** en X, una noticia que genera conversación (y donde el autor contesta) vale decenas de veces más que una que solo recibe likes. Una sola fracción de usuarios reportándola la hunde.

### Meta (Facebook e Instagram)

- **[FILTRADO]** Los *Facebook Files* (Wall Street Journal, 2021) revelaron el sistema de puntos de 2018, llamado *Meaningful Social Interactions*: like = 1 punto, reacción o compartir sin texto = 5, comentario significativo o compartir con texto = 30. En 2020 la reacción "me enoja" se bajó a 0 porque premiaba contenido tóxico.
- **[OFICIAL]** El *Transparency Center* de Meta confirma: suma ponderada de predicciones × degradaciones por integridad (clickbait, baja calidad, contenido desmentido por verificadores).
- **[OFICIAL]** Desde 2018 prioriza amigos y grupos sobre páginas, y desde 2023 reduce deliberadamente las noticias y la política en el feed.

**Conclusión:** en Meta los comentarios largos y la cercanía con quien publica pesan más que el alcance de la fuente. Una nota desmentida pierde la mayor parte de su distribución.

### TikTok

- **[FILTRADO]** Documento interno "TikTok Algo 101" (New York Times, 2021):
  `Plike × Vlike + Pcomment × Vcomment + Eplaytime × Vplaytime + Pplay × Vplay`
- Los valores V no se publicaron. Pruebas externas coinciden en que **la retención** (porcentaje visto, repeticiones) es la señal dominante, por encima de los seguidores.
- Cada video nuevo se prueba con un grupo pequeño y, si retiene, se amplía por oleadas.

**Conclusión:** en TikTok una noticia compite como entretenimiento: un video corto que se ve completo le gana a uno largo con mejor información.

### YouTube

- **[PAPER]** Covington et al., 2016: el ranking optimiza el **tiempo de visualización esperado**, no los clicks.
- **[PAPER]** Zhao et al., 2019: modelo multiobjetivo que combina interacción con **satisfacción** (encuestas "¿te gustó este video?").
- **[OFICIAL]** En temas de noticias, YouTube **eleva fuentes autorizadas** (estantes de "Últimas noticias") y reduce contenido límite o desmentido.

**Conclusión:** el clickbait se castiga solo porque la gente lo abandona; las fuentes reconocidas tienen ventaja en temas noticiosos.

### Google News y Discover

- **[OFICIAL]** Factores declarados: relevancia, prominencia (cuántos medios cubren la historia), autoridad, frescura y ubicación. Desde 2019 premia el **reportaje original** sobre las copias.
- **[FILTRADO]** La documentación interna filtrada en mayo de 2024 (*Content Warehouse API*) mostró atributos como `siteAuthority` y el sistema **NavBoost**, que usa clicks: `goodClicks`, `badClicks` (regresar rápido a los resultados) y `lastLongestClicks`.

**Conclusión:** Google es la red que más pesa la calidad de la fuente y la originalidad. La frescura decae en horas (el simulador usa vida media de 12 h **[ESTIMADO]**).

### Reddit y Hacker News: las fórmulas exactas

Ambas son públicas **[CÓDIGO]**:

```
Reddit hot = signo(votos) × log10(|votos netos|) + (segundos desde 8-dic-2005) / 45000
HN         = (votos − 1) / (horas + 2)^1.8   × penalizaciones
```

En Reddit, **los primeros 10 votos valen lo mismo que los siguientes 90**, y una publicación 12.5 horas más nueva equivale a tener 10 veces más votos. Por eso la primera hora decide todo.

---

## 3. Qué muestra el simulador

Mismas seis noticias, siete rankings (`python3 simulador.py`):

| Noticia | X | Meta | TikTok | YouTube | Google | Reddit |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Reportaje original de medio serio | 3 | 3 | — | — | **1** | **1** |
| Clickbait de página viral | 4 | 4 | — | — | 5 | 2 |
| Hilo de debate donde el autor contesta | **1** | **1** | — | — | 2 | 3 |
| Video técnico de 45 s visto completo | 2 | 2 | **1** | **1** | 3 | 4 |
| Bulo desmentido | 5 | 6 | 2 | 2 | 6 | 6 |
| Nota de agencia de ayer | 6 | 5 | — | — | 4 | 5 |

Lecturas:
1. **Las redes sociales premian la conversación; Google premia la fuente.** El mismo reportaje original queda 3.º en X y Meta pero 1.º en Google.
2. **El bulo sigue rindiendo en TikTok y YouTube** a pesar de los castigos, porque tiene alto tiempo de visualización. Las degradaciones lo reducen, no lo eliminan.
3. **La antigüedad mata más que la falta de calidad.** La nota de agencia, con buena autoridad, queda abajo en casi todo por tener 30 horas.

---

## 4. Factores comunes (lo que funciona en todas)

| Factor | Por qué importa |
|---|---|
| **Respuestas y conversación** | Es el mayor peso positivo en X y Meta. |
| **Tiempo de atención** | Base de YouTube y TikTok; NavBoost lo mide en Google. |
| **Primeras horas** | Todas las fórmulas decaen con el tiempo; el empuje inicial decide el alcance. |
| **Señales negativas** | Un "no me interesa" o un reporte pesa más que decenas de likes. |
| **Originalidad y autoridad** | Decisivo en Google y YouTube para noticias. |
| **Contenido nativo** | X y Meta reducen las publicaciones que sacan al usuario de la plataforma. |

## 5. Aplicación práctica (para FEMO o cualquier marca)

1. **Escribe para provocar respuestas, no likes.** Termina con una pregunta concreta a tu sector y **contesta cada comentario en la primera hora**: en X eso vale 150 likes por respuesta contestada.
2. **Publica el contenido dentro de la red.** Pon el texto o video completo en la publicación y el enlace en un comentario o al final.
3. **Video corto que se vea completo.** Mejor 30–45 s visto al 100 % que 3 minutos visto al 20 %.
4. **Contenido propio y verificable** (casos de obra, datos de tus proyectos): es lo que Google y YouTube clasifican como original y con autoridad.
5. **Evita el clickbait.** Gana el click pero pierde en tiempo de visualización, en "no me interesa" y en las degradaciones de integridad.
6. **Cuida el horario.** Publica cuando tu audiencia está activa para que las primeras interacciones lleguen rápido.

## 6. Cómo seguir haciendo ingeniería inversa

Estos sistemas cambian cada mes. Para medir el estado actual:
- **Auditoría con cuentas de prueba**: varias cuentas nuevas con distintos intereses registran qué les muestra el feed (método usado por Mozilla y AlgorithmWatch).
- **Experimentos A/B propios**: publica variantes de la misma noticia (con o sin enlace, con o sin pregunta) y compara el alcance en las estadísticas de la red.
- **Ajustar los pesos**: cambia las constantes **[ESTIMADO]** de `algoritmos.py` hasta que el simulador reproduzca tus resultados reales.
- **Fuentes a vigilar**: repositorios públicos de X, Meta Transparency Center (*system cards*), Google Search Central Blog, el blog de YouTube y los informes de la Ley de Servicios Digitales (DSA) de la Unión Europea, que obliga a las plataformas a explicar sus sistemas de recomendación.

---

## Uso del código

```bash
cd algoritmos-noticias
python3 simulador.py                       # todas las plataformas
python3 simulador.py X --detalle           # desglose de una plataforma
python3 simulador.py --archivo mis.json    # tus propias publicaciones
python3 -m unittest test_algoritmos        # pruebas
```

Solo usa la biblioteca estándar de Python 3.9+. Para probar tus publicaciones, copia `noticias_ejemplo.json` y cambia los valores; los campos están documentados en la clase `Noticia`.

## Fuentes principales

- Twitter/X, `the-algorithm` y `the-algorithm-ml` (GitHub, marzo 2023).
- Wall Street Journal, *The Facebook Files* (septiembre 2021).
- Meta Transparency Center, *Our approach to ranking* y *system cards* de Feed.
- New York Times, "How TikTok Reads Your Mind" (diciembre 2021).
- Covington, Adams y Sargin, *Deep Neural Networks for YouTube Recommendations* (RecSys 2016).
- Zhao et al., *Recommending What Video to Watch Next: A Multitask Ranking System* (RecSys 2019).
- Google, *How Google News stories are selected*; Google Search Central, actualización de reportaje original (2019).
- Filtración de la *Content Warehouse API* de Google, análisis de Rand Fishkin y Mike King (mayo 2024).
- Código fuente de Reddit (`r2/lib/db/_sorts.pyx`) y fórmula de ranking de Hacker News.
