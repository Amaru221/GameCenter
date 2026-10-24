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

        // 1. Approach the dock and stop just above the slot.
        ParallelAnimation {
            NumberAnimation {
                target: card
                property: "x"
                to: root.target.x - card.width / 2
                duration: 480
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: card
                property: "y"
                to: root.target.y - 24 - card.height / 2
                duration: 480
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: card
                property: "scale"
                to: 0.38
                duration: 480
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: card
                property: "rotation"
                to: 4
                duration: 480
                easing.type: Easing.OutCubic
            }
        }

        // 2. A short breath before going in.
        PauseAnimation { duration: 180 }

        // 3. Slide into the slot; the lower half hides behind the dock.
        ParallelAnimation {
            NumberAnimation {
                target: card
                property: "y"
                to: root.target.y + 14 - card.height / 2
                duration: 220
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: card
                property: "scale"
                to: 0.30
                duration: 220
                easing.type: Easing.InCubic
            }
            NumberAnimation {
                target: card
                property: "rotation"
                to: 0
                duration: 220
                easing.type: Easing.OutCubic
            }
        }

        // 4. A tiny settle back up, like the cartridge finding its stop.
        NumberAnimation {
            target: card
            property: "y"
            to: root.target.y + 7 - card.height / 2
            duration: 120
            easing.type: Easing.OutCubic
        }

        // 5. Rest with the cartridge slightly protruding.
        PauseAnimation { duration: 520 }

        // 5. Hand over to the session chip.
        NumberAnimation {
            target: card
            property: "opacity"
            to: 0
            duration: 180
            easing.type: Easing.InCubic
        }

        ScriptAction { script: root.running = false }
    }
}
