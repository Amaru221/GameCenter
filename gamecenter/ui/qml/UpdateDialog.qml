import QtQuick
import QtQuick.Layouts

Item {
    id: root
    property bool opened: false

    signal closeRequested()
    signal downloadRequested()

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    Rectangle {
        anchors.fill: parent
        color: "#05060a"
        opacity: 0.82

        MouseArea {
            anchors.fill: parent
            onClicked: root.closeRequested()
        }
    }

    Rectangle {
        id: panel
        width: 540
        height: 400
        anchors.centerIn: parent
        radius: 20
        border.width: 1
        border.color: "#2a3140"
        scale: root.opened ? 1 : 0.97
        Behavior on scale { NumberAnimation { duration: 200; easing.type: Easing.OutCubic } }

        gradient: Gradient {
            GradientStop { position: 0.0; color: "#151a23" }
            GradientStop { position: 1.0; color: "#0c0f14" }
        }

        MouseArea { anchors.fill: parent }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 42
                    height: 42
                    radius: 21
                    color: Library.accent

                    Text {
                        anchors.centerIn: parent
                        text: "↑"
                        color: Library.accentText
                        font.pixelSize: 20
                        font.bold: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "Update available"
                        color: "#f2f5fa"
                        font.family: "Sora"
                        font.pixelSize: 20
                        font.bold: true
                    }

                    Text {
                        text: "GameCenter " + Library.updateVersion
                        color: "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }
                }

                Rectangle {
                    width: 30
                    height: 30
                    radius: 15
                    color: closeArea.containsMouse ? "#232936" : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "✕"
                        color: "#aeb8c7"
                        font.pixelSize: 14
                    }

                    MouseArea {
                        id: closeArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closeRequested()
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                text: "You have GameCenter " + Library.version
                      + ". A newer version is ready to download."
                color: "#cfd6e2"
                font.family: "Sora"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: Library.updateNotes !== ""
                radius: 10
                color: "#0d0f14"
                border.width: 1
                border.color: "#232833"
                clip: true

                Text {
                    anchors.fill: parent
                    anchors.margins: 12
                    text: Library.updateNotes
                    color: "#98a3b4"
                    font.family: "Sora"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    elide: Text.ElideRight
                    maximumLineCount: 8
                }
            }

            Item {
                Layout.fillHeight: true
                visible: Library.updateNotes === ""
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 100
                    height: 38
                    radius: 9
                    color: "#171b23"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.centerIn: parent
                        text: "Later"
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closeRequested()
                    }
                }

                Rectangle {
                    width: 150
                    height: 38
                    radius: 9
                    color: Library.accent

                    Text {
                        anchors.centerIn: parent
                        text: "Download"
                        color: Library.accentText
                        font.family: "Sora"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.downloadRequested()
                    }
                }
            }
        }
    }
}
