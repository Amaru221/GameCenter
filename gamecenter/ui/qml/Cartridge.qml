import QtQuick

Item {
    id: card
    objectName: "cartridge"
    width: 208
    height: 288

    property string gameTitle: ""
    property string gameSource: ""
    property string gameMeta: ""
    property string coverUrl: ""
    property bool gameInstalled: true
    property bool showTitle: true
    property string style: "classic"
    property bool interactive: true
    property color cartridgeColor: Library.cartridgeColor

    property real tiltX: 0
    property real tiltY: 0

    signal launchRequested()
    signal contextRequested()
    signal clicked()

    readonly property bool hovered: pointer.containsMouse
    readonly property int shellHeight: style === "ds" ? 210 : (style === "ps2" ? 232 : 230)
    readonly property int shellY: style === "ds" ? 14 : (style === "ps2" ? 3 : 0)

    z: card.hovered ? 1 : 0

    Behavior on tiltY { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
    Behavior on tiltX { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }

    function bindShell() {
        var item = shellLoader.item;
        if (!item) {
            return;
        }
        item.gameTitle = Qt.binding(function() { return card.gameTitle; });
        item.gameSource = Qt.binding(function() { return card.gameSource; });
        item.gameMeta = Qt.binding(function() { return card.gameMeta; });
        item.coverUrl = Qt.binding(function() { return card.coverUrl; });
        item.gameInstalled = Qt.binding(function() { return card.gameInstalled; });
        item.cartridgeColor = Qt.binding(function() { return card.cartridgeColor; });
        item.hovered = Qt.binding(function() { return card.hovered; });
        item.tiltX = Qt.binding(function() { return card.tiltX; });
        item.tiltY = Qt.binding(function() { return card.tiltY; });
    }

    Item {
        id: body
        width: 168
        height: 238
        x: (card.width - width) / 2
        y: 6

        scale: card.hovered ? 1.045 : 1.0
        opacity: card.gameInstalled ? 1.0 : 0.58

        Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        transform: [
            Rotation {
                origin.x: body.width / 2
                origin.y: body.height / 2
                axis { x: 0; y: 1; z: 0 }
                angle: card.tiltY
            },
            Rotation {
                origin.x: body.width / 2
                origin.y: body.height / 2
                axis { x: 1; y: 0; z: 0 }
                angle: -card.tiltX
            }
        ]

        Rectangle {
            x: 6
            y: card.shellY + 16
            width: parent.width - 12
            height: card.shellHeight - 2
            radius: 20
            color: "#000000"
            opacity: card.hovered ? 0.62 : 0.46
            Behavior on opacity { NumberAnimation { duration: 180 } }
        }

        Rectangle {
            x: 0
            y: card.shellY + 5
            width: parent.width
            height: card.shellHeight - 6
            radius: 19
            color: "#101216"
            border.width: 1
            border.color: "#191c21"
        }

        MouseArea {
            id: pointer
            anchors.fill: parent
            enabled: card.interactive
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onClicked: (mouse) => {
                if (mouse.button === Qt.RightButton) {
                    card.contextRequested();
                } else {
                    card.clicked();
                }
            }
            onDoubleClicked: card.launchRequested()
            onPositionChanged: (mouse) => {
                var nx = Math.max(0, Math.min(1, mouse.x / width)) - 0.5;
                var ny = Math.max(0, Math.min(1, mouse.y / height)) - 0.5;
                card.tiltY = nx * 18;
                card.tiltX = ny * 12;
            }
            onExited: {
                card.tiltY = 0;
                card.tiltX = 0;
            }
        }

        Loader {
            id: shellLoader
            anchors.fill: parent
            z: 1
            sourceComponent: card.style === "ds"
                             ? dsShell
                             : (card.style === "ps2" ? ps2Shell : classicShell)
            onLoaded: card.bindShell()
        }
    }

    Text {
        x: 0
        y: 260
        width: card.width
        visible: card.showTitle
        horizontalAlignment: Text.AlignHCenter
        text: card.gameTitle
        color: "#e9eef6"
        font.family: "Sora"
        font.pixelSize: 14
        font.weight: Font.Bold
        font.letterSpacing: 0.2
        elide: Text.ElideRight
        maximumLineCount: 1
    }

    Component { id: classicShell; ClassicShell {} }
    Component { id: dsShell; DSShell {} }
    Component { id: ps2Shell; PS2Shell {} }
}
