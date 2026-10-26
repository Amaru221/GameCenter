import QtQuick

Item {
    id: root
    objectName: "bigPictureCarousel"
    clip: true

    property var games: []
    property int selectedIndex: 0
    property string mode: "arc"

    signal selected(int index)
    signal activated(int index)

    readonly property int windowRadius: 6
    readonly property int windowCount: Math.min(games.length, windowRadius * 2 + 1)
    readonly property int windowStart: {
        if (!games.length) {
            return 0;
        }
        var start = selectedIndex - windowRadius;
        return Math.max(0, Math.min(games.length - windowCount, start));
    }

    readonly property real focusHeight: Math.min(
        height - 18, height * (mode === "wheel" ? 0.66 : 0.9)
    )
    readonly property real focusWidth: focusHeight * 0.72
    readonly property real sideHeight: focusHeight
                                      * (mode === "wheel" ? 0.36 : 0.58)
    readonly property real sideWidth: sideHeight * 0.72
    readonly property real centerX: width / 2
    readonly property real centerY: height / 2
    readonly property real labelSize: Math.max(9, Math.min(14, height * 0.035))

    function horizontalX(offset) {
        if (offset === 0) {
            return root.centerX - root.focusWidth / 2;
        }
        var distance = Math.abs(offset);
        var direction = offset > 0 ? 1 : -1;
        var center = root.centerX + direction
                     * (root.focusWidth / 2 + 14
                        + root.sideWidth / 2
                        + (distance - 1) * (root.sideWidth + 14));
        return center - root.sideWidth / 2;
    }

    function cardX(offset, width) {
        if (mode === "wheel") {
            return root.centerX - width / 2;
        }
        return horizontalX(offset);
    }

    function cardY(offset, height) {
        if (mode === "wheel") {
            var step = root.focusHeight / 2 + root.sideHeight / 2 + 8;
            return root.centerY + offset * step - height / 2;
        }
        if (mode === "arc") {
            var drop = Math.min(9, root.height * 0.03)
                       * Math.pow(Math.min(3, Math.abs(offset)), 1.6);
            return root.centerY - height / 2 + drop;
        }
        if (mode === "ring") {
            var ringAngle = Math.min(60, Math.abs(offset) * 20) * Math.PI / 180;
            var ringDrop = (1 - Math.cos(ringAngle)) * root.height * 0.5;
            return root.centerY - height / 2 + ringDrop;
        }
        return root.centerY - height / 2;
    }

    function cardAngleZ(offset) {
        return mode === "arc" ? offset * 2.4 : 0;
    }

    function cardAngleY(offset) {
        if (mode !== "ring") {
            return 0;
        }
        return Math.max(-64, Math.min(64, -offset * 32));
    }

    function cardAngleX(offset) {
        return mode === "wheel"
               ? Math.max(-45, Math.min(45, offset * 18))
               : 0;
    }

    function cardOpacity(offset) {
        var distance = Math.abs(offset);
        if (distance === 0) {
            return 1;
        }
        if (distance === 1) {
            return 0.72;
        }
        if (distance === 2) {
            return 0.46;
        }
        return 0.22;
    }

    Rectangle {
        visible: root.mode === "ring"
        anchors.centerIn: parent
        width: root.focusWidth + root.sideWidth * 2.6
        height: root.focusHeight * 0.78
        radius: height / 2
        color: "transparent"
        border.width: 1
        border.color: Library.accent
        opacity: 0.16
        z: 0
    }

    Repeater {
        model: root.windowCount

        delegate: Item {
            id: card
            readonly property int absoluteIndex: root.windowStart + index
            readonly property int offset: absoluteIndex - root.selectedIndex
            readonly property bool focused: offset === 0
            readonly property var game: root.games[absoluteIndex] || ({})

            width: focused ? root.focusWidth : root.sideWidth
            height: focused ? root.focusHeight : root.sideHeight
            x: root.cardX(offset, width)
            y: root.cardY(offset, height)
            z: focused ? 100 : 50 - Math.abs(offset) * 4
            opacity: root.cardOpacity(offset)

            property real angleX: root.cardAngleX(offset)
            property real angleY: root.cardAngleY(offset)
            property real angleZ: root.cardAngleZ(offset)

            transform: [
                Rotation {
                    origin.x: card.width / 2
                    origin.y: card.height / 2
                    axis { x: 0; y: 1; z: 0 }
                    angle: card.angleY
                },
                Rotation {
                    origin.x: card.width / 2
                    origin.y: card.height / 2
                    axis { x: 1; y: 0; z: 0 }
                    angle: card.angleX
                },
                Rotation {
                    origin.x: card.width / 2
                    origin.y: card.height / 2
                    axis { x: 0; y: 0; z: 1 }
                    angle: card.angleZ
                }
            ]

            Behavior on x { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
            Behavior on y { NumberAnimation { duration: 280; easing.type: Easing.OutCubic } }
            Behavior on width { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
            Behavior on height { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
            Behavior on opacity { NumberAnimation { duration: 220 } }
            Behavior on angleX { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
            Behavior on angleY { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }
            Behavior on angleZ { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }

            Rectangle {
                anchors.fill: parent
                anchors.margins: -8
                radius: 24
                color: Library.accent
                opacity: card.focused ? 0.12 : 0
                z: -2
            }

            Rectangle {
                anchors.fill: parent
                anchors.margins: -2
                radius: 18
                color: "#000000"
                opacity: card.focused ? 0.45 : 0.3
                y: 5
                z: -1
            }

            Rectangle {
                anchors.fill: parent
                radius: 14
                color: "#0a0e15"
            }

            Rectangle {
                id: cover
                width: parent.width
                height: parent.height - 24
                radius: 14
                color: "#0b0f16"
                border.width: card.focused ? 2 : 1
                border.color: card.focused ? Library.accent : "#243044"
                clip: true

                Image {
                    anchors.fill: parent
                    source: card.game.cover || ""
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: true
                    smooth: true
                }

                Rectangle {
                    width: cover.width * 2
                    height: cover.height * 0.55
                    x: -cover.width * 0.45
                    y: -cover.height * 0.1
                    rotation: -22
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#2effffff" }
                        GradientStop { position: 0.55; color: "#0affffff" }
                        GradientStop { position: 1.0; color: "#00ffffff" }
                    }
                    opacity: card.focused ? 0.16 : 0.05
                }
            }

            Text {
                width: parent.width
                y: parent.height - 21
                text: card.game.title || ""
                color: card.focused ? "#f2f5fa" : "#8b95a5"
                visible: card.focused || root.mode !== "wheel"
                font.family: "Sora"
                font.pixelSize: card.focused
                                ? root.labelSize
                                : Math.max(8, root.labelSize - 1)
                font.bold: card.focused
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
                maximumLineCount: 1
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.selected(card.absoluteIndex)
                onDoubleClicked: root.activated(card.absoluteIndex)
            }
        }
    }

    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height - 2
        width: root.focusWidth * 0.72
        height: 2
        radius: 1
        color: Library.accent
        opacity: 0.55
        visible: root.mode !== "wheel"
    }
}
