import QtQuick

Item {
    id: root
    width: 168
    height: 232
    y: 3

    property string gameTitle: ""
    property string gameSource: ""
    property string gameMeta: ""
    property string coverUrl: ""
    property bool gameInstalled: true
    property color cartridgeColor: Library.cartridgeColor
    property bool hovered: false
    property real tiltX: 0
    property real tiltY: 0

    Rectangle {
        anchors.fill: parent
        radius: 8
        border.width: 2
        border.color: Qt.lighter(root.cartridgeColor, 1.6)
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.darker(root.cartridgeColor, 1.2) }
            GradientStop { position: 0.08; color: Qt.darker(root.cartridgeColor, 1.0) }
            GradientStop { position: 1.0; color: Qt.darker(root.cartridgeColor, 1.9) }
        }
    }

    Rectangle {
        x: 5
        y: 5
        width: parent.width - 10
        height: 24
        radius: 4
        color: Qt.darker(root.cartridgeColor, 1.45)

        Text {
            anchors.centerIn: parent
            text: "GC"
            color: "#e8eefc"
            font.family: "Chakra Petch"
            font.pixelSize: 12
            font.bold: true
            font.letterSpacing: 2.4
        }
    }

    Rectangle {
        x: 5
        y: 32
        width: parent.width - 10
        height: parent.height - 40
        radius: 4
        color: "#090b0e"
        clip: true

        Image {
            anchors.fill: parent
            source: root.coverUrl
            fillMode: Image.PreserveAspectCrop
            verticalAlignment: Image.AlignBottom
            asynchronous: true
            cache: true
            smooth: true
        }

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 18
            color: "#0a0c10"
            opacity: 0.9
        }

        Text {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 7
            anchors.rightMargin: 7
            anchors.bottomMargin: 5
            text: root.gameMeta
            color: "#c3ccda"
            font.family: "Chakra Petch"
            font.pixelSize: 7
            elide: Text.ElideRight
        }
    }

    Rectangle {
        x: 0
        y: 10
        width: 5
        height: parent.height - 20
        color: Qt.darker(root.cartridgeColor, 1.7)
        opacity: 0.95
    }

    Rectangle {
        x: 6
        y: 6
        width: parent.width - 12
        height: 26
        radius: 4
        opacity: 0.35
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#ffffff" }
            GradientStop { position: 1.0; color: "#00ffffff" }
        }
    }
}
