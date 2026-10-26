import QtQuick

// A round favourite star with a golden glow, a pop and a little star burst the
// moment a game is added to the favourites.
Item {
    id: root
    objectName: "favoriteButton"
    width: 52
    height: 52

    property bool favorite: false
    property color accent: "#ffd166"
    signal toggled()

    readonly property bool hovered: pointer.containsMouse

    Item {
        id: starWrap
        anchors.fill: parent
        scale: 1
        rotation: 0
        z: 2

        Canvas {
            id: star
            width: 30
            height: 30
            anchors.centerIn: parent

            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                var cx = width / 2;
                var cy = height / 2;
                var outer = 13;
                var inner = 5.7;
                ctx.beginPath();
                for (var i = 0; i < 10; i++) {
                    var r = (i % 2 === 0) ? outer : inner;
                    var a = -Math.PI / 2 + i * Math.PI / 5;
                    var x = cx + Math.cos(a) * r;
                    var y = cy + Math.sin(a) * r;
                    if (i === 0) {
                        ctx.moveTo(x, y);
                    } else {
                        ctx.lineTo(x, y);
                    }
                }
                ctx.closePath();

                if (root.favorite) {
                    var g = ctx.createLinearGradient(0, 0, width, height);
                    g.addColorStop(0, "#fff6c2");
                    g.addColorStop(0.55, "#ffd166");
                    g.addColorStop(1, "#f59e0b");
                    ctx.fillStyle = g;
                    ctx.fill();
                    ctx.lineWidth = 1.4;
                    ctx.strokeStyle = "#ffe08a";
                } else {
                    ctx.lineWidth = 1.7;
                    ctx.strokeStyle = root.hovered ? "#dfe6f0" : "#8b95a5";
                }
                ctx.stroke();
            }
        }
    }

    Connections {
        target: root
        function onFavoriteChanged() { star.requestPaint(); }
        function onHoveredChanged() { star.requestPaint(); }
    }

    Rectangle {
        anchors.centerIn: parent
        width: 48
        height: 48
        radius: 24
        color: root.accent
        opacity: root.favorite ? 0.16 : 0
        scale: root.favorite ? 1.18 : 0.8
        Behavior on opacity { NumberAnimation { duration: 240 } }
        Behavior on scale { NumberAnimation { duration: 260; easing.type: Easing.OutCubic } }
    }

    Rectangle {
        id: ring
        anchors.centerIn: parent
        width: 46
        height: 46
        radius: 23
        color: root.favorite ? "#2a2410" : "#0d0f14"
        border.width: 1
        border.color: root.favorite
                      ? Qt.lighter(root.accent, 1.05)
                      : (root.hovered ? "#3a4250" : "#232833")
        Behavior on color { ColorAnimation { duration: 180 } }
        Behavior on border.color { ColorAnimation { duration: 180 } }
    }

    Rectangle {
        id: pulse
        anchors.centerIn: parent
        width: 46
        height: 46
        radius: 23
        color: "transparent"
        border.width: 2
        border.color: root.accent
        opacity: 0
        scale: 1
        z: 1
    }

    Text {
        id: burstStar
        objectName: "burstStar"
        text: "★"
        color: root.accent
        font.pixelSize: 16
        anchors.horizontalCenter: parent.horizontalCenter
        y: 18
        opacity: 0
        scale: 0.8
        z: 4
    }

    ParallelAnimation {
        id: burstAnim
        NumberAnimation {
            target: burstStar
            property: "y"
            from: 18
            to: -18
            duration: 520
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: burstStar
            property: "opacity"
            from: 1
            to: 0
            duration: 520
            easing.type: Easing.InQuad
        }
        NumberAnimation {
            target: burstStar
            property: "scale"
            from: 0.8
            to: 1.7
            duration: 520
            easing.type: Easing.OutCubic
        }
    }

    MouseArea {
        id: pointer
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            root.activate()
        }
    }

    ParallelAnimation {
        id: pulseAnim
        NumberAnimation {
            target: pulse
            property: "scale"
            from: 1
            to: 1.8
            duration: 430
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: pulse
            property: "opacity"
            from: 0.85
            to: 0
            duration: 430
            easing.type: Easing.InQuad
        }
    }

    SequentialAnimation {
        id: pop
        NumberAnimation {
            target: starWrap
            property: "scale"
            from: 1
            to: 1.3
            duration: 120
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: starWrap
            property: "scale"
            to: 1
            duration: 260
            easing.type: Easing.OutBack
        }
        NumberAnimation {
            target: starWrap
            property: "rotation"
            from: 0
            to: 8
            duration: 100
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: starWrap
            property: "rotation"
            to: 0
            duration: 160
            easing.type: Easing.OutCubic
        }
    }

    function activate() {
        var wasFavorite = root.favorite;
        root.toggled();
        pop.restart();
        if (!wasFavorite) {
            burstAnim.restart();
            pulseAnim.restart();
        }
    }
}
