import QtQuick
import QtQuick.Controls

Item {
    id: root
    clip: true

    signal detailRequested(int index)

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
    }
}
