import QtQuick
import QtQuick.Layouts

Item {
    id: root

    property var game: ({})
    property bool opened: false

    signal closeRequested()
    signal playRequested()
    signal folderRequested()
    signal copyRequested()
    signal favoriteRequested()
    signal artRequested()

    function cartridgeCenter() {
        if (!detailCard.item) {
            return Qt.point(0, 0);
        }
        var item = detailCard.item;
        var point = item.mapToItem(root, item.width / 2, item.height / 2);
        return Qt.point(point.x, point.y);
    }

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    Rectangle {
        anchors.fill: parent
        color: "#05060a"
        opacity: 0.8

        MouseArea {
            anchors.fill: parent
            onClicked: root.closeRequested()
        }
    }

    Rectangle {
        id: panel
        width: Math.min(parent.width - 80, 980)
        height: 480
        anchors.centerIn: parent
        radius: 20
        border.width: 1
        border.color: "#2a3140"
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#151a23" }
            GradientStop { position: 1.0; color: "#0c0f14" }
        }
        scale: root.opened ? 1 : 0.97
        Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

        MouseArea { anchors.fill: parent }

        RowLayout {
            anchors.fill: parent
            anchors.margins: 32
            spacing: 40

            Item {
                Layout.preferredWidth: 330
                Layout.fillHeight: true

                Loader {
                    id: detailCard
                    anchors.centerIn: parent
                    active: root.opened
                    sourceComponent: Library.cartridgeStyle === "ds" ? ds3dCard : flatCard
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                Text {
                    text: (root.game.source || "").toUpperCase()
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Text {
                        Layout.fillWidth: true
                        text: root.game.title || ""
                        color: "#f2f5fa"
                        font.family: "Sora"
                        font.pixelSize: 28
                        font.weight: Font.Bold
                        wrapMode: Text.WordWrap
                        maximumLineCount: 3
                        elide: Text.ElideRight
                    }

                    Rectangle {
                        width: 34
                        height: 34
                        radius: 17
                        color: "#171b23"
                        border.width: 1
                        border.color: root.game.favorite ? "#ffd166" : "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: root.game.favorite ? "★" : "☆"
                            color: root.game.favorite ? "#ffd166" : "#c9d2e0"
                            font.pixelSize: 15
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.favoriteRequested()
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.maximumWidth: 380
                    height: 46
                    radius: 10
                    color: playArea.pressed ? Qt.darker(Library.accent, 1.2) : Library.accent

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Canvas {
                            width: 14
                            height: 16
                            onPaint: {
                                var ctx = getContext("2d");
                                ctx.reset();
                                ctx.fillStyle = "#ffffff";
                                ctx.beginPath();
                                ctx.moveTo(1, 0);
                                ctx.lineTo(13, 8);
                                ctx.lineTo(1, 16);
                                ctx.closePath();
                                ctx.fill();
                            }
                        }

                        Text {
                            text: "Play"
                            color: Library.accentText
                            font.family: "Sora"
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }
                    }

                    MouseArea {
                        id: playArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.playRequested()
                    }
                }

                RowLayout {
                    spacing: 18

                    Text {
                        text: root.game.sizeText || ""
                        visible: text !== ""
                        color: "#aeb8c7"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }
                    Text {
                        text: root.game.installed !== false ? "Installed" : "Not installed"
                        color: "#aeb8c7"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }
                    Text {
                        text: root.game.playtimeText || ""
                        visible: text !== ""
                        color: "#aeb8c7"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }
                    Text {
                        text: root.game.lastPlayed || ""
                        color: "#aeb8c7"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillHeight: true }

                Text {
                    Layout.fillWidth: true
                    text: root.game.installDir || ""
                    visible: text !== ""
                    color: "#6f7887"
                    font.family: "Sora"
                    font.pixelSize: 11
                    elide: Text.ElideMiddle
                }

                RowLayout {
                    spacing: 10

                    Rectangle {
                        width: 132
                        height: 36
                        radius: 9
                        color: folderArea.containsMouse ? "#202633" : "#171b23"
                        border.width: 1
                        border.color: "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: "Open folder"
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 12
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
                        height: 36
                        radius: 9
                        color: copyArea.containsMouse ? "#202633" : "#171b23"
                        border.width: 1
                        border.color: "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: "Copy App ID"
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 12
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
                        width: 132
                        height: 36
                        radius: 9
                        color: artArea.containsMouse ? "#202633" : "#171b23"
                        border.width: 1
                        border.color: "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: "Choose art"
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 12
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
            }
        }

        Rectangle {
            x: panel.width - 46
            y: 16
            width: 30
            height: 30
            radius: 15
            color: closeArea.containsMouse ? "#232936" : "transparent"

            Text {
                anchors.centerIn: parent
                text: "✕"
                color: "#aeb8c7"
                font.pixelSize: 14
            }

            MouseArea {
                id: closeArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.closeRequested()
            }
        }
    }

    Component {
        id: flatCard

        Cartridge {
            scale: 1.7
            showTitle: false
            style: Library.cartridgeStyle
            gameTitle: root.game.title || ""
            gameSource: root.game.source || ""
            gameMeta: root.game.meta || ""
            coverUrl: root.game.cover || ""
            gameInstalled: root.game.installed !== false
            onLaunchRequested: root.playRequested()
        }
    }

    Component {
        id: ds3dCard

        DsCartridge3D {
            width: 330
            height: 416
            textureUrl: root.game.texture || ""
            onPlayRequested: root.playRequested()
        }
    }
}
