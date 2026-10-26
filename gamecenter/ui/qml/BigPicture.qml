import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "bigPicture"

    property bool opened: false
    property bool appActive: true
    signal closeRequested()

    property string filter: "all"
    property int selectedIndex: 0
    property bool exitConfirmOpen: false
    property int exitFocus: 0
    property string status: ""
    property double openedAt: 0
    property bool detailOpen: false
    property var detailGame: ({})

    readonly property real uiScale: Math.max(1, Math.min(1.5, height / 800))
    readonly property real heroHeight: Math.max(170, Math.min(520, (height - 230) * 0.38))
    readonly property real carouselHeight: Math.max(190, Math.min(640, (height - 230) * 0.48))
    readonly property real smallCardWidth: Math.max(100, carouselHeight * 0.62)
    readonly property real smallCardHeight: carouselHeight * 0.74
    readonly property real cinematicCardWidth: carouselHeight * 0.98
    readonly property real coverWidth: heroHeight * 0.8

    readonly property var games: {
        var list = (Library.bigPictureGames || []).slice();
        if (filter === "favorites") {
            list = list.filter(function(item) { return item.favorite; });
        } else if (filter === "recent") {
            list = list.sort(function(a, b) {
                return (b.lastPlayedTimestamp || 0) - (a.lastPlayedTimestamp || 0);
            });
        }
        return list;
    }

    readonly property var selected: {
        if (!games.length) {
            return ({});
        }
        var index = Math.max(0, Math.min(selectedIndex, games.length - 1));
        return games[index];
    }

    readonly property var hints: {
        if (root.detailOpen) {
            if (Gamepad.connected) {
                return [
                    { key: "A", label: Tr.strings["Play"] },
                    { key: "B", label: Tr.strings["Back"] },
                    { key: "↑ ↓", label: Tr.strings["Select"] },
                    { key: "Start", label: Tr.strings["Exit"] }
                ];
            }
            return [
                { key: "Enter", label: Tr.strings["Play"] },
                { key: "Esc", label: Tr.strings["Back"] },
                { key: "↑ ↓", label: Tr.strings["Select"] },
                { key: "I", label: Tr.strings["Details"] }
            ];
        }
        if (Gamepad.connected) {
            return [
                { key: "A", label: Tr.strings["Play"] },
                { key: "B", label: Tr.strings["Back"] },
                { key: "Y", label: Tr.strings["Details"] },
                { key: "LB / RB", label: Tr.strings["Filter"] },
                { key: "X", label: Tr.strings["Favorite"] },
                { key: "Start", label: Tr.strings["Exit"] }
            ];
        }
        return [
            { key: "← →", label: Tr.strings["Select"] },
            { key: "Enter", label: Tr.strings["Play"] },
            { key: "I", label: Tr.strings["Details"] },
            { key: "Esc", label: Tr.strings["Exit"] },
            { key: "[ ]", label: Tr.strings["Filter"] },
            { key: "F", label: Tr.strings["Favorite"] }
        ];
    }

    visible: opacity > 0
    opacity: opened ? 1 : 0
    focus: opened
    z: 60

    Behavior on opacity { NumberAnimation { duration: 180 } }

    function clampSelection() {
        if (selectedIndex >= games.length) {
            selectedIndex = Math.max(0, games.length - 1);
        }
    }

    onGamesChanged: clampSelection()

    onOpenedChanged: {
        if (opened) {
            selectedIndex = 0;
            exitConfirmOpen = false;
            exitFocus = 0;
            status = "";
            filter = "all";
            detailOpen = false;
            detailGame = ({});
            openedAt = Date.now();
            forceActiveFocus();
        } else {
            Gamepad.showCursor();
        }
    }

    onSelectedIndexChanged: {
        if (typeof carousel !== "undefined" && carousel !== null && games.length) {
            Qt.callLater(function() {
                carousel.positionViewAtIndex(selectedIndex, ListView.Center);
            });
        }
    }

    function moveSelection(dx) {
        if (!games.length) {
            return;
        }
        selectedIndex = Math.max(0, Math.min(games.length - 1,
                                            selectedIndex + dx));
        Qt.callLater(function() {
            carousel.positionViewAtIndex(selectedIndex, ListView.Center);
        });
    }

    function cycleFilter(delta) {
        var order = ["all", "recent", "favorites"];
        var current = order.indexOf(filter);
        filter = order[(current + delta + order.length) % order.length];
        selectedIndex = 0;
        Qt.callLater(function() {
            if (carousel.count > 0) {
                carousel.positionViewAtIndex(0, ListView.Beginning);
            }
        });
    }

    function toggleFavorite() {
        if (!selected.id) {
            return;
        }
        Library.toggleFavoriteById(selected.id);
    }

    function toggleDetailFavorite() {
        if (!detailGame.id) {
            return;
        }
        Library.toggleFavoriteById(detailGame.id);
        detailGame = Library.gameDetailById(detailGame.id);
    }

    function openDetail() {
        if (!selected.id) {
            return;
        }
        detailGame = Library.gameDetailById(selected.id);
        detailOpen = true;
        Library.loadDetailsById(selected.id);
    }

    function launchGame(gameId, title) {
        if (!gameId) {
            return;
        }
        var session = Library.launchById(gameId);
        if (session) {
            status = Tr.strings["Launching..."] + " " + (title || "");
        } else {
            status = Tr.strings["Couldn't launch the game."];
        }
        statusTimer.restart();
    }

    function launchSelected() {
        launchGame(selected.id, selected.title);
    }

    function requestExit() {
        exitConfirmOpen = true;
        exitFocus = 0;
    }

    function activateExitFocus() {
        if (exitFocus === 1) {
            root.closeRequested();
        } else {
            exitConfirmOpen = false;
        }
    }

    Keys.onPressed: (event) => {
        if (root.exitConfirmOpen) {
            if (event.key === Qt.Key_Left) {
                root.exitFocus = 0;
                event.accepted = true;
            } else if (event.key === Qt.Key_Right) {
                root.exitFocus = 1;
                event.accepted = true;
            } else if (event.key === Qt.Key_Return
                       || event.key === Qt.Key_Enter
                       || event.key === Qt.Key_Space) {
                root.activateExitFocus();
                event.accepted = true;
            } else if (event.key === Qt.Key_Escape
                       || event.key === Qt.Key_Backspace) {
                root.exitConfirmOpen = false;
                event.accepted = true;
            }
            return;
        }

        if (root.detailOpen) {
            if (event.key === Qt.Key_Up) {
                gameModal.scrollBy(-120);
                event.accepted = true;
            } else if (event.key === Qt.Key_Down) {
                gameModal.scrollBy(120);
                event.accepted = true;
            } else if (event.key === Qt.Key_Escape
                       || event.key === Qt.Key_Backspace
                       || event.key === Qt.Key_I
                       || event.key === Qt.Key_D) {
                root.detailOpen = false;
                event.accepted = true;
            } else if (event.key === Qt.Key_Return
                       || event.key === Qt.Key_Enter
                       || event.key === Qt.Key_Space) {
                root.detailOpen = false;
                root.launchGame(root.detailGame.id, root.detailGame.title);
                event.accepted = true;
            } else if (event.key === Qt.Key_F) {
                root.toggleDetailFavorite();
                event.accepted = true;
            }
            return;
        }

        if (event.key === Qt.Key_Left) {
            root.moveSelection(-1);
            event.accepted = true;
        } else if (event.key === Qt.Key_Right) {
            root.moveSelection(1);
            event.accepted = true;
        } else if (event.key === Qt.Key_Up) {
            root.cycleFilter(-1);
            event.accepted = true;
        } else if (event.key === Qt.Key_Down) {
            root.cycleFilter(1);
            event.accepted = true;
        } else if (event.key === Qt.Key_Return
                   || event.key === Qt.Key_Enter
                   || event.key === Qt.Key_Space) {
            root.launchSelected();
            event.accepted = true;
        } else if (event.key === Qt.Key_Escape
                   || event.key === Qt.Key_Backspace) {
            root.requestExit();
            event.accepted = true;
        } else if (event.key === Qt.Key_I
                   || event.key === Qt.Key_D) {
            root.openDetail();
            event.accepted = true;
        } else if (event.key === Qt.Key_F) {
            root.toggleFavorite();
            event.accepted = true;
        } else if (event.key === Qt.Key_BracketLeft
                   || event.key === Qt.Key_PageUp) {
            root.cycleFilter(-1);
            event.accepted = true;
        } else if (event.key === Qt.Key_BracketRight
                   || event.key === Qt.Key_PageDown) {
            root.cycleFilter(1);
            event.accepted = true;
        }
    }

    Connections {
        target: Gamepad
        function onNavigate(dx, dy) {
            if (!root.opened || !root.appActive) {
                return;
            }
            if (root.exitConfirmOpen) {
                if (dx < 0) {
                    root.exitFocus = 0;
                } else if (dx > 0) {
                    root.exitFocus = 1;
                }
                return;
            }
            if (root.detailOpen) {
                if (dy !== 0) {
                    gameModal.scrollBy(dy > 0 ? 120 : -120);
                }
                return;
            }
            if (dx !== 0) {
                root.moveSelection(dx);
            } else if (dy !== 0) {
                root.cycleFilter(dy > 0 ? 1 : -1);
            }
        }

        function onAccept() {
            if (!root.opened || !root.appActive) {
                return;
            }
            if (root.exitConfirmOpen) {
                root.activateExitFocus();
            } else if (root.detailOpen) {
                root.detailOpen = false;
                root.launchGame(root.detailGame.id, root.detailGame.title);
            } else {
                root.launchSelected();
            }
        }

        function onBack() {
            if (!root.opened || !root.appActive) {
                return;
            }
            if (root.exitConfirmOpen) {
                root.exitConfirmOpen = false;
            } else if (root.detailOpen) {
                root.detailOpen = false;
            }
        }

        function onMenu() {
            if (!root.opened || !root.appActive
                    || Date.now() - root.openedAt < 500) {
                return;
            }
            root.closeRequested();
        }

        function onPageLeft() {
            if (!root.opened || !root.appActive
                    || root.exitConfirmOpen || root.detailOpen) {
                return;
            }
            root.cycleFilter(-1);
        }

        function onPageRight() {
            if (!root.opened || !root.appActive
                    || root.exitConfirmOpen || root.detailOpen) {
                return;
            }
            root.cycleFilter(1);
        }

        function onFavorite() {
            if (!root.opened || !root.appActive || root.exitConfirmOpen) {
                return;
            }
            if (root.detailOpen) {
                root.toggleDetailFavorite();
            } else {
                root.toggleFavorite();
            }
        }

        function onDetails() {
            if (!root.opened || !root.appActive || root.exitConfirmOpen) {
                return;
            }
            if (root.detailOpen) {
                root.detailOpen = false;
            } else {
                root.openDetail();
            }
        }
    }

    Connections {
        target: Library
        function onDetailsChanged() {
            if (root.opened && root.detailOpen && root.detailGame.id) {
                root.detailGame = Library.gameDetailById(root.detailGame.id);
            }
        }
        function onFailed(message) {
            if (root.opened) {
                root.status = message;
                statusTimer.restart();
            }
        }
    }

    Timer {
        id: statusTimer
        interval: 2400
        repeat: false
        onTriggered: root.status = ""
    }

    Timer {
        interval: 1000
        running: root.opened
        repeat: true
        triggeredOnStart: true
        onTriggered: clock.text = Qt.formatTime(new Date(), "hh:mm")
    }

    Rectangle {
        anchors.fill: parent
        color: "#05070b"
    }

    Image {
        anchors.fill: parent
        source: root.selected.cover || ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: true
        opacity: 0.18
        smooth: true
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#cc05070b" }
            GradientStop { position: 0.45; color: "#99070a10" }
            GradientStop { position: 1.0; color: "#f005070b" }
        }
    }

    RowLayout {
        id: topBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 22 * root.uiScale
        anchors.rightMargin: 22 * root.uiScale
        anchors.topMargin: 10 * root.uiScale
        height: 36 * root.uiScale
        spacing: 10 * root.uiScale

        Text {
            text: "GAMECENTER"
            color: "#f2f5fa"
            font.family: "Chakra Petch"
            font.pixelSize: 15 * root.uiScale
            font.bold: true
            font.letterSpacing: 2.0
        }

        Text {
            text: Tr.strings["BIG PICTURE"]
            color: Library.accent
            font.family: "Chakra Petch"
            font.pixelSize: 9 * root.uiScale
            font.bold: true
            font.letterSpacing: 2.2
        }

        Item { Layout.fillWidth: true }

        Row {
            spacing: 7 * root.uiScale
            Layout.alignment: Qt.AlignVCenter

            Rectangle {
                width: 6 * root.uiScale
                height: 6 * root.uiScale
                radius: width / 2
                color: Gamepad.connected ? "#3ddc97" : "#5f6a7b"
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: Gamepad.connected
                      ? Tr.strings["Controller connected"]
                      : Tr.strings["Keyboard & mouse"]
                color: "#8b95a5"
                font.family: "Sora"
                font.pixelSize: 9 * root.uiScale
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Text {
            id: clock
            color: "#dfe6f0"
            font.family: "Chakra Petch"
            font.pixelSize: 12 * root.uiScale
            font.letterSpacing: 1.0
            Layout.leftMargin: 8 * root.uiScale
        }

        Rectangle {
            width: 88 * root.uiScale
            height: 32 * root.uiScale
            radius: 8 * root.uiScale
            color: exitArea.containsMouse ? "#202633" : "#11161f"
            border.width: 1
            border.color: exitArea.containsMouse ? Library.accent : "#2a3444"

            Text {
                anchors.centerIn: parent
                text: Tr.strings["Exit"]
                color: exitArea.containsMouse ? Library.accent : "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 10 * root.uiScale
            }

            MouseArea {
                id: exitArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.requestExit()
            }
        }
    }

    ColumnLayout {
        anchors.top: topBar.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.leftMargin: 24 * root.uiScale
        anchors.rightMargin: 24 * root.uiScale
        anchors.topMargin: 8 * root.uiScale
        anchors.bottomMargin: 12 * root.uiScale
        spacing: 10 * root.uiScale

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: root.heroHeight
            Layout.maximumHeight: root.heroHeight
            spacing: 22 * root.uiScale

            Rectangle {
                Layout.preferredWidth: root.coverWidth
                Layout.preferredHeight: root.heroHeight
                radius: 18
                color: "#0d1118"
                border.width: 1
                border.color: "#2a3444"
                clip: true

                Image {
                    anchors.fill: parent
                    source: root.selected.cover || ""
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: true
                    smooth: true
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 76
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#00000000" }
                        GradientStop { position: 1.0; color: "#cc05070b" }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: root.heroHeight
                spacing: 10

                RowLayout {
                    spacing: 8

                    Rectangle {
                        width: sourceLabel.implicitWidth + 18
                        height: 25
                        radius: 12.5
                        color: "#121a27"
                        border.width: 1
                        border.color: "#2a3a52"

                        Text {
                            id: sourceLabel
                            anchors.centerIn: parent
                            text: (root.selected.source || "").toUpperCase()
                            color: Library.accent
                            font.family: "Chakra Petch"
                            font.pixelSize: 9
                            font.bold: true
                            font.letterSpacing: 1.2
                        }
                    }

                    Rectangle {
                        width: 88
                        height: 25
                        radius: 12.5
                        color: "#121a27"
                        border.width: 1
                        border.color: "#2a3a52"

                        Text {
                            anchors.centerIn: parent
                            text: root.selected.installed
                                  ? Tr.strings["Installed"]
                                  : Tr.strings["Not installed"]
                            color: "#aeb8c7"
                            font.family: "Sora"
                            font.pixelSize: 9
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: root.selected.title || ""
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: Math.max(26, Math.min(54, root.height * 0.05))
                    font.bold: true
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }

                Text {
                    Layout.fillWidth: true
                    text: root.selected.meta || ""
                    color: "#6f7887"
                    font.family: "Sora"
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 14

                    Repeater {
                        model: {
                            var chips = [];
                            if (root.selected.playtimeText) {
                                chips.push(root.selected.playtimeText);
                            }
                            if (root.selected.lastPlayed) {
                                chips.push(root.selected.lastPlayed);
                            }
                            if (root.selected.sizeText) {
                                chips.push(root.selected.sizeText);
                            }
                            return chips;
                        }

                        Row {
                            spacing: 6

                            Rectangle {
                                width: 5
                                height: 5
                                radius: 2.5
                                color: "#4cc9f0"
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: modelData
                                color: "#9aa6b7"
                                font.family: "Sora"
                                font.pixelSize: 10
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    spacing: 14

                    Rectangle {
                        width: 224 * root.uiScale
                        height: 52 * root.uiScale
                        radius: 26 * root.uiScale
                        color: playArea.pressed
                               ? Qt.darker(Library.accent, 1.2)
                               : Library.accent

                        Row {
                            anchors.centerIn: parent
                            spacing: 10 * root.uiScale

                            Rectangle {
                                width: 22 * root.uiScale
                                height: 22 * root.uiScale
                                radius: width / 2
                                color: "#0b1720"
                                anchors.verticalCenter: parent.verticalCenter

                                Text {
                                    anchors.centerIn: parent
                                    text: "A"
                                    color: Library.accent
                                    font.family: "Chakra Petch"
                                    font.pixelSize: 10 * root.uiScale
                                    font.bold: true
                                }
                            }

                            Canvas {
                                width: 13 * root.uiScale
                                height: 15 * root.uiScale
                                anchors.verticalCenter: parent.verticalCenter
                                onPaint: {
                                    var ctx = getContext("2d");
                                    ctx.reset();
                                    ctx.fillStyle = Library.accentText;
                                    ctx.beginPath();
                                    ctx.moveTo(0, 0);
                                    ctx.lineTo(width, height / 2);
                                    ctx.lineTo(0, height);
                                    ctx.closePath();
                                    ctx.fill();
                                }
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: Tr.strings["Play"]
                                color: Library.accentText
                                font.family: "Sora"
                                font.pixelSize: 14 * root.uiScale
                                font.bold: true
                            }
                        }

                        MouseArea {
                            id: playArea
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.launchSelected()
                        }
                    }

                    Rectangle {
                        width: 142 * root.uiScale
                        height: 52 * root.uiScale
                        radius: 26 * root.uiScale
                        color: detailsArea.containsMouse ? "#1b2535" : "#121a27"
                        border.width: 1
                        border.color: detailsArea.containsMouse
                                      ? Library.accent
                                      : "#2a3a52"

                        Row {
                            anchors.centerIn: parent
                            spacing: 8 * root.uiScale

                            Rectangle {
                                width: 22 * root.uiScale
                                height: 22 * root.uiScale
                                radius: width / 2
                                color: "#0b1720"
                                border.width: 1
                                border.color: "#35506e"
                                anchors.verticalCenter: parent.verticalCenter

                                Text {
                                    anchors.centerIn: parent
                                    text: "Y"
                                    color: Library.accent
                                    font.family: "Chakra Petch"
                                    font.pixelSize: 10 * root.uiScale
                                    font.bold: true
                                }
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: Tr.strings["Details"]
                                color: detailsArea.containsMouse
                                       ? Library.accent
                                       : "#dfe6f0"
                                font.family: "Sora"
                                font.pixelSize: 12 * root.uiScale
                            }
                        }

                        MouseArea {
                            id: detailsArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.openDetail()
                        }
                    }

                    FavoriteButton {
                        favorite: !!root.selected.favorite
                        onToggled: root.toggleFavorite()
                    }

                    Item { Layout.fillWidth: true }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { label: "All games", value: "all" },
                    { label: "Recent", value: "recent" },
                    { label: "Favorites", value: "favorites" }
                ]

                delegate: Rectangle {
                    readonly property bool selected: root.filter === modelData.value
                    width: 112 * root.uiScale
                    height: 32 * root.uiScale
                    radius: 16 * root.uiScale
                    color: selected ? "#1e2c42" : "#101722"
                    border.width: 1
                    border.color: selected ? Library.accent : "#243044"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings[modelData.label]
                        color: selected ? "#f2f5fa" : "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 10 * root.uiScale
                        font.bold: selected
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.filter = modelData.value;
                            root.selectedIndex = 0;
                        }
                    }
                }
            }

            Item { Layout.fillWidth: true }

            Text {
                text: Tr.strings["%1 games"].arg(root.games.length)
                color: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 10 * root.uiScale
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: root.carouselHeight
            spacing: 8

            Rectangle {
                visible: root.games.length > 1
                z: 5
                width: 34 * root.uiScale
                height: 34 * root.uiScale
                radius: 17 * root.uiScale
                Layout.alignment: Qt.AlignVCenter
                opacity: root.selectedIndex > 0 ? 1 : 0.3
                color: leftArea.containsMouse ? "#242c3a" : "#101722"
                border.width: 1
                border.color: leftArea.containsMouse ? Library.accent : "#2a3444"

                Text {
                    anchors.centerIn: parent
                    text: "‹"
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 20 * root.uiScale
                }

                MouseArea {
                    id: leftArea
                    anchors.fill: parent
                    enabled: root.selectedIndex > 0
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.moveSelection(-1)
                }
            }

            ListView {
                id: carousel
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: ListView.Horizontal
                spacing: 14
                clip: true
                model: root.games
                currentIndex: root.selectedIndex
                boundsBehavior: Flickable.StopAtBounds
                snapMode: ListView.SnapToItem
                cacheBuffer: 900
                focus: false

                onCurrentIndexChanged: {
                    if (currentIndex !== root.selectedIndex) {
                        root.selectedIndex = currentIndex;
                    }
                }

                delegate: Item {
                    id: card
                    readonly property bool current: ListView.isCurrentItem

                    width: current ? root.cinematicCardWidth : root.smallCardWidth
                    height: current ? carousel.height - 4 : root.smallCardHeight
                    y: (carousel.height - height) / 2
                    opacity: current ? 1
                                     : (Math.abs(index - carousel.currentIndex) <= 1
                                        ? 0.62 : 0.34)
                    z: current ? 5 : 1

                    Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                    Behavior on height { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }
                    Behavior on opacity { NumberAnimation { duration: 220 } }

                    Rectangle {
                        anchors.fill: parent
                        radius: 16
                        color: Library.accent
                        opacity: card.current ? 0.16 : 0
                        scale: 1.04
                        z: -1
                    }

                    Rectangle {
                        width: parent.width
                        height: parent.height - 24
                        radius: 14
                        color: "#0d1118"
                        border.width: 2
                        border.color: card.current ? Library.accent : "#243044"
                        clip: true

                        Image {
                            anchors.fill: parent
                            source: modelData.cover || ""
                            fillMode: card.current
                                       ? Image.PreserveAspectCrop
                                       : Image.PreserveAspectFit
                            asynchronous: true
                            cache: true
                            smooth: true
                        }
                    }

                    Text {
                        width: parent.width
                        y: parent.height - 21
                        text: modelData.title || ""
                        color: card.current ? "#f2f5fa" : "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 10 * root.uiScale
                        font.bold: card.current
                        horizontalAlignment: Text.AlignHCenter
                        elide: Text.ElideRight
                        maximumLineCount: 1
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.selectedIndex = index;
                        }
                        onDoubleClicked: root.launchSelected()
                    }
                }
            }

            Rectangle {
                visible: root.games.length > 1
                z: 5
                width: 34 * root.uiScale
                height: 34 * root.uiScale
                radius: 17 * root.uiScale
                Layout.alignment: Qt.AlignVCenter
                opacity: root.selectedIndex < root.games.length - 1 ? 1 : 0.3
                color: rightArea.containsMouse ? "#242c3a" : "#101722"
                border.width: 1
                border.color: rightArea.containsMouse ? Library.accent : "#2a3444"

                Text {
                    anchors.centerIn: parent
                    text: "›"
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 20 * root.uiScale
                }

                MouseArea {
                    id: rightArea
                    anchors.fill: parent
                    enabled: root.selectedIndex < root.games.length - 1
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.moveSelection(1)
                }
            }
        }

        Text {
            visible: root.games.length === 0
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            text: Tr.strings["No games in your library"]
            color: "#6f7887"
            font.family: "Sora"
            font.pixelSize: 13
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            Flow {
                Layout.fillWidth: true
                spacing: 14

                Repeater {
                    model: root.hints

                    Row {
                        spacing: 6

                        Rectangle {
                            width: Math.max(24, hintKey.implicitWidth + 12)
                            height: 23
                            radius: 6
                            color: "#141c28"
                            border.width: 1
                            border.color: "#2a3a52"

                            Text {
                                id: hintKey
                                anchors.centerIn: parent
                                text: modelData.key
                                color: "#c9d2e0"
                                font.family: "Chakra Petch"
                                font.pixelSize: 9
                                font.bold: true
                            }
                        }

                        Text {
                            text: modelData.label
                            color: "#8b95a5"
                            font.family: "Sora"
                            font.pixelSize: 9
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }
            }

            Text {
                Layout.maximumWidth: 360
                text: Tr.strings["Click to select · Double-click to play"]
                color: "#4f5b6d"
                font.family: "Sora"
                font.pixelSize: 9
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideRight
            }
        }
    }

    Rectangle {
        visible: root.status !== ""
        z: 5
        width: statusLabel.implicitWidth + 34
        height: 36
        radius: 18
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 64
        color: "#141c28"
        border.width: 1
        border.color: "#2a3a52"

        Text {
            id: statusLabel
            anchors.centerIn: parent
            text: root.status
            color: "#dfe6f0"
            font.family: "Sora"
            font.pixelSize: 11
        }
    }

    Rectangle {
        anchors.fill: parent
        visible: root.exitConfirmOpen
        z: 20
        color: "#05070b"
        opacity: 0.84

        MouseArea {
            anchors.fill: parent
            onClicked: root.exitConfirmOpen = false
        }

        Rectangle {
            width: 470
            height: 224
            radius: 20
            anchors.centerIn: parent
            color: "#11161f"
            border.width: 1
            border.color: "#2a3444"

            MouseArea { anchors.fill: parent }

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 24
                spacing: 10

                Text {
                    Layout.fillWidth: true
                    text: Tr.strings["Exit Big Picture?"]
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 21
                    font.bold: true
                }

                Item { Layout.fillHeight: true }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        width: 130
                        height: 42
                        radius: 10
                        color: root.exitFocus === 0 ? "#202633" : "#121722"
                        border.width: 1
                        border.color: root.exitFocus === 0
                                      ? Library.accent
                                      : "#2a3444"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Cancel"]
                            color: "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: root.exitFocus = 0
                            onClicked: root.exitConfirmOpen = false
                        }
                    }

                    Rectangle {
                        width: 130
                        height: 42
                        radius: 10
                        color: root.exitFocus === 1
                               ? Qt.darker(Library.accent, 1.15)
                               : "#121722"
                        border.width: 1
                        border.color: root.exitFocus === 1
                                      ? Library.accent
                                      : "#2a3444"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Exit"]
                            color: root.exitFocus === 1
                                   ? Library.accentText
                                   : "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 11
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onEntered: root.exitFocus = 1
                            onClicked: root.closeRequested()
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: "A " + Tr.strings["Select"] + "  ·  B " + Tr.strings["Back"]
                    color: "#5f6a7b"
                    font.family: "Sora"
                    font.pixelSize: 9
                    horizontalAlignment: Text.AlignRight
                }
            }
        }
    }

    GameDetail {
        id: gameModal
        z: 70
        anchors.fill: parent
        opened: root.detailOpen
        game: root.detailGame
        showArt: false
        onCloseRequested: root.detailOpen = false
        onPlayRequested: {
            root.detailOpen = false;
            root.launchGame(root.detailGame.id, root.detailGame.title);
        }
        onFolderRequested: Library.openFolderById(root.detailGame.id)
        onCopyRequested: Library.copyAppIdById(root.detailGame.id)
        onFavoriteRequested: {
            Library.toggleFavoriteById(root.detailGame.id);
            root.detailGame = Library.gameDetailById(root.detailGame.id);
        }
        onArtRequested: {}
    }
}
