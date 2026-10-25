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
            enabled: !Library.updateDownloading && !Library.updateInstalling && !Library.updateReady
            onClicked: root.closeRequested()
        }
    }

    Rectangle {
        id: panel
        width: 540
        height: 440
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

                    UpdateGlyph {
                        width: 20
                        height: 20
                        anchors.centerIn: parent
                        color: Library.accentText
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

            }

            Text {
                Layout.fillWidth: true
                text: "You have GameCenter " + Library.version
                      + ". A newer version is ready to download and install."
                color: "#cfd6e2"
                font.family: "Sora"
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }

            Text {
                Layout.fillWidth: true
                visible: Library.updateSizeText !== ""
                text: "Installer: " + Library.updateSizeText
                color: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 10
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

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6
                visible: Library.updateDownloading || Library.updateReady || Library.updateInstalling

                Text {
                    Layout.fillWidth: true
                    text: Library.updateStatus
                    color: "#cfd6e2"
                    font.family: "Sora"
                    font.pixelSize: 12
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 8
                    radius: 4
                    color: "#0d0f14"
                    border.width: 1
                    border.color: "#232833"

                    Rectangle {
                        width: parent.width * Math.max(0, Math.min(1, Library.updateProgress))
                        height: parent.height
                        radius: 4
                        color: Library.accent
                        Behavior on width { NumberAnimation { duration: 120 } }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: Library.updateBytesText
                    color: "#8b95a5"
                    font.family: "Sora"
                    font.pixelSize: 10
                }
            }

            Text {
                Layout.fillWidth: true
                visible: Library.updateError !== ""
                text: Library.updateError
                color: "#ff8a8a"
                font.family: "Sora"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
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
                    opacity: Library.updateDownloading || Library.updateInstalling || Library.updateReady ? 0.45 : 1

                    Text {
                        anchors.centerIn: parent
                        text: "Later"
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }

                    MouseArea {
                        anchors.fill: parent
                        enabled: !Library.updateDownloading && !Library.updateInstalling && !Library.updateReady
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closeRequested()
                    }
                }

                Rectangle {
                    width: 170
                    height: 38
                    radius: 9
                    color: Library.accent
                    opacity: Library.updateDownloading || Library.updateInstalling || Library.updateReady ? 0.6 : 1

                    Text {
                        anchors.centerIn: parent
                        text: Library.updateDownloading
                              ? "Downloading..."
                              : (Library.updateInstalling || Library.updateReady ? "Installing..." : "Update now")
                        color: Library.accentText
                        font.family: "Sora"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        enabled: !Library.updateDownloading && !Library.updateInstalling && !Library.updateReady
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.downloadRequested()
                    }
                }
            }
        }

        Rectangle {
            width: 30
            height: 30
            radius: 15
            z: 2
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 16
            anchors.rightMargin: 16
            color: closeArea.containsMouse ? "#232936" : "transparent"
            opacity: Library.updateDownloading || Library.updateInstalling || Library.updateReady ? 0.4 : 1

            Text {
                anchors.centerIn: parent
                text: "✕"
                color: "#aeb8c7"
                font.pixelSize: 14
            }

            MouseArea {
                id: closeArea
                anchors.fill: parent
                enabled: !Library.updateDownloading && !Library.updateInstalling && !Library.updateReady
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.closeRequested()
            }
        }
    }
}
