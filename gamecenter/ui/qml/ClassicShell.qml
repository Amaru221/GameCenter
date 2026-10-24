import QtQuick
import QtQuick.Shapes

Item {
    id: root
    width: 168
    height: 230

    property string gameTitle: ""
    property string gameSource: ""
    property string gameMeta: ""
    property string coverUrl: ""
    property bool gameInstalled: true
    property bool selected: false
    property bool hovered: false
    property real tiltX: 0
    property real tiltY: 0
    property real flipAngle: 0

    Rectangle {
        id: shell
        anchors.fill: parent
        radius: 19
        border.width: 1
        border.color: "#4c525c"

        gradient: Gradient {
            GradientStop { position: 0.0; color: root.hovered ? "#4f5560" : "#454b55" }
            GradientStop { position: 0.16; color: "#3a3f48" }
            GradientStop { position: 0.72; color: "#2c3038" }
            GradientStop { position: 1.0; color: "#24272e" }
        }

        Rectangle {
            x: 16
            y: 1.5
            width: shell.width - 32
            height: 1.2
            radius: 1
            color: "#ffffff"
            opacity: 0.16
        }

        Rectangle {
            x: (shell.width - width) / 2
            y: 9
            width: 68
            height: 9
            radius: 4.5
            color: "#0a0b0e"
            border.width: 1
            border.color: "#15181d"

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 1
                width: parent.width - 18
                height: 1
                color: "#4c525c"
                opacity: 0.5
            }
        }

        Rectangle {
            id: label
            x: 12 + root.tiltY * 0.65
            y: 23 - root.tiltX * 0.45
            width: shell.width - 24
            height: shell.height - 46
            radius: 9
            color: "#090b0e"
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
                height: 26
                color: "#0a0c10"
                opacity: 0.94
            }

            Row {
                x: 8
                y: 5
                spacing: 6

                Rectangle {
                    width: 16
                    height: 16
                    radius: 8
                    color: "#eef2f7"

                    Text {
                        anchors.centerIn: parent
                        text: root.gameSource.length > 0
                              ? root.gameSource.charAt(0).toUpperCase() : "?"
                        color: "#0b0d10"
                        font.family: "Chakra Petch"
                        font.pixelSize: 9
                        font.bold: true
                    }
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: root.gameSource.toUpperCase()
                    color: "#eef2f7"
                    font.family: "Chakra Petch"
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1.6
                }
            }

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 22
                color: "#0a0c10"
                opacity: 0.94
            }

            Text {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.leftMargin: 8
                anchors.rightMargin: 8
                anchors.bottomMargin: 7
                text: root.gameMeta
                color: "#c3ccda"
                font.family: "Chakra Petch"
                font.pixelSize: 8
                font.letterSpacing: 0.6
                elide: Text.ElideRight
            }
        }

        Rectangle {
            x: 2
            y: 2
            width: shell.width - 4
            height: shell.height * 0.42
            radius: 18
            opacity: 0.10 + Math.abs(root.tiltY) / 140
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#ffffff" }
                GradientStop { position: 1.0; color: "#00ffffff" }
            }
        }

        Shape {
            width: 42
            height: 7
            x: (shell.width - width) / 2
            y: shell.height - 9

            ShapePath {
                strokeColor: "transparent"
                fillColor: "#171a1f"
                startX: 0
                startY: 0
                PathLine { x: 42; y: 0 }
                PathLine { x: 34; y: 7 }
                PathLine { x: 8; y: 7 }
                PathLine { x: 0; y: 0 }
            }
        }
    }

    Rectangle {
        anchors.fill: shell
        radius: shell.radius
        color: "transparent"
        border.width: 2
        border.color: Library.accent
        opacity: root.selected ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 140 } }
    }
}
