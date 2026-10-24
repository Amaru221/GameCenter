import QtQuick

Item {
    id: root
    anchors.fill: parent
    visible: running
    z: 15

    property bool running: false
    property var game: ({})
    property int index: -1
    property point target: Qt.point(0, 0)

    function play(gameData, row, from, to) {
        game = gameData;
        index = row;
        target = to;

        card.x = from.x - card.width / 2;
        card.y = from.y - card.height / 2;
        card.scale = 1.7;
        card.rotation = 0;
        card.opacity = 1;
        running = true;
        fly.restart();
        Library.launch(row);
    }

    Cartridge {
        id: card
        width: 208
        height: 288
        showTitle: false
        interactive: false
        style: Library.cartridgeStyle
        gameTitle: root.game.title || ""
        gameSource: root.game.source || ""
        gameMeta: root.game.meta || ""
        coverUrl: root.game.cover || ""
        gameInstalled: true
        transformOrigin: Item.Center
    }

    SequentialAnimation {
        id: fly

        ParallelAnimation {
            NumberAnimation {
                target: card
                property: "x"
                to: root.target.x - card.width / 2
                duration: 460
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: card
                property: "y"
                to: root.target.y - card.height / 2
                duration: 460
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: card
                property: "scale"
                to: 0.18
                duration: 460
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: card
                property: "rotation"
                to: 7
                duration: 460
                easing.type: Easing.InOutCubic
            }
        }

        NumberAnimation {
            target: card
            property: "opacity"
            to: 0
            duration: 110
            easing.type: Easing.InCubic
        }

        ScriptAction { script: root.running = false }
    }
}
