"""Small, dependency-free translation layer for the UI.

English source strings are the keys. QML reads the whole catalog through the
``Tr`` context property (so bindings re-evaluate when the language changes) and
Python calls :func:`tr` for the messages it builds at runtime.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

LANGUAGES: tuple[tuple[str, str], ...] = (
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("pt", "Português"),
)

CODES = frozenset(code for code, _name in LANGUAGES)

TRANSLATIONS: dict[str, dict[str, str]] = {
    "es": {
        "Settings": "Ajustes",
        "FAVORITES": "FAVORITOS",
        "ALL GAMES": "TODOS LOS JUEGOS",
        "ABOUT": "ACERCA DE",
        "PLAYTIME TIMELINE": "LÍNEA DE TIEMPO",
        "All time": "Tiempo total",
        "1 session": "1 sesión",
        "%1 sessions": "%1 sesiones",
        "Loading description...": "Cargando descripción...",
        "No description available.": "No hay descripción disponible.",
        "Read more": "Leer más",
        "Show less": "Mostrar menos",
        "No sessions recorded yet.": "Aún no hay sesiones registradas.",
        "Launch the game from GameCenter to start the timeline.": (
            "Lanza el juego desde GameCenter para empezar la línea de tiempo."
        ),
        "Added to favorites": "Añadido a favoritos",
        "Removed from favorites": "Quitado de favoritos",
        "STATS": "STATS",
        "Week": "Semana",
        "Month": "Mes",
        "Year": "Año",
        "This week": "Esta semana",
        "Time Played": "Tiempo jugado",
        "Month by Month": "Mes a mes",
        "%1 as a river": "%1 como un río",
        "Your %1 so far, in review": "Tu %1 hasta ahora, en resumen",
        "Watch": "Ver",
        "Open month": "Abrir mes",
        "Days played": "Días jugados",
        "Best day": "Mejor día",
        "Sessions": "Sesiones",
        "Day by day": "Día a día",
        "%1 of %2 days": "%1 de %2 días",
        "%1-day streak": "Racha de %1 días",
        "{change}% vs {label}": "{change}% vs {label}",
        "previous week": "la semana anterior",
        "Other": "Otros",
        "No playtime in this period.": "No hay tiempo jugado en este periodo.",
        "Unknown game": "Juego desconocido",
        "Big Picture": "Big Picture",
        "BIG PICTURE": "BIG PICTURE",
        "All games": "Todos los juegos",
        "Recent": "Recientes",
        "Favorites": "Favoritos",
        "Filter": "Filtro",
        "Favorite": "Favorito",
        "Menu": "Menú",
        "Exit": "Salir",
        "Exit Big Picture?": "¿Salir de Big Picture?",
        "Exit Big Picture": "Salir de Big Picture",
        "Controller connected": "Mando conectado",
        "Keyboard & mouse": "Teclado y ratón",
        "No games in your library": "No hay juegos en tu biblioteca",
        "Launching...": "Iniciando...",
        "Couldn't launch the game.": "No se pudo iniciar el juego.",
        "Click to select · Double-click to play": (
            "Clic para seleccionar · Doble clic para jugar"
        ),
        "Back": "Atrás",
        "Select": "Seleccionar",
        "Details": "Detalles",
        "GAME PROFILE": "PERFIL DEL JUEGO",
        "STATUS": "ESTADO",
        "SCORE": "PUNTUACIÓN",
        "Edit profile": "Editar perfil",
        "Close profile": "Cerrar perfil",
        "Drag to move · Right-drag to rotate": (
            "Arrastra para mover · Botón derecho para rotar"
        ),
        "Playing": "Jugando",
        "On Going": "En curso",
        "Beaten": "Pasado",
        "Completed": "Completado",
        "Played": "Jugado",
        "Plan to Play": "Por jugar",
        "On Hold": "En pausa",
        "Not Played": "Sin jugar",
        "Abandoned": "Abandonado",
        "Not set": "Sin definir",
        "TRACEABILITY": "TRAZABILIDAD",
        "Import another entry's playtime, sessions and cover into this game.": (
            "Importa las horas, sesiones y carátula de otra entrada a este juego."
        ),
        "Source game": "Juego de origen",
        "Choose a game": "Elige un juego",
        "Hide the source after unifying": "Ocultar el origen tras unificar",
        "Avoids duplicate stats. You can restore it from Settings.": (
            "Evita estadísticas duplicadas. Puedes restaurarlo desde Ajustes."
        ),
        "Unify data": "Unificar datos",
        "No games to import.": "No hay juegos para importar.",
        "Choose a different game to import.": "Elige un juego distinto para importar.",
        "Couldn't unify the data.": "No se pudieron unificar los datos.",
        "This game was already unified into {title}.": (
            "Este juego ya se unificó en {title}."
        ),
        "{title} data imported into {target}.": (
            "Datos de {title} importados en {target}."
        ),
        "IMPORTED GAMES": "JUEGOS IMPORTADOS",
        "No entries imported yet.": "Todavía no hay entradas importadas.",
        "Merged into {title}": "Unificado en {title}",
        "Imported": "Importado",
        "Removed": "Eliminado",
        "Arc": "Arco",
        "Flat": "Plano",
        "3D Ring": "Anillo 3D",
        "Vertical Wheel": "Rueda vertical",
        "Mode": "Modo",
        "January": "Enero",
        "February": "Febrero",
        "March": "Marzo",
        "April": "Abril",
        "May": "Mayo",
        "June": "Junio",
        "July": "Julio",
        "August": "Agosto",
        "September": "Septiembre",
        "October": "Octubre",
        "November": "Noviembre",
        "December": "Diciembre",
        "{minutes} min": "{minutes} min",
        "{hours} h": "{hours} h",
        "{hours} h {minutes} min": "{hours} h {minutes} min",
        "APPEARANCE": "APARIENCIA",
        "LANGUAGE": "IDIOMA",
        "Interface language": "Idioma de la interfaz",
        "Accent colour": "Color de acento",
        "Surface colour · navbar, Ready dock and shelf": (
            "Color de superficie · barra, dock Ready y estantería"
        ),
        "Cartridge colour": "Color del cartucho",
        "Cartridge style": "Estilo del cartucho",
        "Classic": "Clásico",
        "Optional. Paste your SteamGridDB API key to choose a cover per game. "
        "It is stored in the system credential store, never in the repository.": (
            "Opcional. Pega tu clave de API de SteamGridDB para elegir una "
            "carátula por juego. Se guarda en el almacén de credenciales del "
            "sistema, nunca en el repositorio."
        ),
        "Key saved — paste a new one to replace it": (
            "Clave guardada: pega una nueva para reemplazarla"
        ),
        "Paste your SteamGridDB API key": "Pega tu clave de API de SteamGridDB",
        "Save": "Guardar",
        "Clear": "Borrar",
        "Get a key at steamgriddb.com/profile/preferences/api": (
            "Consigue una clave en steamgriddb.com/profile/preferences/api"
        ),
        "UPDATES": "ACTUALIZACIONES",
        "Last checked: %1": "Última comprobación: %1",
        "Check automatically": "Comprobar automáticamente",
        "Checking...": "Comprobando...",
        "Check now": "Comprobar ahora",
        "Checking for updates...": "Buscando actualizaciones...",
        "You're up to date.": "Estás al día.",
        "GameCenter %1 is available.": "GameCenter %1 está disponible.",
        "Update now": "Actualizar ahora",
        "GameCenter %1 · MIT": "GameCenter %1 · MIT",
        "Add a game": "Añadir un juego",
        "Pick the root folder and the executable to launch.": (
            "Elige la carpeta raíz y el ejecutable para iniciar."
        ),
        "Title": "Título",
        "Game title": "Título del juego",
        "Root folder": "Carpeta raíz",
        "No folder selected": "Ninguna carpeta seleccionada",
        "Browse...": "Examinar...",
        "Executable": "Ejecutable",
        "No executable found. Choose another folder or put the game executable "
        "at its root.": (
            "No se encontró ningún ejecutable. Elige otra carpeta o coloca el "
            "ejecutable del juego en su raíz."
        ),
        "You can choose a SteamGridDB cover later from the game's detail view.": (
            "Puedes elegir una carátula de SteamGridDB más tarde desde la vista "
            "de detalle del juego."
        ),
        "Cancel": "Cancelar",
        "Add game": "Añadir juego",
        "Choose the game folder": "Elige la carpeta del juego",
        "Choose artwork": "Elegir carátula",
        "Portrait grids from SteamGridDB": "Portadas verticales de SteamGridDB",
        "Looking for artwork...": "Buscando carátulas...",
        "Open Settings": "Abrir ajustes",
        "Try again": "Reintentar",
        "Default": "Predeterminada",
        "Showing %1 of %2 loaded options.": (
            "Mostrando %1 de %2 opciones cargadas."
        ),
        "Showing all %1 options.": "Mostrando las %1 opciones.",
        "Loading...": "Cargando...",
        "Load more": "Cargar más",
        "Ready": "Listo",
        "Inserting...": "Insertando...",
        "Play": "Jugar",
        "Installed": "Instalado",
        "Not installed": "No instalado",
        "Open folder": "Abrir carpeta",
        "Copy App ID": "Copiar App ID",
        "Choose art": "Elegir carátula",
        "No Steam library found.\nInstall a game with Steam and press F5.": (
            "No se encontró ninguna biblioteca de Steam.\n"
            "Instala un juego con Steam y pulsa F5."
        ),
        "No games match your filters.": "Ningún juego coincide con los filtros.",
        "Launch": "Iniciar",
        "Open install folder": "Abrir carpeta de instalación",
        "Cartridge color...": "Color del cartucho...",
        "Remove from library": "Quitar de la biblioteca",
        "Cartridge color": "Color del cartucho",
        "Use default": "Usar predeterminado",
        "All stores": "Todas las tiendas",
        "Local": "Local",
        "1 game": "1 juego",
        "%1 games": "%1 juegos",
        "Recently Played": "Jugados recientemente",
        "Most played": "Más jugados",
        "Size": "Tamaño",
        "Search your games": "Busca tus juegos",
        "LIBRARY": "BIBLIOTECA",
        "STORE": "TIENDA",
        "Scan Steam games": "Escanear juegos de Steam",
        "Scan Epic games": "Escanear juegos de Epic",
        "Scan GOG games": "Escanear juegos de GOG",
        "Scan Battle.net games": "Escanear juegos de Battle.net",
        "Scan Riot games": "Escanear juegos de Riot",
        "Scan all stores": "Escanear todas las tiendas",
        "Restore removed games": "Restaurar juegos quitados",
        "Add game manually...": "Añadir juego manualmente...",
        "GameCenter %1 is available - click to update": (
            "GameCenter %1 está disponible: haz clic para actualizar"
        ),
        "Update available": "Actualización disponible",
        "You have GameCenter %1. A newer version is ready to download and install.": (
            "Tienes GameCenter %1. Hay una versión más reciente lista para "
            "descargar e instalar."
        ),
        "Installer: %1": "Instalador: %1",
        "Later": "Más tarde",
        "Downloading...": "Descargando...",
        "Installing...": "Instalando...",
        "Store coming in v0.2": "Tienda disponible en la v0.2",
        "Game added to your library": "Juego añadido a tu biblioteca",
        "{minutes} min played": "{minutes} min jugados",
        "1 hour played": "1 hora jugada",
        "{hours} hours played": "{hours} horas jugadas",
        "Never played": "Nunca jugado",
        "Played today": "Jugado hoy",
        "Played yesterday": "Jugado ayer",
        "Played {days} days ago": "Jugado hace {days} días",
        "Played {months} month ago": "Jugado hace {months} mes",
        "Played {months} months ago": "Jugado hace {months} meses",
        "Played {years} year ago": "Jugado hace {years} año",
        "Played {years} years ago": "Jugado hace {years} años",
        "Never": "Nunca",
        "No update available.": "No hay actualizaciones disponibles.",
        "This release doesn't include a Windows installer.": (
            "Esta versión no incluye un instalador para Windows."
        ),
        "Downloading update...": "Descargando actualización...",
        "The update file is missing.": "Falta el archivo de actualización.",
        "Installing update. GameCenter will restart...": (
            "Instalando actualización. GameCenter se reiniciará..."
        ),
        "Update downloaded. Installing...": (
            "Actualización descargada. Instalando..."
        ),
        "Saved to the system credential store.": (
            "Guardado en el almacén de credenciales del sistema."
        ),
        "Couldn't save to the credential store.": (
            "No se pudo guardar en el almacén de credenciales."
        ),
        "Key removed.": "Clave eliminada.",
        "Add a SteamGridDB API key in Settings first.": (
            "Añade primero una clave de API de SteamGridDB en Ajustes."
        ),
        "No portrait artwork found for this game.": (
            "No se encontró carátula vertical para este juego."
        ),
        "Library rescanned: {count} game(s).": (
            "Biblioteca reescaneada: {count} juego(s)."
        ),
        "Couldn't scan {label}: {error}": "No se pudo escanear {label}: {error}",
        "{label}: {count} game(s) found.": (
            "{label}: {count} juego(s) encontrados."
        ),
        "Restored {count} removed game(s).": (
            "Restaurados {count} juego(s) quitados."
        ),
        "No removed games to restore.": "No hay juegos quitados para restaurar.",
        "This game has no install folder.": (
            "Este juego no tiene carpeta de instalación."
        ),
        "Removed {title} from the library.": (
            "Se quitó {title} de la biblioteca."
        ),
        "Give the game a title.": "Ponle un título al juego.",
        "Choose a valid root folder.": "Elige una carpeta raíz válida.",
        "No executable found in that folder.": (
            "No se encontró ningún ejecutable en esa carpeta."
        ),
        "That executable doesn't exist.": "Ese ejecutable no existe.",
        "Don't know how to start {title}.": "No se cómo iniciar {title}.",
        "No releases found on GitHub.": "No se encontraron versiones en GitHub.",
        "GitHub answered with an error ({code}).": (
            "GitHub respondió con un error ({code})."
        ),
        "Couldn't reach GitHub.": "No se pudo contactar con GitHub.",
        "GitHub sent an unexpected answer.": "GitHub envió una respuesta inesperada.",
        "This release doesn't include an installer.": (
            "Esta versión no incluye un instalador."
        ),
        "Couldn't prepare the update folder.": (
            "No se pudo preparar la carpeta de actualización."
        ),
        "The update download was incomplete.": (
            "La descarga de la actualización quedó incompleta."
        ),
        "The update file failed its integrity check.": (
            "El archivo de actualización no superó la comprobación de integridad."
        ),
        "Couldn't download the update.": "No se pudo descargar la actualización.",
        "Automatic installation is only available on Windows.": (
            "La instalación automática solo está disponible en Windows."
        ),
        "The downloaded installer is missing.": "Falta el instalador descargado.",
        "Couldn't start the installer.": "No se pudo iniciar el instalador.",
        "SteamGridDB rejected the API key.": (
            "SteamGridDB rechazó la clave de API."
        ),
        "SteamGridDB answered with an error ({code}).": (
            "SteamGridDB respondió con un error ({code})."
        ),
        "Couldn't reach SteamGridDB.": "No se pudo contactar con SteamGridDB.",
        "SteamGridDB sent an unexpected answer.": (
            "SteamGridDB envió una respuesta inesperada."
        ),
        "SteamGridDB didn't return any results.": (
            "SteamGridDB no devolvió ningún resultado."
        ),
        "Couldn't download that artwork.": "No se pudo descargar esa carátula.",
        "That artwork came back empty.": "Esa carátula llegó vacía.",
    },
    "fr": {
        "Settings": "Paramètres",
        "FAVORITES": "FAVORIS",
        "ALL GAMES": "TOUS LES JEUX",
        "ABOUT": "À PROPOS",
        "PLAYTIME TIMELINE": "CHRONOLOGIE",
        "All time": "Temps total",
        "1 session": "1 session",
        "%1 sessions": "%1 sessions",
        "Loading description...": "Chargement de la description...",
        "No description available.": "Aucune description disponible.",
        "Read more": "Lire plus",
        "Show less": "Afficher moins",
        "No sessions recorded yet.": "Aucune session enregistrée.",
        "Launch the game from GameCenter to start the timeline.": (
            "Lancez le jeu depuis GameCenter pour démarrer la chronologie."
        ),
        "Added to favorites": "Ajouté aux favoris",
        "Removed from favorites": "Retiré des favoris",
        "STATS": "STATS",
        "Week": "Semaine",
        "Month": "Mois",
        "Year": "Année",
        "This week": "Cette semaine",
        "Time Played": "Temps joué",
        "Month by Month": "Mois par mois",
        "%1 as a river": "%1 comme une rivière",
        "Your %1 so far, in review": "Votre %1 jusqu'ici, en revue",
        "Watch": "Regarder",
        "Open month": "Ouvrir le mois",
        "Days played": "Jours joués",
        "Best day": "Meilleur jour",
        "Sessions": "Sessions",
        "Day by day": "Jour par jour",
        "%1 of %2 days": "%1 sur %2 jours",
        "%1-day streak": "Série de %1 jours",
        "{change}% vs {label}": "{change}% vs {label}",
        "previous week": "la semaine précédente",
        "Other": "Autres",
        "No playtime in this period.": "Aucun temps de jeu sur cette période.",
        "Unknown game": "Jeu inconnu",
        "Big Picture": "Big Picture",
        "BIG PICTURE": "BIG PICTURE",
        "All games": "Tous les jeux",
        "Recent": "Récents",
        "Favorites": "Favoris",
        "Filter": "Filtre",
        "Favorite": "Favori",
        "Menu": "Menu",
        "Exit": "Quitter",
        "Exit Big Picture?": "Quitter Big Picture ?",
        "Exit Big Picture": "Quitter Big Picture",
        "Controller connected": "Manette connectée",
        "Keyboard & mouse": "Clavier et souris",
        "No games in your library": "Aucun jeu dans votre bibliothèque",
        "Launching...": "Lancement...",
        "Couldn't launch the game.": "Impossible de lancer le jeu.",
        "Click to select · Double-click to play": (
            "Cliquez pour sélectionner · Double-cliquez pour jouer"
        ),
        "Back": "Retour",
        "Select": "Sélectionner",
        "Details": "Détails",
        "GAME PROFILE": "PROFIL DU JEU",
        "STATUS": "STATUT",
        "SCORE": "NOTE",
        "Edit profile": "Modifier le profil",
        "Close profile": "Fermer le profil",
        "Drag to move · Right-drag to rotate": (
            "Glisser pour déplacer · Clic droit pour pivoter"
        ),
        "Playing": "En cours",
        "On Going": "En progression",
        "Beaten": "Terminé",
        "Completed": "Complété",
        "Played": "Joué",
        "Plan to Play": "À jouer",
        "On Hold": "En pause",
        "Not Played": "Non joué",
        "Abandoned": "Abandonné",
        "Not set": "Non défini",
        "TRACEABILITY": "TRAÇABILITÉ",
        "Import another entry's playtime, sessions and cover into this game.": (
            "Importez les heures, sessions et la jaquette d'une autre entrée "
            "dans ce jeu."
        ),
        "Source game": "Jeu source",
        "Choose a game": "Choisir un jeu",
        "Hide the source after unifying": "Masquer la source après l'unification",
        "Avoids duplicate stats. You can restore it from Settings.": (
            "Évite les statistiques en double. Vous pouvez la restaurer dans "
            "les Réglages."
        ),
        "Unify data": "Unifier les données",
        "No games to import.": "Aucun jeu à importer.",
        "Choose a different game to import.": "Choisissez un autre jeu à importer.",
        "Couldn't unify the data.": "Impossible d'unifier les données.",
        "This game was already unified into {title}.": (
            "Ce jeu a déjà été unifié dans {title}."
        ),
        "{title} data imported into {target}.": (
            "Données de {title} importées dans {target}."
        ),
        "IMPORTED GAMES": "JEUX IMPORTÉS",
        "No entries imported yet.": "Aucune entrée importée pour l'instant.",
        "Merged into {title}": "Unifié dans {title}",
        "Imported": "Importé",
        "Removed": "Retiré",
        "Arc": "Arc",
        "Flat": "Plat",
        "3D Ring": "Anneau 3D",
        "Vertical Wheel": "Roue verticale",
        "Mode": "Mode",
        "January": "Janvier",
        "February": "Février",
        "March": "Mars",
        "April": "Avril",
        "May": "Mai",
        "June": "Juin",
        "July": "Juillet",
        "August": "Août",
        "September": "Septembre",
        "October": "Octobre",
        "November": "Novembre",
        "December": "Décembre",
        "{minutes} min": "{minutes} min",
        "{hours} h": "{hours} h",
        "{hours} h {minutes} min": "{hours} h {minutes} min",
        "APPEARANCE": "APPARENCE",
        "LANGUAGE": "LANGUE",
        "Interface language": "Langue de l'interface",
        "Accent colour": "Couleur d'accent",
        "Surface colour · navbar, Ready dock and shelf": (
            "Couleur de surface · barre, dock Ready et étagère"
        ),
        "Cartridge colour": "Couleur de la cartouche",
        "Cartridge style": "Style de cartouche",
        "Classic": "Classique",
        "Optional. Paste your SteamGridDB API key to choose a cover per game. "
        "It is stored in the system credential store, never in the repository.": (
            "Facultatif. Collez votre clé API SteamGridDB pour choisir une "
            "jaquette par jeu. Elle est stockée dans le gestionnaire "
            "d'identifiants du système, jamais dans le dépôt."
        ),
        "Key saved — paste a new one to replace it": (
            "Clé enregistrée — collez-en une nouvelle pour la remplacer"
        ),
        "Paste your SteamGridDB API key": "Collez votre clé API SteamGridDB",
        "Save": "Enregistrer",
        "Clear": "Effacer",
        "Get a key at steamgriddb.com/profile/preferences/api": (
            "Obtenez une clé sur steamgriddb.com/profile/preferences/api"
        ),
        "UPDATES": "MISES À JOUR",
        "Last checked: %1": "Dernière vérification : %1",
        "Check automatically": "Vérifier automatiquement",
        "Checking...": "Vérification...",
        "Check now": "Vérifier maintenant",
        "Checking for updates...": "Recherche de mises à jour...",
        "You're up to date.": "Vous êtes à jour.",
        "GameCenter %1 is available.": "GameCenter %1 est disponible.",
        "Update now": "Mettre à jour",
        "GameCenter %1 · MIT": "GameCenter %1 · MIT",
        "Add a game": "Ajouter un jeu",
        "Pick the root folder and the executable to launch.": (
            "Choisissez le dossier racine et l'exécutable à lancer."
        ),
        "Title": "Titre",
        "Game title": "Titre du jeu",
        "Root folder": "Dossier racine",
        "No folder selected": "Aucun dossier sélectionné",
        "Browse...": "Parcourir...",
        "Executable": "Exécutable",
        "No executable found. Choose another folder or put the game executable "
        "at its root.": (
            "Aucun exécutable trouvé. Choisissez un autre dossier ou placez "
            "l'exécutable du jeu à sa racine."
        ),
        "You can choose a SteamGridDB cover later from the game's detail view.": (
            "Vous pourrez choisir une jaquette SteamGridDB plus tard depuis la "
            "fiche du jeu."
        ),
        "Cancel": "Annuler",
        "Add game": "Ajouter le jeu",
        "Choose the game folder": "Choisir le dossier du jeu",
        "Choose artwork": "Choisir une jaquette",
        "Portrait grids from SteamGridDB": "Jaquettes verticales de SteamGridDB",
        "Looking for artwork...": "Recherche de jaquettes...",
        "Open Settings": "Ouvrir les paramètres",
        "Try again": "Réessayer",
        "Default": "Par défaut",
        "Showing %1 of %2 loaded options.": (
            "Affichage de %1 sur %2 options chargées."
        ),
        "Showing all %1 options.": "Affichage des %1 options.",
        "Loading...": "Chargement...",
        "Load more": "Charger plus",
        "Ready": "Prêt",
        "Inserting...": "Insertion...",
        "Play": "Jouer",
        "Installed": "Installé",
        "Not installed": "Non installé",
        "Open folder": "Ouvrir le dossier",
        "Copy App ID": "Copier l'App ID",
        "Choose art": "Choisir la jaquette",
        "No Steam library found.\nInstall a game with Steam and press F5.": (
            "Aucune bibliothèque Steam trouvée.\n"
            "Installez un jeu avec Steam et appuyez sur F5."
        ),
        "No games match your filters.": "Aucun jeu ne correspond aux filtres.",
        "Launch": "Lancer",
        "Open install folder": "Ouvrir le dossier d'installation",
        "Cartridge color...": "Couleur de la cartouche...",
        "Remove from library": "Retirer de la bibliothèque",
        "Cartridge color": "Couleur de la cartouche",
        "Use default": "Utiliser par défaut",
        "All stores": "Toutes les boutiques",
        "Local": "Local",
        "1 game": "1 jeu",
        "%1 games": "%1 jeux",
        "Recently Played": "Joués récemment",
        "Most played": "Les plus joués",
        "Size": "Taille",
        "Search your games": "Recherchez vos jeux",
        "LIBRARY": "BIBLIOTHÈQUE",
        "STORE": "BOUTIQUE",
        "Scan Steam games": "Scanner les jeux Steam",
        "Scan Epic games": "Scanner les jeux Epic",
        "Scan GOG games": "Scanner les jeux GOG",
        "Scan Battle.net games": "Scanner les jeux Battle.net",
        "Scan Riot games": "Scanner les jeux Riot",
        "Scan all stores": "Scanner toutes les boutiques",
        "Restore removed games": "Restaurer les jeux retirés",
        "Add game manually...": "Ajouter un jeu manuellement...",
        "GameCenter %1 is available - click to update": (
            "GameCenter %1 est disponible - cliquez pour mettre à jour"
        ),
        "Update available": "Mise à jour disponible",
        "You have GameCenter %1. A newer version is ready to download and install.": (
            "Vous avez GameCenter %1. Une version plus récente est prête à être "
            "téléchargée et installée."
        ),
        "Installer: %1": "Programme d'installation : %1",
        "Later": "Plus tard",
        "Downloading...": "Téléchargement...",
        "Installing...": "Installation...",
        "Store coming in v0.2": "Boutique disponible en v0.2",
        "Game added to your library": "Jeu ajouté à votre bibliothèque",
        "{minutes} min played": "{minutes} min jouées",
        "1 hour played": "1 heure jouée",
        "{hours} hours played": "{hours} heures jouées",
        "Never played": "Jamais joué",
        "Played today": "Joué aujourd'hui",
        "Played yesterday": "Joué hier",
        "Played {days} days ago": "Joué il y a {days} jours",
        "Played {months} month ago": "Joué il y a {months} mois",
        "Played {months} months ago": "Joué il y a {months} mois",
        "Played {years} year ago": "Joué il y a {years} an",
        "Played {years} years ago": "Joué il y a {years} ans",
        "Never": "Jamais",
        "No update available.": "Aucune mise à jour disponible.",
        "This release doesn't include a Windows installer.": (
            "Cette version n'inclut pas d'installateur Windows."
        ),
        "Downloading update...": "Téléchargement de la mise à jour...",
        "The update file is missing.": "Le fichier de mise à jour est manquant.",
        "Installing update. GameCenter will restart...": (
            "Installation de la mise à jour. GameCenter va redémarrer..."
        ),
        "Update downloaded. Installing...": (
            "Mise à jour téléchargée. Installation..."
        ),
        "Saved to the system credential store.": (
            "Enregistré dans le gestionnaire d'identifiants du système."
        ),
        "Couldn't save to the credential store.": (
            "Impossible d'enregistrer dans le gestionnaire d'identifiants."
        ),
        "Key removed.": "Clé supprimée.",
        "Add a SteamGridDB API key in Settings first.": (
            "Ajoutez d'abord une clé API SteamGridDB dans les paramètres."
        ),
        "No portrait artwork found for this game.": (
            "Aucune jaquette verticale trouvée pour ce jeu."
        ),
        "Library rescanned: {count} game(s).": (
            "Bibliothèque rescannée : {count} jeu(x)."
        ),
        "Couldn't scan {label}: {error}": "Impossible de scanner {label} : {error}",
        "{label}: {count} game(s) found.": (
            "{label} : {count} jeu(x) trouvé(s)."
        ),
        "Restored {count} removed game(s).": (
            "{count} jeu(x) retiré(s) restauré(s)."
        ),
        "No removed games to restore.": "Aucun jeu retiré à restaurer.",
        "This game has no install folder.": (
            "Ce jeu n'a pas de dossier d'installation."
        ),
        "Removed {title} from the library.": (
            "{title} a été retiré de la bibliothèque."
        ),
        "Give the game a title.": "Donnez un titre au jeu.",
        "Choose a valid root folder.": "Choisissez un dossier racine valide.",
        "No executable found in that folder.": (
            "Aucun exécutable trouvé dans ce dossier."
        ),
        "That executable doesn't exist.": "Cet exécutable n'existe pas.",
        "Don't know how to start {title}.": "Impossible de démarrer {title}.",
        "No releases found on GitHub.": "Aucune version trouvée sur GitHub.",
        "GitHub answered with an error ({code}).": (
            "GitHub a répondu avec une erreur ({code})."
        ),
        "Couldn't reach GitHub.": "Impossible de joindre GitHub.",
        "GitHub sent an unexpected answer.": "GitHub a envoyé une réponse inattendue.",
        "This release doesn't include an installer.": (
            "Cette version n'inclut pas d'installateur."
        ),
        "Couldn't prepare the update folder.": (
            "Impossible de préparer le dossier de mise à jour."
        ),
        "The update download was incomplete.": (
            "Le téléchargement de la mise à jour est incomplet."
        ),
        "The update file failed its integrity check.": (
            "Le fichier de mise à jour a échoué au contrôle d'intégrité."
        ),
        "Couldn't download the update.": (
            "Impossible de télécharger la mise à jour."
        ),
        "Automatic installation is only available on Windows.": (
            "L'installation automatique n'est disponible que sous Windows."
        ),
        "The downloaded installer is missing.": (
            "Le programme d'installation téléchargé est manquant."
        ),
        "Couldn't start the installer.": (
            "Impossible de lancer le programme d'installation."
        ),
        "SteamGridDB rejected the API key.": "SteamGridDB a rejeté la clé API.",
        "SteamGridDB answered with an error ({code}).": (
            "SteamGridDB a répondu avec une erreur ({code})."
        ),
        "Couldn't reach SteamGridDB.": "Impossible de joindre SteamGridDB.",
        "SteamGridDB sent an unexpected answer.": (
            "SteamGridDB a envoyé une réponse inattendue."
        ),
        "SteamGridDB didn't return any results.": (
            "SteamGridDB n'a renvoyé aucun résultat."
        ),
        "Couldn't download that artwork.": (
            "Impossible de télécharger cette jaquette."
        ),
        "That artwork came back empty.": "Cette jaquette est revenue vide.",
    },
    "de": {
        "Settings": "Einstellungen",
        "FAVORITES": "FAVORITEN",
        "ALL GAMES": "ALLE SPIELE",
        "ABOUT": "ÜBER",
        "PLAYTIME TIMELINE": "SPIELZEIT-VERLAUF",
        "All time": "Gesamtzeit",
        "1 session": "1 Sitzung",
        "%1 sessions": "%1 Sitzungen",
        "Loading description...": "Beschreibung wird geladen...",
        "No description available.": "Keine Beschreibung verfügbar.",
        "Read more": "Mehr lesen",
        "Show less": "Weniger anzeigen",
        "No sessions recorded yet.": "Noch keine Sitzungen aufgezeichnet.",
        "Launch the game from GameCenter to start the timeline.": (
            "Starte das Spiel aus GameCenter, um den Verlauf zu beginnen."
        ),
        "Added to favorites": "Zu Favoriten hinzugefügt",
        "Removed from favorites": "Aus Favoriten entfernt",
        "STATS": "STATS",
        "Week": "Woche",
        "Month": "Monat",
        "Year": "Jahr",
        "This week": "Diese Woche",
        "Time Played": "Spielzeit",
        "Month by Month": "Monat für Monat",
        "%1 as a river": "%1 als Fluss",
        "Your %1 so far, in review": "Dein %1 bisher, im Rückblick",
        "Watch": "Ansehen",
        "Open month": "Monat öffnen",
        "Days played": "Gespielte Tage",
        "Best day": "Bester Tag",
        "Sessions": "Sitzungen",
        "Day by day": "Tag für Tag",
        "%1 of %2 days": "%1 von %2 Tagen",
        "%1-day streak": "%1-Tage-Serie",
        "{change}% vs {label}": "{change}% vs {label}",
        "previous week": "die Vorwoche",
        "Other": "Andere",
        "No playtime in this period.": "In diesem Zeitraum wurde nicht gespielt.",
        "Unknown game": "Unbekanntes Spiel",
        "Big Picture": "Big Picture",
        "BIG PICTURE": "BIG PICTURE",
        "All games": "Alle Spiele",
        "Recent": "Neueste",
        "Favorites": "Favoriten",
        "Filter": "Filter",
        "Favorite": "Favorit",
        "Menu": "Menü",
        "Exit": "Beenden",
        "Exit Big Picture?": "Big Picture beenden?",
        "Exit Big Picture": "Big Picture beenden",
        "Controller connected": "Controller verbunden",
        "Keyboard & mouse": "Tastatur und Maus",
        "No games in your library": "Keine Spiele in deiner Bibliothek",
        "Launching...": "Wird gestartet...",
        "Couldn't launch the game.": "Das Spiel konnte nicht gestartet werden.",
        "Click to select · Double-click to play": (
            "Klicken zum Auswählen · Doppelklick zum Spielen"
        ),
        "Back": "Zurück",
        "Select": "Auswählen",
        "Details": "Details",
        "GAME PROFILE": "SPIELPROFIL",
        "STATUS": "STATUS",
        "SCORE": "WERTUNG",
        "Edit profile": "Profil bearbeiten",
        "Close profile": "Profil schließen",
        "Drag to move · Right-drag to rotate": (
            "Ziehen zum Verschieben · Rechtsklick zum Drehen"
        ),
        "Playing": "Spielend",
        "On Going": "Laufend",
        "Beaten": "Geschafft",
        "Completed": "Abgeschlossen",
        "Played": "Gespielt",
        "Plan to Play": "Geplant",
        "On Hold": "Pausiert",
        "Not Played": "Nicht gespielt",
        "Abandoned": "Abgebrochen",
        "Not set": "Nicht festgelegt",
        "TRACEABILITY": "NACHVOLLZIEHBARKEIT",
        "Import another entry's playtime, sessions and cover into this game.": (
            "Importiere Spielzeit, Sitzungen und Cover eines anderen Eintrags "
            "in dieses Spiel."
        ),
        "Source game": "Quellspiel",
        "Choose a game": "Spiel auswählen",
        "Hide the source after unifying": (
            "Quelle nach dem Zusammenführen ausblenden"
        ),
        "Avoids duplicate stats. You can restore it from Settings.": (
            "Vermeidet doppelte Statistiken. Du kannst sie in den Einstellungen "
            "wiederherstellen."
        ),
        "Unify data": "Daten zusammenführen",
        "No games to import.": "Keine Spiele zum Importieren.",
        "Choose a different game to import.": (
            "Wähle ein anderes Spiel zum Importieren."
        ),
        "Couldn't unify the data.": (
            "Die Daten konnten nicht zusammengeführt werden."
        ),
        "This game was already unified into {title}.": (
            "Dieses Spiel wurde bereits in {title} zusammengeführt."
        ),
        "{title} data imported into {target}.": (
            "Daten von {title} in {target} importiert."
        ),
        "IMPORTED GAMES": "IMPORTIERTE SPIELE",
        "No entries imported yet.": "Noch keine Einträge importiert.",
        "Merged into {title}": "Zusammengeführt in {title}",
        "Imported": "Importiert",
        "Removed": "Entfernt",
        "Arc": "Bogen",
        "Flat": "Flach",
        "3D Ring": "3D-Ring",
        "Vertical Wheel": "Vertikales Rad",
        "Mode": "Modus",
        "January": "Januar",
        "February": "Februar",
        "March": "März",
        "April": "April",
        "May": "Mai",
        "June": "Juni",
        "July": "Juli",
        "August": "August",
        "September": "September",
        "October": "Oktober",
        "November": "November",
        "December": "Dezember",
        "{minutes} min": "{minutes} Min.",
        "{hours} h": "{hours} Std.",
        "{hours} h {minutes} min": "{hours} Std. {minutes} Min.",
        "APPEARANCE": "AUSSEHEN",
        "LANGUAGE": "SPRACHE",
        "Interface language": "Sprache der Oberfläche",
        "Accent colour": "Akzentfarbe",
        "Surface colour · navbar, Ready dock and shelf": (
            "Oberflächenfarbe · Leiste, Ready-Dock und Regal"
        ),
        "Cartridge colour": "Kassettenfarbe",
        "Cartridge style": "Kassettenstil",
        "Classic": "Klassisch",
        "Optional. Paste your SteamGridDB API key to choose a cover per game. "
        "It is stored in the system credential store, never in the repository.": (
            "Optional. Füge deinen SteamGridDB-API-Schlüssel ein, um pro Spiel "
            "ein Cover zu wählen. Er wird im Anmeldeinformationsspeicher des "
            "Systems gespeichert, nie im Repository."
        ),
        "Key saved — paste a new one to replace it": (
            "Schlüssel gespeichert – füge einen neuen ein, um ihn zu ersetzen"
        ),
        "Paste your SteamGridDB API key": "SteamGridDB-API-Schlüssel einfügen",
        "Save": "Speichern",
        "Clear": "Löschen",
        "Get a key at steamgriddb.com/profile/preferences/api": (
            "Schlüssel unter steamgriddb.com/profile/preferences/api erhalten"
        ),
        "UPDATES": "UPDATES",
        "Last checked: %1": "Zuletzt geprüft: %1",
        "Check automatically": "Automatisch prüfen",
        "Checking...": "Prüfe...",
        "Check now": "Jetzt prüfen",
        "Checking for updates...": "Suche nach Updates...",
        "You're up to date.": "Du bist auf dem neuesten Stand.",
        "GameCenter %1 is available.": "GameCenter %1 ist verfügbar.",
        "Update now": "Jetzt aktualisieren",
        "GameCenter %1 · MIT": "GameCenter %1 · MIT",
        "Add a game": "Spiel hinzufügen",
        "Pick the root folder and the executable to launch.": (
            "Wähle den Stammordner und die auszuführende Datei."
        ),
        "Title": "Titel",
        "Game title": "Spieltitel",
        "Root folder": "Stammordner",
        "No folder selected": "Kein Ordner ausgewählt",
        "Browse...": "Durchsuchen...",
        "Executable": "Ausführbare Datei",
        "No executable found. Choose another folder or put the game executable "
        "at its root.": (
            "Keine ausführbare Datei gefunden. Wähle einen anderen Ordner oder "
            "lege die Spieldatei im Stammordner ab."
        ),
        "You can choose a SteamGridDB cover later from the game's detail view.": (
            "Du kannst später in der Spielansicht ein SteamGridDB-Cover wählen."
        ),
        "Cancel": "Abbrechen",
        "Add game": "Spiel hinzufügen",
        "Choose the game folder": "Spielordner wählen",
        "Choose artwork": "Artwork wählen",
        "Portrait grids from SteamGridDB": "Hochformat-Cover von SteamGridDB",
        "Looking for artwork...": "Suche Artwork...",
        "Open Settings": "Einstellungen öffnen",
        "Try again": "Erneut versuchen",
        "Default": "Standard",
        "Showing %1 of %2 loaded options.": (
            "Zeige %1 von %2 geladenen Optionen."
        ),
        "Showing all %1 options.": "Zeige alle %1 Optionen.",
        "Loading...": "Lade...",
        "Load more": "Mehr laden",
        "Ready": "Bereit",
        "Inserting...": "Wird eingefügt...",
        "Play": "Spielen",
        "Installed": "Installiert",
        "Not installed": "Nicht installiert",
        "Open folder": "Ordner öffnen",
        "Copy App ID": "App-ID kopieren",
        "Choose art": "Artwork wählen",
        "No Steam library found.\nInstall a game with Steam and press F5.": (
            "Keine Steam-Bibliothek gefunden.\n"
            "Installiere ein Spiel mit Steam und drücke F5."
        ),
        "No games match your filters.": "Keine Spiele entsprechen den Filtern.",
        "Launch": "Starten",
        "Open install folder": "Installationsordner öffnen",
        "Cartridge color...": "Kassettenfarbe...",
        "Remove from library": "Aus Bibliothek entfernen",
        "Cartridge color": "Kassettenfarbe",
        "Use default": "Standard verwenden",
        "All stores": "Alle Stores",
        "Local": "Lokal",
        "1 game": "1 Spiel",
        "%1 games": "%1 Spiele",
        "Recently Played": "Zuletzt gespielt",
        "Most played": "Meistgespielt",
        "Size": "Größe",
        "Search your games": "Spiele durchsuchen",
        "LIBRARY": "BIBLIOTHEK",
        "STORE": "STORE",
        "Scan Steam games": "Steam-Spiele scannen",
        "Scan Epic games": "Epic-Spiele scannen",
        "Scan GOG games": "GOG-Spiele scannen",
        "Scan Battle.net games": "Battle.net-Spiele scannen",
        "Scan Riot games": "Riot-Spiele scannen",
        "Scan all stores": "Alle Stores scannen",
        "Restore removed games": "Entfernte Spiele wiederherstellen",
        "Add game manually...": "Spiel manuell hinzufügen...",
        "GameCenter %1 is available - click to update": (
            "GameCenter %1 ist verfügbar – zum Aktualisieren klicken"
        ),
        "Update available": "Update verfügbar",
        "You have GameCenter %1. A newer version is ready to download and install.": (
            "Du hast GameCenter %1. Eine neuere Version kann heruntergeladen "
            "und installiert werden."
        ),
        "Installer: %1": "Installer: %1",
        "Later": "Später",
        "Downloading...": "Wird heruntergeladen...",
        "Installing...": "Wird installiert...",
        "Store coming in v0.2": "Store kommt in v0.2",
        "Game added to your library": "Spiel zur Bibliothek hinzugefügt",
        "{minutes} min played": "{minutes} Min. gespielt",
        "1 hour played": "1 Stunde gespielt",
        "{hours} hours played": "{hours} Stunden gespielt",
        "Never played": "Nie gespielt",
        "Played today": "Heute gespielt",
        "Played yesterday": "Gestern gespielt",
        "Played {days} days ago": "Vor {days} Tagen gespielt",
        "Played {months} month ago": "Vor {months} Monat gespielt",
        "Played {months} months ago": "Vor {months} Monaten gespielt",
        "Played {years} year ago": "Vor {years} Jahr gespielt",
        "Played {years} years ago": "Vor {years} Jahren gespielt",
        "Never": "Nie",
        "No update available.": "Kein Update verfügbar.",
        "This release doesn't include a Windows installer.": (
            "Dieses Release enthält keinen Windows-Installer."
        ),
        "Downloading update...": "Update wird heruntergeladen...",
        "The update file is missing.": "Die Update-Datei fehlt.",
        "Installing update. GameCenter will restart...": (
            "Update wird installiert. GameCenter wird neu gestartet..."
        ),
        "Update downloaded. Installing...": (
            "Update heruntergeladen. Wird installiert..."
        ),
        "Saved to the system credential store.": (
            "Im Anmeldeinformationsspeicher des Systems gespeichert."
        ),
        "Couldn't save to the credential store.": (
            "Speichern im Anmeldeinformationsspeicher nicht möglich."
        ),
        "Key removed.": "Schlüssel entfernt.",
        "Add a SteamGridDB API key in Settings first.": (
            "Füge zuerst einen SteamGridDB-API-Schlüssel in den Einstellungen hinzu."
        ),
        "No portrait artwork found for this game.": (
            "Kein Hochformat-Artwork für dieses Spiel gefunden."
        ),
        "Library rescanned: {count} game(s).": (
            "Bibliothek neu gescannt: {count} Spiel(e)."
        ),
        "Couldn't scan {label}: {error}": (
            "{label} konnte nicht gescannt werden: {error}"
        ),
        "{label}: {count} game(s) found.": "{label}: {count} Spiel(e) gefunden.",
        "Restored {count} removed game(s).": (
            "{count} entfernte(s) Spiel(e) wiederhergestellt."
        ),
        "No removed games to restore.": (
            "Keine entfernten Spiele zum Wiederherstellen."
        ),
        "This game has no install folder.": (
            "Dieses Spiel hat keinen Installationsordner."
        ),
        "Removed {title} from the library.": (
            "{title} wurde aus der Bibliothek entfernt."
        ),
        "Give the game a title.": "Gib dem Spiel einen Titel.",
        "Choose a valid root folder.": "Wähle einen gültigen Stammordner.",
        "No executable found in that folder.": (
            "In diesem Ordner wurde keine ausführbare Datei gefunden."
        ),
        "That executable doesn't exist.": (
            "Diese ausführbare Datei existiert nicht."
        ),
        "Don't know how to start {title}.": "{title} kann nicht gestartet werden.",
        "No releases found on GitHub.": "Keine Releases auf GitHub gefunden.",
        "GitHub answered with an error ({code}).": (
            "GitHub antwortete mit einem Fehler ({code})."
        ),
        "Couldn't reach GitHub.": "GitHub konnte nicht erreicht werden.",
        "GitHub sent an unexpected answer.": (
            "GitHub hat eine unerwartete Antwort gesendet."
        ),
        "This release doesn't include an installer.": (
            "Dieses Release enthält keinen Installer."
        ),
        "Couldn't prepare the update folder.": (
            "Der Update-Ordner konnte nicht vorbereitet werden."
        ),
        "The update download was incomplete.": (
            "Der Update-Download war unvollständig."
        ),
        "The update file failed its integrity check.": (
            "Die Update-Datei hat die Integritätsprüfung nicht bestanden."
        ),
        "Couldn't download the update.": (
            "Das Update konnte nicht heruntergeladen werden."
        ),
        "Automatic installation is only available on Windows.": (
            "Die automatische Installation ist nur unter Windows verfügbar."
        ),
        "The downloaded installer is missing.": (
            "Der heruntergeladene Installer fehlt."
        ),
        "Couldn't start the installer.": (
            "Der Installer konnte nicht gestartet werden."
        ),
        "SteamGridDB rejected the API key.": (
            "SteamGridDB hat den API-Schlüssel abgelehnt."
        ),
        "SteamGridDB answered with an error ({code}).": (
            "SteamGridDB antwortete mit einem Fehler ({code})."
        ),
        "Couldn't reach SteamGridDB.": (
            "SteamGridDB konnte nicht erreicht werden."
        ),
        "SteamGridDB sent an unexpected answer.": (
            "SteamGridDB hat eine unerwartete Antwort gesendet."
        ),
        "SteamGridDB didn't return any results.": (
            "SteamGridDB hat keine Ergebnisse zurückgegeben."
        ),
        "Couldn't download that artwork.": (
            "Dieses Artwork konnte nicht heruntergeladen werden."
        ),
        "That artwork came back empty.": "Dieses Artwork kam leer zurück.",
    },
    "it": {
        "Settings": "Impostazioni",
        "FAVORITES": "PREFERITI",
        "ALL GAMES": "TUTTI I GIOCHI",
        "ABOUT": "INFORMAZIONI",
        "PLAYTIME TIMELINE": "CRONOLOGIA",
        "All time": "Tempo totale",
        "1 session": "1 sessione",
        "%1 sessions": "%1 sessioni",
        "Loading description...": "Caricamento descrizione...",
        "No description available.": "Nessuna descrizione disponibile.",
        "Read more": "Leggi di più",
        "Show less": "Mostra meno",
        "No sessions recorded yet.": "Nessuna sessione registrata.",
        "Launch the game from GameCenter to start the timeline.": (
            "Avvia il gioco da GameCenter per iniziare la cronologia."
        ),
        "Added to favorites": "Aggiunto ai preferiti",
        "Removed from favorites": "Rimosso dai preferiti",
        "STATS": "STATS",
        "Week": "Settimana",
        "Month": "Mese",
        "Year": "Anno",
        "This week": "Questa settimana",
        "Time Played": "Tempo giocato",
        "Month by Month": "Mese per mese",
        "%1 as a river": "%1 come un fiume",
        "Your %1 so far, in review": "Il tuo %1 finora, in review",
        "Watch": "Guarda",
        "Open month": "Apri mese",
        "Days played": "Giorni giocati",
        "Best day": "Miglior giorno",
        "Sessions": "Sessioni",
        "Day by day": "Giorno per giorno",
        "%1 of %2 days": "%1 di %2 giorni",
        "%1-day streak": "Serie di %1 giorni",
        "{change}% vs {label}": "{change}% vs {label}",
        "previous week": "la settimana precedente",
        "Other": "Altri",
        "No playtime in this period.": "Nessun tempo di gioco in questo periodo.",
        "Unknown game": "Gioco sconosciuto",
        "Big Picture": "Big Picture",
        "BIG PICTURE": "BIG PICTURE",
        "All games": "Tutti i giochi",
        "Recent": "Recenti",
        "Favorites": "Preferiti",
        "Filter": "Filtro",
        "Favorite": "Preferito",
        "Menu": "Menu",
        "Exit": "Esci",
        "Exit Big Picture?": "Uscire da Big Picture?",
        "Exit Big Picture": "Esci da Big Picture",
        "Controller connected": "Controller connesso",
        "Keyboard & mouse": "Tastiera e mouse",
        "No games in your library": "Nessun gioco nella tua libreria",
        "Launching...": "Avvio...",
        "Couldn't launch the game.": "Impossibile avviare il gioco.",
        "Click to select · Double-click to play": (
            "Clicca per selezionare · Doppio clic per giocare"
        ),
        "Back": "Indietro",
        "Select": "Seleziona",
        "Details": "Dettagli",
        "GAME PROFILE": "PROFILO DEL GIOCO",
        "STATUS": "STATO",
        "SCORE": "PUNTEGGIO",
        "Edit profile": "Modifica profilo",
        "Close profile": "Chiudi profilo",
        "Drag to move · Right-drag to rotate": (
            "Trascina per spostare · Tasto destro per ruotare"
        ),
        "Playing": "In gioco",
        "On Going": "In corso",
        "Beaten": "Superato",
        "Completed": "Completato",
        "Played": "Giocato",
        "Plan to Play": "Da giocare",
        "On Hold": "In pausa",
        "Not Played": "Non giocato",
        "Abandoned": "Abbandonato",
        "Not set": "Non impostato",
        "TRACEABILITY": "TRACCIABILITÀ",
        "Import another entry's playtime, sessions and cover into this game.": (
            "Importa ore, sessioni e copertina di un'altra voce in questo gioco."
        ),
        "Source game": "Gioco di origine",
        "Choose a game": "Scegli un gioco",
        "Hide the source after unifying": (
            "Nascondi l'origine dopo l'unificazione"
        ),
        "Avoids duplicate stats. You can restore it from Settings.": (
            "Evita statistiche duplicate. Puoi ripristinarla dalle Impostazioni."
        ),
        "Unify data": "Unifica dati",
        "No games to import.": "Nessun gioco da importare.",
        "Choose a different game to import.": (
            "Scegli un altro gioco da importare."
        ),
        "Couldn't unify the data.": "Impossibile unificare i dati.",
        "This game was already unified into {title}.": (
            "Questo gioco è già stato unificato in {title}."
        ),
        "{title} data imported into {target}.": (
            "Dati di {title} importati in {target}."
        ),
        "IMPORTED GAMES": "GIOCHI IMPORTATI",
        "No entries imported yet.": "Nessuna voce importata.",
        "Merged into {title}": "Unificato in {title}",
        "Imported": "Importato",
        "Removed": "Rimosso",
        "Arc": "Arco",
        "Flat": "Piatto",
        "3D Ring": "Anello 3D",
        "Vertical Wheel": "Ruota verticale",
        "Mode": "Modalità",
        "January": "Gennaio",
        "February": "Febbraio",
        "March": "Marzo",
        "April": "Aprile",
        "May": "Maggio",
        "June": "Giugno",
        "July": "Luglio",
        "August": "Agosto",
        "September": "Settembre",
        "October": "Ottobre",
        "November": "Novembre",
        "December": "Dicembre",
        "{minutes} min": "{minutes} min",
        "{hours} h": "{hours} h",
        "{hours} h {minutes} min": "{hours} h {minutes} min",
        "APPEARANCE": "ASPETTO",
        "LANGUAGE": "LINGUA",
        "Interface language": "Lingua dell'interfaccia",
        "Accent colour": "Colore d'accento",
        "Surface colour · navbar, Ready dock and shelf": (
            "Colore della superficie · barra, dock Ready e scaffale"
        ),
        "Cartridge colour": "Colore della cartuccia",
        "Cartridge style": "Stile della cartuccia",
        "Classic": "Classico",
        "Optional. Paste your SteamGridDB API key to choose a cover per game. "
        "It is stored in the system credential store, never in the repository.": (
            "Facoltativo. Incolla la tua chiave API SteamGridDB per scegliere "
            "una copertina per gioco. Viene salvata nell'archivio credenziali "
            "di sistema, mai nel repository."
        ),
        "Key saved — paste a new one to replace it": (
            "Chiave salvata: incollane una nuova per sostituirla"
        ),
        "Paste your SteamGridDB API key": "Incolla la chiave API SteamGridDB",
        "Save": "Salva",
        "Clear": "Cancella",
        "Get a key at steamgriddb.com/profile/preferences/api": (
            "Ottieni una chiave su steamgriddb.com/profile/preferences/api"
        ),
        "UPDATES": "AGGIORNAMENTI",
        "Last checked: %1": "Ultimo controllo: %1",
        "Check automatically": "Controlla automaticamente",
        "Checking...": "Controllo...",
        "Check now": "Controlla ora",
        "Checking for updates...": "Ricerca aggiornamenti...",
        "You're up to date.": "Sei aggiornato.",
        "GameCenter %1 is available.": "GameCenter %1 è disponibile.",
        "Update now": "Aggiorna ora",
        "GameCenter %1 · MIT": "GameCenter %1 · MIT",
        "Add a game": "Aggiungi un gioco",
        "Pick the root folder and the executable to launch.": (
            "Scegli la cartella principale e l'eseguibile da avviare."
        ),
        "Title": "Titolo",
        "Game title": "Titolo del gioco",
        "Root folder": "Cartella principale",
        "No folder selected": "Nessuna cartella selezionata",
        "Browse...": "Sfoglia...",
        "Executable": "Eseguibile",
        "No executable found. Choose another folder or put the game executable "
        "at its root.": (
            "Nessun eseguibile trovato. Scegli un'altra cartella o metti "
            "l'eseguibile del gioco nella sua radice."
        ),
        "You can choose a SteamGridDB cover later from the game's detail view.": (
            "Puoi scegliere una copertina SteamGridDB più tardi dalla vista di "
            "dettaglio del gioco."
        ),
        "Cancel": "Annulla",
        "Add game": "Aggiungi gioco",
        "Choose the game folder": "Scegli la cartella del gioco",
        "Choose artwork": "Scegli copertina",
        "Portrait grids from SteamGridDB": "Copertine verticali da SteamGridDB",
        "Looking for artwork...": "Ricerca copertine...",
        "Open Settings": "Apri impostazioni",
        "Try again": "Riprova",
        "Default": "Predefinita",
        "Showing %1 of %2 loaded options.": (
            "Mostrando %1 di %2 opzioni caricate."
        ),
        "Showing all %1 options.": "Mostrando tutte le %1 opzioni.",
        "Loading...": "Caricamento...",
        "Load more": "Carica altro",
        "Ready": "Pronto",
        "Inserting...": "Inserimento...",
        "Play": "Gioca",
        "Installed": "Installato",
        "Not installed": "Non installato",
        "Open folder": "Apri cartella",
        "Copy App ID": "Copia App ID",
        "Choose art": "Scegli copertina",
        "No Steam library found.\nInstall a game with Steam and press F5.": (
            "Nessuna libreria Steam trovata.\n"
            "Installa un gioco con Steam e premi F5."
        ),
        "No games match your filters.": "Nessun gioco corrisponde ai filtri.",
        "Launch": "Avvia",
        "Open install folder": "Apri cartella di installazione",
        "Cartridge color...": "Colore della cartuccia...",
        "Remove from library": "Rimuovi dalla libreria",
        "Cartridge color": "Colore della cartuccia",
        "Use default": "Usa predefinito",
        "All stores": "Tutti gli store",
        "Local": "Locale",
        "1 game": "1 gioco",
        "%1 games": "%1 giochi",
        "Recently Played": "Giocati di recente",
        "Most played": "Più giocati",
        "Size": "Dimensione",
        "Search your games": "Cerca i tuoi giochi",
        "LIBRARY": "LIBRERIA",
        "STORE": "STORE",
        "Scan Steam games": "Scansiona giochi Steam",
        "Scan Epic games": "Scansiona giochi Epic",
        "Scan GOG games": "Scansiona giochi GOG",
        "Scan Battle.net games": "Scansiona giochi Battle.net",
        "Scan Riot games": "Scansiona giochi Riot",
        "Scan all stores": "Scansiona tutti gli store",
        "Restore removed games": "Ripristina giochi rimossi",
        "Add game manually...": "Aggiungi gioco manualmente...",
        "GameCenter %1 is available - click to update": (
            "GameCenter %1 è disponibile: fai clic per aggiornare"
        ),
        "Update available": "Aggiornamento disponibile",
        "You have GameCenter %1. A newer version is ready to download and install.": (
            "Hai GameCenter %1. Una versione più recente è pronta per il "
            "download e l'installazione."
        ),
        "Installer: %1": "Programma di installazione: %1",
        "Later": "Più tardi",
        "Downloading...": "Download in corso...",
        "Installing...": "Installazione...",
        "Store coming in v0.2": "Store in arrivo nella v0.2",
        "Game added to your library": "Gioco aggiunto alla tua libreria",
        "{minutes} min played": "{minutes} min giocati",
        "1 hour played": "1 ora giocata",
        "{hours} hours played": "{hours} ore giocate",
        "Never played": "Mai giocato",
        "Played today": "Giocato oggi",
        "Played yesterday": "Giocato ieri",
        "Played {days} days ago": "Giocato {days} giorni fa",
        "Played {months} month ago": "Giocato {months} mese fa",
        "Played {months} months ago": "Giocato {months} mesi fa",
        "Played {years} year ago": "Giocato {years} anno fa",
        "Played {years} years ago": "Giocato {years} anni fa",
        "Never": "Mai",
        "No update available.": "Nessun aggiornamento disponibile.",
        "This release doesn't include a Windows installer.": (
            "Questa versione non include un programma di installazione Windows."
        ),
        "Downloading update...": "Download dell'aggiornamento...",
        "The update file is missing.": "Manca il file di aggiornamento.",
        "Installing update. GameCenter will restart...": (
            "Installazione dell'aggiornamento. GameCenter si riavvierà..."
        ),
        "Update downloaded. Installing...": (
            "Aggiornamento scaricato. Installazione..."
        ),
        "Saved to the system credential store.": (
            "Salvato nell'archivio credenziali di sistema."
        ),
        "Couldn't save to the credential store.": (
            "Impossibile salvare nell'archivio credenziali."
        ),
        "Key removed.": "Chiave rimossa.",
        "Add a SteamGridDB API key in Settings first.": (
            "Aggiungi prima una chiave API SteamGridDB nelle impostazioni."
        ),
        "No portrait artwork found for this game.": (
            "Nessuna copertina verticale trovata per questo gioco."
        ),
        "Library rescanned: {count} game(s).": (
            "Libreria riscansionata: {count} gioco/i."
        ),
        "Couldn't scan {label}: {error}": (
            "Impossibile scansionare {label}: {error}"
        ),
        "{label}: {count} game(s) found.": "{label}: {count} gioco/i trovati.",
        "Restored {count} removed game(s).": (
            "Ripristinati {count} gioco/i rimosso/i."
        ),
        "No removed games to restore.": "Nessun gioco rimosso da ripristinare.",
        "This game has no install folder.": (
            "Questo gioco non ha una cartella di installazione."
        ),
        "Removed {title} from the library.": "{title} rimosso dalla libreria.",
        "Give the game a title.": "Dai un titolo al gioco.",
        "Choose a valid root folder.": "Scegli una cartella principale valida.",
        "No executable found in that folder.": (
            "Nessun eseguibile trovato in quella cartella."
        ),
        "That executable doesn't exist.": "Quell'eseguibile non esiste.",
        "Don't know how to start {title}.": "Non so come avviare {title}.",
        "No releases found on GitHub.": "Nessuna versione trovata su GitHub.",
        "GitHub answered with an error ({code}).": (
            "GitHub ha risposto con un errore ({code})."
        ),
        "Couldn't reach GitHub.": "Impossibile raggiungere GitHub.",
        "GitHub sent an unexpected answer.": (
            "GitHub ha inviato una risposta inattesa."
        ),
        "This release doesn't include an installer.": (
            "Questa versione non include un programma di installazione."
        ),
        "Couldn't prepare the update folder.": (
            "Impossibile preparare la cartella di aggiornamento."
        ),
        "The update download was incomplete.": (
            "Il download dell'aggiornamento è incompleto."
        ),
        "The update file failed its integrity check.": (
            "Il file di aggiornamento non ha superato il controllo di integrità."
        ),
        "Couldn't download the update.": (
            "Impossibile scaricare l'aggiornamento."
        ),
        "Automatic installation is only available on Windows.": (
            "L'installazione automatica è disponibile solo su Windows."
        ),
        "The downloaded installer is missing.": (
            "Manca il programma di installazione scaricato."
        ),
        "Couldn't start the installer.": (
            "Impossibile avviare il programma di installazione."
        ),
        "SteamGridDB rejected the API key.": (
            "SteamGridDB ha rifiutato la chiave API."
        ),
        "SteamGridDB answered with an error ({code}).": (
            "SteamGridDB ha risposto con un errore ({code})."
        ),
        "Couldn't reach SteamGridDB.": (
            "Impossibile raggiungere SteamGridDB."
        ),
        "SteamGridDB sent an unexpected answer.": (
            "SteamGridDB ha inviato una risposta inattesa."
        ),
        "SteamGridDB didn't return any results.": (
            "SteamGridDB non ha restituito risultati."
        ),
        "Couldn't download that artwork.": (
            "Impossibile scaricare quella copertina."
        ),
        "That artwork came back empty.": "Quella copertina è arrivata vuota.",
    },
    "pt": {
        "Settings": "Configurações",
        "FAVORITES": "FAVORITOS",
        "ALL GAMES": "TODOS OS JOGOS",
        "ABOUT": "SOBRE",
        "PLAYTIME TIMELINE": "LINHA DO TEMPO",
        "All time": "Tempo total",
        "1 session": "1 sessão",
        "%1 sessions": "%1 sessões",
        "Loading description...": "Carregando descrição...",
        "No description available.": "Nenhuma descrição disponível.",
        "Read more": "Ler mais",
        "Show less": "Mostrar menos",
        "No sessions recorded yet.": "Nenhuma sessão registrada ainda.",
        "Launch the game from GameCenter to start the timeline.": (
            "Inicie o jogo pelo GameCenter para começar a linha do tempo."
        ),
        "Added to favorites": "Adicionado aos favoritos",
        "Removed from favorites": "Removido dos favoritos",
        "STATS": "STATS",
        "Week": "Semana",
        "Month": "Mês",
        "Year": "Ano",
        "This week": "Esta semana",
        "Time Played": "Tempo jogado",
        "Month by Month": "Mês a mês",
        "%1 as a river": "%1 como um rio",
        "Your %1 so far, in review": "Seu %1 até agora, em resumo",
        "Watch": "Assistir",
        "Open month": "Abrir mês",
        "Days played": "Dias jogados",
        "Best day": "Melhor dia",
        "Sessions": "Sessões",
        "Day by day": "Dia a dia",
        "%1 of %2 days": "%1 de %2 dias",
        "%1-day streak": "Sequência de %1 dias",
        "{change}% vs {label}": "{change}% vs {label}",
        "previous week": "a semana anterior",
        "Other": "Outros",
        "No playtime in this period.": "Nenhum tempo de jogo neste período.",
        "Unknown game": "Jogo desconhecido",
        "Big Picture": "Big Picture",
        "BIG PICTURE": "BIG PICTURE",
        "All games": "Todos os jogos",
        "Recent": "Recentes",
        "Favorites": "Favoritos",
        "Filter": "Filtro",
        "Favorite": "Favorito",
        "Menu": "Menu",
        "Exit": "Sair",
        "Exit Big Picture?": "Sair do Big Picture?",
        "Exit Big Picture": "Sair do Big Picture",
        "Controller connected": "Controle conectado",
        "Keyboard & mouse": "Teclado e mouse",
        "No games in your library": "Nenhum jogo na sua biblioteca",
        "Launching...": "Iniciando...",
        "Couldn't launch the game.": "Não foi possível iniciar o jogo.",
        "Click to select · Double-click to play": (
            "Clique para selecionar · Duplo clique para jogar"
        ),
        "Back": "Voltar",
        "Select": "Selecionar",
        "Details": "Detalhes",
        "GAME PROFILE": "PERFIL DO JOGO",
        "STATUS": "ESTADO",
        "SCORE": "PONTUAÇÃO",
        "Edit profile": "Editar perfil",
        "Close profile": "Fechar perfil",
        "Drag to move · Right-drag to rotate": (
            "Arraste para mover · Botão direito para girar"
        ),
        "Playing": "Jogando",
        "On Going": "Em andamento",
        "Beaten": "Vencido",
        "Completed": "Concluído",
        "Played": "Jogado",
        "Plan to Play": "Para jogar",
        "On Hold": "Em pausa",
        "Not Played": "Não jogado",
        "Abandoned": "Abandonado",
        "Not set": "Não definido",
        "TRACEABILITY": "RASTREABILIDADE",
        "Import another entry's playtime, sessions and cover into this game.": (
            "Importa as horas, sessões e capa de outra entrada para este jogo."
        ),
        "Source game": "Jogo de origem",
        "Choose a game": "Escolhe um jogo",
        "Hide the source after unifying": "Ocultar a origem após unificar",
        "Avoids duplicate stats. You can restore it from Settings.": (
            "Evita estatísticas duplicadas. Podes restaurá-la nas Configurações."
        ),
        "Unify data": "Unificar dados",
        "No games to import.": "Não há jogos para importar.",
        "Choose a different game to import.": (
            "Escolhe um jogo diferente para importar."
        ),
        "Couldn't unify the data.": "Não foi possível unificar os dados.",
        "This game was already unified into {title}.": (
            "Este jogo já foi unificado em {title}."
        ),
        "{title} data imported into {target}.": (
            "Dados de {title} importados em {target}."
        ),
        "IMPORTED GAMES": "JOGOS IMPORTADOS",
        "No entries imported yet.": "Ainda não há entradas importadas.",
        "Merged into {title}": "Unificado em {title}",
        "Imported": "Importado",
        "Removed": "Removido",
        "Arc": "Arco",
        "Flat": "Plano",
        "3D Ring": "Anel 3D",
        "Vertical Wheel": "Roda vertical",
        "Mode": "Modo",
        "January": "Janeiro",
        "February": "Fevereiro",
        "March": "Março",
        "April": "Abril",
        "May": "Maio",
        "June": "Junho",
        "July": "Julho",
        "August": "Agosto",
        "September": "Setembro",
        "October": "Outubro",
        "November": "Novembro",
        "December": "Dezembro",
        "{minutes} min": "{minutes} min",
        "{hours} h": "{hours} h",
        "{hours} h {minutes} min": "{hours} h {minutes} min",
        "APPEARANCE": "APARÊNCIA",
        "LANGUAGE": "IDIOMA",
        "Interface language": "Idioma da interface",
        "Accent colour": "Cor de destaque",
        "Surface colour · navbar, Ready dock and shelf": (
            "Cor da superfície · barra, dock Ready e prateleira"
        ),
        "Cartridge colour": "Cor do cartucho",
        "Cartridge style": "Estilo do cartucho",
        "Classic": "Clássico",
        "Optional. Paste your SteamGridDB API key to choose a cover per game. "
        "It is stored in the system credential store, never in the repository.": (
            "Opcional. Cole sua chave de API do SteamGridDB para escolher uma "
            "capa por jogo. Ela é salva no cofre de credenciais do sistema, "
            "nunca no repositório."
        ),
        "Key saved — paste a new one to replace it": (
            "Chave salva — cole uma nova para substituí-la"
        ),
        "Paste your SteamGridDB API key": "Cole sua chave de API do SteamGridDB",
        "Save": "Salvar",
        "Clear": "Limpar",
        "Get a key at steamgriddb.com/profile/preferences/api": (
            "Obtenha uma chave em steamgriddb.com/profile/preferences/api"
        ),
        "UPDATES": "ATUALIZAÇÕES",
        "Last checked: %1": "Última verificação: %1",
        "Check automatically": "Verificar automaticamente",
        "Checking...": "Verificando...",
        "Check now": "Verificar agora",
        "Checking for updates...": "Buscando atualizações...",
        "You're up to date.": "Você está atualizado.",
        "GameCenter %1 is available.": "GameCenter %1 está disponível.",
        "Update now": "Atualizar agora",
        "GameCenter %1 · MIT": "GameCenter %1 · MIT",
        "Add a game": "Adicionar um jogo",
        "Pick the root folder and the executable to launch.": (
            "Escolha a pasta raiz e o executável para iniciar."
        ),
        "Title": "Título",
        "Game title": "Título do jogo",
        "Root folder": "Pasta raiz",
        "No folder selected": "Nenhuma pasta selecionada",
        "Browse...": "Procurar...",
        "Executable": "Executável",
        "No executable found. Choose another folder or put the game executable "
        "at its root.": (
            "Nenhum executável encontrado. Escolha outra pasta ou coloque o "
            "executável do jogo na raiz."
        ),
        "You can choose a SteamGridDB cover later from the game's detail view.": (
            "Você pode escolher uma capa do SteamGridDB depois na visualização "
            "de detalhes do jogo."
        ),
        "Cancel": "Cancelar",
        "Add game": "Adicionar jogo",
        "Choose the game folder": "Escolha a pasta do jogo",
        "Choose artwork": "Escolher capa",
        "Portrait grids from SteamGridDB": "Capas verticais do SteamGridDB",
        "Looking for artwork...": "Buscando capas...",
        "Open Settings": "Abrir configurações",
        "Try again": "Tentar novamente",
        "Default": "Padrão",
        "Showing %1 of %2 loaded options.": (
            "Mostrando %1 de %2 opções carregadas."
        ),
        "Showing all %1 options.": "Mostrando todas as %1 opções.",
        "Loading...": "Carregando...",
        "Load more": "Carregar mais",
        "Ready": "Pronto",
        "Inserting...": "Inserindo...",
        "Play": "Jogar",
        "Installed": "Instalado",
        "Not installed": "Não instalado",
        "Open folder": "Abrir pasta",
        "Copy App ID": "Copiar App ID",
        "Choose art": "Escolher capa",
        "No Steam library found.\nInstall a game with Steam and press F5.": (
            "Nenhuma biblioteca Steam encontrada.\n"
            "Instale um jogo com o Steam e pressione F5."
        ),
        "No games match your filters.": "Nenhum jogo corresponde aos filtros.",
        "Launch": "Iniciar",
        "Open install folder": "Abrir pasta de instalação",
        "Cartridge color...": "Cor do cartucho...",
        "Remove from library": "Remover da biblioteca",
        "Cartridge color": "Cor do cartucho",
        "Use default": "Usar padrão",
        "All stores": "Todas as lojas",
        "Local": "Local",
        "1 game": "1 jogo",
        "%1 games": "%1 jogos",
        "Recently Played": "Jogados recentemente",
        "Most played": "Mais jogados",
        "Size": "Tamanho",
        "Search your games": "Pesquise seus jogos",
        "LIBRARY": "BIBLIOTECA",
        "STORE": "LOJA",
        "Scan Steam games": "Verificar jogos da Steam",
        "Scan Epic games": "Verificar jogos da Epic",
        "Scan GOG games": "Verificar jogos da GOG",
        "Scan Battle.net games": "Verificar jogos da Battle.net",
        "Scan Riot games": "Verificar jogos da Riot",
        "Scan all stores": "Verificar todas as lojas",
        "Restore removed games": "Restaurar jogos removidos",
        "Add game manually...": "Adicionar jogo manualmente...",
        "GameCenter %1 is available - click to update": (
            "GameCenter %1 está disponível - clique para atualizar"
        ),
        "Update available": "Atualização disponível",
        "You have GameCenter %1. A newer version is ready to download and install.": (
            "Você tem o GameCenter %1. Uma versão mais recente está pronta "
            "para baixar e instalar."
        ),
        "Installer: %1": "Instalador: %1",
        "Later": "Mais tarde",
        "Downloading...": "Baixando...",
        "Installing...": "Instalando...",
        "Store coming in v0.2": "Loja chegando na v0.2",
        "Game added to your library": "Jogo adicionado à sua biblioteca",
        "{minutes} min played": "{minutes} min jogados",
        "1 hour played": "1 hora jogada",
        "{hours} hours played": "{hours} horas jogadas",
        "Never played": "Nunca jogado",
        "Played today": "Jogado hoje",
        "Played yesterday": "Jogado ontem",
        "Played {days} days ago": "Jogado há {days} dias",
        "Played {months} month ago": "Jogado há {months} mês",
        "Played {months} months ago": "Jogado há {months} meses",
        "Played {years} year ago": "Jogado há {years} ano",
        "Played {years} years ago": "Jogado há {years} anos",
        "Never": "Nunca",
        "No update available.": "Nenhuma atualização disponível.",
        "This release doesn't include a Windows installer.": (
            "Esta versão não inclui um instalador para Windows."
        ),
        "Downloading update...": "Baixando atualização...",
        "The update file is missing.": "O arquivo de atualização está ausente.",
        "Installing update. GameCenter will restart...": (
            "Instalando atualização. O GameCenter será reiniciado..."
        ),
        "Update downloaded. Installing...": (
            "Atualização baixada. Instalando..."
        ),
        "Saved to the system credential store.": (
            "Salvo no cofre de credenciais do sistema."
        ),
        "Couldn't save to the credential store.": (
            "Não foi possível salvar no cofre de credenciais."
        ),
        "Key removed.": "Chave removida.",
        "Add a SteamGridDB API key in Settings first.": (
            "Adicione primeiro uma chave de API do SteamGridDB nas configurações."
        ),
        "No portrait artwork found for this game.": (
            "Nenhuma capa vertical encontrada para este jogo."
        ),
        "Library rescanned: {count} game(s).": (
            "Biblioteca verificada novamente: {count} jogo(s)."
        ),
        "Couldn't scan {label}: {error}": (
            "Não foi possível verificar {label}: {error}"
        ),
        "{label}: {count} game(s) found.": (
            "{label}: {count} jogo(s) encontrado(s)."
        ),
        "Restored {count} removed game(s).": (
            "{count} jogo(s) removido(s) restaurado(s)."
        ),
        "No removed games to restore.": "Nenhum jogo removido para restaurar.",
        "This game has no install folder.": (
            "Este jogo não tem pasta de instalação."
        ),
        "Removed {title} from the library.": (
            "{title} foi removido da biblioteca."
        ),
        "Give the game a title.": "Dê um título ao jogo.",
        "Choose a valid root folder.": "Escolha uma pasta raiz válida.",
        "No executable found in that folder.": (
            "Nenhum executável encontrado nessa pasta."
        ),
        "That executable doesn't exist.": "Esse executável não existe.",
        "Don't know how to start {title}.": "Não sei como iniciar {title}.",
        "No releases found on GitHub.": "Nenhuma versão encontrada no GitHub.",
        "GitHub answered with an error ({code}).": (
            "O GitHub respondeu com um erro ({code})."
        ),
        "Couldn't reach GitHub.": "Não foi possível acessar o GitHub.",
        "GitHub sent an unexpected answer.": (
            "O GitHub enviou uma resposta inesperada."
        ),
        "This release doesn't include an installer.": (
            "Esta versão não inclui um instalador."
        ),
        "Couldn't prepare the update folder.": (
            "Não foi possível preparar a pasta de atualização."
        ),
        "The update download was incomplete.": (
            "O download da atualização ficou incompleto."
        ),
        "The update file failed its integrity check.": (
            "O arquivo de atualização falhou na verificação de integridade."
        ),
        "Couldn't download the update.": (
            "Não foi possível baixar a atualização."
        ),
        "Automatic installation is only available on Windows.": (
            "A instalação automática só está disponível no Windows."
        ),
        "The downloaded installer is missing.": (
            "O instalador baixado está ausente."
        ),
        "Couldn't start the installer.": (
            "Não foi possível iniciar o instalador."
        ),
        "SteamGridDB rejected the API key.": (
            "O SteamGridDB rejeitou a chave de API."
        ),
        "SteamGridDB answered with an error ({code}).": (
            "O SteamGridDB respondeu com um erro ({code})."
        ),
        "Couldn't reach SteamGridDB.": (
            "Não foi possível acessar o SteamGridDB."
        ),
        "SteamGridDB sent an unexpected answer.": (
            "O SteamGridDB enviou uma resposta inesperada."
        ),
        "SteamGridDB didn't return any results.": (
            "O SteamGridDB não retornou resultados."
        ),
        "Couldn't download that artwork.": (
            "Não foi possível baixar essa capa."
        ),
        "That artwork came back empty.": "Essa capa veio vazia.",
    },
}

_EXTRA_KEYS = ("Nintendo DS", "PS2", "STEAMGRIDDB")
_KEYS = frozenset(_EXTRA_KEYS).union(
    *(catalog.keys() for catalog in TRANSLATIONS.values())
)

_catalogs: dict[str, dict[str, str]] = {}


def catalog(code: str) -> dict[str, str]:
    """The complete catalog for *code*, falling back to English per key."""
    code = code if code in CODES else "en"
    cached = _catalogs.get(code)
    if cached is not None:
        return cached
    strings = TRANSLATIONS.get(code, {})
    merged = {key: strings.get(key, key) for key in _KEYS}
    _catalogs[code] = merged
    return merged


class Translator(QObject):
    languageChanged = Signal()

    def __init__(self, prefs=None, language: str | None = None) -> None:
        super().__init__()
        if language is None and prefs is not None:
            language = getattr(prefs, "language", "en")
        self._prefs = prefs
        self._language = language if language in CODES else "en"

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._language

    @Property("QVariantMap", notify=languageChanged)
    def strings(self) -> dict[str, str]:
        return catalog(self._language)

    @Property("QVariantList", constant=True)
    def languages(self) -> list[dict]:
        return [{"text": name, "value": code} for code, name in LANGUAGES]

    @Slot(str)
    def setLanguage(self, code: str) -> None:
        if code not in CODES or code == self._language:
            return
        self._language = code
        if self._prefs is not None:
            self._prefs.language = code
        self.languageChanged.emit()

    @Slot(str, result=str)
    def text(self, key: str) -> str:
        return catalog(self._language).get(key, key)


_active: Translator | None = None


def set_active(translator: Translator | None) -> None:
    global _active
    _active = translator


def tr(text: str, **values) -> str:
    """Translate *text* (English source) and fill ``{name}`` placeholders."""
    value = _active.text(text) if _active is not None else text
    if not values:
        return value
    try:
        return value.format(**values)
    except (KeyError, IndexError, ValueError):
        return value
