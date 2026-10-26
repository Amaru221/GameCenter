# WORKFLOW STATE — Estadísticas

## Descripción funcional

- Nueva pestaña **STATS** junto a **LIBRARY** y **STORE**.
- Barra superior de estadísticas con filtros **Week / Month / Year / All time**
  (Year por defecto), selector de año con flechas y banner lateral **“Your
  2026 so far, in review”** con botón **Watch** (recorrido automático de meses).
- Tarjeta principal **Time Played** con el total grande y métricas secundarias:
  comparación con el periodo anterior, días jugados/totales, racha y sesiones.
- Sección **Month by Month**:
  - Gráfico de áreas apiladas **“2026 as a river”** con los juegos principales.
  - Carrusel horizontal de tarjetas mensuales con horas, días jugados, mejor
    día, sesiones, top de juegos con barras de progreso y gráfico diario.
  - Botón **Open month** para enfocar ese mes en el resumen.
- Tema oscuro #0b0f19, tarjetas redondeadas con bordes sutiles, tipografía
  Sora/Chakra Petch y acentos azul/naranja/púrpura/esmeralda.

## Decisiones de arquitectura

- `gamecenter/core/stats.py` agrega `playtime.all_history()`:
  - Cada sesión se atribuye a la fecha local de inicio.
  - Periodos y comparaciones (semana/mes/año/anterior).
  - Días jugados, días transcurridos, racha más larga y sesiones.
  - Tarjetas mensuales, top games con porcentaje, actividad diaria y capas del
    río apilado.
- `playtime.record_session` guarda también `title` y `source` para que el
  historial siga siendo legible si el juego ya no está en la biblioteca.
- `LibraryModel.stats(period, year, month)` devuelve el `QVariantMap` completo.
- `StatsView.qml` es una página con `Flickable` vertical, cabecera responsive
  (banner en la misma fila o debajo según ancho), hero, river chart y carrusel.
- Se corrigió un conflicto importante: la propiedad `data` del componente
  sombreaba el `data` por defecto de `Item` en QML y los hijos visuales no se
  emparentaban. Ahora se llama `statsData`.
- El fondo animado de la app se oculta en la vista de estadísticas para dejar el
  tema oscuro limpio y ahorrar composición.

## Contrato interno

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Library.stats(period, year, month)` | slot → `QVariantMap` | Datos agregados. |
| `statsData.periodLabel` | str | “2026”, “January 2026”, “This week”… |
| `statsData.timeText` | str | Total del periodo, ej. “78h 20m”. |
| `statsData.changeText` | str | “+3% vs 2025” o vacío. |
| `statsData.daysText` | str | “60 of 299 days”. |
| `statsData.streakText` | str | “2-day streak”. |
| `statsData.sessionsText` | str | “100 sessions”. |
| `statsData.months` | list | Tarjetas mensuales. |
| `statsData.river` | map | `{months, layers}` para el gráfico. |
| `StatsView.setPeriod/changeYear/openMonth` | funciones | Cambian el periodo. |
| `StatsView.toggleReview` | función | Activa el auto-scroll de meses. |

## Checklist

### Backend
- [x] Historial con título/fuente por sesión.
- [x] Agregador de periodos, comparaciones, días, rachas y sesiones.
- [x] Tarjetas mensuales con top games, progreso y actividad diaria.
- [x] Río apilado por juego y colores estables.
- [x] `Library.stats` expuesto a QML.
- [x] Tests unitarios de estadísticas.

### Frontend
- [x] Pestaña STATS y navegación Library/Stats/Store.
- [x] Barra de filtros, selector de año y banner Watch.
- [x] Hero “Time Played” y métricas secundarias.
- [x] River chart y leyenda.
- [x] Carrusel mensual con Open month y barras diarias.
- [x] Responsive: banner debajo en ventanas estrechas, scroll vertical.
- [x] Corrección de `data` → `statsData` para el emparentado visual.

### Verificación
- [x] `python -m pytest -q` → **116 passed**.
- [x] Capturas en 1180×800 y 900×620.
- [x] Comprobación de periodos y tarjetas con historial de prueba.
- [x] Carga QML de la ventana completa.

## Notas

- Las estadísticas se construyen desde el historial de sesiones registrado por
  GameCenter; las partidas anteriores a esa función no tienen fecha y no se
  inventan.
- El resumen total de Steam sigue usando su `localconfig.vdf`; el historial
  mensual usa las sesiones lanzadas desde GameCenter.
