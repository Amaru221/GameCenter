import QtQuick
import QtQuick.Layouts

Item {
    id: root
    property bool opened: false
    property int index: -1

    readonly property string currentCover: index >= 0 ? (Library.gameAt(index).cover || "") : ""

    signal closeRequested()
    signal settingsRequested()

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
        width: Math.min(parent.width - 80, 880)
        height: 560
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
            spacing: 14

            RowLayout {
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: "Choose artwork"
                        color: "#f2f5fa"
                        font.family: "Sora"
                        font.pixelSize: 22
                        font.bold: true
                    }

                    Text {
                        text: "Portrait grids from SteamGridDB"
                        color: "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 11
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
                visible: Library.artLoading
                text: "Looking for artwork..."
                color: "#aeb8c7"
                font.family: "Sora"
                font.pixelSize: 13
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !Library.artLoading && Library.artError !== ""
                spacing: 12

                Text {
                    Layout.fillWidth: true
                    text: Library.artError
                    color: "#ff8a8a"
                    font.family: "Sora"
                    font.pixelSize: 13
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    spacing: 10

                    Rectangle {
                        width: 150
                        height: 36
                        radius: 9
                        color: Library.accent

                        Text {
                            anchors.centerIn: parent
                            text: "Open Settings"
                            color: Library.accentText
                            font.family: "Sora"
                            font.pixelSize: 12
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.settingsRequested()
                        }
                    }

                    Rectangle {
                        width: 110
                        height: 36
                        radius: 9
                        color: "#171b23"
                        border.width: 1
                        border.color: "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: "Try again"
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 12
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Library.loadArtOptions(root.index)
                        }
                    }
                }

                Item { Layout.fillHeight: true }
            }

            Flow {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 12
                visible: !Library.artLoading && Library.artError === ""

                // The current cover / fallback.
                Rectangle {
                    width: 150
                    height: 210
                    radius: 10
                    color: "#0d0f14"
                    border.width: 1
                    border.color: defaultArea.containsMouse ? Library.accent : "#2a3140"
                    clip: true

                    Image {
                        anchors.fill: parent
                        anchors.bottomMargin: 28
                        source: root.currentCover
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        cache: true
                    }

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: 28
                        color: "#0a0c10"

                        Text {
                            anchors.centerIn: parent
                            text: "Default"
                            color: "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }
                    }

                    MouseArea {
                        id: defaultArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            Library.resetArt(root.index);
                            root.closeRequested();
                        }
                    }
                }

                Repeater {
                    model: Library.artOptions

                    delegate: Rectangle {
                        width: 150
                        height: 210
                        radius: 10
                        color: "#0d0f14"
                        border.width: 1
                        border.color: optionArea.containsMouse ? Library.accent : "#2a3140"
                        clip: true

                        Image {
                            anchors.fill: parent
                            source: modelData.thumb
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            cache: true
                        }

                        MouseArea {
                            id: optionArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Library.chooseArt(root.index, modelData.url)
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: !Library.artLoading && Library.artError === ""
                text: "Up to 5 options. Pick one to replace the current cover, or keep the default."
                color: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 10
            }
        }
    }
}
