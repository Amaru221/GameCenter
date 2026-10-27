import QtQuick
import QtQuick.Layouts

Item {
    id: root
    objectName: "yearReviewSlide"

    property var slideData: ({})
    property var review: ({})
    property int slideIndex: 0

    readonly property string kind: slideData.type || "intro"
    readonly property var month: slideData.month || ({})
    readonly property var game: slideData.game || ({})
    readonly property var day: slideData.day || ({})
    readonly property var streak: slideData.streak || ({})
    readonly property color accent: slideData.accent || Library.accent

    function tintColor(hex, alpha) {
        var value = String(hex || "#4cc9f0");
        if (value.length !== 7) {
            return Qt.rgba(0.3, 0.79, 0.94, alpha);
        }
        return Qt.rgba(
            parseInt(value.substring(1, 3), 16) / 255,
            parseInt(value.substring(3, 5), 16) / 255,
            parseInt(value.substring(5, 7), 16) / 255,
            alpha
        );
    }

    function peakIndex(values) {
        var best = -1;
        var peak = 0;
        for (var i = 0; i < values.length; i++) {
            if ((values[i] || 0) > peak) {
                peak = values[i];
                best = i;
            }
        }
        return best;
    }

    // Decorative watermark behind the intro and outro.
    Text {
        visible: root.kind === "intro" || root.kind === "outro"
        anchors.centerIn: parent
        text: root.review.year || ""
        color: root.accent
        opacity: 0.045
        font.family: "Sora"
        font.pixelSize: Math.min(460, root.width * 0.46)
        font.bold: true
    }

    Item {
        id: contentHost
        anchors.fill: parent
        opacity: 0
        y: 18

        Component.onCompleted: reveal.start()

        ParallelAnimation {
            id: reveal
            NumberAnimation {
                target: contentHost
                property: "opacity"
                to: 1
                duration: 500
                easing.type: Easing.OutCubic
            }
            NumberAnimation {
                target: contentHost
                property: "y"
                to: 0
                duration: 560
                easing.type: Easing.OutCubic
            }
        }

        // ----------------------------------------------------------------
        // Intro
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "intro"

            ColumnLayout {
                width: Math.min(760, root.width - 80)
                anchors.centerIn: parent
                spacing: 10

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["YEAR IN REVIEW"]
                    tint: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.review.year || ""
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 96
                    font.bold: true
                    font.letterSpacing: -5
                }

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    width: 92
                    height: 3
                    radius: 1.5
                    color: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.review.timeText || "0m"
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 46
                    font.bold: true
                    font.letterSpacing: -1.2
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Time Played"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 10
                    font.bold: true
                    font.letterSpacing: 2.4
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    spacing: 8

                    StoryStat {
                        valueText: root.review.sessionsCount || 0
                        labelText: Tr.strings["Sessions"]
                        tint: root.accent
                    }

                    StoryStat {
                        valueText: root.review.daysPlayed || 0
                        labelText: Tr.strings["Days played"]
                        tint: root.accent
                    }

                    StoryStat {
                        valueText: root.review.totalGames || 0
                        labelText: Tr.strings["Games"]
                        tint: root.accent
                    }
                }

                TopGameCard {
                    visible: (root.review.topGame.name || "") !== ""
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    gameData: root.review.topGame || ({})
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 2
                    text: Tr.strings["Tap to continue"]
                    color: "#687588"
                    font.family: "Sora"
                    font.pixelSize: 10
                }
            }
        }

        // ----------------------------------------------------------------
        // One month
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "month"

            ColumnLayout {
                width: Math.min(790, root.width - 76)
                anchors.centerIn: parent
                spacing: 8

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: (root.month.number || "") + "   ·   "
                          + (root.review.year || "")
                    tint: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.month.name || ""
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 38
                    font.bold: true
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.month.hoursText || "0m"
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 32
                    font.bold: true
                    font.letterSpacing: -0.6
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 8

                    StoryStat {
                        valueText: root.month.daysPlayed || 0
                        labelText: Tr.strings["Days played"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.month.sessionsCount || 0
                        labelText: Tr.strings["Sessions"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.month.bestDayText || "—"
                        labelText: Tr.strings["Best day"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.month.streak || 0
                        labelText: Tr.strings["Days in a row"]
                        tint: root.accent
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10

                    TopGameCard {
                        Layout.fillWidth: true
                        gameData: root.month.mostPlayed || ({})
                    }

                    Rectangle {
                        visible: (root.month.banner
                                  && root.month.banner.label) || false
                        Layout.preferredWidth: 226
                        Layout.fillHeight: true
                        radius: 15
                        color: root.tintColor(
                            root.month.banner ? root.month.banner.tint : "#facc15",
                            0.11
                        )
                        border.width: 1
                        border.color: root.tintColor(
                            root.month.banner ? root.month.banner.tint : "#facc15",
                            0.38
                        )

                        Column {
                            anchors.centerIn: parent
                            width: parent.width - 24
                            spacing: 3

                            Text {
                                width: parent.width
                                text: root.month.banner
                                      ? (root.month.banner.label || "") : ""
                                color: root.month.banner
                                       ? (root.month.banner.tint || "#facc15")
                                       : "#facc15"
                                font.family: "Chakra Petch"
                                font.pixelSize: 9
                                font.bold: true
                                font.letterSpacing: 0.8
                                elide: Text.ElideRight
                            }

                            Text {
                                width: parent.width
                                text: root.month.banner
                                      ? (root.month.banner.value || "") : ""
                                color: "#f8fafc"
                                font.family: "Sora"
                                font.pixelSize: 17
                                font.bold: true
                                elide: Text.ElideRight
                            }

                            Text {
                                width: parent.width
                                text: root.month.banner
                                      ? (root.month.banner.detail || "") : ""
                                color: "#8b95a5"
                                font.family: "Sora"
                                font.pixelSize: 9
                                elide: Text.ElideRight
                            }
                        }
                    }
                }

                TopThreeList {
                    Layout.fillWidth: true
                    Layout.topMargin: 1
                    games: root.month.topGames || []
                }

                MiniBars {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42
                    Layout.topMargin: 1
                    values: root.month.daily || []
                    highlightIndex: -1
                    tint: root.accent
                }
            }
        }

        // ----------------------------------------------------------------
        // Most played game
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "topGame"

            ColumnLayout {
                width: Math.min(720, root.width - 100)
                anchors.centerIn: parent
                spacing: 10

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Most played"]
                    tint: root.accent
                }

                Text {
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    text: root.game.name || ""
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 36
                    font.bold: true
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }

                StoryCover {
                    Layout.alignment: Qt.AlignHCenter
                    cw: 180
                    ch: 232
                    source: root.game.cover || ""
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.game.hoursText || ""
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 44
                    font.bold: true
                    font.letterSpacing: -1.0
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["%1% of your year"].arg(
                              root.game.percentOfYear || 0
                          )
                    color: "#8b95a5"
                    font.family: "Sora"
                    font.pixelSize: 13
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    text: Tr.strings["Tap to continue"]
                    color: "#687588"
                    font.family: "Sora"
                    font.pixelSize: 10
                }
            }
        }

        // ----------------------------------------------------------------
        // Sessions
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "sessions"

            ColumnLayout {
                width: Math.min(760, root.width - 80)
                anchors.centerIn: parent
                spacing: 12

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Sessions"]
                    tint: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.review.sessionsCount || 0
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 96
                    font.bold: true
                    font.letterSpacing: -4
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Sessions"]
                    color: "#8b95a5"
                    font.family: "Sora"
                    font.pixelSize: 16
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    spacing: 8

                    StoryStat {
                        valueText: root.review.averageSessionText || "0m"
                        labelText: Tr.strings["Average session"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.review.daysPlayed || 0
                        labelText: Tr.strings["Days played"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.review.activeMonthCount || 0
                        labelText: Tr.strings["Active months"]
                        tint: root.accent
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 8
                    text: Tr.strings["Monthly rhythm"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1.6
                }

                MiniBars {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 52
                    values: root.review.monthSessions || []
                    highlightIndex: root.peakIndex(root.review.monthSessions || [])
                    tint: root.accent
                }
            }
        }

        // ----------------------------------------------------------------
        // Longest streak
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "streak"

            ColumnLayout {
                width: Math.min(760, root.width - 80)
                anchors.centerIn: parent
                spacing: 10

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Longest streak"]
                    tint: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.streak.days || 0
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 112
                    font.bold: true
                    font.letterSpacing: -5
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Days in a row"]
                    color: "#8b95a5"
                    font.family: "Sora"
                    font.pixelSize: 17
                }

                Row {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 10
                    spacing: 7

                    Repeater {
                        model: Math.min(root.streak.days || 0, 16)
                        Rectangle {
                            width: 9
                            height: 9
                            radius: 4.5
                            color: root.accent
                            opacity: 0.45 + 0.55 * (index / Math.max(1, Math.min(root.streak.days || 0, 16) - 1))
                        }
                    }
                }

                Rectangle {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 10
                    implicitWidth: 240
                    implicitHeight: 42
                    radius: 12
                    color: Qt.rgba(1, 1, 1, 0.055)
                    border.width: 1
                    border.color: root.tintColor(root.accent, 0.22)

                    Text {
                        anchors.centerIn: parent
                        text: root.streak.rangeText || ""
                        color: "#dfe6f0"
                        font.family: "Sora"
                        font.pixelSize: 14
                        font.bold: true
                    }
                }
            }
        }

        // ----------------------------------------------------------------
        // Best day
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "bestDay"

            ColumnLayout {
                width: Math.min(720, root.width - 90)
                anchors.centerIn: parent
                spacing: 12

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Best day"]
                    tint: root.accent
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 18

                    Rectangle {
                        implicitWidth: 118
                        implicitHeight: 126
                        radius: 20
                        color: Qt.rgba(1, 1, 1, 0.06)
                        border.width: 1
                        border.color: root.tintColor(root.accent, 0.35)

                        Column {
                            anchors.centerIn: parent
                            spacing: 1

                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.day.dayNumber || ""
                                color: "#f8fafc"
                                font.family: "Sora"
                                font.pixelSize: 52
                                font.bold: true
                                font.letterSpacing: -2
                            }

                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.day.monthShort || ""
                                color: root.accent
                                font.family: "Chakra Petch"
                                font.pixelSize: 13
                                font.bold: true
                                font.letterSpacing: 1.6
                            }

                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.review.year || ""
                                color: "#7d8798"
                                font.family: "Sora"
                                font.pixelSize: 9
                            }
                        }
                    }

                    ColumnLayout {
                        spacing: 4

                        Text {
                            text: root.day.hoursText || ""
                            color: root.accent
                            font.family: "Sora"
                            font.pixelSize: 46
                            font.bold: true
                            font.letterSpacing: -1.0
                        }

                        Text {
                            text: (root.day.sessionsCount || 0) + " "
                                  + Tr.strings["Sessions"]
                            color: "#8b95a5"
                            font.family: "Sora"
                            font.pixelSize: 12
                        }
                    }
                }

                TopGameCard {
                    visible: root.day.topGame
                             && (root.day.topGame.name || "") !== ""
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 2
                    gameData: root.day.topGame || ({})
                }
            }
        }

        // ----------------------------------------------------------------
        // Busiest month
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "busiest"

            ColumnLayout {
                width: Math.min(780, root.width - 80)
                anchors.centerIn: parent
                spacing: 10

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Busiest month"]
                    tint: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.month.name || ""
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 50
                    font.bold: true
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.month.hoursText || "0m"
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 36
                    font.bold: true
                    font.letterSpacing: -0.8
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 8

                    StoryStat {
                        valueText: root.month.sessionsCount || 0
                        labelText: Tr.strings["Sessions"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.month.daysPlayed || 0
                        labelText: Tr.strings["Days played"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.month.bestDayText || "—"
                        labelText: Tr.strings["Best day"]
                        tint: root.accent
                    }
                }

                TopGameCard {
                    visible: root.month.mostPlayed
                             && (root.month.mostPlayed.name || "") !== ""
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 2
                    gameData: root.month.mostPlayed || ({})
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    text: Tr.strings["Monthly rhythm"]
                    color: "#8b95a5"
                    font.family: "Chakra Petch"
                    font.pixelSize: 9
                    font.bold: true
                    font.letterSpacing: 1.6
                }

                MiniBars {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 44
                    values: root.review.monthTotals || []
                    highlightIndex: root.month.monthIndex || 0
                    tint: root.accent
                }
            }
        }

        // ----------------------------------------------------------------
        // Outro
        // ----------------------------------------------------------------
        Item {
            anchors.fill: parent
            visible: root.kind === "outro"

            ColumnLayout {
                width: Math.min(760, root.width - 80)
                anchors.centerIn: parent
                spacing: 10

                Kicker {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["That's a wrap"]
                    tint: root.accent
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.review.year || ""
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 82
                    font.bold: true
                    font.letterSpacing: -4
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: root.review.timeText || "0m"
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 42
                    font.bold: true
                    font.letterSpacing: -1.0
                }

                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    spacing: 8

                    StoryStat {
                        valueText: root.review.sessionsCount || 0
                        labelText: Tr.strings["Sessions"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.review.daysPlayed || 0
                        labelText: Tr.strings["Days played"]
                        tint: root.accent
                    }
                    StoryStat {
                        valueText: root.review.totalGames || 0
                        labelText: Tr.strings["Games"]
                        tint: root.accent
                    }
                }

                TopGameCard {
                    visible: (root.review.topGame.name || "") !== ""
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 4
                    gameData: root.review.topGame || ({})
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 2
                    text: Tr.strings["See you next year"]
                    color: "#8b95a5"
                    font.family: "Sora"
                    font.pixelSize: 14
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter
                    text: Tr.strings["Tap to close"]
                    color: "#687588"
                    font.family: "Sora"
                    font.pixelSize: 10
                }
            }
        }
    }

    // --------------------------------------------------------------------
    // Reusable story pieces
    // --------------------------------------------------------------------

    component Kicker: Text {
        property color tint: root.accent
        color: tint
        font.family: "Chakra Petch"
        font.pixelSize: 11
        font.bold: true
        font.letterSpacing: 3.0
        horizontalAlignment: Text.AlignHCenter
    }

    component StoryStat: Rectangle {
        property string valueText: ""
        property string labelText: ""
        property color tint: root.accent

        implicitWidth: 118
        implicitHeight: 52
        radius: 14
        color: Qt.rgba(1, 1, 1, 0.055)
        border.width: 1
        border.color: root.tintColor(tint, 0.20)

        Column {
            anchors.centerIn: parent
            spacing: 1

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: valueText
                color: "#f8fafc"
                font.family: "Sora"
                font.pixelSize: 18
                font.bold: true
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: labelText
                color: Qt.rgba(1, 1, 1, 0.54)
                font.family: "Sora"
                font.pixelSize: 9
                font.letterSpacing: 0.3
            }
        }
    }

    component StoryCover: Item {
        id: coverRoot
        property string source: ""
        property real cw: 90
        property real ch: 116

        implicitWidth: cw
        implicitHeight: ch

        scale: 0.86
        Component.onCompleted: rise.start()

        NumberAnimation {
            id: rise
            target: coverRoot
            property: "scale"
            to: 1
            duration: 650
            easing.type: Easing.OutBack
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -10
            radius: width / 2
            color: root.accent
            opacity: 0.13
        }

        Rectangle {
            anchors.fill: parent
            radius: 13
            color: "#070a10"
            border.width: 1
            border.color: root.tintColor(root.accent, 0.40)
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 2
            radius: 11
            color: "#17202f"
            clip: true

            Image {
                anchors.fill: parent
                source: coverRoot.source
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
            }
        }
    }

    component MiniCover: Item {
        property string source: ""
        property real cw: 16
        property real ch: 21
        implicitWidth: cw
        implicitHeight: ch

        Rectangle {
            anchors.fill: parent
            radius: 4
            color: "#0a1019"
            border.width: 1
            border.color: "#2a3a52"
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            radius: 3
            color: "#182234"
            clip: true

            Image {
                anchors.fill: parent
                source: parent.parent.source
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
                cache: true
            }
        }
    }

    component MiniBars: Item {
        id: bars
        objectName: "miniBars"
        property var values: []
        property int highlightIndex: -1
        property color tint: root.accent
        property real reveal: 0
        implicitHeight: 48

        visible: values.length > 0

        NumberAnimation on reveal {
            from: 0
            to: 1
            duration: 950
            easing.type: Easing.OutCubic
        }

        readonly property real peak: {
            var value = 1;
            for (var i = 0; i < values.length; i++) {
                value = Math.max(value, values[i] || 0);
            }
            return value;
        }

        readonly property real barWidth: {
            var count = Math.max(1, values.length);
            var maximum = count <= 12 ? 28 : 14;
            return Math.max(3, Math.min(maximum, width / count - 2));
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            height: parent.height
            spacing: 2

            Repeater {
                model: bars.values.length

                Item {
                    width: bars.barWidth
                    height: bars.height

                    Rectangle {
                        anchors.bottom: parent.bottom
                        width: parent.width
                        height: Math.max(
                            2,
                            (bars.height - 4)
                            * ((bars.values[index] || 0) / bars.peak)
                            * bars.reveal
                        )
                        radius: 1.5
                        color: index === bars.highlightIndex
                               ? bars.tint
                               : Qt.rgba(1, 1, 1, 0.38)
                    }
                }
            }
        }
    }

    component TopGameCard: Rectangle {
        id: topCard
        objectName: "topGameCard"
        property var gameData: ({})
        implicitWidth: 360
        implicitHeight: 86
        radius: 16
        color: Qt.rgba(1, 1, 1, 0.055)
        border.width: 1
        border.color: root.tintColor(root.accent, 0.20)

        RowLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 12

            StoryCover {
                cw: 50
                ch: 66
                source: topCard.gameData.cover || ""
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 1

                Text {
                    Layout.fillWidth: true
                    text: Tr.strings["Most played"]
                    color: root.accent
                    font.family: "Chakra Petch"
                    font.pixelSize: 8
                    font.bold: true
                    font.letterSpacing: 1.3
                }

                Text {
                    Layout.fillWidth: true
                    text: topCard.gameData.name || ""
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 14
                    font.bold: true
                    elide: Text.ElideRight
                    maximumLineCount: 1
                }

                Text {
                    Layout.fillWidth: true
                    text: topCard.gameData.hoursText || ""
                    color: root.accent
                    font.family: "Sora"
                    font.pixelSize: 12
                    font.bold: true
                }
            }
        }
    }

    component TopThreeList: Column {
        property var games: []
        spacing: 5

        Repeater {
            model: games

            RowLayout {
                width: parent.width
                spacing: 8

                Text {
                    Layout.preferredWidth: 18
                    text: (index + 1 < 10 ? "0" : "") + (index + 1)
                    color: "#64748b"
                    font.family: "Chakra Petch"
                    font.pixelSize: 9
                    font.bold: true
                }

                MiniCover {
                    source: modelData.cover || ""
                    cw: 16
                    ch: 21
                }

                Text {
                    Layout.fillWidth: true
                    text: modelData.name
                    color: "#dfe6f0"
                    font.family: "Sora"
                    font.pixelSize: 10
                    elide: Text.ElideRight
                }

                Text {
                    text: modelData.hoursText
                    color: "#f2f5fa"
                    font.family: "Sora"
                    font.pixelSize: 10
                    font.bold: true
                }
            }
        }
    }
}
