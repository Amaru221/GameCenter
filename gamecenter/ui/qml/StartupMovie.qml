import QtQuick
import QtMultimedia

FocusScope {
    id: root
    objectName: "startupMovie"

    // Set by Main while Big Picture is waiting for the intro.
    property bool active: false
    property string movieSource: ""
    property bool started: false
    signal finished()

    z: 80
    visible: opacity > 0
    opacity: active ? 1 : 0
    focus: active

    Behavior on opacity { NumberAnimation { duration: 220 } }

    function finish() {
        // Main owns `active`; this only reports that the intro is over.
        if (active) {
            finished();
        }
    }

    onActiveChanged: {
        if (active) {
            if (!movieSource) {
                Qt.callLater(root.finish);
                return;
            }
            started = false;
            video.source = movieSource;
            video.play();
            if (!active) {
                return;
            }
            started = true;
            guard.restart();
            forceActiveFocus();
        } else {
            started = false;
            guard.stop();
            video.stop();
        }
    }

    Rectangle {
        anchors.fill: parent
        color: "#000000"
    }

    Video {
        id: video
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
        autoPlay: false
        loops: 1
        // Follow the interface-sound switch so a muted app stays silent.
        muted: !Sounds.enabled
        volume: 1.0

        onPlaybackStateChanged: {
            if (root.active && root.started
                    && playbackState === MediaPlayer.StoppedState) {
                root.finish();
            }
        }

        onErrorOccurred: root.finish()
    }

    // A broken codec must never trap the user in a black screen.
    Timer {
        id: guard
        interval: 20000
        running: false
        onTriggered: root.finish()
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.finish()
    }

    Keys.onPressed: (event) => {
        root.finish();
        event.accepted = true;
    }

    Text {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 24
        text: Tr.strings["Click or press any key to skip"]
        color: "#8b95a5"
        font.family: "Sora"
        font.pixelSize: 11
        opacity: 0.82
    }
}
