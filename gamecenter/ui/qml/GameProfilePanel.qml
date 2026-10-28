import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    objectName: "gameProfilePanel"

    property var game: ({})
    property bool expanded: false
    property var candidateModel: []
    property string sourceId: ""
    property bool hideSource: true
    property string message: ""
    property int ratingDraft: -1
    property string loadedGameId: ""
    // Console-style editing: 0 = status, 1 = score.
    property int focusRow: 0
    readonly property int rowCount: 2

    signal profileEdited()
    signal closeRequested()

    readonly property var statusKeys: [
        "playing", "ongoing", "beaten", "completed", "played",
        "plan", "onhold", "notplayed", "abandoned"
    ]
    readonly property var selected: {
        for (var i = 0; i < root.candidateModel.length; ++i) {
            if (root.candidateModel[i].id === root.sourceId) {
                return root.candidateModel[i];
            }
        }
        return null;
    }

    visible: expanded
    implicitHeight: expanded ? content.implicitHeight + 36 : 0
    radius: 18
    color: "#0b0e14"
    border.width: 1
    border.color: "#232a36"

    function statusColor(key) {
        if (key === "playing") return Library.accent;
        if (key === "ongoing") return "#38bdf8";
        if (key === "beaten") return "#a78bfa";
        if (key === "completed") return "#34d399";
        if (key === "played") return "#93c5fd";
        if (key === "plan") return "#facc15";
        if (key === "onhold") return "#fb923c";
        if (key === "notplayed") return "#64748b";
        if (key === "abandoned") return "#f87171";
        return "#64748b";
    }

    function statusLabel(key) {
        if (key === "playing") return Tr.strings["Playing"];
        if (key === "ongoing") return Tr.strings["On Going"];
        if (key === "beaten") return Tr.strings["Beaten"];
        if (key === "completed") return Tr.strings["Completed"];
        if (key === "played") return Tr.strings["Played"];
        if (key === "plan") return Tr.strings["Plan to Play"];
        if (key === "onhold") return Tr.strings["On Hold"];
        if (key === "notplayed") return Tr.strings["Not Played"];
        if (key === "abandoned") return Tr.strings["Abandoned"];
        return Tr.strings["Not set"];
    }

    function reload() {
        if (!game.id) {
            candidateModel = [];
            return;
        }
        loadedGameId = game.id;
        candidateModel = Library.mergeCandidates(game.id);
        // The source is an explicit choice: never pre-select an entry.
        sourceId = "";
        if (game.rating !== undefined && game.rating !== null && game.rating >= 0) {
            ratingDraft = game.rating;
        } else {
            ratingDraft = -1;
        }
    }

    function commitRating() {
        ratingTimer.stop();
        if (!game.id || ratingDraft < 0 || game.rating === ratingDraft) {
            return;
        }
        Library.setGameRating(game.id, ratingDraft);
        root.profileEdited();
    }

    function moveFocus(delta) {
        focusRow = (focusRow + delta + rowCount) % rowCount;
    }

    function adjust(direction) {
        if (focusRow === 0) {
            cycleStatus(direction);
        } else {
            nudgeRating(direction * 5);
        }
    }

    function cycleStatus(direction) {
        if (!game.id) {
            return;
        }
        var order = [""].concat(root.statusKeys);
        var current = order.indexOf(game.status || "");
        if (current < 0) {
            current = 0;
        }
        var next = order[(current + direction + order.length) % order.length];
        Library.setGameStatus(game.id, next);
        root.profileEdited();
    }

    function nudgeRating(delta) {
        if (!game.id) {
            return;
        }
        var base = ratingDraft >= 0 ? ratingDraft : 50;
        ratingDraft = Math.max(0, Math.min(100, base + delta));
        root.commitRating();
    }

    Connections {
        target: Gamepad
        enabled: root.expanded

        function onNavigate(dx, dy) {
            if (!root.expanded) {
                return;
            }
            if (dy !== 0) {
                root.moveFocus(dy > 0 ? 1 : -1);
            } else if (dx !== 0) {
                root.adjust(dx);
            }
        }
    }

    function mergeNow() {
        if (!game.id || !sourceId) {
            return;
        }
        var result = Library.mergeGameData(sourceId, game.id, hideSource);
        if (result && result.ok) {
            message = result.message || "";
            root.profileEdited();
            reload();
        } else {
            message = result && result.message
                      ? result.message
                      : Tr.strings["Couldn't unify the data."];
        }
    }

    onExpandedChanged: {
        if (expanded) {
            focusRow = 0;
            message = "";
            reload();
        }
    }

    onGameChanged: {
        if (expanded && game.id && game.id !== loadedGameId) {
            message = "";
            ratingDraft = -1;
            reload();
        }
    }

    Timer {
        id: ratingTimer
        interval: 420
        onTriggered: root.commitRating()
    }

    ColumnLayout {
        id: content
        anchors.fill: parent
        anchors.margins: 18
        spacing: 14

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: Tr.strings["GAME PROFILE"]
                color: "#dfe6f0"
                font.family: "Chakra Petch"
                font.pixelSize: 11
                font.bold: true
                font.letterSpacing: 2.2
            }

            Item { Layout.fillWidth: true }

            CloseButton {
                width: 28
                height: 28
                onClicked: root.closeRequested()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            visible: (root.game.mergedIntoTitle || "") !== ""
            height: 32
            radius: 9
            color: "#101a24"
            border.width: 1
            border.color: "#28405a"

            Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 12
                anchors.right: parent.right
                anchors.rightMargin: 12
                text: Tr.strings["Merged into {title}"].replace(
                    "{title}", root.game.mergedIntoTitle || ""
                )
                color: "#8ec5e8"
                font.family: "Sora"
                font.pixelSize: 10
                elide: Text.ElideRight
            }
        }

        Text {
            text: Tr.strings["STATUS"]
            color: root.focusRow === 0 ? Library.accent : "#7f8a9b"
            font.family: "Chakra Petch"
            font.pixelSize: 9
            font.bold: true
            font.letterSpacing: 1.8
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: root.statusKeys

                delegate: Rectangle {
                    id: statusPill
                    readonly property bool selected: root.game.status === modelData
                    readonly property color tint: root.statusColor(modelData)

                    width: statusPillText.implicitWidth + (selected ? 34 : 30)
                    height: 30
                    radius: 15
                    color: selected ? tint : "#121722"
                    border.width: 1
                    border.color: selected ? tint : "#243044"

                    Behavior on color { ColorAnimation { duration: 150 } }

                    Row {
                        anchors.centerIn: parent
                        spacing: 6

                        Rectangle {
                            visible: !statusPill.selected
                            width: 6
                            height: 6
                            radius: 3
                            color: statusPill.tint
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            id: statusPillText
                            anchors.verticalCenter: parent.verticalCenter
                            text: root.statusLabel(modelData)
                            color: statusPill.selected ? "#071018" : "#aeb8c7"
                            font.family: "Sora"
                            font.pixelSize: 10
                            font.bold: statusPill.selected
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            var next = root.game.status === modelData
                                       ? ""
                                       : modelData;
                            Library.setGameStatus(root.game.id, next);
                            root.profileEdited();
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#1c2330"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Text {
                text: Tr.strings["SCORE"]
                color: root.focusRow === 1 ? Library.accent : "#7f8a9b"
                font.family: "Chakra Petch"
                font.pixelSize: 9
                font.bold: true
                font.letterSpacing: 1.8
            }

            Item { Layout.fillWidth: true }

            Text {
                text: root.ratingDraft >= 0 ? root.ratingDraft : "—"
                color: root.ratingDraft >= 0 ? "#f2f5fa" : "#5f6a7b"
                font.family: "Chakra Petch"
                font.pixelSize: 22
                font.bold: true
            }

            Text {
                text: "/ 100"
                color: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 10
                Layout.alignment: Qt.AlignBaseline
            }
        }

        Slider {
            id: ratingSlider
            Layout.fillWidth: true
            from: 0
            to: 100
            stepSize: 1
            value: root.ratingDraft >= 0 ? root.ratingDraft : 50

            onMoved: {
                root.ratingDraft = Math.round(value);
                ratingTimer.restart();
            }
            onPressedChanged: {
                if (!pressed) {
                    root.commitRating();
                }
            }

            background: Rectangle {
                x: ratingSlider.leftPadding
                y: ratingSlider.topPadding
                       + (ratingSlider.availableHeight - height) / 2
                width: ratingSlider.availableWidth
                height: 6
                radius: 3
                color: "#1b2331"

                Rectangle {
                    width: parent.width * ratingSlider.visualPosition
                    height: parent.height
                    radius: 3
                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Library.accent }
                        GradientStop { position: 1.0; color: "#a78bfa" }
                    }
                }
            }

            handle: Rectangle {
                x: ratingSlider.leftPadding
                   + ratingSlider.visualPosition
                     * (ratingSlider.availableWidth - width)
                y: ratingSlider.topPadding
                   + (ratingSlider.availableHeight - height) / 2
                width: 16
                height: 16
                radius: 8
                color: "#f2f5fa"
                border.width: 3
                border.color: Library.accent
            }
        }

        Text {
            Layout.fillWidth: true
            text: "↑ ↓  " + Tr.strings["Select"] + "   ·   ← →  "
                  + Tr.strings["Change"]
            color: "#5f6a7b"
            font.family: "Sora"
            font.pixelSize: 9
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#1c2330"
        }

        Text {
            text: Tr.strings["TRACEABILITY"]
            color: "#7f8a9b"
            font.family: "Chakra Petch"
            font.pixelSize: 9
            font.bold: true
            font.letterSpacing: 1.8
        }

        Text {
            Layout.fillWidth: true
            text: Tr.strings["Import another entry's playtime, sessions and cover into this game."]
            color: "#8b95a5"
            font.family: "Sora"
            font.pixelSize: 10
            wrapMode: Text.WordWrap
            lineHeight: 1.25
        }

        Text {
            text: Tr.strings["Source game"]
            color: "#b9c3d2"
            font.family: "Sora"
            font.pixelSize: 11
        }

        PillCombo {
            id: sourceCombo
            objectName: "profileSourceCombo"
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            entries: {
                var out = [];
                for (var i = 0; i < root.candidateModel.length; ++i) {
                    var item = root.candidateModel[i];
                    var prefix = item.sameTitle ? "★ " : "";
                    var extra = item.playtimeText ? " · " + item.playtimeText : "";
                    var removed = item.orphan
                                  ? " · " + Tr.strings["Removed"]
                                  : "";
                    out.push({
                        text: prefix + item.title + " · " + item.source
                              + extra + removed,
                        value: item.id
                    });
                }
                return out;
            }
            value: root.sourceId
            allowEmpty: true
            emptyText: Tr.strings["Choose a game"]
            onSelected: (chosen) => root.sourceId = chosen
        }

        Text {
            Layout.fillWidth: true
            visible: root.candidateModel.length === 0
            text: Tr.strings["No games to import."]
            color: "#6f7887"
            font.family: "Sora"
            font.pixelSize: 10
        }

        Rectangle {
            Layout.fillWidth: true
            visible: root.selected !== null
            height: 62
            radius: 12
            color: "#10151e"
            border.width: 1
            border.color: "#202a39"

            RowLayout {
                anchors.fill: parent
                anchors.margins: 9
                spacing: 10

                Rectangle {
                    width: 36
                    height: 48
                    radius: 7
                    color: "#0a0e15"
                    clip: true

                    Image {
                        anchors.fill: parent
                        source: root.selected ? (root.selected.cover || "") : ""
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        cache: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        Layout.fillWidth: true
                        text: root.selected ? root.selected.title : ""
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 11
                        font.bold: true
                        elide: Text.ElideRight
                    }

                    Text {
                        Layout.fillWidth: true
                        text: root.selected
                              ? root.selected.source
                                + (root.selected.playtimeText
                                   ? " · " + root.selected.playtimeText : "")
                                + (root.selected.orphan
                                   ? " · " + Tr.strings["Removed"] : "")
                              : ""
                        color: "#7f8a9b"
                        font.family: "Sora"
                        font.pixelSize: 9
                        elide: Text.ElideRight
                    }
                }

                Text {
                    text: root.selected
                          ? (root.selected.sessions === 1
                             ? Tr.strings["1 session"]
                             : Tr.strings["%1 sessions"].arg(
                                 root.selected.sessions || 0))
                          : ""
                    color: "#6f7887"
                    font.family: "Sora"
                    font.pixelSize: 9
                    Layout.alignment: Qt.AlignVCenter
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 40
            radius: 10
            color: "#0e131b"
            border.width: 1
            border.color: root.hideSource ? "#2a4058" : "#232a36"

            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 10
                spacing: 9

                Rectangle {
                    width: 18
                    height: 18
                    radius: 5
                    color: root.hideSource ? Library.accent : "#0a0e15"
                    border.width: 1
                    border.color: root.hideSource ? Library.accent : "#354155"

                    Text {
                        anchors.centerIn: parent
                        visible: root.hideSource
                        text: "✓"
                        color: Library.accentText
                        font.pixelSize: 11
                        font.bold: true
                    }
                }

                ColumnLayout {
                    spacing: 0

                    Text {
                        text: Tr.strings["Hide the source after unifying"]
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 10
                    }

                    Text {
                        text: Tr.strings["Avoids duplicate stats. You can restore it from Settings."]
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 8
                    }
                }
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.hideSource = !root.hideSource
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 42
            radius: 10
            opacity: root.sourceId ? 1 : 0.45
            color: root.sourceId ? Library.accent : "#1a2130"

            Text {
                anchors.centerIn: parent
                text: Tr.strings["Unify data"]
                color: root.sourceId ? Library.accentText : "#6f7887"
                font.family: "Sora"
                font.pixelSize: 12
                font.bold: true
            }

            MouseArea {
                anchors.fill: parent
                enabled: root.sourceId !== ""
                cursorShape: Qt.PointingHandCursor
                onClicked: root.mergeNow()
            }
        }

        Text {
            Layout.fillWidth: true
            visible: root.message !== ""
            text: root.message
            color: Library.accent
            font.family: "Sora"
            font.pixelSize: 10
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.topMargin: 2
            text: Tr.strings["IMPORTED GAMES"]
            color: "#7f8a9b"
            font.family: "Chakra Petch"
            font.pixelSize: 9
            font.bold: true
            font.letterSpacing: 1.8
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Repeater {
                model: root.game.mergedSources || []

                delegate: Rectangle {
                    Layout.fillWidth: true
                    height: 58
                    radius: 10
                    color: "#0e131b"
                    border.width: 1
                    border.color: "#202a39"

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 8
                        spacing: 9

                        Rectangle {
                            width: 32
                            height: 42
                            radius: 6
                            color: "#0a0e15"
                            clip: true

                            Image {
                                anchors.fill: parent
                                source: modelData.cover || ""
                                fillMode: Image.PreserveAspectFit
                                asynchronous: true
                                cache: true
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 1

                            Text {
                                Layout.fillWidth: true
                                text: modelData.title || ""
                                color: "#cfd6e2"
                                font.family: "Sora"
                                font.pixelSize: 10
                                font.bold: true
                                elide: Text.ElideRight
                            }

                            Text {
                                Layout.fillWidth: true
                                text: (modelData.source || "")
                                      + (modelData.orphan
                                         ? " · " + Tr.strings["Removed"] : "")
                                      + (modelData.at
                                         ? " · " + Qt.formatDateTime(
                                             new Date(modelData.at * 1000),
                                             "dd/MM/yyyy")
                                         : "")
                                color: "#6f7887"
                                font.family: "Sora"
                                font.pixelSize: 8
                                elide: Text.ElideRight
                            }
                        }

                        ColumnLayout {
                            spacing: 1

                            Text {
                                text: modelData.secondsText || ""
                                color: "#aeb8c7"
                                font.family: "Chakra Petch"
                                font.pixelSize: 9
                                horizontalAlignment: Text.AlignRight
                            }

                            Text {
                                text: modelData.sessions === 1
                                      ? Tr.strings["1 session"]
                                      : Tr.strings["%1 sessions"].arg(
                                          modelData.sessions || 0)
                                color: "#6f7887"
                                font.family: "Sora"
                                font.pixelSize: 8
                                horizontalAlignment: Text.AlignRight
                            }
                        }
                    }
                }
            }
        }

        Text {
            Layout.fillWidth: true
            visible: (root.game.mergedSources || []).length === 0
            text: Tr.strings["No entries imported yet."]
            color: "#5f6a7b"
            font.family: "Sora"
            font.pixelSize: 9
        }
    }
}
