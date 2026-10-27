import QtQuick
import QtQuick.Window

Window {
    id: root
    objectName: "screenshotOverlay"
    visible: opened
    color: "#00000000"
    flags: Qt.FramelessWindowHint
           | Qt.WindowStaysOnTopHint
           | Qt.WindowTransparentForInput
           | Qt.WindowDoesNotAcceptFocus
           | Qt.Tool
           | Qt.NoDropShadowWindowHint

    property bool opened: false
    property var capture: ({})
    property real flash: 0
    property real cardOpacity: 0
    property real cardScale: 0.86
    property real cardRotation: 3

    function play(data) {
        if (!data || !data.path) {
            return;
        }
        capture = data;
        if (data.screenWidth > 0 && data.screenHeight > 0) {
            x = Number(data.screenX || 0);
            y = Number(data.screenY || 0);
            width = Number(data.screenWidth);
            height = Number(data.screenHeight);
        }
        opened = true;
        show();
        flash = 0;
        cardOpacity = 0;
        cardScale = 0.86;
        cardRotation = 3;
        flashAnim.restart();
        cardAnim.restart();
        hideTimer.restart();
    }

    function close() {
        opened = false;
        hide();
        flash = 0;
        cardOpacity = 0;
    }

    Connections {
        target: Screenshots
        function onSaved(path) {
            root.play(Screenshots.lastCapture);
        }
    }

    Timer {
        id: hideTimer
        interval: 2700
        repeat: false
        onTriggered: root.close()
    }

    SequentialAnimation {
        id: flashAnim
        NumberAnimation {
            target: root
            property: "flash"
            to: 0.18
            duration: 55
            easing.type: Easing.OutQuad
        }
        NumberAnimation {
            target: root
            property: "flash"
            to: 0
            duration: 280
            easing.type: Easing.InQuad
        }
    }

    SequentialAnimation {
        id: cardAnim
        PauseAnimation { duration: 150 }
        ParallelAnimation {
            NumberAnimation {
                target: root
                property: "cardOpacity"
                to: 1
                duration: 240
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: root
                property: "cardScale"
                to: 1
                duration: 430
                easing.type: Easing.OutBack
            }
            NumberAnimation {
                target: root
                property: "cardRotation"
                to: -1.5
                duration: 430
                easing.type: Easing.OutCubic
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#ffffff"
        opacity: root.flash
        visible: root.flash > 0
    }

    Rectangle {
        id: card
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 30
        anchors.bottomMargin: 30
        width: 322
        height: 218
        radius: 18
        color: "#0b111b"
        border.width: 1
        border.color: Qt.rgba(
            Library.accent.r,
            Library.accent.g,
            Library.accent.b,
            0.55
        )
        opacity: root.cardOpacity
        scale: root.cardScale
        rotation: root.cardRotation
        transformOrigin: Item.BottomRight

        Rectangle {
            anchors.fill: parent
            anchors.margins: 8
            radius: 12
            color: "#070b12"
            clip: true

            Image {
                anchors.fill: parent
                source: root.capture.url || ""
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                cache: false
            }
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: 50
            radius: 18
            color: "#0b111b"

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 18
                color: "#0b111b"
            }

            Column {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                anchors.verticalCenter: parent.verticalCenter
                spacing: 1

                Text {
                    width: parent.width
                    text: Tr.strings["SCREENSHOT"]
                    color: Library.accent
                    font.family: "Chakra Petch"
                    font.pixelSize: 8
                    font.bold: true
                    font.letterSpacing: 1.8
                }

                Text {
                    width: parent.width
                    text: root.capture.title || ""
                    color: "#f2f5fa"
                    font.family: "Sora"
                    font.pixelSize: 12
                    font.bold: true
                    elide: Text.ElideRight
                }

                Text {
                    width: parent.width
                    text: Tr.strings["Screenshot saved"] + " · "
                          + Qt.formatDateTime(
                                new Date((root.capture.takenAt || 0) * 1000),
                                "dd/MM HH:mm"
                            )
                    color: "#7d8798"
                    font.family: "Sora"
                    font.pixelSize: 9
                    elide: Text.ElideRight
                }
            }
        }
    }
}
