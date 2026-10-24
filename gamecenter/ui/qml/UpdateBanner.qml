import QtQuick
import QtQuick.Layouts

Rectangle {
    id: banner
    width: 400
    height: 66
    radius: 14
    color: "#141821"
    border.width: 1
    border.color: "#2a3140"
    visible: Library.updateAvailable && !Library.updateDismissed

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 16
        anchors.rightMargin: 10
        spacing: 12

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: Library.accent
        }

        Column {
            Layout.fillWidth: true
            spacing: 2

            Text {
                text: "Update available"
                color: "#f2f5fa"
                font.family: "Sora"
                font.pixelSize: 12
                font.bold: true
            }

            Text {
                text: "GameCenter " + Library.updateVersion
                color: "#98a3b4"
                font.family: "Sora"
                font.pixelSize: 11
            }
        }

        Rectangle {
            width: 104
            height: 34
            radius: 9
            color: Library.accent

            Text {
                anchors.centerIn: parent
                text: "Download"
                color: Library.accentText
                font.family: "Sora"
                font.pixelSize: 11
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: Library.openUpdate()
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
                font.pixelSize: 13
            }

            MouseArea {
                id: closeArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: Library.dismissUpdate()
            }
        }
    }
}
