import QtQuick
import QtQuick.Controls

ComboBox {
    id: control

    property var entries: []
    property string value: ""

    implicitHeight: 34
    implicitWidth: 160
    font.family: "Sora"
    font.pixelSize: 12

    model: entries
    textRole: "text"
    valueRole: "value"

    signal selected(string value)

    function syncIndex() {
        var i = control.indexOfValue(control.value);
        if (i >= 0) {
            control.currentIndex = i;
        }
    }

    onActivated: {
        control.value = control.currentValue;
        control.selected(control.currentValue);
    }
    onValueChanged: syncIndex()
    onEntriesChanged: syncIndex()
    Component.onCompleted: syncIndex()

    background: Rectangle {
        radius: 17
        color: "#0d0f14"
        border.width: 1
        border.color: control.activeFocus ? "#3a4250" : "#232833"
    }

    contentItem: Text {
        leftPadding: 14
        rightPadding: 30
        text: control.displayText
        color: "#cfd6e2"
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    indicator: Canvas {
        x: control.width - 22
        y: (control.height - 8) / 2
        width: 10
        height: 8

        onPaint: {
            var ctx = getContext("2d");
            ctx.reset();
            ctx.strokeStyle = "#8b95a5";
            ctx.lineWidth = 1.5;
            ctx.lineCap = "round";
            ctx.beginPath();
            ctx.moveTo(1, 2);
            ctx.lineTo(5, 6);
            ctx.lineTo(9, 2);
            ctx.stroke();
        }
    }

    delegate: ItemDelegate {
        id: entry
        width: control.width - 8
        height: 30
        highlighted: control.highlightedIndex === index

        contentItem: Text {
            text: modelData.text !== undefined ? modelData.text : modelData
            color: "#cfd6e2"
            font.family: "Sora"
            font.pixelSize: 12
            verticalAlignment: Text.AlignVCenter
            leftPadding: 10
            elide: Text.ElideRight
        }

        background: Rectangle {
            radius: 7
            color: entry.highlighted ? "#232936" : "transparent"
        }
    }

    popup: Popup {
        y: control.height + 5
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 10, 260)
        padding: 5

        background: Rectangle {
            color: "#12151b"
            radius: 11
            border.width: 1
            border.color: "#2a3140"
        }

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            boundsBehavior: Flickable.StopAtBounds
        }
    }
}
