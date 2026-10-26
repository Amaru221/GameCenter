import QtQuick

// A compact, high-contrast close control for modal panels.
Item {
    id: root
    objectName: "closeButton"
    width: 36
    height: 36
    property color accent: Library.accent
    signal clicked()

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: pointer.containsMouse ? "#242b38" : "#11161f"
        border.width: 1
        border.color: pointer.containsMouse ? root.accent : "#2f3948"
        Behavior on color { ColorAnimation { duration: 140 } }
        Behavior on border.color { ColorAnimation { duration: 140 } }
    }

    Rectangle {
        anchors.fill: parent
        radius: width / 2
        color: root.accent
        opacity: pointer.containsMouse ? 0.08 : 0
        Behavior on opacity { NumberAnimation { duration: 160 } }
    }

    Item {
        anchors.centerIn: parent
        width: 14
        height: 14
        scale: pointer.containsMouse ? 1.1 : 1
        Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

        Rectangle {
            anchors.centerIn: parent
            width: 15
            height: 2
            radius: 1
            rotation: 45
            color: pointer.containsMouse ? root.accent : "#cfd6e2"
            Behavior on color { ColorAnimation { duration: 140 } }
        }

        Rectangle {
            anchors.centerIn: parent
            width: 15
            height: 2
            radius: 1
            rotation: -45
            color: pointer.containsMouse ? root.accent : "#cfd6e2"
            Behavior on color { ColorAnimation { duration: 140 } }
        }
    }

    MouseArea {
        id: pointer
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }
}
