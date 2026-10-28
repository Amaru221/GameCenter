import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "artPicker"
    property bool opened: false
    property int index: -1

    readonly property string currentCover: index >= 0 ? (Library.gameAt(index).cover || "") : ""

    signal closeRequested
    signal settingsRequested

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity {
        NumberAnimation {
            duration: 180
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
        width: Math.min(parent.width - 80, 880)
        height: 560
        anchors.centerIn: parent
        radius: 20
        border.width: 1
        border.color: "#2a3140"
        scale: root.opened ? 1 : 0.97
        Behavior on scale {
            NumberAnimation {
                duration: 200
                easing.type: Easing.OutCubic
            }
        }

        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: "#151a23"
            }
            GradientStop {
                position: 1.0
                color: "#0c0f14"
            }
        }

        MouseArea {
            anchors.fill: parent
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 28
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                spacing: 18

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: Tr.strings["Choose artwork"]
                        color: "#f2f5fa"
                        font.family: "Sora"
                        font.pixelSize: 22
                        font.bold: true
                    }

                    Text {
                        text: Tr.strings["Portrait grids from SteamGridDB"]
                        color: "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    Text {
                        text: Tr.strings["Use an image from your computer"]
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 10
                    }
                }

                Rectangle {
                    objectName: "browseCoverButton"
                    Layout.alignment: Qt.AlignVCenter
                    width: 132
                    height: 38
                    radius: 10
                    color: browseArea.containsMouse ? "#1e2c42" : "#101722"
                    border.width: 1
                    border.color: browseArea.containsMouse ? Library.accent : "#2a3140"

                    Row {
                        anchors.centerIn: parent
                        spacing: 8

                        Canvas {
                            width: 14
                            height: 14
                            anchors.verticalCenter: parent.verticalCenter
                            onPaint: {
                                var ctx = getContext("2d");
                                ctx.reset();
                                ctx.strokeStyle = browseArea.containsMouse
                                                  ? Library.accent : "#c9d2e0";
                                ctx.lineWidth = 1.4;
                                ctx.lineJoin = "round";
                                ctx.strokeRect(1, 3, 12, 9);
                                ctx.beginPath();
                                ctx.moveTo(3, 10);
                                ctx.lineTo(6.5, 6.5);
                                ctx.lineTo(9, 9);
                                ctx.lineTo(11, 7);
                                ctx.lineTo(13, 10);
                                ctx.stroke();
                            }
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: Tr.strings["Browse..."]
                            color: browseArea.containsMouse ? Library.accent : "#dfe6f0"
                            font.family: "Sora"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: browseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var file = Library.chooseCoverFile();
                            if (file !== "") {
                                Library.setGameCover(root.index, file);
                            }
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: Library.artLoading
                text: Tr.strings["Looking for artwork..."]
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
                            text: Tr.strings["Open Settings"]
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
                            text: Tr.strings["Try again"]
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

                Item {
                    Layout.fillHeight: true
                }
            }

            Flickable {
                id: optionsFlick
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: optionsFlow.height
                clip: true
                visible: !Library.artLoading && Library.artError === ""
                boundsBehavior: Flickable.StopAtBounds

                ScrollBar.vertical: ScrollBar {
                    id: optionsBar
                    policy: ScrollBar.AsNeeded
                    width: 8
                    background: Item {}
                    contentItem: Rectangle {
                        implicitWidth: 6
                        radius: 3
                        color: "#3a465c"
                        opacity: optionsBar.pressed ? 1 : 0.55
                    }
                }

                Flow {
                    id: optionsFlow
                    width: Math.max(0, optionsFlick.width - 14)
                    spacing: 12

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
                                text: Tr.strings["Default"]
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
            }

            RowLayout {
                Layout.fillWidth: true
                visible: !Library.artLoading && Library.artError === ""

                Text {
                    Layout.fillWidth: true
                    text: Library.artHasMore
                          ? Tr.strings["Showing %1 of %2 loaded options."]
                                .arg(Library.artOptions.length).arg(Library.artTotal)
                          : Tr.strings["Showing all %1 options."].arg(Library.artOptions.length)
                    color: "#6f7887"
                    font.family: "Sora"
                    font.pixelSize: 10
                }

                Rectangle {
                    visible: Library.artHasMore
                    width: 110
                    height: 30
                    radius: 8
                    color: moreArea.containsMouse ? "#232936" : "#171b23"
                    border.width: 1
                    border.color: "#2a3140"
                    opacity: Library.artLoadingMore ? 0.6 : 1

                    Text {
                        anchors.centerIn: parent
                        text: Library.artLoadingMore ? Tr.strings["Loading..."] : Tr.strings["Load more"]
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    MouseArea {
                        id: moreArea
                        anchors.fill: parent
                        enabled: !Library.artLoadingMore
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: Library.loadMoreArtOptions()
                    }
                }
            }
        }

        Rectangle {
            id: artClose
            z: 2
            width: 30
            height: 30
            radius: 15
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 16
            anchors.rightMargin: 16
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

    Connections {
        target: Library
        function onArtOptionsChanged() {
            if (Library.artLoading) {
                optionsFlick.contentY = 0;
            }
        }
    }
}
