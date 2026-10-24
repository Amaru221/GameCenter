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
    property bool demoInsert: false

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
        onToastRequested: (message) => toast.show(message)
        onSettingsRequested: settingsOpen = true
    }

    Toolbar {
        id: toolbar
        width: parent.width
        anchors.top: topBar.bottom
        onToastRequested: (message) => toast.show(message)
    }

    LibraryGrid {
        anchors.top: toolbar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 24
        anchors.rightMargin: 24
        anchors.bottomMargin: 78

        onDetailRequested: (index) => {
            detailIndex = index;
            detailGame = Library.gameAt(index);
            detailOpen = true;
        }
    }

    Dock {
        id: dock
        z: 20
        inserting: insertEffect.running
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 10
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
    }

    Connections {
        target: Library
        function onFailed(message) { toast.show(message) }
        function onArtChanged() {
            if (detailOpen) {
                detailGame = Library.gameAt(detailIndex);
            }
            artOpen = false;
        }
    }

    Shortcut {
        sequence: "F5"
        onActivated: Library.refresh()
    }

    Shortcut {
        sequence: "Escape"
        onActivated: {
            if (settingsOpen) {
                settingsOpen = false;
            } else if (artOpen) {
                artOpen = false;
            } else if (detailOpen) {
                detailOpen = false;
            }
        }
    }

    Shortcut {
        sequence: "Ctrl+,"
        onActivated: settingsOpen = true
    }

    Shortcut {
        sequence: "Ctrl+F"
        onActivated: topBar.focusSearch()
    }
}
