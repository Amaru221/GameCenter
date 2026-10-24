import QtQuick

Rectangle {
    id: swatch
    property color colour: "#000000"
    property bool selected: false

    signal clicked()

    width: 24
    height: 24
    radius: 7
    color: colour
    border.width: selected ? 2 : 1
    border.color: selected ? "#ffffff" : "#2a3140"

    readonly property color checkColour:
        (colour.r * 0.299 + colour.g * 0.587 + colour.b * 0.114) > 0.6
        ? "#08131a" : "#ffffff"

    Text {
        anchors.centerIn: parent
        visible: swatch.selected
        text: "✓"
        color: swatch.checkColour
        font.pixelSize: 10
        font.bold: true
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: swatch.clicked()
    }
}
