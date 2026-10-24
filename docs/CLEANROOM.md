# Política de reimplementación limpia

GameCenter es una implementación independiente. La meta es tener una licencia
propia (MIT) sin arrastrar obligaciones de otros proyectos.

## Reglas que seguimos

1. **No se copia código.** Ni archivos, ni funciones, ni estructuras internas de
   otros launchers. Si una idea se toma de otro proyecto, se implementa de nuevo
   con nombres, diseño y estructura propios.
2. **No se copian assets.** Iconos, fuentes, texturas, sonidos y logos son
   originales o generados en tiempo de ejecución. Las portadas de la v0.1 se
   dibujan con `QPainter` a partir del título.
3. **Solo se usan formatos y APIs públicas.** VDF/ACF son formatos de archivo
   documentados públicamente. Las URLs de lanzamiento (`steam://`) son
   interfaces públicas de cada tienda.
4. **Se respetan las marcas.** Los nombres de las tiendas se usan solo para
   indicar la procedencia de un juego, sin sugerir afiliación.

## Registro de referencias

Si en el futuro se consulta el código de otro proyecto para entender un
comportamiento, se anota aquí: proyecto, fecha, qué se aprendió y cómo se
implementó de forma independiente. Nunca se copia el fragmento.

| Fecha | Proyecto | Qué se consultó | Cómo se implementó |
|---|---|---|---|
| — | — | — | — |

## Assets de terceros

- **Fuentes**: Sora y Chakra Petch, SIL Open Font License 1.1. Se incluyen los
  textos de licencia en `gamecenter/ui/fonts/OFL-*.txt`.
- **Carátulas**: se descargan en tiempo de ejecución del CDN público de Steam y
  se cachean en el equipo del usuario. No se incluyen en el repositorio ni se
  redistribuyen; son obra de sus editores y se usan solo para identificar el
  juego.
- **Resto de la interfaz**: dibujada con QPainter/QML, sin assets de terceros.
