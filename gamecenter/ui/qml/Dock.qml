import QtQuick
import QtQuick.Layouts

Rectangle {
    id: dock
    width: 380
    height: 54
    radius: 27
    border.width: 1
    border.color: "#394252"

    gradient: Gradient {
        GradientStop { position: 0.0; color: "#232a35" }
        GradientStop { position: 1.0; color: "#141820" }
    }

    Rectangle {
        x: (dock.width - width) / 2
        y: 0
        width: 90
        height: 8
        radius: 4
        color: "#10141b"
    }

    Rectangle {
        x: 18
        y: 1.5
        width: dock.width - 36
        height: 1
        radius: 1
        color: "#ffffff"
        opacity: 0.10
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 22
        anchors.rightMargin: 22
        spacing: 10

        Rectangle {
            width: 8
            height: 8
            radius: 4
            color: "#3ddc97"
        }

        Text {
            text: "Ready"
            color: "#dfe6f0"
            font.family: "Sora"
            font.pixelSize: 12
        }

        Item { Layout.fillWidth: true }

        Text {
            id: clock
            color: "#aeb8c7"
            font.family: "Chakra Petch"
            font.pixelSize: 12
            font.letterSpacing: 1
        }
    }

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: clock.text = Qt.formatTime(new Date(), "hh:mm")
    }
}
