import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    objectName: "yearReview"
    anchors.fill: parent
    visible: opacity > 0
    opacity: opened ? 1 : 0
    z: 32
    clip: true
    focus: opened

    property bool opened: false
    property var review: ({})
    property int year: new Date().getFullYear()
    property var slides: []
    property int currentIndex: 0
    property bool paused: false
    property real progress: 0
    readonly property int storyMs: 7200

    readonly property var currentSlide: (
        slides.length > 0
        && currentIndex >= 0
        && currentIndex < slides.length
    ) ? slides[currentIndex] : ({})
    readonly property color accent: currentSlide.accent || Library.accent

    signal closeRequested()

    Behavior on opacity { NumberAnimation { duration: 240; easing.type: Easing.OutCubic } }

    function open(data, selectedYear) {
        if (!data || data.hasData === false) {
            return;
        }
        review = data;
        year = selectedYear;
        slides = data.slides || [];
        if (slides.length === 0) {
            return;
        }
        currentIndex = 0;
        progress = 0;
        paused = false;
        opened = true;
        forceActiveFocus();
    }

    function close() {
        opened = false;
        paused = true;
        closeRequested();
    }

    function next() {
        if (!opened) {
            return;
        }
        if (currentIndex < slides.length - 1) {
            currentIndex += 1;
        } else {
            close();
        }
    }

    function previous() {
        if (currentIndex > 0) {
            currentIndex -= 1;
        } else {
            progress = 0;
        }
    }

    function togglePause() {
        paused = !paused;
    }

    function reloadSlide() {
        if (!opened) {
            return;
        }
        slideLoader.active = false;
        Qt.callLater(function() {
            if (root.opened) {
                slideLoader.active = true;
            }
        });
    }

    onCurrentIndexChanged: {
        progress = 0;
        reloadSlide();
    }

    onOpenedChanged: {
        if (opened) {
            progress = 0;
            paused = false;
            forceActiveFocus();
            reloadSlide();
        }
    }

    Keys.onLeftPressed: previous()
    Keys.onRightPressed: next()
    Keys.onSpacePressed: togglePause()
    Keys.onEscapePressed: close()

    // ---- background -----------------------------------------------------

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#05070b" }
            GradientStop { position: 0.55; color: "#090e17" }
            GradientStop { position: 1.0; color: "#04060a" }
        }
    }

    Rectangle {
        id: orbA
        width: 620
        height: 620
        radius: 310
        color: root.accent
        opacity: 0.16
        x: root.width * 0.55
        y: -220

        Behavior on color { ColorAnimation { duration: 700 } }

        SequentialAnimation on x {
            // Decorative: keep it asleep until the story is actually on screen.
            // A running animation inside a closed overlay still forces the
            // whole window to repaint at the monitor refresh rate.
            running: root.opened
            loops: Animation.Infinite
            NumberAnimation {
                from: root.width * 0.55
                to: root.width * 0.48
                duration: 7000
                easing.type: Easing.InOutSine
            }
            NumberAnimation {
                from: root.width * 0.48
                to: root.width * 0.55
                duration: 7000
                easing.type: Easing.InOutSine
            }
        }
    }

    Rectangle {
        id: orbB
        width: 520
        height: 520
        radius: 260
        color: root.accent
        opacity: 0.10
        x: -180
        y: root.height * 0.55

        Behavior on color { ColorAnimation { duration: 700 } }

        SequentialAnimation on y {
            // Same as orbA: only alive while the review is open.
            running: root.opened
            loops: Animation.Infinite
            NumberAnimation {
                from: root.height * 0.55
                to: root.height * 0.48
                duration: 9000
                easing.type: Easing.InOutSine
            }
            NumberAnimation {
                from: root.height * 0.48
                to: root.height * 0.55
                duration: 9000
                easing.type: Easing.InOutSine
            }
        }
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#00000055" }
            GradientStop { position: 0.35; color: "#00000000" }
            GradientStop { position: 1.0; color: "#000000aa" }
        }
    }

    // ---- current story slide -------------------------------------------

    Loader {
        id: slideLoader
        anchors.fill: parent
        anchors.topMargin: 76
        anchors.bottomMargin: 18
        asynchronous: false
        active: false
        sourceComponent: storyComponent

        onLoaded: {
            if (item) {
                item.slideData = root.currentSlide;
                item.review = root.review;
                item.slideIndex = root.currentIndex;
            }
        }
    }

    Component {
        id: storyComponent
        YearReviewSlide {}
    }

    // Tap left third to go back, rest to advance.
    MouseArea {
        anchors.fill: parent
        onClicked: (mouse) => {
            if (mouse.x < width * 0.30) {
                root.previous();
            } else {
                root.next();
            }
        }
    }

    // ---- progress, pause and close -------------------------------------

    Item {
        id: topBar
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: 20
        anchors.leftMargin: 24
        anchors.rightMargin: 24
        height: 56

        Row {
            id: segments
            anchors.left: parent.left
            anchors.right: buttons.left
            anchors.rightMargin: 16
            anchors.top: parent.top
            height: 4
            spacing: 4

            Repeater {
                model: root.slides.length

                Rectangle {
                    width: Math.max(
                        4,
                        (segments.width - (root.slides.length - 1) * 4)
                        / Math.max(1, root.slides.length)
                    )
                    height: 4
                    radius: 2
                    color: "#ffffff"
                    opacity: 0.20

                    Rectangle {
                        width: parent.width * (
                            index < root.currentIndex
                            ? 1
                            : (index === root.currentIndex ? root.progress : 0)
                        )
                        height: parent.height
                        radius: 2
                        color: "#ffffff"
                        opacity: 0.96
                    }
                }
            }
        }

        Row {
            id: buttons
            anchors.right: parent.right
            anchors.top: parent.top
            spacing: 8

            StoryButton {
                icon: root.paused ? "play" : "pause"
                onClicked: root.togglePause()
            }

            StoryButton {
                icon: "close"
                onClicked: root.close()
            }
        }

        RowLayout {
            anchors.left: parent.left
            anchors.right: buttons.left
            anchors.top: segments.bottom
            anchors.topMargin: 8
            spacing: 8

            Text {
                text: Tr.strings["YEAR IN REVIEW"]
                color: "#dfe6f0"
                opacity: 0.72
                font.family: "Chakra Petch"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 2.4
            }

            Item { Layout.fillWidth: true }

            Text {
                text: root.year + "  ·  "
                      + (root.currentIndex + 1) + "/" + root.slides.length
                color: "#8b95a5"
                font.family: "Chakra Petch"
                font.pixelSize: 10
                font.letterSpacing: 1.0
            }

            Text {
                visible: root.paused
                text: Tr.strings["Paused"]
                color: "#facc15"
                font.family: "Sora"
                font.pixelSize: 10
                font.bold: true
            }
        }
    }

    Timer {
        interval: 50
        repeat: true
        running: root.opened && !root.paused
        onTriggered: {
            root.progress += 50 / root.storyMs;
            if (root.progress >= 1) {
                root.next();
            }
        }
    }

    Connections {
        target: Gamepad
        enabled: root.opened
        function onNavigate(dx, dy) {
            if (dx < 0) {
                root.previous();
            } else if (dx > 0) {
                root.next();
            }
        }
        function onBack() { root.close() }
        function onAccept() { root.togglePause() }
        function onPageLeft() { root.previous() }
        function onPageRight() { root.next() }
    }

    component StoryButton: Rectangle {
        id: button
        property string icon: "close"
        width: 34
        height: 34
        radius: 17
        color: hoverArea.containsMouse
               ? Qt.rgba(1, 1, 1, 0.17)
               : Qt.rgba(1, 1, 1, 0.07)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.14)

        signal clicked()

        Canvas {
            width: 14
            height: 14
            anchors.centerIn: parent
            property string iconName: button.icon
            onIconNameChanged: requestPaint()
            Component.onCompleted: requestPaint()

            onPaint: {
                var ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = "#eef2f8";
                ctx.fillStyle = "#eef2f8";
                ctx.lineWidth = 1.6;
                ctx.lineCap = "round";
                if (iconName === "close") {
                    ctx.beginPath();
                    ctx.moveTo(2, 2);
                    ctx.lineTo(12, 12);
                    ctx.moveTo(12, 2);
                    ctx.lineTo(2, 12);
                    ctx.stroke();
                } else if (iconName === "pause") {
                    ctx.fillRect(3, 1, 3, 12);
                    ctx.fillRect(8, 1, 3, 12);
                } else {
                    ctx.beginPath();
                    ctx.moveTo(3, 1);
                    ctx.lineTo(13, 7);
                    ctx.lineTo(3, 13);
                    ctx.closePath();
                    ctx.fill();
                }
            }
        }

        MouseArea {
            id: hoverArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: button.clicked()
        }
    }
}
