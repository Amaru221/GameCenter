import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
    id: root
    objectName: "settingsPanel"
    property bool opened: false
    signal closeRequested()
    signal updateRequested()

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    // Keyboard capture for custom screenshot shortcuts. While recording, the
    // next combination (modifiers + key) becomes the shortcut.
    focus: Screenshots.recording
    Keys.onPressed: (event) => {
        if (!Screenshots.recording) {
            return;
        }
        event.accepted = true;
        Screenshots.recordKey(event.key, event.modifiers);
    }
    Keys.onEscapePressed: (event) => {
        if (Screenshots.recording || Gamepad.capturing) {
            event.accepted = true;
            Screenshots.cancelRecording();
            Gamepad.cancelCapture();
        }
    }

    onOpenedChanged: {
        if (!opened) {
            if (Screenshots.recording) {
                Screenshots.cancelRecording();
            }
            if (Gamepad.capturing) {
                Gamepad.cancelCapture();
            }
        }
    }

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
            objectName: "settingsScroll"
            anchors.fill: parent
            anchors.leftMargin: 30
            anchors.topMargin: 30
            anchors.bottomMargin: 30
            // Leave room for the pinned close button on the right edge.
            anchors.rightMargin: 70
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            ScrollBar.vertical.policy: ScrollBar.AlwaysOn

            ColumnLayout {
                width: scroll.availableWidth - 16
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

                    // Space for the pinned close button outside the scroller.
                    Item { width: 34; height: 1 }
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
                    spacing: 10

                    Text {
                        Layout.fillWidth: true
                        text: Tr.strings["Keyboard shortcut"]
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 13
                    }

                    Rectangle {
                        objectName: "screenshotShortcutChip"
                        Layout.preferredWidth: 200
                        height: 34
                        radius: 9
                        color: Screenshots.recording ? "#182233" : "#10141b"
                        border.width: 1
                        border.color: Screenshots.recording
                                      ? Library.accent
                                      : (Screenshots.shortcut !== "" ? "#33415a" : "#232833")

                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 20
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            text: Screenshots.recording
                                  ? (Screenshots.lastKeyPress !== ""
                                     ? Screenshots.lastKeyPress
                                     : Tr.strings["Press the keys you want to use."])
                                  : (Screenshots.shortcutLabel !== ""
                                     ? Screenshots.shortcutLabel
                                     : Tr.strings["None"])
                            color: Screenshots.recording
                                   ? Library.accent
                                   : (Screenshots.shortcut !== "" ? "#eef2f8" : "#7d8798")
                            font.family: "Chakra Petch"
                            font.pixelSize: Screenshots.recording ? 10 : 12
                            font.bold: !Screenshots.recording
                        }
                    }

                    Rectangle {
                        objectName: "screenshotRecordButton"
                        width: Screenshots.recording ? 82 : 92
                        height: 34
                        radius: 9
                        color: recordArea.containsMouse
                               ? (Screenshots.recording ? "#3a2028" : "#1e2c42")
                               : (Screenshots.recording ? "#2a1a20" : "#171b23")
                        border.width: 1
                        border.color: Screenshots.recording
                                      ? "#a24a5c"
                                      : (recordArea.containsMouse ? Library.accent : "#2a3140")

                        Text {
                            anchors.centerIn: parent
                            text: Screenshots.recording
                                  ? Tr.strings["Cancel"]
                                  : Tr.strings["Record"]
                            color: Screenshots.recording ? "#ffb4c0" : "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 11
                            font.bold: Screenshots.recording
                        }

                        MouseArea {
                            id: recordArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (Screenshots.recording) {
                                    Screenshots.cancelRecording();
                                } else {
                                    Screenshots.startRecording();
                                    root.forceActiveFocus();
                                }
                            }
                        }
                    }

                    Rectangle {
                        objectName: "screenshotClearButton"
                        visible: !Screenshots.recording && Screenshots.shortcut !== ""
                        width: 72
                        height: 34
                        radius: 9
                        color: clearArea.containsMouse ? "#232936" : "transparent"
                        border.width: 1
                        border.color: clearArea.containsMouse ? "#3b4a63" : "#232833"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Clear"]
                            color: "#8b95a5"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            id: clearArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Screenshots.clearShortcut()
                        }
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

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    Text {
                        Layout.fillWidth: true
                        text: Tr.strings["Gamepad shortcut"]
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 13
                    }

                    Rectangle {
                        objectName: "gamepadShortcutChip"
                        Layout.preferredWidth: 200
                        height: 34
                        radius: 9
                        color: Gamepad.capturing ? "#182233" : "#10141b"
                        border.width: 1
                        border.color: Gamepad.capturing
                                      ? Library.accent
                                      : (Gamepad.screenshotCombo !== "" ? "#33415a" : "#232833")

                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 20
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            text: Gamepad.capturing
                                  ? (Gamepad.capturePreview !== ""
                                     ? Gamepad.capturePreview
                                     : Tr.strings["Press the gamepad buttons you want to use."])
                                  : (Gamepad.screenshotCombo !== ""
                                     ? Gamepad.screenshotComboLabel
                                     : Tr.strings["Hold Select for %1 seconds."]
                                           .arg(Gamepad.screenshotHoldSeconds))
                            color: Gamepad.capturing
                                   ? Library.accent
                                   : (Gamepad.screenshotCombo !== "" ? "#eef2f8" : "#7d8798")
                            font.family: "Chakra Petch"
                            font.pixelSize: Gamepad.capturing ? 9 : 11
                            font.bold: !Gamepad.capturing
                        }
                    }

                    Rectangle {
                        objectName: "gamepadRecordButton"
                        width: Gamepad.capturing ? 82 : 92
                        height: 34
                        radius: 9
                        enabled: Gamepad.connected
                        opacity: Gamepad.connected ? 1 : 0.45
                        color: padArea.containsMouse && enabled
                               ? (Gamepad.capturing ? "#3a2028" : "#1e2c42")
                               : (Gamepad.capturing ? "#2a1a20" : "#171b23")
                        border.width: 1
                        border.color: Gamepad.capturing
                                      ? "#a24a5c"
                                      : (padArea.containsMouse && enabled
                                         ? Library.accent : "#2a3140")

                        Text {
                            anchors.centerIn: parent
                            text: Gamepad.capturing
                                  ? Tr.strings["Cancel"]
                                  : Tr.strings["Record"]
                            color: Gamepad.capturing ? "#ffb4c0" : "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 11
                            font.bold: Gamepad.capturing
                        }

                        MouseArea {
                            id: padArea
                            anchors.fill: parent
                            hoverEnabled: true
                            enabled: Gamepad.connected
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Gamepad.capturing
                                       ? Gamepad.cancelCapture()
                                       : Gamepad.startCapture()
                        }
                    }

                    Rectangle {
                        objectName: "gamepadClearButton"
                        visible: !Gamepad.capturing && Gamepad.screenshotCombo !== ""
                        width: 72
                        height: 34
                        radius: 9
                        color: padClearArea.containsMouse ? "#232936" : "transparent"
                        border.width: 1
                        border.color: padClearArea.containsMouse ? "#3b4a63" : "#232833"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Clear"]
                            color: "#8b95a5"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            id: padClearArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Gamepad.clearScreenshotCombo()
                        }
                    }
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
                    text: Tr.strings["SOUND"]
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
                            text: Tr.strings["Interface sounds"]
                            color: "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 12
                        }

                        Text {
                            text: Tr.strings["Short cues for navigation, modals and launching games."]
                            color: "#6f7887"
                            font.family: "Sora"
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                    }

                    Rectangle {
                        objectName: "soundToggle"
                        width: 44
                        height: 24
                        radius: 12
                        color: Sounds.enabled ? Library.accent : "#2a3140"
                        Layout.alignment: Qt.AlignVCenter

                        Rectangle {
                            width: 18
                            height: 18
                            radius: 9
                            color: "#ffffff"
                            x: Sounds.enabled ? 23 : 3
                            anchors.verticalCenter: parent.verticalCenter
                            Behavior on x { NumberAnimation { duration: 140 } }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: Sounds.setEnabled(!Sounds.enabled)
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    height: 1
                    color: "#232936"
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    height: 1
                    color: "#232936"
                }

                Text {
                    text: Tr.strings["STARTUP MOVIE"]
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
                            text: Tr.strings["Startup movie in Big Picture"]
                            color: "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 12
                        }

                        Text {
                            text: Tr.strings["Play a short intro when Big Picture opens."]
                            color: "#6f7887"
                            font.family: "Sora"
                            font.pixelSize: 10
                            wrapMode: Text.WordWrap
                        }
                    }

                    Rectangle {
                        objectName: "startupMovieToggle"
                        width: 44
                        height: 24
                        radius: 12
                        color: StartupMovies.enabled ? Library.accent : "#2a3140"
                        Layout.alignment: Qt.AlignVCenter

                        Rectangle {
                            width: 18
                            height: 18
                            radius: 9
                            color: "#ffffff"
                            x: StartupMovies.enabled ? 23 : 3
                            anchors.verticalCenter: parent.verticalCenter
                            Behavior on x { NumberAnimation { duration: 140 } }
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: StartupMovies.setEnabled(!StartupMovies.enabled)
                        }
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    visible: StartupMovies.enabled
                    spacing: 10

                    Text {
                        text: Tr.strings["Movie"]
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 13
                    }

                    PillCombo {
                        objectName: "startupMovieCombo"
                        Layout.fillWidth: true
                        Layout.minimumWidth: 160
                        value: StartupMovies.selected
                        entries: StartupMovies.options
                        enabled: StartupMovies.options.length > 0
                        onSelected: (chosen) => StartupMovies.setSelected(chosen)
                    }

                    Rectangle {
                        objectName: "startupMovieBrowse"
                        width: 104
                        height: 34
                        radius: 9
                        color: browseMovieArea.containsMouse ? "#1e2c42" : "#171b23"
                        border.width: 1
                        border.color: browseMovieArea.containsMouse
                                      ? Library.accent
                                      : "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Browse..."]
                            color: "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            id: browseMovieArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: movieDialog.open()
                        }
                    }

                    Rectangle {
                        objectName: "startupMovieRemove"
                        visible: StartupMovies.selectedIsCustom
                        width: 88
                        height: 34
                        radius: 9
                        color: removeMovieArea.containsMouse ? "#3a2028" : "transparent"
                        border.width: 1
                        border.color: removeMovieArea.containsMouse
                                      ? "#a24a5c"
                                      : "#2a3140"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings["Remove"]
                            color: "#e0a5ae"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }

                        MouseArea {
                            id: removeMovieArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: StartupMovies.removeSelected()
                        }
                    }
                }

                Text {
                    Layout.fillWidth: true
                    visible: StartupMovies.error !== ""
                    text: StartupMovies.error
                    color: "#ff8a8a"
                    font.family: "Sora"
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                }

                FileDialog {
                    id: movieDialog
                    title: Tr.strings["Choose a startup movie"]
                    nameFilters: [
                        Tr.strings["Video files (*.webm *.mp4 *.m4v *.mov *.mkv)"],
                        Tr.strings["All files (*)"]
                    ]
                    onAccepted: StartupMovies.importMovie(selectedFile)
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

        // Pinned outside the ScrollView: the close button never scrolls away.
        Rectangle {
            id: closeButton
            objectName: "settingsClose"
            z: 3
            width: 30
            height: 30
            radius: 15
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 18
            anchors.rightMargin: 18
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
}
