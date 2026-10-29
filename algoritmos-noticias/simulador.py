"""Muestra cómo ordena cada plataforma el mismo conjunto de noticias.

Uso:
    python3 simulador.py                    # todas las plataformas
    python3 simulador.py X --detalle        # una plataforma con desglose
    python3 simulador.py --archivo mis.json # tus propias publicaciones
"""

import argparse
import json
from pathlib import Path

from algoritmos import PLATAFORMAS, Noticia, rankear


def cargar(ruta: Path) -> list[Noticia]:
    return [Noticia(**d) for d in json.loads(ruta.read_text(encoding="utf-8"))]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plataforma", nargs="?", choices=list(PLATAFORMAS))
    ap.add_argument("--archivo", type=Path,
                    default=Path(__file__).with_name("noticias_ejemplo.json"))
    ap.add_argument("--detalle", action="store_true", help="muestra el desglose")
    args = ap.parse_args()

    noticias = cargar(args.archivo)
    for nombre in [args.plataforma] if args.plataforma else PLATAFORMAS:
        print(f"\n=== {nombre} ===")
        for i, (n, r) in enumerate(rankear(noticias, nombre), 1):
            print(f"{i}. {r.puntuacion:12.4f}  {n.titulo[:70]}")
            if args.detalle:
                for k, v in r.desglose.items():
                    print(f"      {k:16} {v:.4f}" if isinstance(v, (int, float)) else f"      {k}: {v}")


if __name__ == "__main__":
    main()
