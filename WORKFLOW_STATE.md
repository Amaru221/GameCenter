# WORKFLOW STATE — Big Picture con mando

## Descripción funcional

- Modo **Big Picture** a pantalla completa dentro de la ventana, con estética de
  sofá: portada grande, información del juego, carrusel horizontal, filtros y
  barra de pistas de mando.
- Entrada desde el menú superior, `Ctrl+B` o el botón **Start** del mando.
- Totalmente manejable con mando Xbox/XInput:
  - D-pad/stick izquierdo: seleccionar juego.
  - A: jugar.
  - B: abrir confirmación de salida / cancelar.
  - LB/RB: filtro All / Recent / Favorites.
  - X: favorito.
  - Start: menú de salida.
- Teclado: flechas, Enter, Escape, `[`/`]`, `F`. Ratón: tarjetas, filtros,
  Play, favorito, flechas del carrusel, botón Exit y confirmación.
- La salida siempre pide confirmación; nunca se sale por accidente.

## Decisiones de arquitectura

- `gamecenter/core/gamepad.py`: `GamepadManager(QObject)` basado en XInput
  (`xinput1_4/1_3/9_1_0.dll`), sin dependencias nuevas.
  - Sondeo a 30 Hz, detección de conexión, flancos de botones y repetición de
    navegación (350 ms inicial, 130 ms).
  - Señales semánticas: `navigate`, `accept`, `back`, `menu`, `pageLeft`,
    `pageRight`, `favorite`, `connectedChanged`.
  - `GC_NO_GAMEPAD=1` lo desactiva (tests/entornos sin XInput).
- `LibraryModel`:
  - `bigPictureGames` (`QVariantList`, notify `changed`) con todos los juegos.
  - `launchById(gameId)` y `toggleFavoriteById(gameId)`.
  - `changed` se emite al cambiar favoritos/playtime para refrescar la lista.
- `BigPicture.qml`: overlay z=60, foco de teclado propio, carrusel con foco,
  filtros, barra de pistas y diálogo de salida.
- `Gamepad` se expone como contexto QML desde `create_engine`.

## Contrato interno

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Gamepad.connected` | bool | Mando XInput activo. |
| `Gamepad.navigate(dx, dy)` | signal | Movimiento. |
| `Gamepad.accept/back/menu` | signals | A/B/Start. |
| `Gamepad.pageLeft/pageRight` | signals | LB/RB. |
| `Gamepad.favorite` | signal | X. |
| `Library.bigPictureGames` | `QVariantList` | Juegos con carátula, fuente, favorito, etc. |
| `Library.launchById(gameId)` | slot → `str` | Lanza y devuelve id de sesión. |
| `Library.toggleFavoriteById(gameId)` | slot → `bool` | Alterna favorito. |
| `BigPicture.opened` | bool | Visible. |
| `BigPicture.closeRequested` | signal | Salida confirmada. |

## Checklist

### Backend
- [x] `gamepad.py` XInput con conexión, flancos y repetición.
- [x] `Gamepad` expuesto al contexto QML y desactivable.
- [x] `Library.bigPictureGames`, `launchById`, `toggleFavoriteById`.
- [x] `changed` al alternar favorito/terminar sesión.
- [x] Tests de mapeo de ejes/botones.

### Frontend
- [x] `BigPicture.qml` con portada, información, Play y favorito.
- [x] Carrusel con foco, flechas de ratón, filtros y contador.
- [x] Mando, teclado y ratón.
- [x] Confirmación de salida con A/B/flechas/ratón.
- [x] Barra de pistas y estado de conexión.
- [x] Entrada desde menú, `Ctrl+B` y Start.
- [x] Integración en `Main.qml` sin romper modales existentes.

### Verificación
- [x] `python -m pytest -q` → **122 passed**.
- [x] Capturas 1180×800, 900×620 y confirmación de salida.
- [x] Prueba QML de apertura, navegación y confirmación de salida.
- [x] README/CHANGELOG actualizados.

## Notas

- El soporte de mando nativo es **XInput (Windows)**; en Linux o sin mando la
  interfaz queda disponible con teclado y ratón, y la barra de pistas cambia.
- El modo Big Picture se dibuja dentro de la ventana actual, no fuerza
  fullscreen del sistema.
