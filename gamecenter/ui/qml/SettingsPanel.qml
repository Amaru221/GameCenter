import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property bool opened: false
    signal closeRequested()
    signal updateRequested()

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
        height: 740
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

        ScrollView {
            id: scroll
            anchors.fill: parent
            anchors.margins: 30
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            ColumnLayout {
                width: scroll.availableWidth
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true

                    Text {
                        Layout.fillWidth: true
                        text: Tr.strings["Settings"]
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
                    text: Tr.strings["LANGUAGE"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Text {
                        Layout.fillWidth: true
                        text: Tr.strings["Interface language"]
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 13
                    }

                    PillCombo {
                        objectName: "languageCombo"
                        Layout.preferredWidth: 190
                        entries: Tr.languages
                        value: Tr.language
                        onSelected: (chosen) => Tr.setLanguage(chosen)
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    height: 1
                    color: "#232936"
                }

                Text {
                    text: Tr.strings["APPEARANCE"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                Text {
                    text: Tr.strings["Accent colour"]
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 13
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 6

                    Repeater {
                        model: Library.palette

                        delegate: ColorSwatch {
                            colour: modelData
                            selected: Library.accent.toLowerCase() === modelData.toLowerCase()
                            onClicked: Library.setAccent(modelData)
                        }
                    }
                }

                Text {
                    Layout.topMargin: 2
                    text: Tr.strings["Surface colour · navbar, Ready dock and shelf"]
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 13
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 6

                    Repeater {
                        model: Library.surfacePalette

                        delegate: ColorSwatch {
                            colour: modelData
                            selected: Library.surfaceColor.toLowerCase() === modelData.toLowerCase()
                            onClicked: Library.setSurfaceColor(modelData)
                        }
                    }
                }

                Text {
                    Layout.topMargin: 2
                    text: Tr.strings["Cartridge colour"]
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 13
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 6

                    Repeater {
                        model: Library.cartridgePalette

                        delegate: ColorSwatch {
                            colour: modelData
                            selected: Library.cartridgeColor.toLowerCase() === modelData.toLowerCase()
                            onClicked: Library.setCartridgeColor(modelData)
                        }
                    }
                }

                Text {
                    Layout.topMargin: 4
                    text: Tr.strings["Cartridge style"]
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 13
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Repeater {
                        model: [
                            { text: Tr.strings["Classic"], value: "classic" },
                            { text: Tr.strings["Nintendo DS"], value: "ds" },
                            { text: Tr.strings["PS2"], value: "ps2" }
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
                    text: Tr.strings["SCREENSHOTS"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                Text {
                    Layout.fillWidth: true
                    text: Tr.strings["Captures a screenshot of the game you're playing."]
                    color: "#98a3b4"
                    font.family: "Sora"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Text {
                        Layout.fillWidth: true
                        text: Tr.strings["Keyboard shortcut"]
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 13
                    }

                    PillCombo {
                        objectName: "screenshotShortcutCombo"
                        Layout.preferredWidth: 220
                        entries: [
                            { text: Tr.strings["Ctrl + Page Down"], value: "ctrl+pagedown" },
                            { text: Tr.strings["Ctrl + F12"], value: "ctrl+f12" },
                            { text: Tr.strings["F12"], value: "f12" },
                            { text: Tr.strings["Print Screen"], value: "printscreen" },
                            { text: Tr.strings["Ctrl + Shift + S"], value: "ctrl+shift+s" },
                            { text: Tr.strings["None"], value: "none" }
                        ]
                        value: Screenshots.shortcut
                        onSelected: (chosen) => Screenshots.setShortcut(chosen)
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: Screenshots.error !== ""
                    text: Screenshots.error
                    color: "#ff8a8a"
                    font.family: "Sora"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                Text {
                    Layout.fillWidth: true
                    text: Tr.strings["Gamepad: hold Select for %1 seconds."]
                              .arg(Gamepad.screenshotHoldSeconds)
                    color: "#98a3b4"
                    font.family: "Sora"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        Layout.fillWidth: true
                        text: Tr.strings["Screenshots are saved in %1."]
                                  .arg(Screenshots.directory)
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 10
                        wrapMode: Text.WordWrap
                    }

                    Rectangle {
                        width: 172
                        height: 34
                        radius: 9
                        color: openShotsArea.containsMouse ? "#1e2c42" : "#171b23"
                        border.width: 1
                        border.color: openShotsArea.containsMouse
                                      ? Library.accent
                                      : "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Open screenshots folder"]
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            id: openShotsArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Screenshots.openFolder()
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    height: 1
                    color: "#232936"
                }

                Text {
                    text: Tr.strings["STEAMGRIDDB"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                Text {
                    Layout.fillWidth: true
                    text: Tr.strings["Optional. Paste your SteamGridDB API key to choose a cover per game. "
                                     + "It is stored in the system credential store, never in the repository."]
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
                                         ? Tr.strings["Key saved — paste a new one to replace it"]
                                         : Tr.strings["Paste your SteamGridDB API key"]
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
                            text: Tr.strings["Save"]
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
                            text: Tr.strings["Clear"]
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
                    text: Tr.strings["Get a key at steamgriddb.com/profile/preferences/api"]
                    color: Library.accent
                    font.family: "Sora"
                    font.pixelSize: 11

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Qt.openUrlExternally("https://www.steamgriddb.com/profile/preferences/api")
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    height: 1
                    color: "#232936"
                }

                Text {
                    text: Tr.strings["UPDATES"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    Column {
                        Layout.fillWidth: true
                        spacing: 2

                        Text {
                            text: "GameCenter " + Library.version
                            color: "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 12
                        }

                        Text {
                            text: Tr.strings["Last checked: %1"].arg(Library.lastUpdateCheckText)
                            color: "#6f7887"
                            font.family: "Sora"
                            font.pixelSize: 10
                        }
                    }

                    Row {
                        spacing: 8
                        Layout.alignment: Qt.AlignVCenter

                        Text {
                            text: Tr.strings["Check automatically"]
                            color: "#98a3b4"
                            font.family: "Sora"
                            font.pixelSize: 11
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Rectangle {
                            width: 44
                            height: 24
                            radius: 12
                            color: Library.checkUpdatesEnabled ? Library.accent : "#2a3140"
                            anchors.verticalCenter: parent.verticalCenter

                            Rectangle {
                                width: 18
                                height: 18
                                radius: 9
                                color: "#ffffff"
                                x: Library.checkUpdatesEnabled ? 23 : 3
                                anchors.verticalCenter: parent.verticalCenter
                                Behavior on x { NumberAnimation { duration: 140 } }
                            }

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: Library.setCheckUpdates(!Library.checkUpdatesEnabled)
                            }
                        }
                    }

                    Rectangle {
                        width: 110
                        height: 34
                        radius: 9
                        color: "#171b23"
                        border.width: 1
                        border.color: "#2a3140"
                        opacity: Library.updateChecking ? 0.6 : 1

                        Text {
                            anchors.centerIn: parent
                            text: Library.updateChecking ? Tr.strings["Checking..."] : Tr.strings["Check now"]
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            anchors.fill: parent
                            enabled: !Library.updateChecking
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Library.checkForUpdates()
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: Library.updateChecking
                          ? Tr.strings["Checking for updates..."]
                          : (Library.updateError !== ""
                             ? Library.updateError
                             : (Library.updateAvailable
                                ? Tr.strings["GameCenter %1 is available."].arg(Library.updateVersion)
                                : Tr.strings["You're up to date."]))
                    color: Library.updateError !== ""
                           ? "#ff8a8a"
                           : (Library.updateAvailable ? Library.accent : "#8b95a5")
                    font.family: "Sora"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                Rectangle {
                    visible: Library.updateAvailable
                    width: 160
                    height: 34
                    radius: 9
                    color: Library.accent

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Update now"]
                        color: Library.accentText
                        font.family: "Sora"
                        font.pixelSize: 11
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.updateRequested()
                    }
                }

                Item { Layout.preferredHeight: 4 }

                Text {
                    text: Tr.strings["GameCenter %1 · MIT"].arg(Library.version)
                    color: "#5f6a7b"
                    font.family: "Sora"
                    font.pixelSize: 11
                }
            }
        }
    }
}
