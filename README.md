# GameCenter

Launcher de juegos **local-first** para Windows y Linux: reúne tu biblioteca,
la muestra como una estantería y lanza los juegos con un doble clic.

> Estado: **v0.1 (MVP)** — solo Steam, solo local. Sin red, sin cuentas, sin telemetría.

## Qué hace hoy

- Detecta Steam y todas sus bibliotecas (`libraryfolders.vdf`).
- Lee los manifiestos instalados (`appmanifest_*.acf`).
- Lista los juegos con portada generada en tiempo de ejecución (sin imágenes externas).
- Busca por título y filtra por tienda.
- Lanza el juego con `steam://rungameid/<appid>`.
- Abre la carpeta de instalación y copia el App ID desde el menú contextual.

## Requisitos

- Python 3.10+
- PySide6 6.6+

## Ejecutar

```bash
pip install -e .
python -m gamecenter
```

Solo escanear (sin abrir la interfaz):

```bash
python -m gamecenter --scan
python -m gamecenter --scan --json
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Estructura

```
gamecenter/
  cli.py              entrada: GUI o --scan
  core/
    models.py         modelo Game
    vdf.py            lector de VDF (formato de Valve)
    steam.py          detección de Steam y manifiestos
    launch.py         lanzar juegos y abrir carpetas
  ui/
    covers.py         portadas generadas de forma determinista
    theme.py          hoja de estilos
    main_window.py    ventana principal
tests/                pruebas del parser y del escáner
docs/CLEANROOM.md     política de reimplementación limpia
```

## Hoja de ruta

| Versión | Contenido |
|---|---|
| 0.1 | Steam local, búsqueda, filtros, lanzar |
| 0.2 | Heroic, Lutris, Epic, Flatpak, GOG |
| 0.3 | Tiempo jugado, ordenar, favoritos |
| 0.4 | Carátulas opcionales desde SteamGridDB (con consentimiento) |
| 0.5 | Vista tipo cartucho, dock de sesiones |
| 0.6 | Empaquetado (PyInstaller/Inno Setup) y actualizaciones firmadas |

## Privacidad

La v0.1 **no hace ninguna petición de red**. Todo se lee de archivos locales de
Steam y se dibuja en pantalla. Cuando se añadan tiendas o carátulas online, cada
función de red será explícita, documentada y desactivable.

## Licencia

MIT. Eres libre de usarlo, modificarlo y distribuirlo.

### Nota de reimplementación limpia

Este proyecto se escribió desde cero. No contiene código, iconos, fuentes,
texturas ni sonidos copiados de otros launchers. Solo se usaron formatos de
archivo públicos (VDF, ACF) y el comportamiento observable de un lanzador.
Ver [docs/CLEANROOM.md](docs/CLEANROOM.md).
