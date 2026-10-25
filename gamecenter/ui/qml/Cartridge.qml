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
    property bool selected: false
    property bool showTitle: true
    property bool favorite: false
    property string style: "classic"
    property bool interactive: true

    property real tiltX: 0
    property real tiltY: 0
    property real flipAngle: 0

    property real _flipStart: 0
    property real _pressX: 0
    property real _pressY: 0
    property bool _flipping: false
    property bool _flipMoved: false

    signal launchRequested()
    signal contextRequested()
    signal clicked()
    signal favoriteRequested()

    readonly property bool hovered: pointer.containsMouse
    readonly property int shellHeight: style === "ds" ? 210 : (style === "ps2" ? 232 : 230)
    readonly property int shellY: style === "ds" ? 14 : (style === "ps2" ? 3 : 0)
    readonly property real flatDepthOpacity:
        style === "ds"
        ? Math.max(0, 1 - Math.abs(Math.sin(flipAngle * Math.PI / 180)))
        : 1

    z: card.hovered ? 1 : 0

    Behavior on tiltY { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
    Behavior on tiltX { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
    Behavior on flipAngle {
        enabled: !card._flipping
        NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
    }

    onStyleChanged: flipAngle = 0

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
        item.selected = Qt.binding(function() { return card.selected; });
        item.hovered = Qt.binding(function() { return card.hovered; });
        item.tiltX = Qt.binding(function() { return card.tiltX; });
        item.tiltY = Qt.binding(function() { return card.tiltY; });
        item.flipAngle = Qt.binding(function() { return card.flipAngle; });
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

        Item {
            anchors.fill: parent
            opacity: card.flatDepthOpacity

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
        }

        MouseArea {
            id: pointer
            anchors.fill: parent
            enabled: card.interactive
            hoverEnabled: true
            cursorShape: card._flipping ? Qt.ClosedHandCursor : Qt.PointingHandCursor
            acceptedButtons: Qt.LeftButton | Qt.RightButton

            onPressed: (mouse) => {
                if (mouse.button === Qt.LeftButton && card.style === "ds") {
                    card._flipping = true;
                    card._flipMoved = false;
                    card._pressX = mouse.x;
                    card._pressY = mouse.y;
                    card._flipStart = card.flipAngle;
                }
            }
            onPositionChanged: (mouse) => {
                if (card._flipping) {
                    var dx = mouse.x - card._pressX;
                    var dy = mouse.y - card._pressY;
                    if (Math.abs(dx) > 4 || Math.abs(dy) > 4) {
                        card._flipMoved = true;
                    }
                    card.flipAngle = Math.max(-180, Math.min(180, card._flipStart + dx * 1.2));
                    card.tiltX = Math.max(-12, Math.min(12, dy * 0.25));
                } else {
                    var nx = Math.max(0, Math.min(1, mouse.x / width)) - 0.5;
                    var ny = Math.max(0, Math.min(1, mouse.y / height)) - 0.5;
                    card.tiltY = nx * 18;
                    card.tiltX = ny * 12;
                }
            }
            onReleased: (mouse) => {
                if (!card._flipping) {
                    return;
                }
                card._flipping = false;
                card.tiltX = 0;
                card.tiltY = 0;
                if (card._flipMoved) {
                    if (card.flipAngle > 90) {
                        card.flipAngle = 180;
                    } else if (card.flipAngle < -90) {
                        card.flipAngle = -180;
                    } else {
                        card.flipAngle = 0;
                    }
                } else {
                    card.clicked();
                }
            }
            onClicked: (mouse) => {
                if (mouse.button === Qt.RightButton) {
                    card.contextRequested();
                } else if (card.style !== "ds") {
                    card.clicked();
                }
            }
            onDoubleClicked: card.launchRequested()
            onExited: {
                if (!card._flipping) {
                    card.tiltY = 0;
                    card.tiltX = 0;
                }
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

    Rectangle {
        x: card.width - 44
        y: card.style === "classic" ? 10 : 18
        width: 22
        height: 22
        radius: 11
        color: "#0d0f14"
        border.width: 1
        border.color: card.favorite ? "#ffd166" : "#2a3140"
        visible: card.interactive && (card.favorite || card.hovered)
        opacity: card.favorite || card.hovered ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 140 } }

        Text {
            anchors.centerIn: parent
            text: card.favorite ? "★" : "☆"
            color: card.favorite ? "#ffd166" : "#c9d2e0"
            font.pixelSize: 12
        }

        MouseArea {
            anchors.fill: parent
            enabled: card.interactive
            cursorShape: Qt.PointingHandCursor
            onClicked: card.favoriteRequested()
        }
    }

    Text {
        x: 0
        y: 254
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
