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

    onBigPictureOpenChanged: {
        if (bigPictureOpen) {
            requestActivate();
        }
    }

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

    Image {
        anchors.fill: parent
        visible: window.currentView === "library"
        source: "image://bg/1"
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }

    Rectangle {
        anchors.fill: parent
        visible: window.currentView === "library"
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
    }

    UpdateBanner {
        id: updateBanner
        z: 5
        anchors.left: parent.left
        anchors.bottom: dock.top
        anchors.leftMargin: 24
        anchors.bottomMargin: 12
        onOpenRequested: updateOpen = true
    }

    Dock {
        id: dock
        z: detailOpen ? 5 : 20
        inserting: insertEffect.running
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 10
    }

    SlotCartridge {
        id: slotCard
        z: detailOpen ? 5 : 19
        x: dock.x + dock.width / 2 - width / 2
        y: dock.y - height
        game: window.slotGame
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
        anchors.bottom: dock.top
        anchors.bottomMargin: 12

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
        onCloseRequested: detailOpen = false
        onPlayRequested: {
            var from = detail.cartridgeCenter();
            var to = Qt.point(dock.x + dock.width / 2, dock.y + 4);
            insertEffect.play(detailGame, detailIndex, from, to);
            detailOpen = false;
        }
        onFolderRequested: Library.openFolder(detailIndex)
        onCopyRequested: Library.copyAppId(detailIndex)
        onFavoriteRequested: {
            Library.toggleFavorite(detailIndex);
            detailGame = Library.gameAt(detailIndex);
            toast.show(detailGame.favorite
                       ? Tr.strings["Added to favorites"]
                       : Tr.strings["Removed from favorites"]);
        }
        onArtRequested: {
            artOpen = true;
            Library.loadArtOptions(detailIndex);
        }
    }

    InsertEffect {
        id: insertEffect
        z: 15
        anchors.fill: parent
        onInserted: (sessionId) => window.commitSlot(sessionId)
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

    BigPicture {
        id: bigPicture
        anchors.fill: parent
        appActive: window.active
        opened: window.bigPictureOpen
        onCloseRequested: window.bigPictureOpen = false
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
            if (detailOpen) {
                detailGame = Library.gameAt(detailIndex);
            }
        }
        function onDetailsChanged() {
            if (detailOpen) {
                detailGame = Library.gameAt(detailIndex);
            }
        }
    }

    Shortcut {
        sequence: "F5"
        enabled: !window.bigPictureOpen
        onActivated: {
            Library.refresh();
            if (window.currentView === "stats") {
                statsView.refresh();
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        enabled: !window.bigPictureOpen
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
        enabled: !window.bigPictureOpen
        onActivated: {
            if (!bigPictureOpen && !detailOpen && !settingsOpen
                    && !updateOpen && !addOpen && !artOpen) {
                bigPictureOpen = true;
            }
        }
    }

    Shortcut {
        sequence: "Ctrl+,"
        enabled: !window.bigPictureOpen
        onActivated: settingsOpen = true
    }

    Shortcut {
        sequence: "Ctrl+F"
        enabled: !window.bigPictureOpen
        onActivated: topBar.focusSearch()
    }
}
