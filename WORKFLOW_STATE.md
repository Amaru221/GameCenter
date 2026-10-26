# WORKFLOW STATE — Filtros completos e idiomas

## Descripción funcional

1. **Filtro "All stores"**: debe mostrar siempre todas las tiendas soportadas
   (Steam, Epic Games, GOG, Battle.net, Riot) más la entrada **Local**, aunque
   alguna tienda no tenga juegos instalados en este momento.
2. **Segundo filtro (ordenación)**: añadir la opción **Most played**, que ordena
   de mayor a menor tiempo jugado (`playtime_minutes`) y desempata por título.
3. **Idiomas**:
   - Interfaz: selector de idioma en **Settings** con inglés, español, francés,
     alemán, italiano y portugués. El cambio se aplica al instante y se persiste
     en `settings.json` (`language`).
   - Instalador Inno Setup: añadir francés, alemán, italiano, portugués,
     portugués de Brasil, neerlandés, polaco, ruso y japonés además de inglés y
     español.

## Decisión de arquitectura

- Un único catálogo de traducciones en Python (`gamecenter/core/i18n.py`) usa el
  texto inglés como clave. Se expone a QML mediante el objeto `Tr`:
  - `Tr.strings["Settings"]` → texto traducido (binding reactivo).
  - `Tr.language`, `Tr.languages`, `Tr.setLanguage(code)`.
- `LibraryModel` crea el `Translator` con las preferencias, lo registra como
  traductor activo y emite `changed`/`dataChanged` al cambiar de idioma.
- Los módulos de core traducen sus mensajes visibles con `tr("...")`.
- No se añaden dependencias ni pasos de compilación (`.qm`/`lrelease`).

## Contrato de API (UI interna)

| Elemento | Tipo | Descripción |
| --- | --- | --- |
| `Tr.language` | `str` (notify) | Código activo: `en`, `es`, `fr`, `de`, `it`, `pt`. |
| `Tr.languages` | `list[{text,value}]` | Idiomas disponibles para el `PillCombo`. |
| `Tr.strings` | `dict[str,str]` (notify) | Catálogo completo; las claves ausentes caen a inglés. |
| `Tr.setLanguage(code)` | slot | Cambia idioma, persiste y emite `languageChanged`. |
| `Tr.text(key)` | slot → `str` | Traducción puntual desde Python/QML. |
| `Library.translator` | `QObject` (constant) | Instancia `Tr` del modelo. |
| `Library.setSort("most")` | slot | Orden por tiempo jugado descendente. |
| `Library.sourceOptions` | `list[{text,value}]` | Todas las tiendas conocidas (sin `local`). |
| `Preferences.language` | propiedad | Persistida en `settings.json`. |

## Checklist

### Backend
- [x] `gamecenter/core/i18n.py` con catálogo en/es/fr/de/it/pt.
- [x] `Preferences.language` con validación y persistencia.
- [x] `LibraryModel`: `translator`, `setLanguage` vía `Tr`, mensajes traducidos.
- [x] `sourceOptions` incluye siempre Steam, Epic, GOG, Battle.net y Riot.
- [x] Orden `most` por `playtime_minutes` descendente.
- [x] Mensajes de core (`manual`, `launch`, `updater`, `steamgriddb`) traducidos.
- [x] `app.py` expone `Tr` al contexto QML.

### Frontend
- [x] `Toolbar.qml`: "All stores" con todas las tiendas, opción "Most played" y textos traducidos.
- [x] `SettingsPanel.qml`: sección LANGUAGE con selector + scroll para el panel.
- [x] Resto de QML usa `Tr.strings` para todos los textos visibles.
- [x] `Main.qml` refresca el detalle al cambiar de idioma.

### Empaquetado y documentación
- [x] `packaging/gamecenter.iss`: nuevos idiomas del instalador.
- [x] README y CHANGELOG actualizados.
- [x] Tests: orden `most`, catálogo de tiendas, cambio de idioma.

## Verificación

- `python -m compileall -q gamecenter tests` → OK.
- `python -m pytest -q` → **92 passed**.
- Carga headless de `Main.qml` y cambio de idioma en caliente comprobado en
  `tests/test_ui_smoke.py::test_qml_reacts_to_language_change`.
- Capturas revisadas: panel de Ajustes en inglés y español; toolbar con el
  nuevo desplegable de ordenación.

## Notas

- El catálogo usa el texto inglés como clave; cualquier clave ausente cae a
  inglés, así que añadir un idioma nuevo es solo añadir su diccionario.
- El idioma se guarda en `settings.json` (`language`) y se aplica al instante
  sin reiniciar.
