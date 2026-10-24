import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property bool opened: false
    signal closeRequested()

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    Rectangle {
        anchors.fill: parent
        color: "#05060a"
        opacity: 0.8

        MouseArea {
            anchors.fill: parent
            onClicked: root.closeRequested()
        }
    }

    Rectangle {
        id: panel
        width: Math.min(parent.width - 80, 900)
        height: 620
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
            anchors.margins: 30
            spacing: 12

            RowLayout {
                Layout.fillWidth: true

                Text {
                    Layout.fillWidth: true
                    text: "Settings"
                    color: "#f2f5fa"
                    font.family: "Sora"
                    font.pixelSize: 24
                    font.bold: true
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
                text: "APPEARANCE"
                color: "#8b95a5"
                font.family: "Chakra Petch"
                font.pixelSize: 11
                font.bold: true
                font.letterSpacing: 2.4
            }

            Text {
                text: "Accent colour"
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 13
            }

            Flow {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: Library.palette

                    delegate: Rectangle {
                        width: 30
                        height: 30
                        radius: 8
                        color: modelData
                        border.width: Library.accent.toLowerCase() === modelData.toLowerCase() ? 2 : 1
                        border.color: Library.accent.toLowerCase() === modelData.toLowerCase()
                                      ? "#ffffff" : "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            visible: Library.accent.toLowerCase() === modelData.toLowerCase()
                            text: "✓"
                            color: Library.accentText
                            font.pixelSize: 12
                            font.bold: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Library.setAccent(modelData)
                        }
                    }
                }
            }

            Text {
                Layout.topMargin: 4
                text: "Cartridge style"
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 13
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Repeater {
                    model: [
                        { text: "Classic", value: "classic" },
                        { text: "Nintendo DS", value: "ds" },
                        { text: "PS2", value: "ps2" }
                    ]

                    delegate: Rectangle {
                        width: 160
                        height: 54
                        radius: 10
                        color: Library.cartridgeStyle === modelData.value ? "#1e2a3a" : "#12151b"
                        border.width: 1
                        border.color: Library.cartridgeStyle === modelData.value
                                      ? Library.accent : "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: modelData.text
                            color: "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 12
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Library.setCartridgeStyle(modelData.value)
                        }
                    }
                }

                Item { Layout.fillWidth: true }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 4
                height: 1
                color: "#232936"
            }

            Text {
                text: "STEAMGRIDDB"
                color: "#8b95a5"
                font.family: "Chakra Petch"
                font.pixelSize: 11
                font.bold: true
                font.letterSpacing: 2.4
            }

            Text {
                Layout.fillWidth: true
                text: "Optional. Paste your SteamGridDB API key to choose a cover per game. "
                      + "It is stored in the system credential store, never in the repository."
                color: "#98a3b4"
                font.family: "Sora"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                TextField {
                    id: keyField
                    Layout.fillWidth: true
                    placeholderText: Library.hasSteamGridKey
                                     ? "Key saved — paste a new one to replace it"
                                     : "Paste your SteamGridDB API key"
                    echoMode: TextInput.Password
                    color: "#e8edf5"
                    placeholderTextColor: "#6f7887"
                    font.family: "Sora"
                    font.pixelSize: 12
                    selectByMouse: true

                    background: Rectangle {
                        radius: 8
                        color: "#0d0f14"
                        border.width: 1
                        border.color: keyField.activeFocus ? Library.accent : "#2a3140"
                    }
                }

                Rectangle {
                    width: 84
                    height: 36
                    radius: 9
                    color: Library.accent

                    Text {
                        anchors.centerIn: parent
                        text: "Save"
                        color: Library.accentText
                        font.family: "Sora"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            Library.saveSteamGridKey(keyField.text);
                            keyField.text = "";
                        }
                    }
                }

                Rectangle {
                    width: 84
                    height: 36
                    radius: 9
                    color: "#171b23"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.centerIn: parent
                        text: "Clear"
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 12
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Library.clearSteamGridKey()
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: text !== ""
                text: Library.credentialsMessage
                color: Library.hasSteamGridKey ? "#3ddc97" : "#ff8a8a"
                font.family: "Sora"
                font.pixelSize: 11
            }

            Text {
                text: "Get a key at steamgriddb.com/profile/preferences/api"
                color: Library.accent
                font.family: "Sora"
                font.pixelSize: 11

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: Qt.openUrlExternally("https://www.steamgriddb.com/profile/preferences/api")
                }
            }

            Item { Layout.fillHeight: true }

            Text {
                text: "GameCenter " + Library.version + " · MIT"
                color: "#5f6a7b"
                font.family: "Sora"
                font.pixelSize: 11
            }
        }
    }
}
