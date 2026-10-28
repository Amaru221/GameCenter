import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "topBar"
    height: 62
    signal toastRequested(string message)
    signal settingsRequested()
    signal updateRequested()
    signal scanRequested(string source)
    signal restoreHiddenRequested()
    signal addRequested()
    signal viewRequested(string view)
    signal bigPictureRequested()

    property string currentView: "library"

    readonly property bool searchFocused: search.activeFocus

    function focusSearch() {
        if (currentView !== "library") {
            return;
        }
        search.forceActiveFocus();
    }

    function clearSearchFocus() {
        search.focus = false;
    }

    onCurrentViewChanged: {
        if (currentView !== "library") {
            clearSearchFocus();
        }
    }

    function openMenu() {
        mainMenu.open();
    }

    Rectangle {
        anchors.fill: parent
        color: Library.surfaceColor
        opacity: 0.94
    }
    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: "#1c2028"
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 24
        anchors.rightMargin: 24
        spacing: 12

        RowLayout {
            spacing: 10

            Item {
                width: 26
                height: 30

                Rectangle {
                    anchors.fill: parent
                    radius: 6
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#454b55" }
                        GradientStop { position: 1.0; color: "#20242b" }
                    }
                    border.width: 1
                    border.color: "#565e6a"
                }
                Rectangle {
                    width: 14
                    height: 4
                    radius: 2
                    color: "#0a0b0e"
                    anchors.top: parent.top
                    anchors.topMargin: 4
                    anchors.horizontalCenter: parent.horizontalCenter
                }
                Rectangle {
                    width: 16
                    height: 10
                    radius: 2
                    color: Library.accent
                    anchors.centerIn: parent
                    anchors.verticalCenterOffset: 4
                }
            }

            Text {
                text: "GAMECENTER"
                color: "#f2f5fa"
                font.family: "Chakra Petch"
                font.pixelSize: 19
                font.bold: true
                font.letterSpacing: 2.4
            }
        }

        Item { Layout.fillWidth: true }

        Rectangle {
            objectName: "searchBox"
            Layout.preferredWidth: 380
            Layout.fillWidth: true
            Layout.minimumWidth: 140
            Layout.maximumWidth: 420
            visible: root.currentView === "library"
            height: 40
            radius: 20
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 12
                spacing: 8

                Canvas {
                    width: 16
                    height: 16
                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();
                        ctx.strokeStyle = "#8b95a5";
                        ctx.lineWidth = 1.6;
                        ctx.lineCap = "round";
                        ctx.beginPath();
                        ctx.arc(7, 7, 5, 0, Math.PI * 2);
                        ctx.moveTo(11, 11);
                        ctx.lineTo(15, 15);
                        ctx.stroke();
                    }
                }

                TextField {
                    id: search
                    Layout.fillWidth: true
                    placeholderText: Tr.strings["Search your games"]
                    placeholderTextColor: "#6f7887"
                    color: "#e8edf5"
                    background: null
                    font.family: "Sora"
                    font.pixelSize: 13
                    selectByMouse: true
                    onTextChanged: Library.setQuery(text)
                }
            }
        }

        Item { Layout.fillWidth: true }

        Rectangle {
            width: 300
            height: 38
            radius: 19
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            Row {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 2

                Repeater {
                    model: [
                        { label: "LIBRARY", value: "library" },
                        { label: "STATS", value: "stats" },
                        { label: "STORE", value: "store" }
                    ]

                    delegate: Rectangle {
                        width: (parent.width - 4) / 3
                        height: 30
                        radius: 15
                        color: root.currentView === modelData.value
                               ? "#232936"
                               : "transparent"

                        Text {
                            anchors.centerIn: parent
                            text: Tr.strings[modelData.label]
                            color: root.currentView === modelData.value
                                   ? "#f2f5fa"
                                   : "#7b8494"
                            font.family: "Chakra Petch"
                            font.pixelSize: 11
                            font.bold: true
                            font.letterSpacing: 1.4
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
                                if (modelData.value === "store") {
                                    root.toastRequested(
                                        Tr.strings["Store coming in v0.2"]
                                    );
                                } else {
                                    root.viewRequested(modelData.value);
                                }
                            }
                        }
                    }
                }
            }
        }

        Rectangle {
            id: updateButton
            visible: Library.updateAvailable
            width: 38
            height: 38
            radius: 19
            color: updateHover.containsMouse ? "#171d27" : "#0d0f14"
            border.width: 1
            border.color: updateHover.containsMouse ? Library.accent : "#2a3140"
            scale: updateHover.containsMouse ? 1.06 : 1.0

            // Announce the badge once, then stay still. An infinite pulse here
            // would repaint the whole window at the monitor refresh rate for
            // as long as an update is pending.
            onVisibleChanged: {
                if (visible) {
                    updateDotPulse.restart();
                }
            }

            Behavior on color { ColorAnimation { duration: 140 } }
            Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

            Rectangle {
                anchors.fill: parent
                radius: parent.radius
                color: "transparent"
                border.width: 1
                border.color: Library.accent
                opacity: updateHover.containsMouse ? 0.35 : 0
                Behavior on opacity { NumberAnimation { duration: 140 } }
            }

            UpdateGlyph {
                width: 20
                height: 20
                anchors.centerIn: parent
                color: Library.accent
            }

            Rectangle {
                id: updateDot
                width: 8
                height: 8
                radius: 4
                color: Library.accent
                border.width: 2
                border.color: "#0d0f14"
                anchors.top: parent.top
                anchors.right: parent.right
                anchors.topMargin: 3
                anchors.rightMargin: 3
            }

            SequentialAnimation {
                id: updateDotPulse
                NumberAnimation {
                    target: updateDot
                    property: "scale"
                    to: 1.25
                    duration: 260
                    easing.type: Easing.OutQuad
                }
                NumberAnimation {
                    target: updateDot
                    property: "scale"
                    to: 1.0
                    duration: 260
                    easing.type: Easing.InOutQuad
                }
            }

            MouseArea {
                id: updateHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.updateRequested()
            }

            ToolTip.visible: updateHover.containsMouse
            ToolTip.text: Tr.strings["GameCenter %1 is available - click to update"].arg(Library.updateVersion)
        }

        Rectangle {
            width: 38
            height: 38
            radius: 19
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            Canvas {
                width: 18
                height: 18
                anchors.centerIn: parent

                onPaint: {
                    var ctx = getContext("2d");
                    ctx.reset();
                    ctx.strokeStyle = "#c9d2e0";
                    ctx.lineWidth = 1.6;
                    ctx.lineCap = "round";
                    ctx.beginPath();
                    ctx.arc(9, 9, 3.2, 0, Math.PI * 2);
                    ctx.stroke();
                    for (var i = 0; i < 8; i++) {
                        var angle = i * Math.PI / 4;
                        ctx.beginPath();
                        ctx.moveTo(9 + Math.cos(angle) * 5.3, 9 + Math.sin(angle) * 5.3);
                        ctx.lineTo(9 + Math.cos(angle) * 7.2, 9 + Math.sin(angle) * 7.2);
                        ctx.stroke();
                    }
                }
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.settingsRequested()
            }
        }

        Rectangle {
            id: menuButton
            width: 38
            height: 38
            radius: 19
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            Column {
                anchors.centerIn: parent
                spacing: 4
                Repeater {
                    model: 3
                    Rectangle {
                        width: 15
                        height: 1.6
                        radius: 1
                        color: "#c9d2e0"
                    }
                }
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: mainMenu.open()
            }

            Popup {
                id: mainMenu
                objectName: "mainMenu"
                width: 272
                x: -width + parent.width
                y: parent.height + 8
                padding: 8
                modal: false
                focus: true
                closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                // Small declarative model: sections, spacers and rows live in
                // one list so the popup can be styled freely.
                property var entries: [
                    { kind: "section", text: Tr.strings["STORES"] },
                    {
                        kind: "item",
                        text: Tr.strings["Scan Steam games"],
                        dot: "#66c0f4",
                        action: "scan",
                        value: "steam"
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Scan Epic games"],
                        dot: "#d9e2ee",
                        action: "scan",
                        value: "epic"
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Scan GOG games"],
                        dot: "#b48cf0",
                        action: "scan",
                        value: "gog"
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Scan Battle.net games"],
                        dot: "#3aa9ff",
                        action: "scan",
                        value: "battlenet"
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Scan Riot games"],
                        dot: "#ff4655",
                        action: "scan",
                        value: "riot"
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Scan all stores"],
                        dot: Library.accent,
                        action: "scan",
                        value: ""
                    },
                    { kind: "space" },
                    { kind: "section", text: Tr.strings["LIBRARY"] },
                    {
                        kind: "item",
                        text: Tr.strings["Restore removed games"],
                        action: "restore",
                        enabled: Library.hiddenCount > 0
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Add game manually..."],
                        action: "add"
                    },
                    { kind: "space" },
                    { kind: "section", text: Tr.strings["APP"] },
                    {
                        kind: "item",
                        text: Tr.strings["Big Picture"],
                        action: "bigpicture"
                    },
                    {
                        kind: "item",
                        text: Tr.strings["Settings"],
                        action: "settings"
                    }
                ]

                function run(entry) {
                    if (entry.action === "scan") {
                        root.scanRequested(entry.value);
                    } else if (entry.action === "restore") {
                        root.restoreHiddenRequested();
                    } else if (entry.action === "add") {
                        root.addRequested();
                    } else if (entry.action === "bigpicture") {
                        root.bigPictureRequested();
                    } else if (entry.action === "settings") {
                        root.settingsRequested();
                    }
                    mainMenu.close();
                }

                background: Rectangle {
                    radius: 14
                    border.width: 1
                    border.color: "#31405a"
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: "#1a2130" }
                        GradientStop { position: 1.0; color: "#0c1017" }
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 10
                        height: 1
                        radius: 1
                        color: Qt.rgba(Library.accent.r, Library.accent.g,
                                       Library.accent.b, 0.35)
                    }
                }

                contentItem: Column {
                    width: mainMenu.availableWidth
                    spacing: 2

                    Repeater {
                        model: mainMenu.entries

                        delegate: Item {
                            id: menuRow
                            readonly property bool section: modelData.kind === "section"
                            readonly property bool spacer: modelData.kind === "space"
                            readonly property bool row: modelData.kind === "item"
                            readonly property bool hovered: rowArea.containsMouse
                                        && modelData.enabled !== false

                            width: mainMenu.width - 16
                            height: section ? 24 : (spacer ? 9 : 36)

                            Text {
                                visible: menuRow.section
                                anchors.left: parent.left
                                anchors.leftMargin: 10
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: 4
                                text: menuRow.section ? modelData.text : ""
                                color: "#6f7887"
                                font.family: "Chakra Petch"
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 2.2
                            }

                            Rectangle {
                                visible: menuRow.spacer
                                anchors.verticalCenter: parent.verticalCenter
                                x: 8
                                width: parent.width - 16
                                height: 1
                                color: "#232c3c"
                            }

                            Rectangle {
                                visible: menuRow.row
                                anchors.fill: parent
                                radius: 9
                                color: menuRow.hovered ? "#212b3c" : "transparent"

                                Rectangle {
                                    visible: menuRow.hovered
                                    anchors.left: parent.left
                                    anchors.leftMargin: 3
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: 2
                                    height: parent.height - 14
                                    radius: 1
                                    color: Library.accent
                                }
                            }

                            Rectangle {
                                visible: menuRow.row && modelData.dot !== undefined
                                anchors.left: parent.left
                                anchors.leftMargin: 12
                                anchors.verticalCenter: parent.verticalCenter
                                width: 7
                                height: 7
                                radius: 3.5
                                color: modelData.dot !== undefined
                                       ? modelData.dot : "transparent"
                            }

                            Text {
                                visible: menuRow.row
                                anchors.left: parent.left
                                anchors.leftMargin:
                                    modelData.dot !== undefined ? 30 : 14
                                anchors.right: parent.right
                                anchors.rightMargin: 12
                                anchors.verticalCenter: parent.verticalCenter
                                text: menuRow.row ? modelData.text : ""
                                color: modelData.enabled === false
                                       ? "#5f6a7b"
                                       : (menuRow.hovered ? "#ffffff" : "#dfe6f0")
                                font.family: "Sora"
                                font.pixelSize: 12
                                elide: Text.ElideRight
                            }

                            MouseArea {
                                id: rowArea
                                anchors.fill: parent
                                enabled: menuRow.row && modelData.enabled !== false
                                hoverEnabled: menuRow.row
                                cursorShape: Qt.PointingHandCursor
                                onClicked: mainMenu.run(modelData)
                            }
                        }
                    }
                }
            }
        }
    }
}
