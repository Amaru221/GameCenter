# WORKFLOW STATE - Fluidez de Big Picture, Stats y sonidos de interfaz

## Feature 0.20.2 - Rendimiento, UX y sonidos estilo PS5

### Descripcion funcional

1. **Big Picture mas fluido**
   - Menos delegados vivos en el carrusel (ventana de 9 tarjetas en vez de 13)
     para recortar decodificacion de imagenes, sombras y animaciones fuera de
     pantalla.
   - Animaciones mas cortas y con salida suave (180-220 ms) para que la respuesta
     al mando/teclado se sienta inmediata sin perder el fundido.
   - La ventana de 9 tarjetas mantiene sus posiciones cuando se desplaza por el
     centro de una biblioteca larga; un deslizamiento direccional de 190 ms
     acompania el cambio para que no parezca un intercambio de caratulas.
   - Las caratulas se decodifican a un tamano maximo (`sourceSize`) y el fondo a
     baja resolucion; hero, fondo y tarjeta comparten cache para que el cambio de
     juego no vuelva a leer el archivo.
   - Solo la tarjeta enfocada pinta el glow y el brillo decorativo: menos overdraw
     por frame.
   - El fondo del modo Big Picture usa `mipmap` y un tamano de origen acotado.

2. **Estadisticas mas fluidas**
   - El grafico "river" se separa en dos capas: un Canvas estatico con las pilas
     y un Canvas superpuesto que solo dibuja la guia y los puntos del hover. Mover
     el raton ya no repinta todas las curvas.
   - `Library.stats()` y `Library.yearReview()` se memorizan por periodo/ano/mes/
     idioma. El cache se invalida al cambiar el historial, la biblioteca o el
     idioma.
   - `playtime.all_history()` cachea el JSON por ruta y `mtime`, evitando leer el
     archivo en cada refresco.
   - Las URLs de caratula se cachean por juego y se invalidan al llegar arte nuevo;
     construir el mapa de caratulas de Stats deja de hacer `stat()` por juego.
   - El refresco de Stats se difiere un frame (`Qt.callLater`) para que el cambio
     de vista pinte antes de recalcular.

3. **Sonidos de interfaz estilo PS5 (unicos, sintetizados)**
   - Navegar entre juegos: tick moderno, redondo y con cuerpo grave (sin armonicos
     brillantes de 8 bits).
   - Abrir/cerrar el modal de detalle: swell ascendente / descenso aireado.
   - Cambiar de pestana/filtro/modo o periodo de Stats: blip de dos tonos.
   - Iniciar un juego: swell grave con quinta y shimmer.
   - Entrar en Big Picture: arranque calido tipo consola (acorde ascendente,
     sub, shimmer y aire).
   - Favorito: click sutil.
   - Los WAV se generan una vez en la cache local (`QStandardPaths.CacheLocation`)
     y se reproducen con `QSoundEffect` (baja latencia). No se anaden binarios al
     repositorio.
   - Ajuste "Efectos de sonido" en Settings para silenciarlos. Se recuerda en
     `settings.json`.

### Decisiones de arquitectura

- `gamecenter/core/sounds.py` encapsula sintesis, cache y reproduccion. Expone
  `Sounds` como context property. Si no hay dispositivo de audio, Qt esta en
  offscreen o `GC_NO_SOUND=1`, el manager queda inactivo y todos los slots son
  no-op (tests y CI seguros).
- El pool de efectos es de 3 voces por sonido para que la navegacion rapida no
  corte el cue anterior.
- La preferencia vive en `Preferences.sound_enabled` y `SoundManager` la expone a
  QML con `enabled` / `setEnabled`.
- `LibraryModel` mantiene caches de Stats y de URLs de caratula; se invalidan con
  las senales existentes (`changed`, `playtimeChanged`, `languageChanged`).
- `playtime.all_history()` usa una cache module-level con `(ruta, mtime_ns)` como
  clave; las escrituras existentes ya cambian el mtime.
- En `BigPictureCarousel` la ventana se reduce a radio 4. La posicion sigue
  calculandose por offset, pero `windowStart` es mutable: antes de cada paso se
  recentra de forma invisible sobre la tarjeta que esta en pantalla (mismos
  juegos en las mismas posiciones) y despues se anima un unico slot real. Asi
  las caratulas conservan su identidad y no se intercambia el contenido.
- Un salto lejano (seleccion programatica o reset de filtro) recoloca la ventana
  en el destino y muestra el resultado sin animacion; los pasos normales de
  mando/teclado siempre transicionan.
- El Canvas del river se divide en `riverChart` (estatico) y `riverHover` (solo
  hover). `chartCard.hoverIndex` sigue siendo la unica fuente de verdad.

### Contrato de API

| Elemento | Tipo | Descripcion |
| --- | --- | --- |
| `Sounds.navigate()` | Slot | Tick de navegacion entre juegos. |
| `Sounds.open()` | Slot | Swell al abrir el modal de detalle. |
| `Sounds.close()` | Slot | Descenso al cerrar el modal. |
| `Sounds.tab()` | Slot | Cambio de pestana, filtro, modo o periodo. |
| `Sounds.launch()` | Slot | Inicio de juego. |
| `Sounds.toggle()` | Slot | Favorito / ajuste puntual. |
| `Sounds.startup()` | Slot | Arranque tipo consola al entrar en Big Picture. |
| `Sounds.enabled` | bool (notify enabledChanged) | Silencia o activa los efectos. |
| `Sounds.setEnabled(bool)` | Slot | Persiste la preferencia. |
| `Preferences.sound_enabled` | property bool | Valor guardado en settings.json. |
| `Library.stats(period, year, month)` | Slot | Mismo contrato; ahora cacheado. |
| `Library.yearReview(year)` | Slot | Mismo contrato; ahora cacheado. |
| `playtime.all_history()` | function | Mismo contrato; cache por mtime. |

### Checklist

#### Backend
- [x] `core/sounds.py`: sintesis WAV de 7 cues, cache en disco, pool `QSoundEffect`, fallback sin audio.
- [x] `preferences.py`: `sound_enabled` (default true) con getter/setter persistente.
- [x] `app.py`: instanciar `SoundManager`, exponer `Sounds` y precargar en idle.
- [x] `library_model.py`: cache de `stats()` / `yearReview()` y de URLs de caratula, invalidados por senales.
- [x] `playtime.py`: cache de `all_history()` por ruta + `mtime`.
- [x] `packaging/gamecenter.spec`: incluir `PySide6.QtMultimedia` como hidden import.
- [x] Tests de sonido (WAV valido, manager inactivo en offscreen, preferencia) y de cache de Stats.

#### Frontend
- [x] `BigPicture.qml`: hooks de sonido, `closeDetail()`, imagenes con `sourceSize`/`mipmap`.
- [x] `BigPictureCarousel.qml`: radio 4, animaciones 180-220 ms, menos overdraw, `sourceSize`.
- [x] `BigPictureCarousel.qml`: recentrado invisible + transicion real de un slot; salto lejano instantaneo.
- [x] `Main.qml`: sonido en el cambio de vista Biblioteca/Stats/Tienda y arranque al entrar en Big Picture.
- [x] `StatsView.qml`: Canvas de hover separado, refresco diferido, sonidos de pestana/periodo/ano, `sourceSize` en caratulas.
- [x] `SettingsPanel.qml`: toggle "Efectos de sonido" enlazado a `Sounds.enabled`.
- [x] `i18n.py`: traducciones ES/FR/DE/IT/PT de las etiquetas nuevas.
- [x] README/CHANGELOG actualizados.

### Verificacion

- [x] `python -m pytest -q` -> **199 passed**.
- [x] Comprobar navegacion, apertura/cierre de modal, filtros/modos y lanzamiento con sonido.
- [x] Comprobar hover del grafico de Stats sin tirones y cambio de periodo instantaneo.
- [x] Comprobar que Big Picture sigue montandose solo al abrirse.
- [x] Prueba visual en ventana real (no offscreen).

# WORKFLOW STATE — Atajos personalizados, carátulas locales y pulido de UI

## Feature 0.20.1 — Stats sin header, navbar superior y estadísticas destacadas

### Descripción funcional

1. **Sesiones cortas**: ninguna sesión se descarta por duración. Se guardan
   también las de menos de 5 minutos (y las de menos de 1 s se redondean a 1 s
   en vez de perderse por el truncado a entero). El historial conserva hasta
   5.000 sesiones por juego para que las estadísticas sigan creciendo con el uso.
2. **Estadísticas sin header**: al entrar en Stats desaparece la barra superior
   completa (logo, buscador, píldoras, ajustes y menú). La vista ocupa todo el
   alto de la ventana.
3. **Píldoras y año en la fila superior de Stats**: el selector de periodo
   (Week/Month/Year/All time) queda a la izquierda; a la derecha se alinean las
   píldoras **Biblioteca / Stats / Tienda**, el selector de año (`‹ 2026 ›`) y
   el botón de resumen anual con su tamaño original (340 px). Al volver a
   Biblioteca reaparece el navbar superior de siempre.
   *Tienda* mantiene el aviso de “próximamente”.
4. **Más jugado dentro de Tiempo jugado**: la tarjeta de *Most played* deja de
   estar anclada a la derecha y pasa a vivir junto a las horas, dentro del mismo
   bloque, para no tapar el año gigante del banner.
5. **Etiqueta “Mejor día” → “Tiempo de juego”** en la fila de métricas de cada
   tarjeta (el valor sigue siendo el tiempo del mejor día y debajo su fecha).
6. **Fila de métricas alineada**: días jugados, tiempo de juego y sesiones
   comparten altura de etiqueta, valor y detalle; los tres quedan alineados.
7. **Estadísticas destacadas por tarjeta** (día, semana o mes), calculadas
   siempre desde el historial y actualizadas al refrescar:
   - **Sesión más larga** (`2h 15m`) con fecha (o juego, en tarjetas de día).
   - **Día con más sesiones** (fecha + `N sesiones`) en tarjetas de semana/mes;
     en tarjetas de día se sustituye por **Juegos jugados**.
   - **Media por sesión**.
8. **Estadísticas destacadas del periodo** (fila bajo el banner):
   - **Sesión más larga** (duración + fecha + juego).
   - **Día / mes con más sesiones** (según el periodo: mes en Year/All time,
     día en Week/Month).
   - **Media por sesión**.
   - **Día favorito** (día de la semana con más sesiones).

### Decisiones de arquitectura

- `playtime.record_session()` y `playtime.add_seconds()` aceptan cualquier
  duración positiva; se redondea al segundo más cercano con mínimo 1 s. No hay
  umbral de 5 minutos en ningún punto del flujo (tracker → `_session_ended` →
  historial → resumen → stats).
- `MAX_HISTORY` sube de 200 a 5.000 para no tirar sesiones antiguas cuando el
  usuario acumula historial; el recorte sigue existiendo como guardarraíl.
- `stats.py` gana helpers puros (`_longest_session`, `_busiest_day`,
  `_busiest_month`, `_favorite_weekday`, `_highlights`) reutilizados por el
  resumen del periodo y por `_bucket_payload()`. Todo se recalcula en cada
  `build()`, sin caché, así los datos se actualizan solos.
- `StatsView.qml` coloca las píldoras (`statsViewTabs`) y el `YearPicker` en la
  fila superior, entre `PeriodTabs` y `ReviewBanner`; `Main.qml` oculta `TopBar`
  en Stats y estira `StatsView` hasta los bordes.
- El panel de *Most played* se convierte en una fila dentro del bloque de
  tiempo jugado; conserva `objectName: "topGamePanel"` para no romper los tests
  existentes.
- Las tarjetas renderizan `month.highlights` con un componente `MiniStat`; el
  resumen del periodo renderiza `statsData.highlights` con `HighlightTile`.

### Contrato de API

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `stats.highlights` | `list` | Hasta 4 destacados del periodo: `{label, value, detail, tint}`. |
| `stats.longestSession` | `object` | `{seconds, text, dateText, timestamp, game, gameId}` o `{}`. |
| `stats.busiestDay` | `object` | `{dateText, timestamp, sessions, sessionsText}` o `{}`. |
| `stats.busiestMonth` | `object` | `{monthIndex, name, sessions, sessionsText}` o `{}`. |
| `stats.favoriteWeekday` | `object` | `{name, sessions, sessionsText}` o `{}`. |
| `stats.averageSessionText` | `string` | Duración media por sesión del periodo. |
| `buckets[].longestSessionText` | `string` | Duración de la sesión más larga del bucket. |
| `buckets[].longestSessionDateText` | `string` | Fecha `dd/mm` de esa sesión. |
| `buckets[].longestSessionGame` | `string` | Juego de esa sesión. |
| `buckets[].busiestDayDateText` | `string` | Día con más sesiones dentro del bucket. |
| `buckets[].busiestDaySessionsText` | `string` | `1 session` / `N sessions`. |
| `buckets[].averageSessionText` | `string` | Media por sesión del bucket. |
| `buckets[].gamesCount` | `int` | Juegos distintos jugados en el bucket. |
| `buckets[].highlights` | `list` | 3 destacados listos para pintar. |
| `StatsView.currentView` | `string` | Vista activa (Stats). |
| `StatsView.viewRequested(view)` | `signal` | Biblioteca / Stats / Tienda desde el navbar inferior. |
| `StatsView.highlights` | `list` | Atajo a `statsData.highlights`. |
| `statsViewTabs` | QML | Píldoras Biblioteca/Stats/Tienda de la fila superior. |
| `statsPeriodTabs` | QML | Selector Week/Month/Year/All time. |
| `statsYearPicker` | QML | Selector de año de la fila superior. |

### Checklist

#### Backend
- [x] `playtime.py`: sin mínimo de duración, redondeo a 1 s y `MAX_HISTORY = 5000`.
- [x] `stats.py`: helpers de sesión más larga, día/mes con más sesiones, día favorito y media.
- [x] `stats.py`: `highlights` del periodo y por bucket; campos nuevos en `build()`.
- [x] Traducciones ES/FR/DE/IT/PT de las etiquetas nuevas.
- [x] Tests de sesiones cortas, destacados por bucket y destacados del periodo.

#### Frontend
- [x] `StatsView.qml`: píldoras Biblioteca/Stats/Tienda + año en la fila superior, entre periodo y resumen.
- [x] `Main.qml`: ocultar `TopBar` en Stats, `StatsView` a pantalla completa y puente `viewRequested`.
- [x] `StatsView.qml`: *Most played* dentro del bloque de tiempo jugado y año visible.
- [x] `StatsView.qml`: fila de métricas alineada y etiqueta “Tiempo de juego”.
- [x] `StatsView.qml`: `HighlightTile` del periodo y `MiniStat` en cada tarjeta.
- [x] Tests QML del navbar inferior, `topGamePanel` reubicado y destacados.
- [x] README/CHANGELOG actualizados y verificación visual.

### Verificación

- [x] `python -m pytest -q` → **189 passed**.
- [x] Capturas de Stats (Week/Month/Year) con píldoras y año arriba, año visible y destacados.
- [x] Comprobar que Biblioteca recupera el navbar superior y que una sesión de 90 s aparece en Stats.

## Ajuste fino 0.20.0 — Modal de Big Picture, gatillos y filtros

### Descripción funcional

- **Big Picture**
  - El cambio de modo del carrusel ya **no muestra un toast**: el propio botón
    *Mode* indica el modo activo.
  - Nuevo **botón ☰** en la barra superior con el menú de la app: *Scan all
    stores*, *Restore removed games*, *Add game manually…*, *Settings* y *Exit*.
    *Settings* y *Add game* cierran Big Picture y abren el panel en la ventana
    principal (con su fundido de salida).
  - **Dentro de la ficha**: **X** favorito, **Y** abre/cierra el **perfil**,
    **LB/RB** abren el **visor de capturas** (y navegan por él), **B** cierra
    primero el perfil y después la ficha, **A** sigue jugando.
  - El **perfil** se edita con mando/teclado: **↑↓** alterna *estado* ↔
    *puntuación*, **←→** cambia el valor (estado anterior/siguiente, puntuación
    ±5). La sección activa se resalta en el color de acento y una pista muestra
    las teclas.
  - Las píldoras de filtro se dimensionan por su texto (`implicitWidth` +
    `Layout.preferredWidth`): ya no se solapan ni ignoran el layout.
- **Mando**: los **gatillos analógicos LT/RT** se leen de `bLeftTrigger`/
  `bRightTrigger` (umbral 60/255) y cuentan como botones. La captura **acumula**
  los botones mantenidos, así que una combinación se guarda igual sin importar
  el orden en que se suelten (`LT+RT`, `LB+RT`, `A+X`). Los dos bits libres de
  `wButtons` que usan algunas **paletas traseras** (estilo SCUF) se exponen como
  `P1`/`P2` con nombres estables. La casilla muestra en vivo los botones
  detectados mientras se graba.
- **Paletas con macros** (BSP G6): no llegan como botones porque el mando emite
  teclas. El grabador de teclado expone `lastKeyPress` (última combinación
  recibida, aunque se rechace) para diagnosticarlo, y `F13`–`F24` valen como
  atajo global: la vía recomendada es programar la macro como `Ctrl+F13` en la
  app del mando y grabarla como atajo de teclado.

### Decisiones de arquitectura

- `BigPicture.qml` gana `toggleProfile()` y `screenshotsStep(delta)`; el modal
  (`GameDetail`) ya exponía `profileOpen`, `openViewer`, `nextViewer`,
  `previousViewer` y `closeViewer`.
- El panel de perfil conserva su edición con ratón y añade `moveFocus`,
  `adjust`, `cycleStatus` y `nudgeRating`, usados por `Gamepad.navigate` y por
  las teclas de Big Picture (que mantiene el foco).
- `GamepadManager.buttons_mask()` convierte `wButtons` + gatillos en una máscara
  única; `BUTTON_ORDER` y `GAMEPAD_BUTTONS` incluyen `LT`/`RT`.
- Los tests de UI destruyen ahora los `QQmlApplicationEngine` de forma
  determinista (cerrar raíces + `shiboken6.delete`): dejar que Python los
  recolecte con ventanas vivas bloqueaba la carga del siguiente engine.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `BigPicture.settingsRequested()` | signal | Abrir Ajustes tras cerrar Big Picture. |
| `BigPicture.addRequested()` | signal | Abrir *Add game* tras cerrar Big Picture. |
| `BigPicture.toggleProfile()` | función | Abre/cierra el perfil del juego abierto. |
| `BigPicture.screenshotsStep(delta)` | función | Abre el visor o navega por las capturas. |
| `GameProfilePanel.focusRow` | `int` | 0 = estado, 1 = puntuación. |
| `GameProfilePanel.moveFocus(delta)` | función | Cambia de fila. |
| `GameProfilePanel.adjust(direction)` | función | Modifica el valor de la fila activa. |
| `GameDetail.profileMoveFocus(delta)` | función | Puente hacia el panel. |
| `GameDetail.profileAdjust(direction)` | función | Puente hacia el panel. |
| `gamepad.buttons_mask(pad)` | función | `wButtons` + `LT`/`RT` sintéticos. |
| `gamepad.LEFT_TRIGGER/RIGHT_TRIGGER` | int | Bits sintéticos de los gatillos. |

### Verificación

- [x] `python -m pytest -q` → **179 passed**.
- [x] Capturas: Big Picture con menú abierto, ficha con perfil y barra de pistas;
      biblioteca y filtros sin solapes.
- [x] Leyenda flotante dentro de la ficha (barra inferior, sobre el modal) con
      A/B/X/Y/LB-RB/↑↓/Start.
- [x] `tools/idle_probe.py` → 0 frames en reposo (sin regresiones de consumo).

## Feature 0.20.0 — Atajos personalizados, carátulas del sistema y pulido visual

### Descripción funcional

1. **Atajos de captura personalizados**
   - **Teclado**: en Ajustes → SCREENSHOTS, el botón **Record** pone el atajo en
     modo escucha; las siguientes teclas pulsadas (con sus modificadores) se
     convierten en el atajo. Escape cancela. `Clear` deja el atajo vacío.
   - **Mando**: el botón **Record** del atajo de mando escucha el mando; al
     soltar se guarda la combinación pulsada (p. ej. `LB+RB`). Si no hay
     combinación guardada se mantiene el comportamiento histórico
     (**mantener Select 5 s**). `Clear` vuelve a ese valor por defecto.
   - Los atajos se validan: se exige al menos un modificador salvo en teclas de
     función (`F1`–`F24`) y `Print`. El atajo de teclado se registra como global
     en Windows (`RegisterHotKey`); si el sistema lo rechaza se avisa en Ajustes.
2. **Carátula desde el sistema**: en *Choose artwork* hay un botón
   **Browse…** que abre el selector de archivos y usa la imagen elegida
   (png/jpg/jpeg/webp/bmp) como carátula, copiándola a la caché de la app.
3. **Menús modernos**: el menú contextual de las carátulas y el menú de las tres
   rayas se reestilizan (fondo con degradado, borde de acento, iconos, texto de
   sección, hover con barra de acento y mejor contraste).
4. **Separación título/carátula**: el título de la biblioteca baja unos píxeles
   para no quedar pegado al cartucho.
5. **Marca del cartucho**: el hueco donde ponía `GC` (PS2 y DS) muestra la
   tienda del juego (`STEAM`, `EPIC`, `GOG`, `BATTLE.NET`, `RIOT`) o `LOCAL`.
6. **Big Picture**:
   - la leyenda de botones sube a la barra superior, entre
     `GAMECENTER BIG PICTURE` y el estado del mando.
   - la hora local gana protagonismo (píldora con acento).
   - al liberar la franja inferior, el carrusel gana altura; ninguna carátula se
     recorta en la animación (se limita su posición al área visible).
   - las píldoras de filtro (`All games`, `Recent`, `Favorites`) ajustan su
     ancho al texto para que no se desborde en otros idiomas.
7. **Dock**: el punto verde, `Ready` y la hora quedan centrados verticalmente.
8. **Stats**: al pasar el puntero por la gráfica “a river” aparece un
   **tooltip** con la fecha del punto, el total del periodo y el desglose por
   juego (color + horas), con guía vertical y puntos resaltados.

### Decisiones de arquitectura

- **`core/shortcuts.py`** (nuevo): fuente única para normalizar atajos
  (`"Ctrl+Alt+P"`), convertir `Qt.Key` + modificadores a texto canónico y
  traducir a `(mods, VK)` de Windows. Preferencias y `ScreenshotManager` lo
  comparten, así no hay dos listas de teclas.
- El formato guardado pasa a ser **texto canónico estilo Qt**
  (`Ctrl+PageDown`). Los valores antiguos (`ctrl+pagedown`, `f12`, `none`…) se
  migran al cargar, sin romper `settings.json` existentes.
- `ScreenshotManager` gana `recording` + `startRecording/cancelRecording/
  recordKey`. Al entrar en escucha se **desregistra el hotkey global** para que
  el sistema no se coma la combinación que el usuario quiere capturar.
- `GamepadManager` recibe las preferencias, expone `screenshotCombo`
  (`""` = mantener Select 5 s), `capturing`, `startCapture/cancelCapture` y
  `comboCaptured`. Mientras captura no despacha navegación/A/B/…; al completar
  persiste la combinación. El disparo es por flanco (una captura por pulsación).
- `Main.qml` desactiva sus `Shortcut` mientras se graba un atajo (si no,
  `Ctrl+B` o `Escape` ganarían al grabador).
- La carátula local se copia a `~/.cache/gamecenter/art/local/` con nombre
  estable por juego y se sirve por el proveedor `image://art` existente.
- Los menús se construyen con `Menu` + `delegate` propio (icono, texto y atajo
  opcional) reutilizando un estilo común en cada archivo.
- El tooltip de Stats se dibuja en QML sobre el `Canvas` (sin repintar el
  `Canvas` más que al cambiar el índice) con los datos de `river.layers`.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `shortcuts.normalize(value)` | función | Texto canónico (`"Ctrl+Alt+P"`), `""` para ninguno, `None` si no es válido. |
| `shortcuts.from_key(key, modifiers)` | función | Atajo canónico desde `Qt.Key` + modificadores. |
| `shortcuts.to_vk(sequence)` | función | `(mods, vk)` para `RegisterHotKey` o `None`. |
| `Preferences.screenshot_gamepad` | `str` | Combinación de mando (p. ej. `LB+RB`); `""` = mantener Select. |
| `Screenshots.recording` | `bool` | Está escuchando teclas. |
| `Screenshots.startRecording()` / `cancelRecording()` | slots | Entrar/salir de escucha. |
| `Screenshots.recordKey(key, modifiers)` | slot → `str` | Guarda y devuelve el atajo capturado. |
| `Screenshots.clearShortcut()` | slot | Deja el atajo de teclado vacío. |
| `Gamepad.screenshotCombo` | `str` | Combinación configurada (`""` = Select 5 s). |
| `Gamepad.capturing` | `bool` | Está escuchando el mando. |
| `Gamepad.startCapture()` / `cancelCapture()` | slots | Entrar/salir de escucha. |
| `Gamepad.setScreenshotCombo(combo)` / `clearScreenshotCombo()` | slots | Guardar/limpiar. |
| `Gamepad.comboCaptured(combo)` | signal | Combinación capturada. |
| `Library.chooseCoverFile()` | slot → `str` | Selector de archivos; ruta o `""`. |
| `Library.setGameCover(row, path)` | slot | Valida, copia a caché y aplica la carátula. |
| `GameDetail.artChanged` | signal | (existente) refresca la tarjeta tras cambiar la carátula. |

### Checklist

#### Backend
- [x] `core/shortcuts.py` con normalización, captura y VK.
- [x] `preferences.py`: atajos canónicos, migración y `screenshotGamepad`.
- [x] `screenshots.py`: grabación de teclas, secuencias libres y hotkey global.
- [x] `gamepad.py`: combinación personalizada, captura y disparo por flanco.
- [x] `app.py`: pasar preferencias al `GamepadManager`.
- [x] `library_model.py`: carátula desde archivo del sistema.
- [x] Traducciones ES/FR/DE/IT/PT.

#### Frontend
- [x] `SettingsPanel.qml`: grabador de atajos de teclado y mando.
- [x] `ArtPicker.qml`: botón *Browse…*.
- [x] `TopBar.qml` y `LibraryGrid.qml`: menús modernos.
- [x] `Cartridge.qml`: más aire bajo la carátula.
- [x] `PS2Shell.qml` / `DSShell.qml`: marca de tienda en vez de `GC`.
- [x] `BigPicture.qml` / `BigPictureCarousel.qml`: leyenda arriba, hora
      destacada, filtros que no desbordan y carátulas sin recortes.
- [x] `Dock.qml`: punto, texto y hora centrados.
- [x] `StatsView.qml`: tooltip de la gráfica.
- [x] `Main.qml`: atajos desactivados durante la grabación.

#### Tests y docs
- [x] Tests de `shortcuts`, preferencias, `ScreenshotManager`, `GamepadManager`
      y carátula local.
- [x] Test QML de los nuevos controles y del tooltip.
- [x] README/CHANGELOG/WORKFLOW y verificación visual.

### Verificación

- [x] `python -m pytest -q` → **174 passed**.
- [x] Capturas de Ajustes (atajos), menú superior y contextual, biblioteca
      (clásico, PS2 y DS), *Choose artwork*, Big Picture (arco y anillo) y Stats
      con el tooltip abierto.
- [x] `tools/idle_probe.py` sigue dando 0 frames en reposo tras los cambios.
- [ ] Prueba real de captura con un atajo personalizado en un juego abierto.

## Feature 0.19.1 — Idle silencioso: la ventana deja de repintarse sin cambios

### Descripción funcional

- Con la aplicación abierta y **sin interacción**, GameCenter deja de repintar la
  ventana. Antes se renderizaba a la frecuencia del monitor (medido: **179,8 fps**
  en 1920×1080 @ 179 Hz, 17 % CPU y 12-30 % GPU) porque tres animaciones
  decorativas seguían corriendo dentro de overlays cerrados.
- La **biblioteca**, la **ficha**, **Stats** y el **dock** se siguen viendo y
  comportando igual; solo cambia que ya no se dibujan frames que el usuario no
  puede percibir.
- Los orbes del **Year in Review** siguen animándose mientras la presentación
  está abierta; al cerrarla se detienen.
- El punto del **aviso de actualización** deja de latir de forma infinita: hace
  un pulso corto cuando aparece y se queda fijo. La señal visual (punto + borde
  de acento + tooltip) se mantiene.
- **Big Picture** se crea la primera vez que se abre y se destruye al cerrar
  (con su fundido de 180 ms intacto). Antes existía desde el arranque y su
  carrusel generaba repintados continuos.
- El reloj del dock solo reescribe el texto cuando cambia el minuto.

### Decisiones de arquitectura

- **Causa raíz** (medida con `QQuickWindow.frameSwapped` + bisección del árbol
  QML): `visible: false` u `opacity: 0` **no detienen una animación QML**. Un
  `NumberAnimation` con `loops: Animation.Infinite` dentro de un overlay cerrado
  sigue marcando la escena como sucia y el render loop (threaded, por defecto en
  Windows) dibuja **la ventana completa** en cada refresco del monitor.
- Las animaciones decorativas se condicionan con `running:` a que su dueño esté
  abierto. Es la forma mínima y sin riesgo: no cambia el árbol de items, ni los
  ids, ni los `findChild` de los tests.
- `BigPicture` pasa a un `Loader` con `active` gobernado por
  `window.bigPictureMounted`. La destrucción se retrasa 220 ms tras cerrar para
  respetar el fundido de salida y evitar destruir el item dentro de la emisión
  de su propia señal. `Main` conserva `bigPictureOpen` como única fuente de
  verdad; el componente sigue leyendo `opened` de esa propiedad.
- El pulso del aviso de actualización pasa de `loops: Animation.Infinite` a un
  `SequentialAnimation` **one-shot** disparado con `onVisibleChanged`. Un punto
  de 8 px no justifica repintar la ventana entera a 180 Hz mientras haya una
  actualización pendiente.
- `tools/idle_probe.py` mide fps reales + CPU del proceso en reposo y sirve de
  guardarraíl (`--max-fps`). Es una herramienta de desarrollo, no se empaqueta.
- `tests/test_idle_animations.py` vigila el patrón: cualquier
  `loops: Animation.Infinite` debe llevar un `running:` en su mismo bloque.

### Contrato de API (adiciones QML)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `YearReview.orbA/orbB` animations | `running` | Solo animan con `root.opened`. |
| `TopBar.updateDot` | `Rectangle` | Punto del aviso; `dotPulse` one-shot al aparecer. |
| `Main.bigPictureMounted` | `bool` | Big Picture instanciado (abierto o fundiendo). |
| `Main.bigPictureLoader` | `Loader` | Crea/destruye `BigPicture` bajo demanda. |
| `Dock.clock` | `Text` | Solo se reasigna si el minuto cambió. |
| `tools/idle_probe.py` | script | `--seconds`, `--max-fps`; imprime fps y CPU. |

### Checklist

#### Frontend
- [x] `YearReview.qml`: `running: root.opened` en los dos orbes.
- [x] `TopBar.qml`: pulso infinito → one-shot al aparecer el aviso.
- [x] `Main.qml`: `Loader` + `bigPictureMounted` con destrucción diferida.
- [x] `Dock.qml`: reloj sin reescrituras redundantes.

#### Herramientas y tests
- [x] `tools/idle_probe.py` (fps + CPU en reposo, umbral configurable).
- [x] `tests/test_idle_animations.py` (guardarraíl de animaciones infinitas +
      Big Picture bajo demanda).
- [x] README/CHANGELOG actualizados.

### Verificación

- [x] `python -m pytest -q` → **163 passed**.
- [x] `python tools/idle_probe.py --seconds 8 --settle 6` → **0 frames en 8 s,
      CPU 0,40 %** (`RESULT ok`).
- [x] Antes/después con la app real (1920×1080 @ 179 Hz, 12 hilos):

  | | Antes | Después |
  | --- | --- | --- |
  | Frames en reposo | 179,8 fps | **0 fps** |
  | CPU (media) | 17,0 % (pico 25 %) | **0,58 %** (pico 6,2 % al arrancar) |
  | GPU (media) | 11,9 % (pico 20 %) | **0,00 %** |
  | CPU acumulada en 15 s | 7,3 s | **1,6 s** |

- [x] Capturas de verificación: biblioteca, Big Picture (montado bajo demanda,
      carrusel y pistas correctos), Stats, Year in Review (orbes y diapositivas)
      y ficha con el blur intacto.
- [x] Big Picture entra/sale con su fundido de 180 ms y se vuelve a montar al
      reabrir (cubierto por test).
- [x] Tras usar la app, vuelve a reposo: 0,0 fps medidos después de abrir/cerrar
      Big Picture y después del Year in Review.


## Feature 0.19.0 — Overlay de captura y capturas en el timeline

### Descripción funcional

- **Ubicación actual de las capturas**: `%APPDATA%/GameCenter/screenshots/`
  (Linux: la carpeta `GameCenter/screenshots` dentro de `XDG_CONFIG_HOME` o
  `~/.config`). El índice nuevo vive en `%APPDATA%/GameCenter/screenshots.json`.
- Al guardar una captura:
  - aparece un **flash breve** sobre la pantalla del juego,
  - se muestra una **tarjeta con la miniatura** en la esquina inferior derecha,
    siempre encima, sin foco y con ratón atravesable,
  - desaparece sola a los ~2,7 s.
- El índice vincula cada PNG con:
  - `gameId`,
  - `sessionId`,
  - inicio de la sesión,
  - instante de la captura.
- En la ficha del juego:
  - el **timeline de sesiones** muestra las **2 primeras capturas** a la derecha
    de cada sesión,
  - si hay más, aparece la **tercera miniatura con un contador +N**,
  - una sección **SCREENSHOTS** reúne todas las capturas del juego,
  - al pulsar cualquier miniatura se abre un **visor a pantalla completa** con
    anterior/siguiente, contador y fecha.
- Las capturas sin sesión identificable siguen apareciendo en la galería del
  juego; las que ya no existen en disco se ignoran. Las capturas antiguas sin
  índice se recuperan por el prefijo del título y la marca `YYYYMMDD-HHMMSS`
  del nombre de archivo.

### Decisiones de arquitectura

- `core/screenshot_store.py`: índice JSON atómico, filtrado de archivos
  inexistentes y URL `file://` lista para QML.
- `SessionTracker.list` expone `startedAt` para que el manager pueda guardar el
  inicio exacto de la sesión.
- `ScreenshotManager` guarda el índice al capturar y expone `lastCapture`
  (`path`, `url`, `gameId`, `title`, `takenAt` y geometría de la pantalla).
- `ScreenshotOverlay.qml` es una **ventana top-level independiente** con flags
  `Frameless | StaysOnTop | TransparentForInput | DoesNotAcceptFocus | Tool`.
  Se crea una sola vez desde `app.py` (no anidada en `Main`) para evitar
  problemas de ciclo de vida y poder superponerse al juego.
- `LibraryModel._detail_payload` cruza el índice con `history_for(game)` por
  `sessionStartedAt` (tolerancia 2 s) y, como respaldo, por el intervalo
  `[start, start + seconds]`.
- `GameDetail.qml` incorpora `ShotThumb`, la galería, el visor y los atajos
  Escape/←/→ cuando el visor está abierto.
- Los tests de UI definen `GC_NO_OVERLAY=1` para no crear ventanas top-level en
  cada engine; el overlay se valida aparte.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `screenshot_store.index_path()` | función | `config_dir()/screenshots.json`. |
| `screenshot_store.record(...)` | función | Indexa un PNG con juego/sesión/tiempos. |
| `screenshot_store.for_game(game_id)` | función | Capturas existentes con `url`. |
| `SessionTracker.list[].startedAt` | int | Inicio de la sesión activa. |
| `Screenshots.lastCapture` | `QVariantMap` | Datos de la última captura y geometría de pantalla. |
| `ScreenshotOverlay.play(capture)` | función QML | Muestra flash + tarjeta. |
| `gameDetail.screenshots` | list | Todas las capturas del juego, recientes primero. |
| `gameDetail.screenshotCount` | int | Total de capturas. |
| `history[].screenshots` | list | Capturas asociadas a esa sesión. |
| `history[].previewScreenshots` | list | Primeras 2 capturas. |
| `history[].overflowScreenshot` | object | Tercera captura para el contador. |
| `history[].overflowCount` | int | `total - 2`. |
| `GameDetail.openViewer(shots,index)` | función | Abre el visor. |
| `GameDetail.viewerOpen` | bool | Visor visible. |

### Checklist

- [x] `screenshot_store.py` e índice atómico.
- [x] `SessionTracker.startedAt` y `ScreenshotManager` con `lastCapture`.
- [x] Overlay top-level con flash y tarjeta click-through.
- [x] Timeline con 2 miniaturas + contador `+N`.
- [x] Miniaturas más grandes, líneas separadas y scroll propio del timeline.
- [x] X de “Add a game” anclada a la esquina superior derecha.
- [x] Scrollbar de Ajustes separada de la X de cierre.
- [x] Galería SCREENSHOTS en la ficha.
- [x] Visor a pantalla completa con anterior/siguiente y teclado.
- [x] Traducciones ES/FR/DE/IT/PT.
- [x] Tests de índice, captura, asociación a sesiones y QML.
- [x] Recuperación de capturas antiguas por título + timestamp.
- [x] README/CHANGELOG/WORKFLOW y verificación visual.

### Verificación

- [x] `python -m pytest -q` → **161 passed**.
- [x] Captura del detalle con timeline (2 miniaturas + `+2`), galería y visor.
- [x] Timeline con 9 sesiones: scroll vertical, miniaturas 64×40 y líneas largas.
- [x] Captura del diálogo Add a game con la X en la esquina derecha.
- [x] Captura de Ajustes con scrollbar visible sin solapar la X.
- [x] Comprobado el overlay como ventana independiente (`opened=true`,
  `cardOpacity=1`, geometría de pantalla).
- [x] Índice aislado en tests; sin residuos en `%APPDATA%`.

## Feature 0.18.0 — Review anual estilo Instagram Stories

### Descripción funcional

- El botón **Review year** de Estadísticas abre una presentación **a pantalla
  completa**, inmersiva y animada, en lugar de recorrer las tarjetas actuales.
- La presentación incluye:
  - apertura con el año, tiempo total, sesiones, días, juegos y juego más
    jugado;
  - una diapositiva por **mes activo** con horas, sesiones, días, mejor día,
    racha, carátula del juego principal, top 3 y actividad diaria;
  - diapositivas dedicadas a **most played game**, **sessions**,
    **longest streak**, **best day** y **busiest month**;
  - cierre con el resumen del año y “See you next year”.
- Estilo stories: barras de progreso segmentadas, avance automático (7,2 s),
  pausa/reanudación, cierre, navegación con ←/→/Espacio/Esc, mando
  (D-pad/LB/RB/B/A) y tap en el tercio izquierdo/derecho.
- Fondo con degradado por acento, orbes animados, watermark del año, tarjetas
  de cristal, carátulas grandes, revelados escalonados y barras animadas.
- El acento de cada diapositiva sale del color del juego/mes protagonista.

### Decisiones de arquitectura

- `stats.year_review()` reutiliza `build(period="year")` y añade:
  `bestDay`, `longestStreak`, `busiestMonth`, `mostSessionsMonth`,
  `mostDaysMonth`, `totalGames`, `activeMonths`, ritmo mensual y una lista
  `slides` ya ordenada con su `type` y `accent`.
- `Library.yearReview(year)` expone el payload por QML con las carátulas
  actuales.
- `YearReview.qml` gestiona la presentación, el temporizador, las barras y la
  navegación; `YearReviewSlide.qml` renderiza cada tipo de diapositiva.
- El overlay vive en `Main.qml` (z 32) para cubrir también la barra superior y
  las tarjetas. Los atajos globales de `Main` se desactivan mientras está
  abierto.
- `StatsView` emite `reviewRequested(year)` y conserva `Review year` como
  entrada; se elimina el antiguo `reviewTimer` que autoavanzaba el carrusel.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Library.yearReview(year)` | slot → `QVariantMap` | Payload completo del recap anual. |
| `stats.year_review()` | función | Construye resumen, meses activos y slides. |
| `review.slides` | `list` | Diapositivas ordenadas: `intro`, `month`, `topGame`, `sessions`, `streak`, `bestDay`, `busiest`, `outro`. |
| `review.slides[].accent` | string | Color dominante de la diapositiva. |
| `review.bestDay` | object | Fecha, horas, sesiones y juego principal del mejor día. |
| `review.longestStreak` | object | Días, inicio, fin y rango de la mejor racha. |
| `review.busiestMonth` | object | Mes con más horas. |
| `review.averageSessionText` | string | Duración media por sesión. |
| `review.monthSessions/monthTotals` | list | Ritmo mensual para las barras. |
| `StatsView.reviewRequested(year)` | signal | Abre el recap desde el botón. |
| `YearReview.open(data, year)` | función QML | Inicia la presentación. |
| `YearReview.next/previous/close/togglePause` | funciones QML | Navegación. |
| `YearReview.storyMs` | int | 7200 ms por diapositiva. |
| `YearReview.currentSlide/currentIndex/progress/paused` | propiedades | Estado de la historia. |

### Checklist

- [x] Backend: `year_review`, slides, best day, streak, busiest month y ritmo.
- [x] `LibraryModel.yearReview` y carátulas.
- [x] `YearReview.qml`: progreso, timer, pausa, navegación, teclado y mando.
- [x] `YearReviewSlide.qml`: intro, meses, top game, sesiones, racha, mejor día,
      mes ajetreado y outro animados.
- [x] `StatsView`: botón Review year, señal y eliminación del autoavance.
- [x] `Main`: overlay a pantalla completa y atajos bloqueados.
- [x] Traducciones ES/FR/DE/IT/PT.
- [x] Tests backend y QML del payload, slides y navegación.
- [x] README/CHANGELOG/WORKFLOW y verificación visual.

### Verificación

- [x] `python -m pytest -q` → **158 passed**.
- [x] Capturas offscreen de intro, mes, top game, sesiones, racha, mejor día,
      mes ajetreado y outro.
- [x] Comprobado el progreso segmentado, la pausa y la navegación QML.

## Refinamiento 0.17.0 — Estadísticas por periodo y tarjetas enriquecidas

### Descripción funcional

- La granularidad del desglose sigue al filtro:
  - **Week** → una tarjeta por día (7 días).
  - **Month** → una tarjeta por semana del mes.
  - **Year** → una tarjeta por mes (comportamiento anterior).
  - **All time** conserva el desglose mensual del año seleccionado y el total
    histórico (decisión tomada para no introducir un cuarto tipo de tarjeta).
- El banner superior de tiempo jugado muestra el **juego con más horas del
  periodo** (carátula, nombre, horas y etiqueta del periodo).
- Las tarjetas muestran:
  - carátula del juego más jugado junto al nombre,
  - **top 3** numerado con carátula, horas detalladas en negrita y barra,
  - fila **Other games** con las horas del resto, sin barra,
  - **rombo + número dentro del mismo contenedor** para las métricas líderes
    (horas, días jugados y sesiones), sin insignias sueltas arriba,
  - un **banner único** por tarjeta: *Busiest month/week/day*, *Longest streak*
    o *Best day*,
  - etiquetas de métricas y gráfico con mejor tipografía y contraste.
- Los títulos del gráfico y del banner de repaso se adaptan al periodo.
- `Other games`, `Most days played`, `Longest streak`, días de la semana y
  títulos por periodo se traducen en ES/FR/DE/IT/PT.

### Decisiones de arquitectura

- `stats.build()` construye `buckets` genéricos (`kind` = `month`, `week` o
  `day`) con el mismo payload que antes usaban los meses. `months` se conserva
  como alias compatible con el desglose anual.
- `_day_buckets()` recorre los 7 días del periodo semanal; `_week_buckets()`
  parte el mes en semanas de lunes a domingo; `_months()` mantiene el desglose
  mensual. Los tres usan `_bucket_payload()`.
- `_annotate_buckets()` calcula los máximos del periodo y genera el `banner`
  único. `topSessions`/`topDays` solo se marcan si el máximo es mayor que 1
  para evitar destacados triviales en tarjetas diarias.
- `_river()` ahora recibe los buckets del periodo, no solo los meses, y expone
  `labels` además de `months`.
- `LibraryModel.stats()` sigue pasando el mapa de carátulas.
- `StatsView` usa `statsData.buckets`, `bucketsKind`, `topGame` y
  `river.labels`; `months` queda como alias para el carrusel anual.

### Contrato de API (adiciones)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `stats.buckets` | `list` | Tarjetas del periodo actual (mes, semana o día). |
| `stats.bucketsKind` | `string` | `month`, `week` o `day`. |
| `stats.buckets[].kind` | `string` | Tipo de la tarjeta. |
| `stats.buckets[].rangeText` | `string` | Rango legible (`26–27 Oct`, `26/10`…). |
| `stats.buckets[].topGames` | `list` | Como máximo 3 juegos, con carátula y horas detalladas. |
| `stats.buckets[].otherHoursText` | `string` | Tiempo agrupado en Other games (sin barra). |
| `stats.buckets[].hasOtherGames` | `bool` | Hay juegos fuera del top 3. |
| `stats.buckets[].topHours/topSessions/topDays` | `bool` | Líder del periodo (sesiones/días solo si el máximo > 1). |
| `stats.buckets[].banner` | `object` | `{label, value, detail, tint}` del destacado único. |
| `stats.buckets[].streak` | `int` | Racha dentro de la tarjeta. |
| `stats.topGame` | `object` | Juego con más horas del periodo (incluye `cover`). |
| `stats.river.labels` | `list` | Etiquetas de los buckets del periodo. |
| `StatsView.bucketsKind` | `string` | Tipo de tarjeta activo. |
| `StatsView.topGame` | `object` | Atajo a `statsData.topGame`. |
| `StatsView.reviewText()` | función | Texto del banner de repaso por periodo. |
| `StatsView.riverSubtitle()` | función | Subtítulo del gráfico por periodo. |

### Checklist

- [x] Backend: buckets de días, semanas y meses; top 3 + Other games + banners.
- [x] Backend: `topGame` del periodo y `river.labels`.
- [x] Traducciones nuevas y tests de periodos, top 3, Other games y banners.
- [x] QML: tarjetas con rombo+número, top 3 con carátula, Other games y banner.
- [x] QML: hero con juego más jugado y chips/labels restilizados.
- [x] QML: títulos y banner de repaso según periodo.
- [x] Tests QML de buckets por periodo y tarjetas enriquecidas.
- [x] README/CHANGELOG/WORKFLOW actualizados.
- [x] Verificación visual Week/Month/Year con capturas 1180×1400.

### Verificación

- [x] `python -m pytest -q` → **155 passed**.
- [x] Capturas offscreen de Week (días), Month (semanas) y Year (meses) con
  tarjetas completas, top 3, Other games y banners.
- [x] Comprobado que `topSessions`/`topDays` no destacan valores triviales de 1.
- [x] Comprobado el hero con el top game del periodo.

## Feature 0.17.0 — Capturas de juego, cartucho tras el dock y meses destacados

### Descripción funcional

- **Capturas de pantalla del juego**:
  - Se configura el atajo de teclado desde **Ajustes → SCREENSHOTS**.
  - Por defecto el teclado usa **Ctrl + Av Pág** (`Ctrl+PageDown`).
  - En mando, el atajo por defecto es **mantener Select/View 5 segundos**.
  - Solo se captura cuando hay una sesión de juego activa lanzada desde
    GameCenter; el PNG se guarda en `%APPDATA%/GameCenter/screenshots/`.
  - El atajo de teclado es **global en Windows** (funciona con el juego en
    primer plano) y local en el resto de plataformas.
  - Se muestra un aviso con el nombre del archivo guardado.
- **Inserción del cartucho**:
  - El cartucho que vuela al dock pasa **por detrás de la cara frontal del
    dock** (banner) y **por delante de la pletina oscura** de inserción.
  - La pletina es una pieza más oscura que el banner, situada detrás del
    cartucho, para que la animación se lea como una inserción real.
  - El cartucho que ya estaba en la ranura queda también detrás del banner.
- **Estadísticas**:
  - Cada tarjeta mensual muestra la **carátula del juego más jugado** junto al
    nombre del mes (con tooltip de título y horas).
  - Se añaden **tres insignias estéticas** en el mes del año con:
    - **más horas** jugadas,
    - **más sesiones**,
    - **más días** jugados.
  - En caso de empate, la insignia se muestra en todos los meses empatados.

### Decisiones de arquitectura

- `ScreenshotManager` (`core/screenshots.py`) centraliza la captura, el guardado
  y el registro del atajo global. Usa `QScreen.grabWindow(0)` sobre la pantalla
  del cursor y escribe en `config_dir()/screenshots/`.
- En Windows el atajo se registra con `RegisterHotKey` y un
  `QAbstractNativeEventFilter` (sin dependencias nuevas). Solo permanece
  registrado **mientras hay una sesión de juego activa**, para no apropiarse de
  la combinación cuando no hay partida. Si el sistema rechaza la combinación, el
  error se muestra en Ajustes y se mantiene el `Shortcut` local de QML como
  respaldo.
- `GamepadManager` incorpora la señal `screenshot` y un temporizador de flanco
  sobre `BUTTON_BACK` (Select/View): 5 s mantenidos. El resto del mapeo no
  cambia.
- `Preferences` valida el atajo contra una lista curada y lo persiste como
  `screenshotShortcut`.
- El `InsertEffect` deja de ser hijo de la ventana y pasa a vivir dentro de
  `libraryDock`, entre la pletina (`z: 12`) y el dock (`z: 20`). Así comparte
  el mismo contexto de apilado: pletina < cartucho en ranura < cartucho volando
  < cara frontal del dock.
- `stats.build()` recibe un mapa de carátulas desde `LibraryModel` para no
  acoplar el agregador a los proveedores de imágenes. Tras construir los meses,
  calcula los máximos anuales y añade `topHours`, `topSessions`, `topDays` y
  `mostPlayed` a cada mes.
- `StatsView.MonthCard` pinta la carátula y un componente `HighlightBadge` con
  degradado, borde y punto de color; las etiquetas se traducen vía `Tr`.

### Contrato de API

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `settings.json → screenshotShortcut` | string | `ctrl+pagedown` (defecto), `ctrl+f12`, `f12`, `printscreen`, `ctrl+shift+s`, `none`. |
| `Screenshots.shortcut` | `string` (notify `changed`) | Atajo persistido actual. |
| `Screenshots.setShortcut(value)` | slot | Valida, persiste y vuelve a registrar el atajo. |
| `Screenshots.shortcutSequence` | `string` | Secuencia Qt para el `Shortcut` local (`Ctrl+PageDown`…). |
| `Screenshots.localShortcutEnabled` | `bool` | `true` si el hotkey global no está activo (Linux o conflicto). |
| `Screenshots.registered` | `bool` | El atajo global está registrado en el sistema. |
| `Screenshots.error` | `string` | Mensaje si el sistema rechaza el atajo. |
| `Screenshots.directory` | `string` | Carpeta de capturas. |
| `Screenshots.captureIfPlaying()` | slot → `string` | Captura solo si hay sesión activa; devuelve la ruta. |
| `Screenshots.capture()` | slot → `string` | Captura siempre la pantalla actual. |
| `Screenshots.openFolder()` | slot | Abre la carpeta de capturas. |
| `Screenshots.saved(path)` / `failed(message)` | signals | Resultado de la captura para el toast. |
| `Gamepad.screenshot` | signal | Select/View mantenido 5 s. |
| `Gamepad.screenshotHoldSeconds` | `real` (constant) | 5.0. |
| `InsertEffect` | QML Item | Ahora hijo de `libraryDock`; `z: 15`. |
| `insertPlate` | QML Item | Pletina oscura detrás del cartucho; `z: 12`. |
| `slotCartridge` | QML Item | Cartucho en ranura; `z: 13`. |
| `dock` | QML Item | Cara frontal del banner; `z: 20`. |
| `stats.build(..., covers=...)` | parámetro opcional | `{game_id: cover_url}`. |
| `stats.months[].mostPlayed` | `object` | `{gameId, name, hoursText, cover, …}` del juego con más horas del mes. |
| `stats.months[].topHours/topSessions/topDays` | `bool` | El mes es el máximo del año en esa métrica. |
| `Library.stats()` | slot | Pasa las carátulas actuales de la biblioteca. |

### Checklist

#### Backend
- [x] `core/screenshots.py`: captura, guardado, hotkey global Windows y API QML.
- [x] `preferences.py`: `screenshotShortcut` validado y persistido.
- [x] `gamepad.py`: señal `screenshot` al mantener Select 5 s.
- [x] `app.py`: exponer `Screenshots` y conectar mando + hotkey.
- [x] `stats.py`: carátulas en `topGames`, `mostPlayed` y flags de máximos.
- [x] `library_model.py`: `stats()` pasa el mapa de carátulas.
- [x] Traducciones ES/FR/DE/IT/PT y tests de backend.

#### Frontend
- [x] `SettingsPanel.qml`: sección SCREENSHOTS con atajo, ayuda de mando y carpeta.
- [x] `Main.qml`: mover `InsertEffect` a `libraryDock`, pletina, z-order y toast de captura.
- [x] `StatsView.qml`: carátula junto al nombre y tres insignias de destacado.
- [x] `Dock.qml`: boca de ranura coherente con la pletina (si hace falta).
- [x] Tests QML de capas, ajuste de captura y estadísticas.
- [x] README/CHANGELOG y verificación visual.

### Verificación
- [x] `python -m pytest -q` → **150 passed**.
- [x] Capturas de ajustes, inserción (fotograma intermedio) y Stats con insignias.
- [x] Comprobación del atajo global con `WM_HOTKEY` simulado y captura PNG real.
- [x] Captura real de pantalla guardada en `screenshots/` (405 KB).
- [x] Comprobación visual del apilado: pletina (12) < ranura (13) < cartucho
  volando (15) < dock (20).

## Feature 0.16.5 — Modal de juego a pantalla completa

### Descripción funcional

- La ficha del juego deja de ser una caja centrada: pasa a ocupar **toda la
  ventana** con un fondo **blur opaco translúcido** (cristal esmerilado) sobre
  la escena que queda detrás.
- La **carátula/cartucho 3D** queda **fija en la esquina superior izquierda**,
  fuera del área de scroll. El visor 3D es más ancho que el modelo para que,
  al rotarlo, **ninguna esquina se recorte**:
  - arrastrar sobre el cartucho **rota** el modelo (sin desplazarlo),
  - doble clic sigue lanzando el juego.
- El **buscador se oculta en Estadísticas** (y `Ctrl+F` solo funciona en la
  biblioteca). Al entrar en Stats tampoco se muestra el **dock inferior**
  (ranura Ready, reloj y cartucho insertado) ni el aviso de actualización: es
  una ventana dedicada solo a estadísticas.
- El **carrusel de meses va del más reciente al más antiguo**: primero el mes
  actual y al final enero.
- Si el buscador tiene el foco y se pulsa en cualquier otro sitio de la
  ventana, el campo **pierde el foco** y desaparece el cursor de escritura,
  sin bloquear el clic que se estaba haciendo.

### Decisión de arquitectura

- `GameDetail.qml` recibe `backdropItem` (la escena a difuminar). Se captura
  una sola vez por apertura con `ShaderEffectSource` (`live: false`) y se
  procesa con `MultiEffect` de `QtQuick.Effects`; es barato y no requiere
  refactorizar el render.
- `Main.qml` agrupa la escena de biblioteca en un `Item` (`libraryScene`) para
  poder pasarla como `backdropItem`. La ficha y el toast quedan fuera.
- En Big Picture no se captura la escena (la ficha es hija del propio root):
  `backdropItem` queda a `null` y la ficha usa `image://bg/1` difuminado como
  respaldo. `GameDetail` funciona igual en ambos contextos.
- El cartucho vive en `cartridgeHost`, fijado arriba a la izquierda
  (`cartridgeMarginX/Y`), fuera del `Flickable` que recorta el contenido.
- El visor 3D es mayor que la tarjeta (`cartridgeWidth/Height`) y el modelo se
  reduce dentro con `DsCartridge3D.modelScale`, dejando margen en los cuatro
  lados para rotaciones de hasta ±50° de inclinación y giro completo.
- La ficha compacta (<940 px) mantiene la portada pequeña dentro del contenido
  y oculta el cartucho fijo para no tapar la lectura.
- El buscador se oculta con `visible` en `TopBar.qml`; el foco se limpia con una
  capa `MouseArea` de guardia en `Main.qml` que deja pasar el pulso
  (`mouse.accepted = false` + `propagateComposedEvents`).
- El dock, la ranura y el `UpdateBanner` viven en `libraryDock` (dentro de
  `libraryScene`) y solo son visibles en la biblioteca. `StatsView` usa todo el
  alto disponible.
- `StatsView.months` invierte `statsData.months` (que sigue en orden
  cronológico en el backend) y `carouselIndexForMonth()` traduce el mes
  calendario a su posición invertida; el `MonthCard` conserva el
  `monthIndex` original para abrir el mes correcto.

### Contrato de API (QML)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `GameDetail.backdropItem` | `Item` | Escena a desenfocar; `null` usa `image://bg/1`. |
| `GameDetail.compact` | `bool` (readonly) | `width < 940`; layout de una columna. |
| `GameDetail.cartridgeMarginX/Y` | `real` (readonly) | Posición fija del cartucho (24, 72). |
| `GameDetail.cartridgeWidth/Height` | `real` (readonly) | Visor 3D ancho (hasta 400×480). |
| `DsCartridge3D.modelScale` | `real` | Escala del modelo dentro del visor (0.82 en la ficha). |
| `GameDetail.scrollBy(delta)` | función | Sin cambios (mando/teclado en Big Picture). |
| `TopBar.searchFocused` | `bool` (readonly) | El `TextField` tiene el foco activo. |
| `TopBar.clearSearchFocus()` | función | Quita el foco del buscador. |
| `StatsView.months` | `list` (readonly) | Meses en orden inverso (actual → enero). |
| `StatsView.carouselIndexForMonth(monthIndex)` | función | Índice del mes en el carrusel invertido. |
| `DsCartridge3D.interactive` | `bool` | Desactiva su `MouseArea` para que la ficha gestione la rotación. |
| `Cartridge.interactive` | `bool` | El 2D sigue interactivo (hover y doble clic) pero sin desplazarse. |

### Checklist

#### Backend
- [x] Traducciones nuevas (ES/FR/DE/IT/PT) de las pistas de arrastre.

#### Frontend
- [x] `GameDetail.qml`: overlay a pantalla completa, sin caja, con blur + tinte.
- [x] `GameDetail.qml`: carátula fija arriba a la izquierda, rotable y nunca recortada.
- [x] `DsCartridge3D.qml`: visor ampliado (`modelScale`) para no cortar esquinas al rotar.
- [x] `Main.qml`: escena envuelta para el blur, `backdropItem` y toast recolocado.
- [x] `TopBar.qml`: buscador oculto en Estadísticas y API de foco.
- [x] `Main.qml`: ocultar dock/ranura/aviso en Stats y usar todo el alto.
- [x] `StatsView.qml`: meses del actual a enero conservando `monthIndex`.
- [x] `Main.qml`: capa de guardia para limpiar el foco al pulsar fuera.
- [x] `DsCartridge3D.qml`/`Cartridge.qml`: el 3D desactiva su `MouseArea` (rota la ficha); el 2D mantiene hover y doble clic.
- [x] `BigPicture.qml`: pasa `backdropItem: null` explícito y conserva el scroll.
- [x] Tests QML: buscador oculto en stats, foco del buscador y ficha abierta.
- [x] Tests QML: dock oculto en stats y meses en orden inverso.
- [x] README/CHANGELOG/WORKFLOW actualizados.
- [x] Verificación visual (normal, compacta y Big Picture).

### Verificación
- [x] `python -m pytest -q` → **140 passed**.
- [x] Capturas de la ficha a 1180×800 (clásico y DS 3D), 900×620 (compacta) y
  dentro de Big Picture, incluida la rotación extrema (±50° de inclinación y
  giro completo) para comprobar que no se corta ninguna esquina.
- [x] Comprobado con `QTest`: el buscador se oculta en Stats, el clic fuera
  quita el foco y el clic sigue abriendo la ficha del juego.
- [x] Captura de Stats sin dock (todo el alto) con octubre primero y la
  comprobación de que la lista termina en enero.

## Feature 0.16.0 — Perfil de juego, unificación y estado

### Descripción funcional

- Añadir a la ficha de cada juego un **perfil GameCenter** independiente de la
  tienda: puntuación 0–100 y estado (Playing, On Going, Beaten, Completed,
  Played, Plan to Play, On Hold, Not Played, Abandoned).
- El perfil se muestra siempre en la información del juego con un diseño
  moderno y se edita desde los **ajustes del juego** (engranaje / Edit profile).
- Permitir **unificar manualmente** los datos de otra entrada conocida, aunque
  ya no aparezca en la biblioteca, sobre el juego abierto (destino):
  - el selector de origen empieza **vacío**: no se preselecciona ninguna entrada,
  - suma horas y contador de sesiones,
  - mueve el timeline de sesiones al ID destino,
  - guarda una **captura de la carátula del origen** en disco para recaps,
  - si el destino no tiene carátula real, adopta la del origen,
  - deja un registro de trazabilidad (`mergedSources`) visible en la ficha,
  - permite ocultar el origen tras unificar para no duplicar estadísticas.
- La identidad sigue siendo el ID de tienda, pero el perfil permite reconstruir
  una trazabilidad constante entre plataformas.

### Contrato de API

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `profiles.json` | archivo | `%APPDATA%/GameCenter/profiles.json`; metadatos por ID. |
| `profiles.rating` | int/null | 0–100; `null` si no se ha puntuado. |
| `profiles.status` | string | `playing`, `ongoing`, `beaten`, `completed`, `played`, `plan`, `onhold`, `notplayed`, `abandoned`. |
| `profiles.merged_sources` | list | Registros importados con id, título, fuente, fecha, segundos, sesiones y captura. |
| `profiles.merged_into` | string | ID destino cuando esta entrada ya fue unificada. |
| `profiles.extra_seconds` | int | Horas importadas que se suman a las de Steam en el destino. |
| `Library.mergeCandidates(gameId)` | slot → `QVariantList` | Entradas importables, incluidas las retiradas con datos (`orphan`); mismo título primero. |
| `Library.mergeGameData(sourceId, targetId, hideSource)` | slot → `QVariantMap` | `{ok, message, targetId}`. |
| `Library.setGameRating(gameId, rating)` | slot | Guarda 0–100. |
| `Library.setGameStatus(gameId, status)` | slot | Guarda el estado validado. |
| `Library.rowForId(gameId)` | slot → int | Fila visible actual o `-1`. |
| `gameDetailById()/gameAt()` | payload | Añade `rating`, `hasRating`, `status`, `mergedSources`, `mergedInto`, `mergedIntoTitle`; cada sesión lleva `imported`. |
| `GameDetail.profileChanged()` | signal | El padre recarga la ficha tras editar o unificar. |

### Checklist

#### Backend
- [x] `profiles.py`: lectura/escritura atómica, estados válidos, rating 0–100, registros de fusión.
- [x] `playtime.py`: helpers para escribir/limpiar resumen y mover historial entre IDs.
- [x] `sources/__init__.py`: sumar `extra_seconds` del perfil a las horas de Steam y restar el tiempo ya unificado del origen.
- [x] `LibraryModel`: candidatos, merge, rating y status; refresco de datos.
- [x] Captura de carátula en `recap_covers/` y adopción si el destino no tiene.
- [x] Tests de perfiles, merge, rating/status, entradas eliminadas y aislamiento de rutas.

#### Frontend
- [x] `GameProfilePanel.qml`: estados, slider 0–100, selector de origen vacío, unificación, registros importados.
- [x] `GameDetail.qml`: tira de perfil visible, botón de ajustes y panel expandible.
- [x] `Main.qml`/`BigPicture.qml`: recargar ficha con `profileChanged`.
- [x] Traducciones ES/FR/DE/IT/PT.
- [x] Verificación visual en ventana normal, compacta y Big Picture.

### Verificación
- [x] `python -m pytest -q` → **138 passed**.
- [x] Capturas de la ficha con perfil y del panel de unificación (normal, 900×620 y Big Picture).
- [x] README/CHANGELOG/WORKFLOW actualizados.

## Versión 0.15.2

- Carrusel de Big Picture con **cuatro modos**: **Arco**, **Plano**, **Anillo
  3D** y **Rueda vertical**, conmutables con **LB/RB**, `C`/`Tab` o la píldora
  de modo; la navegación y los filtros se adaptan a cada modo.
- Las carátulas se muestran **completas** (`PreserveAspectFit`) y la tarjeta
  seleccionada **nunca se solapa con la barra inferior**, en cualquier tamaño.
- Efecto visual moderno tipo PS5: halo de acento, sombra en profundidad, brillo
  de cristal, pista del anillo y transiciones animadas entre modos.
- Barra superior reducida (altura, márgenes, tipografía y botón Exit) para que
  el carrusel sea el protagonista; hero contenido y carrusel más alto.
- El puntero del ratón se oculta al recibir cualquier entrada de mando
  (`GamepadManager._hide_cursor`) y reaparece al detectar movimiento del ratón
  (`_poll_cursor`), sin bloquear los clics.
- `Gamepad.showCursor()` se llama al cerrar Big Picture y al salir de la app.
- Tests: **125 passed**.

## Descripción funcional

- Modo **Big Picture** a pantalla completa (sin barra de título ni barra de
  Windows), con portada grande, información del juego, filtros y un carrusel
  cinematográfico con cuatro modos: **Arco**, **Plano**, **Anillo 3D** y
  **Rueda vertical**.
- El juego seleccionado ocupa mucho más ancho y alto que los laterales; el
  resto queda en segundo plano con menor opacidad y profundidad.
- Las carátulas se ven completas, sin recortes, y la tarjeta seleccionada queda
  siempre por encima de la barra de pistas.
- Entrada desde el menú, `Ctrl+B` o **Start** del mando.
- Salida:
  - **Start** vuelve a pulsarse y sale directamente del modo,
  - botón **Exit** de la esquina para ratón (con confirmación),
  - **B** es “volver”: cierra la ficha del juego, no sale del modo.
- **Y/Triángulo** abre la ficha del juego seleccionado, con descripción,
  metadata y timeline. También se abre con el botón **Details** del ratón.
- Mando Xbox/XInput:
  - D-pad/stick: navegar (arriba/abajo o izquierda/derecha según el modo).
  - A: jugar.
  - B: volver / cerrar ficha.
  - Y: abrir/cerrar ficha.
  - LB/RB: cambiar el modo del carrusel.
  - X: favorito.
  - Start: salir.
- Teclado: flechas, Enter, Esc, `I`, `C`/`Tab` (modo), `[`/`]` (filtros), `F`.
  Ratón: tarjetas, flechas, píldora de modo, filtros, Play, Details, favorito,
  Exit y confirmación.

## Decisiones de arquitectura

- `GamepadManager` XInput añade la señal `details` mapeada a **Y**.
- `Main.qml` enlaza `visibility` a `Window.FullScreen` al abrir Big Picture y
  vuelve a `Window.Windowed` al cerrar. `requestActivate()` trae la ventana al
  frente al entrar.
- `BigPicture.qml` usa `uiScale` y alturas proporcionales al alto de pantalla
  para adaptarse de 620 px a pantallas grandes. `heroHeight` y
  `carouselHeight` se recalculan según el modo para reservar espacio a las
  tarjetas superiores/inferiores de la rueda vertical y evitar solapes.
- El carrusel vive en `BigPictureCarousel.qml`:
  - `mode` admite `arc`, `flat`, `ring` y `wheel`.
  - posiciona una ventana de tarjetas (`windowStart`) alrededor de la
    seleccionada con transformaciones y animaciones.
  - `arc` aplica caída y giro Z; `flat` mantiene una fila; `ring` reparte las
    tarjetas en profundidad con giro Y y una pista elíptica; `wheel` apila las
    tarjetas arriba/abajo con giro X.
  - las carátulas usan `Image.PreserveAspectFit` y cada tarjeta tiene fondo
    opaco, halo, sombra y brillo de cristal.
- La ficha reutiliza `GameDetail.qml` dentro de Big Picture:
  - `Library.gameDetailById`, `loadDetailsById`, `openFolderById`,
    `copyAppIdById` evitan depender de filas filtradas.
  - `GameDetail` gana `showArt` (oculta “Choose art” en Big Picture) y
    `scrollBy()` para el scroll con stick/D-pad.
  - La descripción carga con `Library.loadDetailsById`.
- La B ya no abre la salida; Start cierra el modo directamente. El botón Exit
  conserva confirmación.

## Contrato interno

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Gamepad.connected` | bool | Mando XInput activo. |
| `Gamepad.navigate/accept/back/menu` | signals | D-pad/A/B/Start. |
| `Gamepad.pageLeft/pageRight/favorite/details` | signals | LB/RB (modo), X, Y. |
| `Library.bigPictureGames` | `QVariantList` | Juegos para Big Picture. |
| `Library.launchById(gameId)` | slot → `str` | Lanza y devuelve sesión. |
| `Library.toggleFavoriteById(gameId)` | slot → `bool` | Alterna favorito. |
| `Library.gameDetailById(gameId)` | slot → `QVariantMap` | Ficha completa por id. |
| `Library.loadDetailsById(gameId)` | slot | Carga descripción por id. |
| `Library.openFolderById/copyAppIdById` | slots | Acciones por id. |
| `BigPicture.detailOpen` | bool | Ficha abierta. |
| `BigPicture.carouselMode` | `string` | `arc`, `flat`, `ring` o `wheel`. |
| `BigPicture.cycleMode(delta)` | función | Cambia el modo del carrusel. |
| `BigPicture.openDetail()` | función | Abre ficha del seleccionado. |
| `BigPictureCarousel.mode` | `string` | Modo de presentación activo. |
| `BigPictureCarousel.selectedIndex` | `int` | Tarjeta enfocada. |
| `BigPictureCarousel.selected/activated` | signals | Clic y doble clic. |
| `GameDetail.scrollBy(delta)` | función | Scroll para mando/teclado. |

## Checklist

### Backend
- [x] XInput con conexión, flancos, repetición y señal `details` (Y).
- [x] `Gamepad` expuesto al contexto QML y desactivable.
- [x] Ocultación/restauración del cursor con la entrada de mando.
- [x] API de biblioteca por id + ficha completa.
- [x] Carga de descripción por id y acciones de carpeta/AppID.
- [x] Tests de mapeo y API.

### Frontend
- [x] Big Picture fullscreen y retorno a ventana.
- [x] Layout responsive con `uiScale` y alturas adaptadas al modo.
- [x] Carrusel con modos Arco, Plano, Anillo 3D y Rueda vertical.
- [x] Carátulas completas y tarjeta enfocada siempre sobre la barra de pistas.
- [x] Navegación y pistas adaptadas a cada modo; LB/RB y `C`/`Tab` cambian modo.
- [x] Start sale; B vuelve; Y abre ficha; botón Details para ratón.
- [x] Ficha con descripción y timeline reutilizando `GameDetail`.
- [x] Scroll de la ficha con stick/D-pad y teclado.
- [x] Pistas de mando/teclado actualizadas.
- [x] Entrada desde menú, `Ctrl+B` y Start.

### Verificación
- [x] `python -m pytest -q` → **125 passed**.
- [x] Capturas de los cuatro modos en 800×800, 1280×720 y 1920×1080.
- [x] Prueba QML de apertura de ficha, navegación y cambio de modo.
- [x] README/CHANGELOG actualizados.

## Notas

- El soporte nativo de mando es **XInput (Windows)**.
- El modo se dibuja a pantalla completa real mediante `Window.FullScreen`;
  al salir vuelve a `Window.Windowed`.
- La ficha del juego dentro de Big Picture oculta el botón de carátula para
  centrarse en descripción y timeline.
- El perfil vive en `%APPDATA%/GameCenter/profiles.json`; las capturas de
  carátula de las fusiones se guardan en `%APPDATA%/GameCenter/recap_covers/`.
- El origen de una unificación se vacía (horas/sesiones/timeline) y, por
  defecto, se oculta para no duplicar estadísticas. Se puede restaurar desde
  Ajustes; un origen ya unificado no se puede volver a importar.
- Las horas nativas de Steam se conservan en Steam; el tiempo importado hacia
  un destino Steam se superpone desde el perfil (`extra_seconds`) sin tocar
  `localconfig.vdf`.
