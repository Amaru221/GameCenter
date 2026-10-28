import QtQuick

Item {
    id: root
    width: 168
    height: 210
    y: 14

    property string gameTitle: ""
    property string gameSource: ""
    property string gameMeta: ""
    property string coverUrl: ""
    property bool gameInstalled: true
    property color cartridgeColor: Library.cartridgeColor
    property bool hovered: false
    property real tiltX: 0
    property real tiltY: 0

    // The store this game belongs to (or LOCAL), shown on the shell.
    readonly property string sourceTag: {
        var value = (root.gameSource || "").toUpperCase();
        if (value.indexOf("EPIC") === 0) return "EPIC";
        if (value.indexOf("BATTLE") === 0) return "BATTLE.NET";
        if (value.indexOf("LOCAL") === 0) return "LOCAL";
        return value.length > 0 ? value : "GAME";
    }

    Rectangle {
        anchors.fill: parent
        radius: 12
        border.width: 1
        border.color: Qt.lighter(root.cartridgeColor, 1.35)
        gradient: Gradient {
            GradientStop { position: 0.0; color: root.hovered ? Qt.lighter(root.cartridgeColor, 1.15) : root.cartridgeColor }
            GradientStop { position: 1.0; color: Qt.darker(root.cartridgeColor, 1.55) }
        }
    }

    Rectangle {
        x: 10
        y: 1
        width: parent.width - 20
        height: 1.5
        radius: 1
        color: "#ffffff"
        opacity: 0.14
    }

    Rectangle {
        width: 54
        height: 8
        radius: 4
        color: "#0b0d10"
        anchors.top: parent.top
        anchors.topMargin: 7
        anchors.horizontalCenter: parent.horizontalCenter
    }

    Rectangle {
        id: label
        x: 14
        y: 24
        width: parent.width - 28
        height: parent.height - 46
        radius: 6
        color: "#0b0d10"
        border.width: 1
        border.color: "#15181d"
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
            width: parent.width
            height: 20
            color: "#0a0c10"
            opacity: 0.94
        }

        Text {
            x: 8
            width: parent.width - 16
            y: 5
            text: root.sourceTag
            color: "#eef2f7"
            font.family: "Chakra Petch"
            font.pixelSize: 9
            font.bold: true
            font.letterSpacing: 1.6
            elide: Text.ElideRight
        }

        Rectangle {
            anchors.bottom: parent.bottom
            width: parent.width
            height: 18
            color: "#0a0c10"
            opacity: 0.94
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
        width: 30
        height: 5
        radius: 2.5
        color: "#171a1f"
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 9
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
