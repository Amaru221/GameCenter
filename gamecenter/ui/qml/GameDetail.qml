import QtQuick
import QtQuick.Controls
import QtQuick.Effects
import QtQuick.Layouts

Item {
    id: root
    objectName: "gameDetail"

    property var game: ({})
    property bool opened: false
    property bool descriptionExpanded: false
    property bool showArt: true
    property bool profileOpen: false
    // Item behind the overlay that gets blurred. When null (Big Picture) the
    // artwork background is used instead.
    property var backdropItem: null

    signal profileChanged()
    signal closeRequested()
    signal playRequested()
    signal folderRequested()
    signal copyRequested()
    signal favoriteRequested()
    signal artRequested()

    // The cartridge stays pinned to the top-left corner of the overlay.
    readonly property real cartridgeMarginX: 24
    readonly property real cartridgeMarginY: 72

    readonly property var history: root.game.history || []
    readonly property var screenshots: root.game.screenshots || []
    property bool viewerOpen: false
    property var viewerShots: []
    property int viewerIndex: 0

    readonly property var viewerShot: (
        viewerOpen
        && viewerShots.length > 0
        && viewerIndex >= 0
        && viewerIndex < viewerShots.length
    ) ? viewerShots[viewerIndex] : ({})
    readonly property bool viewerHasPrev: viewerIndex > 0
    readonly property bool viewerHasNext: viewerIndex < viewerShots.length - 1
    readonly property bool compact: root.width < 940
    readonly property bool is3d: Library.cartridgeStyle === "ds"
    // The 3D viewport is deliberately larger than the card: the model is scaled
    // down inside it so every corner stays visible while rotating.
    readonly property real cartridgeWidth: root.is3d
                                           ? Math.min(400, Math.max(300, root.width * 0.34))
                                           : 260
    readonly property real cartridgeHeight: root.is3d
                                            ? root.cartridgeWidth * 1.2
                                            : 350
    readonly property real cartridgeGutter: root.compact
                                             ? 0
                                             : root.cartridgeWidth + 52

    function cartridgeCenter() {
        if (cartridgeHost.visible && cartridgeHost.height > 0) {
            var point = cartridgeHost.mapToItem(
                root, cartridgeHost.width / 2, cartridgeHost.height / 2
            );
            return Qt.point(point.x, point.y);
        }
        return Qt.point(root.width / 2, root.height / 2);
    }

    function sessionDate(timestamp) {
        if (!timestamp) {
            return "";
        }
        return Qt.formatDateTime(new Date(timestamp * 1000), "dd/MM/yyyy · HH:mm");
    }

    function historyMax() {
        var peak = 1;
        for (var i = 0; i < root.history.length; i++) {
            peak = Math.max(peak, root.history[i].seconds || 0);
        }
        return peak;
    }

    function openViewer(shots, index) {
        if (!shots || shots.length === 0) {
            return;
        }
        viewerShots = shots;
        viewerIndex = Math.max(0, Math.min(index, shots.length - 1));
        viewerOpen = true;
    }

    function closeViewer() {
        viewerOpen = false;
    }

    function nextViewer() {
        if (viewerIndex < viewerShots.length - 1) {
            viewerIndex += 1;
        }
    }

    function previousViewer() {
        if (viewerIndex > 0) {
            viewerIndex -= 1;
        }
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
        return "#3a465c";
    }

    function scrollBy(delta) {
        var maximum = Math.max(0, scroller.contentHeight - scroller.height);
        scroller.contentY = Math.max(
            0, Math.min(maximum, scroller.contentY + delta)
        );
    }

    readonly property var infoChips: {
        var out = [];
        if (root.game.sizeText) {
            out.push(root.game.sizeText);
        }
        out.push(root.game.installed !== false
                 ? Tr.strings["Installed"]
                 : Tr.strings["Not installed"]);
        if (root.game.playtimeText) {
            out.push(root.game.playtimeText);
        }
        if (root.game.lastPlayed) {
            out.push(root.game.lastPlayed);
        }
        if (root.game.genres) {
            out.push(root.game.genres);
        }
        if (root.game.developers) {
            out.push(root.game.developers);
        }
        if (root.game.mergedIntoTitle) {
            out.push(Tr.strings["Merged into {title}"].replace(
                "{title}", root.game.mergedIntoTitle
            ));
        }
        return out;
    }

    visible: opacity > 0
    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 180 } }

    onOpenedChanged: {
        if (opened) {
            descriptionExpanded = false;
            profileOpen = false;
            viewerOpen = false;
            scroller.contentY = 0;
            Qt.callLater(function() {
                scroller.contentY = 0;
                blurSource.scheduleUpdate();
            });
        } else {
            viewerOpen = false;
        }
    }

    onWidthChanged: {
        if (blurSource) {
            blurSource.scheduleUpdate();
        }
    }

    onHeightChanged: {
        if (blurSource) {
            blurSource.scheduleUpdate();
        }
    }

    // --- Full-screen frosted backdrop -------------------------------------
    Image {
        anchors.fill: parent
        visible: root.backdropItem === null || root.backdropItem === undefined
        source: "image://bg/1"
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }

    ShaderEffectSource {
        id: blurSource
        anchors.fill: parent
        sourceItem: root.backdropItem
        live: false
        // Keep the real scene visible while the overlay fades in/out; hiding it
        // from the first frame would flash the window background.
        hideSource: root.opened
                    && root.opacity > 0.9
                    && sourceItem !== null
                    && sourceItem !== undefined
        recursive: false
    }

    MultiEffect {
        anchors.fill: parent
        visible: root.backdropItem !== null && root.backdropItem !== undefined
        source: blurSource
        blurEnabled: true
        blur: 0.9
        blurMax: 48
        saturation: -0.18
    }

    Rectangle {
        anchors.fill: parent
        color: "#05070b"
        opacity: 0.66
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#00000000" }
            GradientStop { position: 0.62; color: "#00000000" }
            GradientStop { position: 1.0; color: "#33000000" }
        }
    }

    MouseArea {
        anchors.fill: parent
        onClicked: root.closeRequested()
    }

    // --- Scrollable information -------------------------------------------
    Flickable {
        id: scroller
        objectName: "detailScroller"
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: root.compact ? 64 : 52
        anchors.bottomMargin: root.compact ? 22 : 36
        anchors.leftMargin: root.compact ? 22 : (root.cartridgeGutter + 26)
        anchors.rightMargin: root.compact ? 22 : 58
        contentWidth: width - 14
        contentHeight: content.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        ScrollBar.vertical: ScrollBar {
            id: scrollBar
            policy: ScrollBar.AsNeeded
            width: 8
            background: Item {}
            contentItem: Rectangle {
                implicitWidth: 6
                radius: 3
                color: "#3a465c"
                opacity: scrollBar.pressed ? 1 : 0.55
            }
        }

        ColumnLayout {
            id: content
            width: scroller.width - 14
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 5
                    height: 5
                    radius: 2.5
                    color: Library.accent
                }

                Text {
                    text: (root.game.source || "").toUpperCase()
                    color: "#a3adbd"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                Rectangle {
                    visible: (root.game.releaseDate || "") !== ""
                    width: releaseLabel.implicitWidth + 16
                    height: 20
                    radius: 10
                    color: "#1a2130"
                    border.width: 1
                    border.color: "#2b3445"

                    Text {
                        id: releaseLabel
                        anchors.centerIn: parent
                        text: root.game.releaseDate || ""
                        color: "#a3adbd"
                        font.family: "Sora"
                        font.pixelSize: 10
                    }
                }

                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                Rectangle {
                    id: compactCover
                    visible: root.compact
                    width: 84
                    height: 112
                    radius: 10
                    color: "#0d0f14"
                    border.width: 1
                    border.color: "#2a3140"
                    clip: true

                    Image {
                        anchors.fill: parent
                        source: root.game.cover || ""
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                        cache: true
                        smooth: true
                    }
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6

                    Text {
                        Layout.fillWidth: true
                        text: root.game.title || ""
                        color: "#f5f8fd"
                        font.family: "Sora"
                        font.pixelSize: root.compact ? 24 : 32
                        font.bold: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 2
                        elide: Text.ElideRight
                    }
                }

                FavoriteButton {
                    Layout.alignment: Qt.AlignTop
                    favorite: !!root.game.favorite
                    onToggled: root.favoriteRequested()
                }
            }

            Rectangle {
                id: profileStrip
                Layout.fillWidth: true
                height: 74
                radius: 16
                color: "#0e131c"
                border.width: 1
                border.color: root.profileOpen ? Library.accent : "#232a36"

                readonly property bool hasRating: root.game.hasRating === true
                readonly property int score: hasRating
                                               ? Math.max(0, Math.min(100, root.game.rating))
                                               : 0
                readonly property string statusKey: root.game.status || ""

                Rectangle {
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 150
                    radius: parent.radius
                    color: Library.accent
                    opacity: 0.05
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 16

                    ColumnLayout {
                        spacing: 3

                        Text {
                            text: Tr.strings["STATUS"]
                            color: "#6f7887"
                            font.family: "Chakra Petch"
                            font.pixelSize: 8
                            font.bold: true
                            font.letterSpacing: 1.6
                        }

                        RowLayout {
                            spacing: 6

                            Rectangle {
                                width: 6
                                height: 6
                                radius: 3
                                color: root.statusColor(profileStrip.statusKey)
                            }

                            Text {
                                text: root.statusLabel(profileStrip.statusKey)
                                color: profileStrip.statusKey !== ""
                                       ? "#dfe6f0"
                                       : "#7f8a9b"
                                font.family: "Sora"
                                font.pixelSize: 11
                                font.bold: profileStrip.statusKey !== ""
                            }
                        }
                    }

                    Rectangle {
                        width: 1
                        height: 38
                        color: "#232a36"
                    }

                    ColumnLayout {
                        spacing: 3

                        Text {
                            text: Tr.strings["SCORE"]
                            color: "#6f7887"
                            font.family: "Chakra Petch"
                            font.pixelSize: 8
                            font.bold: true
                            font.letterSpacing: 1.6
                        }

                        RowLayout {
                            spacing: 5

                            Text {
                                text: profileStrip.hasRating
                                      ? profileStrip.score
                                      : "—"
                                color: profileStrip.hasRating
                                       ? "#f2f5fa"
                                       : "#5f6a7b"
                                font.family: "Chakra Petch"
                                font.pixelSize: 20
                                font.bold: true
                            }

                            Text {
                                text: "/ 100"
                                color: "#6f7887"
                                font.family: "Sora"
                                font.pixelSize: 9
                                Layout.alignment: Qt.AlignBaseline
                            }

                            Rectangle {
                                width: 76
                                height: 5
                                radius: 2.5
                                color: "#1b2331"

                                Rectangle {
                                    width: parent.width
                                           * (profileStrip.score / 100)
                                    height: parent.height
                                    radius: parent.radius
                                    gradient: Gradient {
                                        GradientStop { position: 0.0; color: Library.accent }
                                        GradientStop { position: 1.0; color: "#a78bfa" }
                                    }
                                }
                            }
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Rectangle {
                        width: Math.max(104, editProfileLabel.implicitWidth + 24)
                        height: 30
                        radius: 15
                        color: editProfileArea.containsMouse
                               ? "#1d2635"
                               : "#11161f"
                        border.width: 1
                        border.color: root.profileOpen
                                      ? Library.accent
                                      : "#2a3444"

                        Text {
                            id: editProfileLabel
                            anchors.centerIn: parent
                            text: root.profileOpen
                                  ? Tr.strings["Close profile"]
                                  : Tr.strings["Edit profile"]
                            color: root.profileOpen
                                   ? Library.accent
                                   : "#cfd6e2"
                            font.family: "Sora"
                            font.pixelSize: 10
                        }

                        MouseArea {
                            id: editProfileArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.profileOpen = !root.profileOpen
                        }
                    }
                }
            }

            Text {
                text: Tr.strings["ABOUT"]
                color: "#a3adbd"
                font.family: "Chakra Petch"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 2.2
            }

            Text {
                Layout.fillWidth: true
                text: {
                    var description = root.game.description || "";
                    if (description) {
                        return description;
                    }
                    return root.game.detailsLoaded
                           ? Tr.strings["No description available."]
                           : Tr.strings["Loading description..."];
                }
                color: (root.game.description || "") !== ""
                       ? "#c8d1df"
                       : "#7f8a9b"
                font.family: "Sora"
                font.pixelSize: root.compact ? 12 : 13
                wrapMode: Text.WordWrap
                lineHeight: 1.3
                maximumLineCount: root.descriptionExpanded
                                  ? 1000
                                  : (root.compact ? 4 : 6)
                elide: Text.ElideRight
            }

            Text {
                visible: (root.game.description || "").length > 240
                text: root.descriptionExpanded
                      ? Tr.strings["Show less"]
                      : Tr.strings["Read more"]
                color: Library.accent
                font.family: "Sora"
                font.pixelSize: 11

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.descriptionExpanded = !root.descriptionExpanded
                }
            }

            Flow {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: root.infoChips

                    Rectangle {
                        width: chipLabel.implicitWidth + 22
                        height: 26
                        radius: 13
                        color: "#141a25"
                        border.width: 1
                        border.color: "#2a3344"

                        Text {
                            id: chipLabel
                            anchors.centerIn: parent
                            text: modelData
                            color: "#b6c0cf"
                            font.family: "Sora"
                            font.pixelSize: 10
                        }
                    }
                }
            }

            Flow {
                Layout.fillWidth: true
                spacing: 10

                Rectangle {
                    width: 150
                    height: 42
                    radius: 11
                    color: playArea.pressed
                           ? Qt.darker(Library.accent, 1.2)
                           : Library.accent

                    Row {
                        anchors.centerIn: parent
                        spacing: 9

                        Canvas {
                            width: 12
                            height: 14
                            anchors.verticalCenter: parent.verticalCenter
                            onPaint: {
                                var ctx = getContext("2d");
                                ctx.reset();
                                ctx.fillStyle = Library.accentText;
                                ctx.beginPath();
                                ctx.moveTo(0, 0);
                                ctx.lineTo(12, 7);
                                ctx.lineTo(0, 14);
                                ctx.closePath();
                                ctx.fill();
                            }
                        }

                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            text: Tr.strings["Play"]
                            color: Library.accentText
                            font.family: "Sora"
                            font.pixelSize: 13
                            font.bold: true
                        }
                    }

                    MouseArea {
                        id: playArea
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.playRequested()
                    }
                }

                Rectangle {
                    width: 132
                    height: 42
                    radius: 10
                    color: folderArea.containsMouse ? "#202633" : "#151a23"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Open folder"]
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    MouseArea {
                        id: folderArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.folderRequested()
                    }
                }

                Rectangle {
                    width: 132
                    height: 42
                    radius: 10
                    color: copyArea.containsMouse ? "#202633" : "#151a23"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Copy App ID"]
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    MouseArea {
                        id: copyArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.copyRequested()
                    }
                }

                Rectangle {
                    visible: root.showArt
                    width: 132
                    height: 42
                    radius: 10
                    color: artArea.containsMouse ? "#202633" : "#151a23"
                    border.width: 1
                    border.color: "#2a3140"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Choose art"]
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    MouseArea {
                        id: artArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.artRequested()
                    }
                }
            }

            GameProfilePanel {
                id: profilePanel
                Layout.fillWidth: true
                game: root.game
                expanded: root.profileOpen
                onProfileEdited: root.profileChanged()
                onCloseRequested: root.profileOpen = false
            }

            Text {
                Layout.fillWidth: true
                visible: (root.game.installDir || "") !== ""
                text: root.game.installDir || ""
                color: "#6f7887"
                font.family: "Sora"
                font.pixelSize: 10
                elide: Text.ElideMiddle
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 2
                Layout.preferredHeight: timeline.implicitHeight + 36
                radius: 18
                color: "#0b0e14"
                border.width: 1
                border.color: "#232a36"

                ColumnLayout {
                    id: timeline
                    x: 18
                    y: 18
                    width: parent.width - 36
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        ColumnLayout {
                            spacing: 2

                            Text {
                                text: Tr.strings["PLAYTIME TIMELINE"]
                                color: "#dfe6f0"
                                font.family: "Chakra Petch"
                                font.pixelSize: 11
                                font.bold: true
                                font.letterSpacing: 2.2
                            }

                            Text {
                                text: root.game.sessionCount === 1
                                      ? Tr.strings["1 session"]
                                      : Tr.strings["%1 sessions"].arg(root.game.sessionCount || 0)
                                color: "#6f7887"
                                font.family: "Sora"
                                font.pixelSize: 10
                            }
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: Tr.strings["All time"] + ": "
                                  + (root.game.playtimeText
                                     || root.game.historyTotalText
                                     || "—")
                            color: "#8b95a5"
                            font.family: "Sora"
                            font.pixelSize: 11
                        }
                    }

                    Row {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 36
                        spacing: 5
                        visible: root.history.length > 0

                        Repeater {
                            model: Math.min(14, root.history.length)

                            Item {
                                width: 10
                                height: 36

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width
                                    height: Math.max(
                                        4,
                                        32 * ((root.history[index].seconds || 0)
                                              / root.historyMax())
                                    )
                                    radius: 4
                                    color: index === 0
                                           ? Library.accent
                                           : Qt.darker(Library.accent, 1.35)
                                    opacity: index === 0 ? 1 : 0.6
                                }
                            }
                        }
                    }

                    Flickable {
                        id: sessionFlick
                        objectName: "sessionFlick"
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(
                            360,
                            Math.max(72, sessionColumn.implicitHeight)
                        )
                        contentWidth: width
                        contentHeight: sessionColumn.implicitHeight
                        clip: true
                        boundsBehavior: Flickable.StopAtBounds
                        visible: root.history.length > 0

                        ScrollBar.vertical: ScrollBar {
                            id: sessionScrollBar
                            policy: ScrollBar.AsNeeded
                            width: 6
                            background: Item {}
                            contentItem: Rectangle {
                                implicitWidth: 5
                                radius: 2.5
                                color: sessionScrollBar.pressed
                                       ? Library.accent
                                       : "#4a586f"
                                opacity: sessionScrollBar.pressed ? 1 : 0.85
                            }
                        }

                        Column {
                            id: sessionColumn
                            width: sessionFlick.width - 12
                            spacing: 0

                            Repeater {
                                model: root.history

                                Item {
                                    width: parent.width
                                    height: 72
                                    readonly property var sessionShots: modelData.screenshots || []
                                    readonly property var previewShots: modelData.previewScreenshots || []
                                    readonly property var overflowShot: modelData.overflowScreenshot || ({})
                                    readonly property int overflowCount: modelData.overflowCount || 0
                                    readonly property bool hasShots: sessionShots.length > 0

                                    Rectangle {
                                        x: 8
                                        y: index === 0 ? 36 : 0
                                        width: 2
                                        height: index === 0
                                                ? 36
                                                : (index === root.history.length - 1
                                                   ? 36
                                                   : 72)
                                        color: "#26303f"
                                    }

                                    Rectangle {
                                        x: 2
                                        y: 29
                                        width: 14
                                        height: 14
                                        radius: 7
                                        color: index === 0
                                               ? Library.accent
                                               : "#2a3140"
                                        border.width: 2
                                        border.color: index === 0
                                                      ? Qt.lighter(Library.accent, 1.3)
                                                      : "#11151d"
                                    }

                                    Text {
                                        x: 30
                                        y: 13
                                        width: Math.max(
                                            20,
                                            parent.width - 30
                                            - (shotRow.visible
                                               ? shotRow.width + 16
                                               : 0)
                                        )
                                        text: root.sessionDate(modelData.timestamp)
                                        color: "#cfd6e2"
                                        font.family: "Sora"
                                        font.pixelSize: 11
                                        elide: Text.ElideRight
                                    }

                                    Text {
                                        x: 30
                                        y: 33
                                        width: Math.max(
                                            20,
                                            parent.width - 30
                                            - (shotRow.visible
                                               ? shotRow.width + 16
                                               : 0)
                                        )
                                        text: modelData.duration
                                              + (modelData.imported
                                                 ? " - " + Tr.strings["Imported"]
                                                 : "")
                                        color: "#7b8494"
                                        font.family: "Chakra Petch"
                                        font.pixelSize: 10
                                        font.letterSpacing: 0.6
                                        elide: Text.ElideRight
                                    }

                                    Row {
                                        id: shotRow
                                        anchors.right: parent.right
                                        anchors.rightMargin: 8
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 5
                                        visible: hasShots

                                        Repeater {
                                            model: previewShots

                                            ShotThumb {
                                                thumbWidth: 64
                                                thumbHeight: 40
                                                corner: 8
                                                shot: modelData
                                                onClicked: root.openViewer(
                                                    sessionShots, index
                                                )
                                            }
                                        }

                                        ShotThumb {
                                            visible: overflowCount > 0
                                            more: true
                                            moreCount: overflowCount
                                            thumbWidth: 64
                                            thumbHeight: 40
                                            corner: 8
                                            shot: overflowShot
                                            onClicked: root.openViewer(sessionShots, 2)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 14
                        visible: root.history.length === 0

                        Rectangle {
                            width: 44
                            height: 44
                            radius: 22
                            color: "#121722"
                            border.width: 1
                            border.color: "#232a36"

                            Text {
                                anchors.centerIn: parent
                                text: "◷"
                                color: Library.accent
                                font.pixelSize: 18
                            }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2

                            Text {
                                text: Tr.strings["No sessions recorded yet."]
                                color: "#cfd6e2"
                                font.family: "Sora"
                                font.pixelSize: 12
                            }

                            Text {
                                Layout.fillWidth: true
                                text: Tr.strings["Launch the game from GameCenter to start the timeline."]
                                color: "#6f7887"
                                font.family: "Sora"
                                font.pixelSize: 10
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.topMargin: 12
                Layout.preferredHeight: galleryFlow.implicitHeight + 66
                visible: root.screenshots.length > 0
                radius: 18
                color: "#0b0e14"
                border.width: 1
                border.color: "#232a36"

                ColumnLayout {
                    x: 18
                    y: 18
                    width: parent.width - 36
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Text {
                            text: Tr.strings["SCREENSHOTS"]
                            color: "#dfe6f0"
                            font.family: "Chakra Petch"
                            font.pixelSize: 11
                            font.bold: true
                            font.letterSpacing: 2.2
                        }

                        Item { Layout.fillWidth: true }

                        Text {
                            text: root.screenshots.length === 1
                                  ? Tr.strings["1 screenshot"]
                                  : Tr.strings["%1 screenshots"].arg(
                                        root.screenshots.length
                                    )
                            color: "#6f7887"
                            font.family: "Sora"
                            font.pixelSize: 10
                        }
                    }

                    Flow {
                        id: galleryFlow
                        Layout.fillWidth: true
                        spacing: 8

                        Repeater {
                            model: root.screenshots

                            ShotThumb {
                                thumbWidth: 96
                                thumbHeight: 54
                                shot: modelData
                                onClicked: root.openViewer(root.screenshots, index)
                            }
                        }
                    }
                }
            }
        }
    }

    // --- Pinned cartridge (never clipped by the scrolling column) ----------
    Item {
        id: cartridgeHost
        objectName: "detailCartridge"
        z: 4
        width: root.cartridgeWidth
        height: root.cartridgeHeight
        x: root.cartridgeMarginX
        y: root.cartridgeMarginY
        visible: root.opened && !root.compact

        Loader {
            id: detailCard
            anchors.centerIn: parent
            active: root.opened && !root.compact
            sourceComponent: root.is3d ? ds3dCard : flatCard
        }

        // Drag rotates the 3D card. Its viewport is larger than the model, so
        // the corners stay visible at any angle and the card never moves.
        MouseArea {
            id: cartridgePointer
            anchors.fill: parent
            z: 2
            enabled: root.is3d
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor

            property real lastX: 0
            property real lastY: 0
            property bool moved: false

            onPressed: (mouse) => {
                lastX = mouse.x;
                lastY = mouse.y;
                moved = false;
            }

            onPositionChanged: (mouse) => {
                if (!pressed) {
                    return;
                }
                var dx = mouse.x - lastX;
                var dy = mouse.y - lastY;
                if (Math.abs(dx) + Math.abs(dy) > 2) {
                    moved = true;
                }
                var item = detailCard.item;
                if (item && item.yaw !== undefined) {
                    item.yaw += dx * 0.55;
                    item.pitch = Math.max(
                        -50,
                        Math.min(50, item.pitch - dy * 0.4)
                    );
                }
                lastX = mouse.x;
                lastY = mouse.y;
            }

            onDoubleClicked: {
                if (!moved) {
                    root.playRequested();
                }
            }
        }

        Rectangle {
            visible: root.is3d
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            anchors.horizontalCenter: parent.horizontalCenter
            width: dragHint.implicitWidth + 22
            height: 26
            radius: 13
            color: "#1b2230"
            border.width: 1
            border.color: "#2b3445"
            opacity: cartridgePointer.containsMouse ? 0.95 : 0.55
            Behavior on opacity { NumberAnimation { duration: 160 } }

            Text {
                id: dragHint
                anchors.centerIn: parent
                text: Tr.strings["Drag to rotate"]
                color: "#98a3b4"
                font.family: "Sora"
                font.pixelSize: 9
            }

            MouseArea { anchors.fill: parent }
        }
    }

    // --- Screenshot viewer ------------------------------------------------
    Rectangle {
        id: shotViewer
        anchors.fill: parent
        z: 20
        visible: opacity > 0
        opacity: root.viewerOpen ? 1 : 0
        color: "#05070b"
        Behavior on opacity { NumberAnimation { duration: 180 } }

        MouseArea {
            anchors.fill: parent
            onClicked: root.closeViewer()
        }

        Image {
            anchors.fill: parent
            anchors.topMargin: 74
            anchors.bottomMargin: 88
            anchors.leftMargin: root.compact ? 30 : 70
            anchors.rightMargin: root.compact ? 30 : 70
            source: root.viewerShot.url || ""
            fillMode: Image.PreserveAspectFit
            asynchronous: true
            cache: true
        }

        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 58
            color: "#0b0f19"
            opacity: 0.94

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 22
                anchors.rightMargin: 18
                spacing: 12

                Column {
                    Layout.fillWidth: true
                    spacing: 1

                    Text {
                        text: Tr.strings["SCREENSHOTS"]
                        color: Library.accent
                        font.family: "Chakra Petch"
                        font.pixelSize: 9
                        font.bold: true
                        font.letterSpacing: 2.0
                    }

                    Text {
                        width: parent.width
                        text: root.game.title || ""
                        color: "#f2f5fa"
                        font.family: "Sora"
                        font.pixelSize: 13
                        font.bold: true
                        elide: Text.ElideRight
                    }
                }

                Text {
                    text: (root.viewerIndex + 1) + " / " + root.viewerShots.length
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                }

                Rectangle {
                    width: 30
                    height: 30
                    radius: 15
                    color: closeViewerArea.containsMouse ? "#232936" : "#171b23"

                    Text {
                        anchors.centerIn: parent
                        text: "×"
                        color: "#dfe6f0"
                        font.pixelSize: 16
                    }

                    MouseArea {
                        id: closeViewerArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.closeViewer()
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 30
            text: root.viewerShot.dateText || ""
            color: "#8b95a5"
            font.family: "Sora"
            font.pixelSize: 11
        }

        Rectangle {
            visible: root.viewerHasPrev
            anchors.left: parent.left
            anchors.leftMargin: root.compact ? 8 : 24
            anchors.verticalCenter: parent.verticalCenter
            width: 42
            height: 42
            radius: 21
            color: prevViewerArea.containsMouse ? "#232936" : "#10141b"
            border.width: 1
            border.color: "#2a3140"

            Text {
                anchors.centerIn: parent
                text: "‹"
                color: "#dfe6f0"
                font.pixelSize: 26
            }

            MouseArea {
                id: prevViewerArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.previousViewer()
            }
        }

        Rectangle {
            visible: root.viewerHasNext
            anchors.right: parent.right
            anchors.rightMargin: root.compact ? 8 : 24
            anchors.verticalCenter: parent.verticalCenter
            width: 42
            height: 42
            radius: 21
            color: nextViewerArea.containsMouse ? "#232936" : "#10141b"
            border.width: 1
            border.color: "#2a3140"

            Text {
                anchors.centerIn: parent
                text: "›"
                color: "#dfe6f0"
                font.pixelSize: 26
            }

            MouseArea {
                id: nextViewerArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.nextViewer()
            }
        }
    }

    Shortcut {
        sequence: "Escape"
        enabled: root.viewerOpen
        onActivated: root.closeViewer()
    }

    Shortcut {
        sequence: "Left"
        enabled: root.viewerOpen
        onActivated: root.previousViewer()
    }

    Shortcut {
        sequence: "Right"
        enabled: root.viewerOpen
        onActivated: root.nextViewer()
    }

    CloseButton {
        z: 5
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 16
        anchors.rightMargin: 18
        onClicked: root.closeRequested()
    }

    Component {
        id: flatCard

        Cartridge {
            width: 208
            height: 288
            scale: 1.12
            transformOrigin: Item.Center
            showTitle: false
            interactive: true
            style: Library.cartridgeStyle
            gameTitle: root.game.title || ""
            gameSource: root.game.source || ""
            gameMeta: root.game.meta || ""
            coverUrl: root.game.cover || ""
            gameInstalled: root.game.installed !== false
            cartridgeColor: root.game.cartridgeColor || Library.cartridgeColor
            onLaunchRequested: root.playRequested()
        }
    }

    Component {
        id: ds3dCard

        DsCartridge3D {
            width: root.cartridgeWidth
            height: root.cartridgeHeight
            modelScale: 0.82
            interactive: false
            textureUrl: root.game.texture || ""
            cartridgeColor: root.game.cartridgeColor || Library.cartridgeColor
            onPlayRequested: root.playRequested()
        }
    }

    component ShotThumb: Item {
        id: thumb
        property var shot: ({})
        property real thumbWidth: 48
        property real thumbHeight: 30
        property bool more: false
        property int moreCount: 0
        property real corner: 6

        width: thumbWidth
        height: thumbHeight
        implicitWidth: thumbWidth
        implicitHeight: thumbHeight

        signal clicked()

        Rectangle {
            anchors.fill: parent
            radius: thumb.corner
            color: "#070b12"
            border.width: 1
            border.color: hoverArea.containsMouse
                          ? Library.accent
                          : "#2a3a52"
            Behavior on border.color { ColorAnimation { duration: 120 } }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1.5
            radius: Math.max(2, thumb.corner - 1)
            color: "#17202f"
            clip: true

            Image {
                anchors.fill: parent
                source: thumb.shot.url || ""
                sourceSize.width: Math.round(thumb.thumbWidth * 2)
                sourceSize.height: Math.round(thumb.thumbHeight * 2)
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
            }

            Rectangle {
                visible: thumb.more
                anchors.fill: parent
                color: "#05070b"
                opacity: 0.72
            }

            Text {
                visible: thumb.more
                anchors.centerIn: parent
                text: "+" + thumb.moreCount
                color: "#f8fafc"
                font.family: "Sora"
                font.pixelSize: Math.max(9, thumb.thumbHeight * 0.32)
                font.bold: true
            }
        }

        MouseArea {
            id: hoverArea
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: thumb.clicked()
        }
    }
}
