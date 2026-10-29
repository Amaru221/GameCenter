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

    readonly property int windowRadius: 4
    readonly property int windowCount: Math.min(games.length, windowRadius * 2 + 1)
    readonly property int centerSlot: Math.floor(windowCount / 2)

    // `windowStart` is mutable on purpose: before every step we recentre the
    // window on the card that is currently on screen. That recentre is
    // invisible (the same games stay at the same screen positions), and it lets
    // the following step animate a single real slot without swapping covers.
    property int windowStart: 0
    property int displayIndex: 0
    property int pendingIndex: 0
    property bool suspendCardAnimations: false
    property bool syncing: false

    readonly property real cardPad: Math.max(6, height * 0.02)
    readonly property real focusHeight: {
        // Never taller/wider than the viewport: the focused cover must always
        // be fully visible, including while the carousel slides.
        var byHeight = Math.max(140, height - cardPad * 2);
        var byWidth = Math.max(140, (width - 8) / 0.72);
        return Math.min(
            byHeight,
            byWidth,
            height * (mode === "wheel" ? 0.66 : 0.9)
        )
    }
    readonly property real focusWidth: focusHeight * 0.72
    readonly property real sideHeight: focusHeight
                                      * (mode === "wheel" ? 0.36 : 0.58)
    readonly property real sideWidth: sideHeight * 0.72
    readonly property real centerX: width / 2
    readonly property real centerY: height / 2
    readonly property real labelSize: Math.max(9, Math.min(14, height * 0.035))
    readonly property real slotStep: focusWidth / 2 + 14 + sideWidth / 2

    function maxWindowStart() {
        return Math.max(0, games.length - windowCount);
    }

    function centerWindow(index) {
        if (!games.length) {
            windowStart = 0;
            return;
        }
        var start = Math.max(
            0,
            Math.min(maxWindowStart(), index - centerSlot)
        );
        if (start !== windowStart) {
            suspendCardAnimations = true;
            windowStart = start;
        }
    }

    onSelectedIndexChanged: {
        if (syncing || !games.length) {
            return;
        }
        pendingIndex = Math.max(0, Math.min(selectedIndex, games.length - 1));
        if (Math.abs(pendingIndex - displayIndex) > windowRadius) {
            // A far jump (programmatic selection, filter reset) cannot be
            // disguised as a one-slot slide: place the window on the target and
            // show it immediately.
            suspendCardAnimations = true;
            centerWindow(pendingIndex);
            displayIndex = pendingIndex;
            Qt.callLater(function() {
                root.suspendCardAnimations = false;
            });
            return;
        }
        // Recentre for the card currently on screen (invisible), then let the
        // next tick animate the real one-slot step.
        centerWindow(displayIndex);
        stepTimer.restart();
    }

    onGamesChanged: {
        syncing = true;
        suspendCardAnimations = true;
        windowStart = 0;
        displayIndex = games.length
                       ? Math.max(0, Math.min(selectedIndex, games.length - 1))
                       : 0;
        pendingIndex = displayIndex;
        Qt.callLater(function() {
            root.centerWindow(root.displayIndex);
            root.suspendCardAnimations = false;
            root.syncing = false;
        });
    }

    Component.onCompleted: {
        displayIndex = selectedIndex;
        pendingIndex = selectedIndex;
        centerWindow(displayIndex);
        Qt.callLater(function() {
            root.suspendCardAnimations = false;
        });
    }

    Timer {
        id: stepTimer
        interval: 1
        repeat: false
        onTriggered: {
            if (!root.games.length) {
                return;
            }
            root.suspendCardAnimations = false;
            root.displayIndex = Math.max(
                0, Math.min(root.pendingIndex, root.games.length - 1)
            );
        }
    }

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

    function cardX(offset, cardWidth) {
        if (mode === "wheel") {
            return root.centerX - cardWidth / 2;
        }
        return horizontalX(offset);
    }

    function cardY(offset, cardHeight) {
        var y = root.centerY - cardHeight / 2;
        if (mode === "wheel") {
            var step = root.focusHeight / 2 + root.sideHeight / 2 + 8;
            y = root.centerY + offset * step - cardHeight / 2;
        } else if (mode === "arc") {
            var drop = Math.min(9, root.height * 0.03)
                       * Math.pow(Math.min(3, Math.abs(offset)), 1.6);
            y += drop;
        } else if (mode === "ring") {
            var ringAngle = Math.min(60, Math.abs(offset) * 20) * Math.PI / 180;
            var ringDrop = (1 - Math.cos(ringAngle)) * root.height * 0.5;
            y += ringDrop;
        }
        // Clamp to the viewport so no cover is ever cropped vertically.
        return Math.max(
            root.cardPad,
            Math.min(root.height - cardHeight - root.cardPad, y)
        );
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

    Item {
        anchors.fill: parent

        Repeater {
            model: root.windowCount

            delegate: Item {
                id: card
                readonly property int absoluteIndex: root.windowStart + index
                readonly property int offset: absoluteIndex - root.displayIndex
                readonly property bool focused: offset === 0
                readonly property var game: root.games[absoluteIndex] || ({})

            width: focused ? root.focusWidth : root.sideWidth
            height: focused ? root.focusHeight : root.sideHeight
            x: root.cardX(offset, width)
            y: root.cardY(offset, height)
            z: focused ? 100 : 50 - Math.abs(offset) * 4
            opacity: root.cardOpacity(offset)
            antialiasing: true

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

            // Snappy, console-style response: short enough to keep up with the
            // gamepad's 130 ms repeat, long enough to read as motion. The
            // invisible window recentre disables them for a single frame.
            Behavior on x {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 190; easing.type: Easing.OutCubic }
            }
            Behavior on y {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 190; easing.type: Easing.OutCubic }
            }
            Behavior on width {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
            }
            Behavior on height {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
            }
            Behavior on opacity {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 150 }
            }
            Behavior on angleX {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
            }
            Behavior on angleY {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
            }
            Behavior on angleZ {
                enabled: !root.suspendCardAnimations
                NumberAnimation { duration: 180; easing.type: Easing.OutCubic }
            }

            // The glow and the drop shadow are expensive overdraw; only the
            // focused cover needs them. Side cards keep a cheap border.
            Rectangle {
                anchors.fill: parent
                anchors.margins: -8
                radius: 24
                color: Library.accent
                opacity: 0.12
                visible: card.focused
                z: -2
            }

            Rectangle {
                anchors.fill: parent
                anchors.margins: -2
                radius: 18
                color: "#000000"
                opacity: 0.45
                y: 5
                visible: card.focused
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
                    sourceSize.width: 512
                    fillMode: Image.PreserveAspectFit
                    asynchronous: true
                    cache: true
                    smooth: true
                    mipmap: true
                }

                Rectangle {
                    visible: card.focused
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
                    opacity: 0.16
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
