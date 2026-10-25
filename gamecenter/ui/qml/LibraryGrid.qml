import QtQuick
import QtQuick.Controls

Item {
    id: root
    objectName: "libraryGrid"
    clip: true

    signal detailRequested(int index)

    function openColorPicker(row) {
        colorPopup.row = row;
        colorPopup.open();
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: 18
        color: Library.surfaceColor
        opacity: 0.35
    }

    GridView {
        id: grid
        anchors.fill: parent
        model: Library
        cellWidth: 208
        cellHeight: 292
        leftMargin: 4
        topMargin: 6
        cacheBuffer: 600
        boundsBehavior: Flickable.StopAtBounds
        flow: GridView.LeftToRight

        ScrollBar.vertical: ScrollBar {
            id: bar
            policy: ScrollBar.AsNeeded
            visible: grid.contentHeight > grid.height
            width: 8
            background: Item {}
            contentItem: Rectangle {
                implicitWidth: 6
                radius: 3
                color: "#3a465c"
                opacity: bar.pressed ? 1 : 0.55
            }
        }

        delegate: Cartridge {
            gameTitle: model.title
            gameSource: model.source
            gameMeta: model.meta
            coverUrl: model.cover
            gameInstalled: model.installed
            favorite: model.favorite
            style: Library.cartridgeStyle
            cartridgeColor: model.cartridgeColor

            onLaunchRequested: Library.launch(index)
            onFavoriteRequested: Library.toggleFavorite(index)
            onClicked: root.detailRequested(index)
            onContextRequested: {
                contextMenu.row = index;
                contextMenu.popup();
            }
        }
    }

    Text {
        anchors.centerIn: parent
        visible: grid.count === 0
        width: parent.width * 0.6
        horizontalAlignment: Text.AlignCenter
        wrapMode: Text.WordWrap
        text: Library.total === 0
              ? "No Steam library found.\nInstall a game with Steam and press F5."
              : "No games match your filters."
        color: "#98a3b4"
        font.family: "Sora"
        font.pixelSize: 13
        lineHeight: 1.4
    }

    Menu {
        id: contextMenu
        property int row: -1
        width: 200

        background: Rectangle {
            color: "#12151b"
            radius: 11
            border.width: 1
            border.color: "#2a3140"
        }

        delegate: MenuItem {
            id: entry
            width: contextMenu.width - 10
            implicitHeight: 32
            highlighted: contextMenu.currentIndex === index

            contentItem: Text {
                leftPadding: 12
                text: entry.text
                color: entry.enabled ? "#dfe6f0" : "#5f6a7b"
                font.family: "Sora"
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }

            background: Rectangle {
                radius: 7
                color: entry.highlighted ? "#232936" : "transparent"
            }
        }

        MenuItem {
            text: "Launch"
            onTriggered: Library.launch(contextMenu.row)
        }
        MenuSeparator {
            contentItem: Rectangle {
                implicitHeight: 1
                color: "#232936"
            }
        }
        MenuItem {
            text: "Open install folder"
            onTriggered: Library.openFolder(contextMenu.row)
        }
        MenuItem {
            text: "Copy App ID"
            onTriggered: Library.copyAppId(contextMenu.row)
        }
        MenuItem {
            text: "Cartridge color..."
            onTriggered: {
                colorPopup.row = contextMenu.row;
                colorPopup.open();
            }
        }
        MenuSeparator {
            contentItem: Rectangle {
                implicitHeight: 1
                color: "#232936"
            }
        }
        MenuItem {
            text: "Remove from library"
            onTriggered: Library.removeGame(contextMenu.row)
        }
    }

    Popup {
        id: colorPopup
        property int row: -1
        parent: root.Window.window ? root.Window.window.contentItem : root
        anchors.centerIn: parent
        width: 340
        height: 190
        modal: true
        focus: true
        padding: 0
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        background: Rectangle {
            color: "#12151b"
            radius: 14
            border.width: 1
            border.color: "#2a3140"
        }

        contentItem: Column {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 12

            Text {
                text: "Cartridge color"
                color: "#f2f5fa"
                font.family: "Sora"
                font.pixelSize: 15
                font.bold: true
            }

            Flow {
                width: parent.width
                spacing: 8

                Repeater {
                    model: Library.cartridgePalette

                    delegate: ColorSwatch {
                        colour: modelData
                        selected: Library.cartridgeColorAt(colorPopup.row).toLowerCase() === modelData.toLowerCase()
                        onClicked: {
                            Library.setGameCartridgeColor(colorPopup.row, modelData);
                            colorPopup.close();
                        }
                    }
                }
            }

            Rectangle {
                width: 124
                height: 32
                radius: 8
                color: "#171b23"
                border.width: 1
                border.color: "#2a3140"

                Text {
                    anchors.centerIn: parent
                    text: "Use default"
                    color: "#cfd6e2"
                    font.family: "Sora"
                    font.pixelSize: 11
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        Library.resetGameCartridgeColor(colorPopup.row);
                        colorPopup.close();
                    }
                }
            }
        }
    }
}
