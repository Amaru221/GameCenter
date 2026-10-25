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

    function focusSearch() {
        search.forceActiveFocus();
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
        spacing: 16

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
            Layout.preferredWidth: 420
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
                    placeholderText: "Search your games"
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
            width: 214
            height: 38
            radius: 19
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            Row {
                anchors.fill: parent
                anchors.margins: 4
                spacing: 2

                Rectangle {
                    width: 105
                    height: 30
                    radius: 15
                    color: "#232936"

                    Text {
                        anchors.centerIn: parent
                        text: "LIBRARY"
                        color: "#f2f5fa"
                        font.family: "Chakra Petch"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 1.4
                    }
                }

                Rectangle {
                    width: 99
                    height: 30
                    radius: 15
                    color: "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: "STORE"
                        color: "#7b8494"
                        font.family: "Chakra Petch"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 1.4
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.toastRequested("Store coming in v0.2")
                    }
                }
            }
        }

        Rectangle {
            visible: Library.updateAvailable
            width: 38
            height: 38
            radius: 19
            color: "#0d0f14"
            border.width: 1
            border.color: Library.accent

            Text {
                anchors.centerIn: parent
                text: "↑"
                color: Library.accent
                font.family: "Sora"
                font.pixelSize: 16
                font.bold: true
            }

            MouseArea {
                id: updateHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.updateRequested()
            }

            ToolTip.visible: updateHover.containsMouse
            ToolTip.text: "GameCenter " + Library.updateVersion + " is available"
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

            Menu {
                id: mainMenu
                width: 250
                x: -width + parent.width
                y: parent.height + 8

                background: Rectangle {
                    color: "#12151b"
                    radius: 11
                    border.width: 1
                    border.color: "#2a3140"
                }

                delegate: MenuItem {
                    id: entry
                    width: mainMenu.width - 10
                    implicitHeight: 32
                    highlighted: mainMenu.currentIndex === index

                    contentItem: Text {
                        leftPadding: 12
                        text: entry.text
                        color: entry.enabled ? "#dfe6f0" : "#5f6a7b"
                        font.family: "Sora"
                        font.pixelSize: 12
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }

                    background: Rectangle {
                        radius: 7
                        color: entry.highlighted ? "#232936" : "transparent"
                    }
                }

                MenuItem {
                    text: "Scan Steam games"
                    onTriggered: root.scanRequested("steam")
                }
                MenuItem {
                    text: "Scan Battle.net games"
                    onTriggered: root.scanRequested("battlenet")
                }
                MenuItem {
                    text: "Scan all stores"
                    onTriggered: root.scanRequested("")
                }
                MenuSeparator {
                    contentItem: Rectangle {
                        implicitHeight: 1
                        color: "#232936"
                    }
                }
                MenuItem {
                    text: "Restore removed games"
                    enabled: Library.hiddenCount > 0
                    onTriggered: root.restoreHiddenRequested()
                }
                MenuSeparator {
                    contentItem: Rectangle {
                        implicitHeight: 1
                        color: "#232936"
                    }
                }
                MenuItem {
                    text: "Add game manually..."
                    onTriggered: root.addRequested()
                }
                MenuItem {
                    text: "Settings"
                    onTriggered: root.settingsRequested()
                }
            }
        }
    }
}
