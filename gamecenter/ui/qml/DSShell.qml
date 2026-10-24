import QtQuick

Item {
    id: root
    width: 168
    height: 210
    y: 14

    property string gameTitle: ""
    property string gameSource: ""
    property string gameMeta: ""
    property string coverUrl: ""
    property bool gameInstalled: true
    property bool selected: false
    property bool hovered: false
    property real tiltX: 0
    property real tiltY: 0

    Flipable {
        id: flip
        objectName: "dsFlip"
        anchors.fill: parent
        property bool flipped: false

        front: Item {
            anchors.fill: parent

            Rectangle {
                anchors.fill: parent
                radius: 12
                border.width: 1
                border.color: "#4d535e"
                gradient: Gradient {
                    GradientStop { position: 0.0; color: root.hovered ? "#454a54" : "#3a3f48" }
                    GradientStop { position: 1.0; color: "#22262c" }
                }
            }

            Rectangle {
                width: 54
                height: 8
                radius: 4
                color: "#0b0d10"
                anchors.top: parent.top
                anchors.topMargin: 7
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Rectangle {
                id: label
                x: 14
                y: 24
                width: parent.width - 28
                height: parent.height - 46
                radius: 6
                color: "#0b0d10"
                border.width: 1
                border.color: "#15181d"
                clip: true

                Image {
                    anchors.fill: parent
                    source: root.coverUrl
                    fillMode: Image.PreserveAspectCrop
                    verticalAlignment: Image.AlignBottom
                    asynchronous: true
                    cache: true
                    smooth: true
                }

                Rectangle {
                    width: parent.width
                    height: 20
                    color: "#0a0c10"
                    opacity: 0.94
                }

                Text {
                    x: 8
                    y: 5
                    text: "DS"
                    color: "#eef2f7"
                    font.family: "Chakra Petch"
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 18
                    color: "#0a0c10"
                    opacity: 0.94
                }

                Text {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.leftMargin: 7
                    anchors.rightMargin: 7
                    anchors.bottomMargin: 5
                    text: root.gameMeta
                    color: "#c3ccda"
                    font.family: "Chakra Petch"
                    font.pixelSize: 7
                    elide: Text.ElideRight
                }
            }

            Rectangle {
                width: 30
                height: 5
                radius: 2.5
                color: "#171a1f"
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 9
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Rectangle {
                anchors.fill: parent
                radius: 12
                color: "transparent"
                border.width: 2
                border.color: Library.accent
                visible: root.selected
            }
        }

        back: Item {
            anchors.fill: parent

            Rectangle {
                anchors.fill: parent
                radius: 12
                border.width: 1
                border.color: "#454b56"
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#333842" }
                    GradientStop { position: 1.0; color: "#1b1e24" }
                }
            }

            Row {
                anchors.centerIn: parent
                anchors.verticalCenterOffset: -12
                spacing: 6

                Repeater {
                    model: 5

                    Rectangle {
                        width: 18
                        height: 56
                        radius: 3
                        border.width: 1
                        border.color: "#d8b25e"
                        gradient: Gradient {
                            GradientStop { position: 0.0; color: "#f7df9c" }
                            GradientStop { position: 0.45; color: "#b8862f" }
                            GradientStop { position: 1.0; color: "#6f4d14" }
                        }
                    }
                }
            }

            Rectangle {
                width: 14
                height: 14
                radius: 7
                color: "#0d0f12"
                border.width: 1
                border.color: "#4a505a"
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 30
            }

            Column {
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 11
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 4

                Repeater {
                    model: 3
                    Rectangle {
                        width: 60
                        height: 2
                        radius: 1
                        color: "#12151a"
                    }
                }
            }

            Rectangle {
                anchors.fill: parent
                radius: 12
                color: "transparent"
                border.width: 2
                border.color: Library.accent
                visible: root.selected
            }
        }

        transform: Rotation {
            origin.x: flip.width / 2
            origin.y: flip.height / 2
            axis { x: 0; y: 1; z: 0 }
            angle: flip.flipped ? 180 : 0
            Behavior on angle { NumberAnimation { duration: 450; easing.type: Easing.InOutCubic } }
        }
    }

    Rectangle {
        width: 22
        height: 22
        radius: 11
        color: "#0d0f14"
        border.width: 1
        border.color: "#3a4250"
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: 7
        anchors.bottomMargin: 7
        z: 10
        opacity: root.hovered || flip.flipped ? 1 : 0.65

        Text {
            anchors.centerIn: parent
            text: "↻"
            color: "#cfd6e2"
            font.pixelSize: 12
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: flip.flipped = !flip.flipped
        }
    }
}
