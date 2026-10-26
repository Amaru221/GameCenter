import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var game: ({})
    property bool opened: false
    property bool descriptionExpanded: false
    property bool showArt: true

    signal closeRequested()
    signal playRequested()
    signal folderRequested()
    signal copyRequested()
    signal favoriteRequested()
    signal artRequested()

    readonly property var history: root.game.history || []

    function cartridgeCenter() {
        if (detailCard.item) {
            var item = detailCard.item;
            var point = item.mapToItem(root, item.width / 2, item.height / 2);
            return Qt.point(point.x, point.y);
        }
        if (compactCover.visible) {
            var coverPoint = compactCover.mapToItem(
                root, compactCover.width / 2, compactCover.height / 2
            );
            return Qt.point(coverPoint.x, coverPoint.y);
        }
        return Qt.point(root.width / 2, root.height / 2);
    }

    function sessionDate(timestamp) {
        if (!timestamp) {
            return "";
        }
        return Qt.formatDateTime(new Date(timestamp * 1000), "dd/MM/yyyy · HH:mm");
    }

    function historyMax() {
        var peak = 1;
        for (var i = 0; i < root.history.length; i++) {
            peak = Math.max(peak, root.history[i].seconds || 0);
        }
        return peak;
    }

    function scrollBy(delta) {
        var maximum = Math.max(0, scroller.contentHeight - scroller.height);
        scroller.contentY = Math.max(
            0, Math.min(maximum, scroller.contentY + delta)
        );
    }

    readonly property var infoChips: {
        var out = [];
        if (root.game.sizeText) {
            out.push(root.game.sizeText);
        }
        out.push(root.game.installed !== false
                 ? Tr.strings["Installed"]
                 : Tr.strings["Not installed"]);
        if (root.game.playtimeText) {
            out.push(root.game.playtimeText);
        }
        if (root.game.lastPlayed) {
            out.push(root.game.lastPlayed);
        }
        if (root.game.genres) {
            out.push(root.game.genres);
        }
        if (root.game.developers) {
            out.push(root.game.developers);
        }
        return out;
    }

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    onOpenedChanged: {
        if (opened) {
            descriptionExpanded = false;
            scroller.contentY = 0;
            Qt.callLater(function() { scroller.contentY = 0; });
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#05060a"
        opacity: 0.84

        MouseArea {
            anchors.fill: parent
            onClicked: root.closeRequested()
        }
    }

    Rectangle {
        id: panel
        readonly property bool compact: width < 900

        width: Math.min(parent.width - 36, 1080)
        height: Math.min(parent.height - 36, 780)
        anchors.centerIn: parent
        radius: 22
        border.width: 1
        border.color: "#2a3140"

        gradient: Gradient {
            GradientStop { position: 0.0; color: "#161b25" }
            GradientStop { position: 0.55; color: "#10141c" }
            GradientStop { position: 1.0; color: "#0a0d12" }
        }

        scale: root.opened ? 1 : 0.97
        Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

        MouseArea { anchors.fill: parent }

        Flickable {
            id: scroller
            anchors.fill: parent
            anchors.margins: panel.compact ? 20 : 28
            contentWidth: width - 16
            contentHeight: content.implicitHeight
            clip: true
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                id: scrollBar
                policy: ScrollBar.AsNeeded
                width: 8
                background: Item {}
                contentItem: Rectangle {
                    implicitWidth: 6
                    radius: 3
                    color: "#3a465c"
                    opacity: scrollBar.pressed ? 1 : 0.55
                }
            }

            ColumnLayout {
                id: content
                width: scroller.width - 16
                spacing: 16

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Rectangle {
                        width: 5
                        height: 5
                        radius: 2.5
                        color: Library.accent
                    }

                    Text {
                        text: (root.game.source || "").toUpperCase()
                        color: "#8b95a5"
                        font.family: "Chakra Petch"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 2.4
                    }

                    Rectangle {
                        visible: (root.game.releaseDate || "") !== ""
                        width: releaseLabel.implicitWidth + 16
                        height: 20
                        radius: 10
                        color: "#121722"
                        border.width: 1
                        border.color: "#232a36"

                        Text {
                            id: releaseLabel
                            anchors.centerIn: parent
                            text: root.game.releaseDate || ""
                            color: "#8b95a5"
                            font.family: "Sora"
                            font.pixelSize: 10
                        }
                    }

                    Item { Layout.fillWidth: true }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: panel.compact ? 16 : 30

                    Item {
                        Layout.preferredWidth: panel.compact ? 0 : 300
                        Layout.minimumHeight: panel.compact ? 0 : 330
                        Layout.fillHeight: true
                        visible: !panel.compact

                        Loader {
                            id: detailCard
                            anchors.centerIn: parent
                            active: root.opened && !panel.compact
                            sourceComponent: Library.cartridgeStyle === "ds"
                                             ? ds3dCard
                                             : flatCard
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop
                        spacing: 14

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 16

                            Rectangle {
                                id: compactCover
                                visible: panel.compact
                                width: 84
                                height: 112
                                radius: 10
                                color: "#0d0f14"
                                border.width: 1
                                border.color: "#2a3140"
                                clip: true

                                Image {
                                    anchors.fill: parent
                                    source: root.game.cover || ""
                                    fillMode: Image.PreserveAspectCrop
                                    asynchronous: true
                                    cache: true
                                    smooth: true
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 6

                                Text {
                                    Layout.fillWidth: true
                                    text: root.game.title || ""
                                    color: "#f2f5fa"
                                    font.family: "Sora"
                                    font.pixelSize: panel.compact ? 24 : 30
                                    font.bold: true
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                }
                            }

                            FavoriteButton {
                                Layout.alignment: Qt.AlignTop
                                favorite: !!root.game.favorite
                                onToggled: root.favoriteRequested()
                            }
                        }

                        Text {
                            text: Tr.strings["ABOUT"]
                            color: "#8b95a5"
                            font.family: "Chakra Petch"
                            font.pixelSize: 10
                            font.bold: true
                            font.letterSpacing: 2.2
                        }

                        Text {
                            Layout.fillWidth: true
                            text: {
                                var description = root.game.description || "";
                                if (description) {
                                    return description;
                                }
                                return root.game.detailsLoaded
                                       ? Tr.strings["No description available."]
                                       : Tr.strings["Loading description..."];
                            }
                            color: (root.game.description || "") !== ""
                                   ? "#b9c3d2"
                                   : "#6f7887"
                            font.family: "Sora"
                            font.pixelSize: panel.compact ? 12 : 13
                            wrapMode: Text.WordWrap
                            lineHeight: 1.3
                            maximumLineCount: root.descriptionExpanded
                                              ? 1000
                                              : (panel.compact ? 4 : 6)
                            elide: Text.ElideRight
                        }

                        Text {
                            visible: (root.game.description || "").length > 240
                            text: root.descriptionExpanded
                                  ? Tr.strings["Show less"]
                                  : Tr.strings["Read more"]
                            color: Library.accent
                            font.family: "Sora"
                            font.pixelSize: 11

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: root.descriptionExpanded = !root.descriptionExpanded
                            }
                        }

                        Flow {
                            Layout.fillWidth: true
                            spacing: 8

                            Repeater {
                                model: root.infoChips

                                Rectangle {
                                    width: chipLabel.implicitWidth + 22
                                    height: 26
                                    radius: 13
                                    color: "#121722"
                                    border.width: 1
                                    border.color: "#232a36"

                                    Text {
                                        id: chipLabel
                                        anchors.centerIn: parent
                                        text: modelData
                                        color: "#aeb8c7"
                                        font.family: "Sora"
                                        font.pixelSize: 10
                                    }
                                }
                            }
                        }

                        Flow {
                            Layout.fillWidth: true
                            spacing: 10

                            Rectangle {
                                width: 150
                                height: 42
                                radius: 11
                                color: playArea.pressed
                                       ? Qt.darker(Library.accent, 1.2)
                                       : Library.accent

                                Row {
                                    anchors.centerIn: parent
                                    spacing: 9

                                    Canvas {
                                        width: 12
                                        height: 14
                                        anchors.verticalCenter: parent.verticalCenter
                                        onPaint: {
                                            var ctx = getContext("2d");
                                            ctx.reset();
                                            ctx.fillStyle = Library.accentText;
                                            ctx.beginPath();
                                            ctx.moveTo(0, 0);
                                            ctx.lineTo(12, 7);
                                            ctx.lineTo(0, 14);
                                            ctx.closePath();
                                            ctx.fill();
                                        }
                                    }

                                    Text {
                                        anchors.verticalCenter: parent.verticalCenter
                                        text: Tr.strings["Play"]
                                        color: Library.accentText
                                        font.family: "Sora"
                                        font.pixelSize: 13
                                        font.bold: true
                                    }
                                }

                                MouseArea {
                                    id: playArea
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.playRequested()
                                }
                            }

                            Rectangle {
                                width: 132
                                height: 42
                                radius: 10
                                color: folderArea.containsMouse ? "#202633" : "#151a23"
                                border.width: 1
                                border.color: "#2a3140"

                                Text {
                                    anchors.centerIn: parent
                                    text: Tr.strings["Open folder"]
                                    color: "#cfd6e2"
                                    font.family: "Sora"
                                    font.pixelSize: 11
                                }

                                MouseArea {
                                    id: folderArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.folderRequested()
                                }
                            }

                            Rectangle {
                                width: 132
                                height: 42
                                radius: 10
                                color: copyArea.containsMouse ? "#202633" : "#151a23"
                                border.width: 1
                                border.color: "#2a3140"

                                Text {
                                    anchors.centerIn: parent
                                    text: Tr.strings["Copy App ID"]
                                    color: "#cfd6e2"
                                    font.family: "Sora"
                                    font.pixelSize: 11
                                }

                                MouseArea {
                                    id: copyArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.copyRequested()
                                }
                            }

                            Rectangle {
                                visible: root.showArt
                                width: 132
                                height: 42
                                radius: 10
                                color: artArea.containsMouse ? "#202633" : "#151a23"
                                border.width: 1
                                border.color: "#2a3140"

                                Text {
                                    anchors.centerIn: parent
                                    text: Tr.strings["Choose art"]
                                    color: "#cfd6e2"
                                    font.family: "Sora"
                                    font.pixelSize: 11
                                }

                                MouseArea {
                                    id: artArea
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.artRequested()
                                }
                            }
                        }

                        Text {
                            Layout.fillWidth: true
                            visible: (root.game.installDir || "") !== ""
                            text: root.game.installDir || ""
                            color: "#5f6a7b"
                            font.family: "Sora"
                            font.pixelSize: 10
                            elide: Text.ElideMiddle
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 2
                    Layout.preferredHeight: timeline.implicitHeight + 36
                    radius: 18
                    color: "#0b0e14"
                    border.width: 1
                    border.color: "#232a36"

                    ColumnLayout {
                        id: timeline
                        x: 18
                        y: 18
                        width: parent.width - 36
                        spacing: 14

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 12

                            ColumnLayout {
                                spacing: 2

                                Text {
                                    text: Tr.strings["PLAYTIME TIMELINE"]
                                    color: "#dfe6f0"
                                    font.family: "Chakra Petch"
                                    font.pixelSize: 11
                                    font.bold: true
                                    font.letterSpacing: 2.2
                                }

                                Text {
                                    text: root.game.sessionCount === 1
                                          ? Tr.strings["1 session"]
                                          : Tr.strings["%1 sessions"].arg(root.game.sessionCount || 0)
                                    color: "#6f7887"
                                    font.family: "Sora"
                                    font.pixelSize: 10
                                }
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                text: Tr.strings["All time"] + ": "
                                      + (root.game.playtimeText
                                         || root.game.historyTotalText
                                         || "—")
                                color: "#8b95a5"
                                font.family: "Sora"
                                font.pixelSize: 11
                            }
                        }

                        Row {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            spacing: 5
                            visible: root.history.length > 0

                            Repeater {
                                model: Math.min(14, root.history.length)

                                Item {
                                    width: 10
                                    height: 36

                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: parent.width
                                        height: Math.max(
                                            4,
                                            32 * ((root.history[index].seconds || 0)
                                                  / root.historyMax())
                                        )
                                        radius: 4
                                        color: index === 0
                                               ? Library.accent
                                               : Qt.darker(Library.accent, 1.35)
                                        opacity: index === 0 ? 1 : 0.6
                                    }
                                }
                            }
                        }

                        Column {
                            Layout.fillWidth: true
                            spacing: 0
                            visible: root.history.length > 0

                            Repeater {
                                model: root.history

                                Item {
                                    width: parent.width
                                    height: 56

                                    Rectangle {
                                        x: 8
                                        y: index === 0 ? 27 : 0
                                        width: 2
                                        height: index === 0
                                                ? 29
                                                : (index === root.history.length - 1
                                                   ? 27
                                                   : 56)
                                        color: "#26303f"
                                    }

                                    Rectangle {
                                        x: 3
                                        y: 21
                                        width: 12
                                        height: 12
                                        radius: 6
                                        color: index === 0
                                               ? Library.accent
                                               : "#2a3140"
                                        border.width: 2
                                        border.color: index === 0
                                                      ? Qt.lighter(Library.accent, 1.3)
                                                      : "#11151d"
                                    }

                                    Text {
                                        x: 30
                                        y: 10
                                        text: root.sessionDate(modelData.timestamp)
                                        color: "#cfd6e2"
                                        font.family: "Sora"
                                        font.pixelSize: 11
                                    }

                                    Text {
                                        x: 30
                                        y: 28
                                        text: modelData.duration
                                        color: "#7b8494"
                                        font.family: "Chakra Petch"
                                        font.pixelSize: 10
                                        font.letterSpacing: 0.6
                                    }
                                }
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14
                            visible: root.history.length === 0

                            Rectangle {
                                width: 44
                                height: 44
                                radius: 22
                                color: "#121722"
                                border.width: 1
                                border.color: "#232a36"

                                Text {
                                    anchors.centerIn: parent
                                    text: "◷"
                                    color: Library.accent
                                    font.pixelSize: 18
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Text {
                                    text: Tr.strings["No sessions recorded yet."]
                                    color: "#cfd6e2"
                                    font.family: "Sora"
                                    font.pixelSize: 12
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: Tr.strings["Launch the game from GameCenter to start the timeline."]
                                    color: "#6f7887"
                                    font.family: "Sora"
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }
            }
        }

        CloseButton {
            z: 5
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 12
            anchors.rightMargin: 12
            onClicked: root.closeRequested()
        }
    }

    Component {
        id: flatCard

        Cartridge {
            width: 208
            height: 288
            scale: 1.12
            transformOrigin: Item.Center
            showTitle: false
            style: Library.cartridgeStyle
            gameTitle: root.game.title || ""
            gameSource: root.game.source || ""
            gameMeta: root.game.meta || ""
            coverUrl: root.game.cover || ""
            gameInstalled: root.game.installed !== false
            cartridgeColor: root.game.cartridgeColor || Library.cartridgeColor
            onLaunchRequested: root.playRequested()
        }
    }

    Component {
        id: ds3dCard

        DsCartridge3D {
            width: 330
            height: 416
            scale: 0.8
            textureUrl: root.game.texture || ""
            cartridgeColor: root.game.cartridgeColor || Library.cartridgeColor
            onPlayRequested: root.playRequested()
        }
    }
}
