import QtQuick
import QtQuick.Layouts

Rectangle {
    id: dock
    objectName: "dock"
    readonly property bool idle: Sessions.count === 0
    property bool inserting: false
    width: idle ? 380 : Math.min(920, 180 + Sessions.count * 204)
    height: 54
    radius: 27
    border.width: 1
    border.color: Qt.lighter(Library.surfaceColor, 1.6)
    clip: true

    gradient: Gradient {
        GradientStop { position: 0.0; color: Qt.lighter(Library.surfaceColor, 1.3) }
        GradientStop { position: 1.0; color: Qt.darker(Library.surfaceColor, 1.05) }
    }

    Behavior on width { NumberAnimation { duration: 220; easing.type: Easing.OutCubic } }

    Rectangle {
        x: (dock.width - width) / 2
        y: -1
        width: 150
        height: 11
        radius: 5.5
        color: "#10141b"
        border.width: 1
        border.color: Qt.darker(Library.surfaceColor, 2.1)
    }

    Rectangle {
        x: (dock.width - width) / 2
        y: 0
        width: 150
        height: 7
        radius: 3.5
        color: Library.accent
        opacity: dock.inserting ? 0.9 : 0
        Behavior on opacity { NumberAnimation { duration: 140 } }
    }

    Rectangle {
        x: 18
        y: 1.5
        width: dock.width - 36
        height: 1
        radius: 1
        color: "#ffffff"
        opacity: 0.10
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 18
        spacing: 10

        Row {
            visible: dock.idle
            Layout.alignment: Qt.AlignVCenter
            spacing: 10

            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: "#3ddc97"
            }

            Text {
                text: Tr.strings["Ready"]
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 12
            }
        }

        Row {
            visible: dock.inserting
            Layout.alignment: Qt.AlignVCenter
            spacing: 8

            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: Library.accent
            }

            Text {
                text: Tr.strings["Inserting..."]
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 12
            }
        }

        Row {
            visible: !dock.idle
            opacity: dock.inserting ? 0 : 1
            Behavior on opacity { NumberAnimation { duration: 180 } }
            Layout.alignment: Qt.AlignVCenter
            spacing: 8

            Repeater {
                model: Sessions.list

                delegate: Rectangle {
                    width: 194
                    height: 38
                    radius: 10
                    color: "#0d0f14"
                    border.width: 1
                    border.color: "#2a3140"

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 5
                        spacing: 8

                        Image {
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 28
                            source: modelData.cover
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            cache: true
                        }

                        Column {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                width: parent.width
                                text: modelData.title
                                color: "#dfe6f0"
                                font.family: "Sora"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.elapsed
                                color: "#8b95a5"
                                font.family: "Chakra Petch"
                                font.pixelSize: 9
                                font.letterSpacing: 0.8
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 18
                            Layout.preferredHeight: 18
                            radius: 9
                            color: ejectArea.containsMouse ? "#232936" : "#171b23"

                            Text {
                                anchors.centerIn: parent
                                text: "×"
                                color: "#aeb8c7"
                                font.pixelSize: 12
                            }

                            MouseArea {
                                id: ejectArea
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Sessions.eject(modelData.id)
                            }
                        }
                    }
                }
            }
        }

        Item { Layout.fillWidth: true }

        Text {
            id: clock
            color: "#aeb8c7"
            font.family: "Chakra Petch"
            font.pixelSize: 12
            font.letterSpacing: 1
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: clock.text = Qt.formatTime(new Date(), "hh:mm")
    }
}
