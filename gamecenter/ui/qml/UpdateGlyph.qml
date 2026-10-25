import QtQuick

Item {
    id: root
    property color color: "#ffffff"

    onColorChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onPaint: {
            var ctx = getContext("2d");
            ctx.reset();
            ctx.strokeStyle = root.color;
            ctx.lineWidth = 1.7;
            ctx.lineCap = "round";
            ctx.lineJoin = "round";

            // Shaft
            ctx.beginPath();
            ctx.moveTo(10, 3);
            ctx.lineTo(10, 12.4);
            ctx.stroke();

            // Arrow head
            ctx.beginPath();
            ctx.moveTo(5.9, 8.3);
            ctx.lineTo(10, 12.5);
            ctx.lineTo(14.1, 8.3);
            ctx.stroke();

            // Tray
            ctx.beginPath();
            ctx.moveTo(3.5, 14.8);
            ctx.lineTo(3.5, 16.6);
            ctx.lineTo(16.5, 16.6);
            ctx.lineTo(16.5, 14.8);
            ctx.stroke();
        }
    }
}
