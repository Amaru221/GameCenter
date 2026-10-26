import QtQuick

Item {
    id: root
    objectName: "insertEffect"
    anchors.fill: parent
    visible: running
    z: 15

    property bool running: false
    property var game: ({})
    property int index: -1
    property point target: Qt.point(0, 0)
    property string sessionId: ""

    signal inserted(string sessionId)

    function play(gameData, row, from, to) {
        game = gameData;
        index = row;
        target = to;

        card.x = from.x - card.width / 2;
        card.y = from.y - card.height / 2;
        card.scale = 1.7;
        card.rotation = 0;
        card.opacity = 1;

        // Guard the slot update before the session appears, so the previous
        // cartridge stays in place while this one flies in.
        running = true;
        sessionId = Library.launch(row);
        fly.restart();
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
        cartridgeColor: root.game.cartridgeColor || Library.cartridgeColor
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
                to: 0.40
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
                to: 0.34
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
            to: root.target.y + 1 - card.height / 2
            duration: 120
            easing.type: Easing.OutCubic
        }

        // 5. The cartridge has found its stop: hand the slot over to it.
        ScriptAction {
            script: {
                if (root.sessionId !== "") {
                    root.inserted(root.sessionId);
                }
            }
        }

        // 6. Rest with the cartridge slightly protruding.
        PauseAnimation { duration: 520 }

        // 7. The dock's slot cartridge takes over from the flying one.
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
