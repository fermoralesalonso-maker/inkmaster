import unittest

from algoritmos import (Noticia, diversidad_autores_x, ranking_google_news,
                        ranking_hackernews, ranking_meta, ranking_reddit,
                        ranking_tiktok, ranking_x, ranking_youtube)


class PruebasX(unittest.TestCase):
    def test_respuesta_vale_27_likes(self):
        likes = ranking_x(Noticia("a", p_like=0.27)).puntuacion
        resp = ranking_x(Noticia("b", p_respuesta=0.01)).puntuacion
        self.assertAlmostEqual(likes, resp)

    def test_un_reporte_borra_mucho_engagement(self):
        n = Noticia("c", p_like=0.5, p_repost=0.1, p_reporte=0.002)
        self.assertLess(ranking_x(n).puntuacion, ranking_x(Noticia("d", p_like=0.5, p_repost=0.1)).puntuacion / 2)

    def test_diversidad_autores(self):
        self.assertEqual(diversidad_autores_x([10, 10, 10, 10]), [10, 5, 2.5, 2.5])


class PruebasOtras(unittest.TestCase):
    def test_meta_castiga_desmentidas(self):
        base = dict(p_like=0.1, p_respuesta=0.05)
        self.assertLess(ranking_meta(Noticia("x", desmentida=True, **base)).puntuacion,
                        ranking_meta(Noticia("y", **base)).puntuacion * 0.25)

    def test_tiktok_premia_retencion(self):
        corto = Noticia("v", es_video=True, duracion_seg=30, vista_esperada_seg=30, p_like=0.1)
        largo = Noticia("w", es_video=True, duracion_seg=120, vista_esperada_seg=30, p_like=0.1)
        self.assertGreater(ranking_tiktok(corto).puntuacion, ranking_tiktok(largo).puntuacion)

    def test_youtube_autoridad(self):
        kw = dict(p_click=0.2, vista_esperada_seg=100)
        self.assertGreater(ranking_youtube(Noticia("a", autoridad_fuente=0.9, **kw)).puntuacion,
                           ranking_youtube(Noticia("b", autoridad_fuente=0.1, **kw)).puntuacion)

    def test_google_frescura_vida_media(self):
        a = ranking_google_news(Noticia("a", horas=0)).desglose["frescura"]
        b = ranking_google_news(Noticia("b", horas=12)).desglose["frescura"]
        self.assertAlmostEqual(b, a / 2)

    def test_reddit_10x_votos_igual_a_12_5_horas(self):
        viejo = ranking_reddit(Noticia("a", horas=12.5, votos_arriba=1000)).puntuacion
        nuevo = ranking_reddit(Noticia("b", horas=0, votos_arriba=100)).puntuacion
        self.assertAlmostEqual(viejo, nuevo, places=5)

    def test_hn_decae_con_el_tiempo(self):
        self.assertGreater(ranking_hackernews(Noticia("a", horas=1, votos_arriba=50)).puntuacion,
                           ranking_hackernews(Noticia("b", horas=10, votos_arriba=50)).puntuacion)


if __name__ == "__main__":
    unittest.main()
