# WORKFLOW STATE — Cartucho en ejecución dentro de la ranura

## Descripción funcional

- Mientras un juego está en ejecución, su cartucho queda **visible sobresaliendo
  de la ranura de inserción** del dock. No desaparece al terminar la animación.
- Si hay **varios juegos ejecutándose**, la ranura muestra el **último lanzado**
  (el último elemento de `Sessions.list`).
- Al **lanzar otro juego mientras hay uno en la ranura**, el cartucho anterior
  permanece visible durante la animación de aproximación; cuando el nuevo
  cartucho se asienta en la ranura, lo reemplaza.
- Cuando un juego termina o se expulsa, la ranura pasa al siguiente juego en
  ejecución más reciente; si no queda ninguno, el cartucho se oculta con un
  fundido.

## Decisión de arquitectura

- La ranura se dibuja con un nuevo `SlotCartridge.qml`, situado en `Main.qml`
  entre el `InsertEffect` (z=15) y el `Dock` (z=20). Su parte inferior queda
  tapada por el dock, de modo que solo sobresale la parte superior.
- `Library` expone:
  - `launch(row)` ahora devuelve el **id de sesión** (`""` si falla).
  - `sessionCard(gameId)` devuelve los datos completos de la tarjeta
    (título, tienda, meta, carátula, color) para una sesión en ejecución.
- `InsertEffect` conserva su animación y emite `inserted(sessionId)` justo
  cuando el cartucho se asienta; en ese momento `Main` actualiza la ranura.
- `Main` centraliza la elección de la sesión visible:
  - `commitSlot(id)` prioriza la sesión indicada y cae al último juego en
    ejecución si esa sesión ya terminó.
  - `refreshSlot()` se ejecuta cuando cambia `Sessions` o el idioma y mantiene
    la tarjeta actual si la animación está en curso.
- Se amplía el margen inferior de `LibraryGrid` para que el cartucho sobresalga
  sin tapar la última fila de juegos.

## Contrato interno

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Library.launch(row)` | slot → `str` | Inicia el juego y devuelve el id de sesión. |
| `Library.sessionCard(gameId)` | slot → `QVariantMap` | Datos de cartucho para una sesión. |
| `InsertEffect.inserted(sessionId)` | signal | El cartucho acaba de asentarse en la ranura. |
| `Main.slotGame` | `var` | Datos del cartucho que se muestra en la ranura. |
| `Main.commitSlot(id)` | function | Fija la sesión visible al terminar la inserción. |
| `Main.refreshSlot(force)` | function | Recalcula la sesión visible. |
| `SlotCartridge.game` | `var` | Datos del cartucho a dibujar. |

## Checklist

### Backend
- [x] `LibraryModel.launch` devuelve el id de sesión.
- [x] `LibraryModel.sessionCard` devuelve los datos de la tarjeta.
- [x] Tests del id de sesión y de `sessionCard`.

### Frontend
- [x] Nuevo `SlotCartridge.qml` con cartucho escalado y fundido.
- [x] `Main.qml`: propiedades/funciones de ranura, conexión con `Sessions`,
      `InsertEffect.inserted` y ajuste del margen inferior.
- [x] `InsertEffect.qml`: guarda `sessionId`, bloquea la actualización durante
      la animación y emite `inserted` al asentarse.
- [x] La ranura refleja el último juego, el anterior al expulsar y se oculta al
      no quedar sesiones.

### Verificación
- [x] `python -m pytest -q`.
- [x] Captura con `GC_DEMO=1 GC_SESSION=1` para revisar el cartucho sobresalido.
- [x] Prueba manual: lanzar dos juegos y comprobar que el segundo reemplaza al
      primero al finalizar su animación.

## Resultado

- `python -m pytest -q` → **95 passed**.
- Prueba de integración de la animación (QML + sesiones): durante el vuelo la
  ranura conserva `Alpha Quest`; al asentarse pasa a `Beta Racer` y la sesión
  anterior sigue viva en el dock.
- Captura de `GC_DEMO=1 GC_SESSION=1`: el cartucho sobresale 44 px de la ranura,
  centrado, sin tapar la última fila de la biblioteca.

## Notas

- El carrito de la ranura se dibuja en un contenedor recortado (`SlotCartridge`)
  para que la parte inferior quede oculta en el dock y no asome por debajo.
- `InsertEffect` mantiene la guarda `running` mientras lanza la sesión, de modo
  que el cartucho anterior no desaparece antes de que el nuevo se asiente.
