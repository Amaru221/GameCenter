# GameCenter

Launcher de juegos **local-first** para Windows y Linux: reúne tu biblioteca,
la muestra como una estantería y lanza los juegos con un doble clic.

> Estado: **v0.1 (MVP)** — solo Steam. Sin cuentas, sin telemetría.

![Vista de GameCenter](docs/preview.png)

## Qué hace hoy

- Detecta Steam y todas sus bibliotecas (`libraryfolders.vdf`).
- Lee los manifiestos instalados (`appmanifest_*.acf`).
- Lista los juegos como cartuchos con inclinación 3D al pasar el ratón.
- Usa la carátula oficial de Steam (CDN público) y la cachea; sin conexión dibuja
  una portada generada.
- Busca por título y filtra por tienda; ordena por reciente, título o tamaño.
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
  cli.py                entrada: GUI o --scan
  core/
    models.py           modelo Game
    vdf.py              lector de VDF (formato de Valve)
    steam.py            detección de Steam y manifiestos
    launch.py           lanzar juegos y abrir carpetas
  ui/
    app.py              arranque de Qt Quick y proveedores de imágenes
    library_model.py    modelo, filtros, orden y acciones
    artwork.py          carátulas del CDN de Steam con caché
    covers.py           portadas, fondo y logo generados con QPainter
    qml/                Main, TopBar, Toolbar, Cartridge, LibraryGrid, Dock
    fonts/              Sora y Chakra Petch (SIL OFL 1.1)
tools/screenshot.py     render de la ventana a PNG (desarrollo)
tests/                  parser, escáner, modelo y carga del QML
docs/CLEANROOM.md       política de reimplementación limpia
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

La única petición de red es la de carátulas: se envía el **AppID** de cada juego
instalado al CDN público de Steam
(`shared.akamai.steamstatic.com`) y la imagen se guarda en
`~/.cache/gamecenter/art`. No se envían cuentas, rutas ni datos del equipo.

Para que la app sea 100 % offline:

```bash
GC_NO_ART=1 python -m gamecenter
```

En ese caso se usan las portadas generadas localmente. Las carátulas son obra de
sus editores y se muestran solo para identificar el juego; no se redistribuyen.

## Interfaz

Qt Quick (QML) sobre PySide6. La ventana se compone de:

- **Cartuchos 3D**: plástico con bisel, muesca, etiqueta interior y agarre
  inferior. Al pasar el ratón se inclinan (`Rotation` en dos ejes), la etiqueta
  se mueve con paralaje y el brillo responde a la inclinación.
- **Fondo mesh**: degradado radial multicolor generado con QPainter, viñeta y
  grano, sin imágenes ni shaders.
- **Cristal**: barra superior y dock con degradados translúcidos y bordes.

## Licencia

MIT para el código. Las fuentes incluidas son SIL OFL 1.1 y Qt/PySide6 es
LGPL-3.0; ver `THIRD_PARTY_NOTICES.md`.

### Nota de reimplementación limpia

Este proyecto se escribió desde cero. No contiene código, iconos, fuentes,
texturas ni sonidos copiados de otros launchers. Solo se usaron formatos de
archivo públicos (VDF, ACF) y el comportamiento observable de un lanzador.
Ver [docs/CLEANROOM.md](docs/CLEANROOM.md).
