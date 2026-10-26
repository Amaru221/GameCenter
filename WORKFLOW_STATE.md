# WORKFLOW STATE — Resumen de juego, timeline y favoritos

## Descripción funcional

- El detalle del juego muestra primero un **resumen** con los datos actuales
  (título, tienda, tamaño, instalación, tiempo total, última partida) más una
  **descripción**, géneros, estudio y año.
- El panel es **responsive**: dos columnas con cartucho grande en ventanas
  anchas y una vista compacta con miniatura en ventanas estrechas; el contenido
  se desplaza cuando la altura es reducida.
- Debajo del resumen aparece un **timeline de sesiones** con fecha/hora y
  duración, una tira de actividad y el tiempo total.
- La **estrella de favoritos** se rediseña con brillo, rebote, destello y un
  aviso al añadir el juego.

## Decisiones de arquitectura

- `gamecenter/core/metadata.py` obtiene descripciones de la API pública de
  Steam Store:
  - Steam con AppID numérico → `appdetails`.
  - Otras tiendas → `storesearch` por título con umbral de similitud 0.94.
  - Caché por juego/idioma en `%APPDATA%/GameCenter/metadata.json`; TTL de 30
    días (24 h para “sin resultados”).
  - `GC_NO_METADATA=1` desactiva las peticiones.
- `playtime.py` añade un historial global `history.json` por juego con sesiones
  `{start, seconds}` (máximo 200). Las sesiones de Steam también se registran
  aquí, sin escribir en su `localconfig.vdf`.
- `LibraryModel`:
  - `loadDetails(row)` carga la descripción desde caché o en segundo plano.
  - `gameAt(row)` añade `description`, `developers`, `genres`, `releaseDate`,
    `detailsLoaded`, `history`, `sessionCount` y `historyTotalText`.
  - `_session_ended` registra el timeline para todas las tiendas.
- El detalle se dibuja con un `Flickable` y `panel.compact` para adaptar el
  layout. El dock baja de capa mientras el detalle está abierto y recupera su
  capa al cerrarlo, manteniendo la animación de inserción por encima del modal.
- `FavoriteButton.qml` encapsula la estrella animada y el efecto de destello.

## Contrato interno

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Library.loadDetails(row)` | slot | Carga la descripción (caché o red). |
| `Library.gameAt(row)` | slot → `QVariantMap` | Incluye resumen, descripción e historial. |
| `Library.detailsChanged` | signal | La descripción está lista. |
| `metadata.cached(game, lang)` | función | Metadatos frescos o `None`. |
| `metadata.fetch(game, lang)` | función | Descarga y cachea. |
| `playtime.record_session(game, start, seconds)` | función | Añade una sesión al timeline. |
| `playtime.history_for(game)` | función | Sesiones más recientes primero. |
| `FavoriteButton.activate()` | función | Dispara el rebote y el destello. |

## Checklist

### Backend
- [x] `metadata.py` con búsqueda, limpieza HTML, caché y tests.
- [x] `playtime.py` con historial global y tests.
- [x] `LibraryModel.loadDetails` + `detailsChanged`.
- [x] `gameAt` con descripción e historial.
- [x] Timeline registrado también para Steam.
- [x] i18n para textos nuevos, duraciones y avisos de favoritos.

### Frontend
- [x] `GameDetail.qml` rediseñado, responsive y con scroll.
- [x] Timeline con fechas, duraciones, barras y estado vacío.
- [x] `FavoriteButton.qml` con brillo, rebote y destello.
- [x] Descripción con estados de carga/no disponible y “Leer más”.
- [x] Capas del dock/detalle corregidas.

### Verificación
- [x] `python -m pytest -q` → **108 passed**.
- [x] Capturas en 1180×800 y 900×620 con descripción e historial de prueba.
- [x] Estrella animada verificada con `activate()` (destello en movimiento).
- [x] Carga QML de la ventana completa.

## Notas

- Las sesiones anteriores a esta versión no tienen fecha y no se inventan: el
  timeline empieza a llenarse con las sesiones nuevas. El tiempo total anterior
  sigue apareciendo en “All time”.
- Las descripciones de tiendas sin coincidencia exacta en Steam muestran “No
  hay descripción disponible” y se reintentan tras 24 h.
