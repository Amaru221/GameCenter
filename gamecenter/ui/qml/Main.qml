import QtQuick
import QtQuick.Window

Window {
    id: window
    width: 1180
    height: 800
    minimumWidth: 900
    minimumHeight: 620
    visible: true
    title: "GameCenter"
    color: "#07080b"
    visibility: bigPictureOpen ? Window.FullScreen : Window.Windowed

    property var detailGame: ({})
    property int detailIndex: -1
    property bool detailOpen: false
    property bool settingsOpen: false
    property bool artOpen: false
    property bool updateOpen: false
    property bool addOpen: false
    property bool demoInsert: false
    property var slotGame: ({})
    property string slotSessionId: ""
    property string currentView: "library"
    property bool bigPictureOpen: false
    // Big Picture is only instantiated while it is open (plus its fade-out).
    property bool bigPictureMounted: false

    onBigPictureOpenChanged: {
        if (bigPictureOpen) {
            bigPictureMounted = true;
            topBar.clearSearchFocus();
            requestActivate();
        } else if (bigPictureMounted) {
            // Keep the item alive for the 180 ms fade-out, then free it.
            bigPictureUnmountTimer.restart();
        }
    }

    onDetailOpenChanged: topBar.clearSearchFocus()
    onSettingsOpenChanged: topBar.clearSearchFocus()
    onArtOpenChanged: topBar.clearSearchFocus()
    onAddOpenChanged: topBar.clearSearchFocus()
    onUpdateOpenChanged: topBar.clearSearchFocus()

    function latestSession() {
        var list = Sessions.list;
        return list.length > 0 ? list[list.length - 1] : null;
    }

    function sessionById(sessionId) {
        var list = Sessions.list;
        for (var i = 0; i < list.length; i++) {
            if (list[i].id === sessionId) {
                return list[i];
            }
        }
        return null;
    }

    function setSlotSession(session) {
        if (!session) {
            slotSessionId = "";
            slotGame = ({});
            return;
        }
        slotSessionId = session.id;
        slotGame = Library.sessionCard(session.gameId);
    }

    function commitSlot(sessionId) {
        var session = sessionById(sessionId);
        if (!session) {
            session = latestSession();
        }
        setSlotSession(session);
    }

    function fileName(path) {
        var parts = String(path || "").split(/[\\/]/);
        return parts[parts.length - 1];
    }

    function refreshSlot(force) {
        if (insertEffect.running) {
            return;
        }
        var latest = latestSession();
        if (!latest) {
            if (slotSessionId !== "" || force) {
                slotSessionId = "";
                slotGame = ({});
            }
            return;
        }
        if (force || latest.id !== slotSessionId || !slotGame.title) {
            setSlotSession(latest);
        }
    }

    Component.onCompleted: refreshSlot(true)

    onDemoInsertChanged: {
        if (!demoInsert) {
            return;
        }
        var from = detail.cartridgeCenter();
        var to = Qt.point(dock.x + dock.width / 2, dock.y + 4);
        insertEffect.play(detailGame, -1, from, to);
        detailOpen = false;
    }

    // The library scene is captured (once) by the game detail overlay to build
    // its frosted-glass backdrop. The detail and the toast stay outside so the
    // capture never includes the modal itself.
    Item {
        id: libraryScene
        anchors.fill: parent

        Image {
            anchors.fill: parent
            source: "image://bg/1"
            fillMode: Image.PreserveAspectCrop
            smooth: true
        }

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#00000000" }
                GradientStop { position: 0.55; color: "#12070a0d" }
                GradientStop { position: 1.0; color: "#4d05060a" }
            }
        }

        TopBar {
            id: topBar
            width: parent.width
            anchors.top: parent.top
            currentView: window.currentView
            onToastRequested: (message) => toast.show(message)
            onSettingsRequested: settingsOpen = true
            onUpdateRequested: updateOpen = true
            onScanRequested: (source) => Library.scanStore(source)
            onRestoreHiddenRequested: Library.restoreHiddenGames()
            onAddRequested: addOpen = true
            onViewRequested: (view) => window.currentView = view
            onBigPictureRequested: window.bigPictureOpen = true
        }

        Toolbar {
            id: toolbar
            width: parent.width
            visible: window.currentView === "library"
            anchors.top: topBar.bottom
            onToastRequested: (message) => toast.show(message)
            onAddRequested: addOpen = true
        }

        LibraryGrid {
            anchors.top: toolbar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 24
            anchors.rightMargin: 24
            anchors.bottomMargin: 104
            visible: window.currentView === "library"

            onDetailRequested: (index) => {
                detailOpen = true;
                detailIndex = index;
                detailGame = Library.gameAt(index);
                Library.loadDetails(index);
            }
        }

        StatsView {
            id: statsView
            anchors.top: topBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            visible: window.currentView === "stats"
            onReviewRequested: (year) => {
                topBar.clearSearchFocus();
                var data = Library.yearReview(year);
                if (data && data.hasData) {
                    yearReview.open(data, year);
                } else {
                    toast.show(Tr.strings["No playtime in this period."]);
                }
            }
        }

        // Library dock: only exists in the library view. Stats is a clean,
        // dedicated window with no cartridge slot, clock or update banner.
        Item {
            id: libraryDock
            objectName: "libraryDock"
            anchors.fill: parent
            visible: window.currentView === "library"

            UpdateBanner {
                id: updateBanner
                z: 5
                anchors.left: parent.left
                anchors.bottom: dock.top
                anchors.leftMargin: 24
                anchors.bottomMargin: 12
                onOpenRequested: updateOpen = true
            }

            // Dark insertion plate ("pletina"): the cartridge slides in front
            // of it but behind the opaque front face of the dock below. All
            // four layers share this parent, so the stacking is stable.
            Item {
                id: insertPlate
                objectName: "insertPlate"
                z: 12
                width: 174
                height: 36
                x: dock.x + (dock.width - width) / 2
                y: dock.y - 12

                Rectangle {
                    anchors.fill: parent
                    radius: 11
                    gradient: Gradient {
                        GradientStop {
                            position: 0.0
                            color: Qt.darker(Library.surfaceColor, 1.55)
                        }
                        GradientStop {
                            position: 1.0
                            color: Qt.darker(Library.surfaceColor, 1.95)
                        }
                    }
                    border.width: 1
                    border.color: Qt.darker(Library.surfaceColor, 2.25)
                }

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 5
                    radius: 7
                    color: "#05070a"
                    opacity: 0.92
                }

                Rectangle {
                    x: 10
                    y: parent.height - 7
                    width: parent.width - 20
                    height: 2
                    radius: 1
                    color: Library.accent
                    opacity: dock.inserting ? 0.82 : 0.18
                    Behavior on opacity { NumberAnimation { duration: 160 } }
                }
            }

            SlotCartridge {
                id: slotCard
                objectName: "slotCartridge"
                z: 13
                x: dock.x + dock.width / 2 - width / 2
                y: dock.y - height
                game: window.slotGame
            }

            // The flying cartridge is a sibling of the dock, between the dark
            // plate (12) and the dock front face (20). It is never painted on
            // top of the banner again.
            InsertEffect {
                id: insertEffect
                z: 15
                anchors.fill: parent
                onInserted: (sessionId) => window.commitSlot(sessionId)
            }

            Dock {
                id: dock
                z: 20
                inserting: insertEffect.running
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 10
            }
        }
    }

    Rectangle {
        id: toast
        property string message: ""
        width: label.implicitWidth + 36
        height: 38
        radius: 19
        z: 25
        color: "#1a1f29"
        border.width: 1
        border.color: "#2f394b"
        opacity: 0
        visible: opacity > 0
        anchors.horizontalCenter: parent.horizontalCenter
        y: dock.y - height - 12

        Behavior on opacity { NumberAnimation { duration: 180 } }

        Text {
            id: label
            anchors.centerIn: parent
            text: toast.message
            color: "#e6ebf3"
            font.family: "Sora"
            font.pixelSize: 12
        }

        Timer {
            id: hideTimer
            interval: 2400
            onTriggered: toast.opacity = 0
        }

        function show(text) {
            message = text;
            opacity = 1;
            hideTimer.restart();
        }
    }

    GameDetail {
        id: detail
        z: 10
        anchors.fill: parent
        game: detailGame
        opened: detailOpen
        backdropItem: libraryScene
        onCloseRequested: detailOpen = false
        onPlayRequested: {
            var from = detail.cartridgeCenter();
            var to = Qt.point(dock.x + dock.width / 2, dock.y + 4);
            insertEffect.play(detailGame, detailIndex, from, to);
            detailOpen = false;
        }
        onFolderRequested: Library.openFolderById(detailGame.id)
        onCopyRequested: Library.copyAppIdById(detailGame.id)
        onFavoriteRequested: {
            var gameId = detailGame.id;
            Library.toggleFavoriteById(gameId);
            detailGame = Library.gameDetailById(gameId);
            toast.show(detailGame.favorite
                       ? Tr.strings["Added to favorites"]
                       : Tr.strings["Removed from favorites"]);
        }
        onArtRequested: {
            artOpen = true;
            Library.loadArtOptions(detailIndex);
        }
        onProfileChanged: {
            if (detailGame.id) {
                var gameId = detailGame.id;
                detailGame = Library.gameDetailById(gameId);
                var row = Library.rowForId(gameId);
                if (row >= 0) {
                    detailIndex = row;
                }
            }
        }
    }

    AddGameDialog {
        id: addGameDialog
        z: 35
        anchors.fill: parent
        opened: addOpen
        onCloseRequested: addOpen = false
        onAdded: {
            addOpen = false;
            toast.show(Tr.strings["Game added to your library"]);
        }
    }

    ArtPicker {
        id: artPicker
        z: 30
        anchors.fill: parent
        opened: artOpen
        index: detailIndex
        onCloseRequested: artOpen = false
        onSettingsRequested: {
            artOpen = false;
            settingsOpen = true;
        }
    }

    SettingsPanel {
        id: settingsPanel
        z: 40
        anchors.fill: parent
        opened: settingsOpen
        onCloseRequested: settingsOpen = false
        onUpdateRequested: {
            settingsOpen = false;
            updateOpen = true;
        }
    }

    UpdateDialog {
        id: updateDialog
        z: 45
        anchors.fill: parent
        opened: updateOpen
        onCloseRequested: updateOpen = false
        onDownloadRequested: Library.downloadUpdate()
    }

    YearReview {
        id: yearReview
        z: 32
        anchors.fill: parent
    }

    // Big Picture is created on demand: keeping the whole carousel alive (and
    // silently repainting the window) from startup was one of the biggest idle
    // costs of the app.
    Loader {
        id: bigPictureLoader
        anchors.fill: parent
        active: window.bigPictureMounted
        sourceComponent: bigPictureComponent
    }

    Component {
        id: bigPictureComponent
        BigPicture {
            id: bigPicture
            anchors.fill: parent
            appActive: window.active
            opened: window.bigPictureOpen
            onCloseRequested: window.bigPictureOpen = false
        }
    }

    Timer {
        id: bigPictureUnmountTimer
        interval: 220
        onTriggered: window.bigPictureMounted = false
    }

    // While the search box holds the focus, any click anywhere clears it. The
    // press is not accepted, so the click still reaches the item below (game,
    // button, modal...) as usual.
    MouseArea {
        id: searchFocusGuard
        z: 100
        anchors.fill: parent
        visible: topBar.searchFocused
        enabled: visible
        acceptedButtons: Qt.LeftButton | Qt.RightButton | Qt.MiddleButton
        propagateComposedEvents: true
        onPressed: (mouse) => {
            topBar.clearSearchFocus();
            mouse.accepted = false;
        }
    }

    Connections {
        target: Tr
        function onLanguageChanged() {
            refreshSlot(true);
            if (detailOpen) {
                detailGame = Library.gameAt(detailIndex);
                Library.loadDetails(detailIndex);
            }
        }
    }

    Connections {
        target: Sessions
        function onChanged() {
            refreshSlot();
        }
    }

    Connections {
        target: Gamepad
        function onMenu() {
            if (!window.bigPictureOpen
                    && !yearReview.opened
                    && window.active
                    && !window.detailOpen
                    && !window.settingsOpen
                    && !window.updateOpen
                    && !window.addOpen
                    && !window.artOpen) {
                window.bigPictureOpen = true;
            }
        }
    }

    Connections {
        target: Library
        function onFailed(message) { toast.show(message) }
        function onNotice(message) { toast.show(message) }
        function onAppearanceChanged() { refreshSlot(true); }
        function onArtChanged() {
            refreshSlot(true);
            if (detailOpen) {
                detailGame = Library.gameAt(detailIndex);
            }
            artOpen = false;
        }
        function onPlaytimeChanged() {
            if (detailOpen && detailGame.id) {
                var gameId = detailGame.id;
                var row = Library.rowForId(gameId);
                if (row >= 0) {
                    detailIndex = row;
                }
                detailGame = Library.gameDetailById(gameId);
            }
        }
        function onDetailsChanged() {
            if (detailOpen && detailGame.id) {
                var gameId = detailGame.id;
                var row = Library.rowForId(gameId);
                if (row >= 0) {
                    detailIndex = row;
                }
                detailGame = Library.gameDetailById(gameId);
            }
        }
    }

    Connections {
        target: Screenshots
        function onSaved(path) {
            toast.show(Tr.strings["Screenshot saved: %1"].arg(window.fileName(path)));
        }
        function onFailed(message) { toast.show(message) }
    }

    Shortcut {
        sequence: Screenshots.shortcutSequence
        enabled: Screenshots.localShortcutEnabled && !Screenshots.recording
        onActivated: Screenshots.captureIfPlaying()
    }

    Shortcut {
        sequence: "F5"
        enabled: !window.bigPictureOpen && !yearReview.opened
                 && !Screenshots.recording
        onActivated: {
            Library.refresh();
            if (window.currentView === "stats") {
                statsView.refresh();
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        enabled: !window.bigPictureOpen && !yearReview.opened
                 && !detail.viewerOpen
                 && !Screenshots.recording
        onActivated: {
            if (updateOpen) {
                updateOpen = false;
            } else if (settingsOpen) {
                settingsOpen = false;
            } else if (addOpen) {
                addOpen = false;
            } else if (artOpen) {
                artOpen = false;
            } else if (detailOpen) {
                detailOpen = false;
            }
        }
    }

    Shortcut {
        sequence: "Ctrl+B"
        enabled: !window.bigPictureOpen && !yearReview.opened
                 && !Screenshots.recording
        onActivated: {
            if (!bigPictureOpen && !detailOpen && !settingsOpen
                    && !updateOpen && !addOpen && !artOpen) {
                bigPictureOpen = true;
            }
        }
    }

    Shortcut {
        sequence: "Ctrl+,"
        enabled: !window.bigPictureOpen && !yearReview.opened
                 && !Screenshots.recording
        onActivated: settingsOpen = true
    }

    Shortcut {
        sequence: "Ctrl+F"
        enabled: !window.bigPictureOpen
                 && !yearReview.opened
                 && window.currentView === "library"
                 && !window.detailOpen
                 && !window.settingsOpen
                 && !window.updateOpen
                 && !window.addOpen
                 && !window.artOpen
                 && !Screenshots.recording
        onActivated: topBar.focusSearch()
    }
}
