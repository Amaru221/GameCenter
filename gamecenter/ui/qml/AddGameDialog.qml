import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

Item {
    id: root
    property bool opened: false
    property string folder: ""
    property var executableEntries: []

    signal closeRequested()
    signal added()

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    onOpenedChanged: {
        if (opened) {
            titleField.text = "";
            folder = "";
            executableEntries = [];
        }
    }

    function refreshExecutables() {
        var list = Library.executablesIn(folder);
        var out = [];
        for (var i = 0; i < list.length; i++) {
            out.push({
                text: list[i].split(/[\\/]/).pop(),
                value: list[i]
            });
        }
        executableEntries = out;
        if (out.length > 0) {
            executableCombo.value = out[0].value;
        }
    }

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
        width: 560
        height: 460
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

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: Tr.strings["Add a game"]
                        color: "#f2f5fa"
                        font.family: "Sora"
                        font.pixelSize: 22
                        font.bold: true
                    }

                    Text {
                        text: Tr.strings["Pick the root folder and the executable to launch."]
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
                text: Tr.strings["Title"]
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 12
            }

            TextField {
                id: titleField
                Layout.fillWidth: true
                placeholderText: Tr.strings["Game title"]
                color: "#e8edf5"
                placeholderTextColor: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 12
                selectByMouse: true

                background: Rectangle {
                    radius: 8
                    color: "#0d0f14"
                    border.width: 1
                    border.color: "#2a3140"
                }
            }

            Text {
                text: Tr.strings["Root folder"]
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 12
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    Layout.fillWidth: true
                    height: 36
                    radius: 8
                    color: "#0d0f14"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.leftMargin: 10
                        anchors.rightMargin: 10
                        text: root.folder === "" ? Tr.strings["No folder selected"] : Library.localPath(root.folder)
                        color: root.folder === "" ? "#6f7887" : "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 11
                        elide: Text.ElideMiddle
                    }
                }

                Rectangle {
                    width: 100
                    height: 36
                    radius: 9
                    color: "#171b23"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Browse..."]
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: folderDialog.open()
                    }
                }
            }

            Text {
                text: Tr.strings["Executable"]
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 12
            }

            PillCombo {
                id: executableCombo
                Layout.fillWidth: true
                entries: root.executableEntries
                value: ""
                onSelected: (chosen) => value = chosen
            }

            Text {
                Layout.fillWidth: true
                visible: root.folder !== "" && root.executableEntries.length === 0
                text: Tr.strings["No executable found. Choose another folder or put the game executable at its root."]
                color: "#ff8a8a"
                font.family: "Sora"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
            }

            Text {
                Layout.fillWidth: true
                text: Tr.strings["You can choose a SteamGridDB cover later from the game's detail view."]
                color: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 10
                wrapMode: Text.WordWrap
            }

            Item { Layout.fillHeight: true }

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
                        text: Tr.strings["Cancel"]
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
                    width: 130
                    height: 38
                    radius: 9
                    color: Library.accent
                    opacity: canAdd ? 1 : 0.45

                    readonly property bool canAdd:
                        titleField.text.trim() !== ""
                        && root.folder !== ""
                        && executableCombo.value !== ""

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Add game"]
                        color: Library.accentText
                        font.family: "Sora"
                        font.pixelSize: 12
                        font.bold: true
                    }

                    MouseArea {
                        anchors.fill: parent
                        enabled: parent.canAdd
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (Library.addManualGame(
                                    titleField.text,
                                    root.folder,
                                    executableCombo.value)) {
                                root.added();
                                root.closeRequested();
                            }
                        }
                    }
                }
            }
        }
    }

    FolderDialog {
        id: folderDialog
        title: Tr.strings["Choose the game folder"]
        onAccepted: {
            root.folder = selectedFolder.toString();
            root.refreshExecutables();
        }
    }
}
