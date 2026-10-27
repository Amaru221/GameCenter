import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    objectName: "statsView"
    color: "#0b0f19"

    property var statsData: ({})
    property string period: "year"
    property int selectedYear: new Date().getFullYear()
    property int selectedMonth: -1
    property bool reviewing: false

    readonly property bool narrow: width < 1080
    // Newest month first: the current month (or December) leads the carousel
    // and January closes it.
    readonly property var months: {
        var list = (statsData.months || []).slice();
        list.reverse();
        return list;
    }
    readonly property var river: statsData.river || ({})

    function carouselIndexForMonth(monthIndex) {
        var count = root.months.length;
        if (count === 0) {
            return -1;
        }
        return Math.max(0, Math.min(count - 1, count - 1 - monthIndex));
    }

    function refresh() {
        statsData = Library.stats(
            period,
            selectedYear,
            period === "month" ? selectedMonth : -1
        );
        if (period === "month" && selectedMonth >= 0) {
            Qt.callLater(function() {
                if (carousel.count > 0) {
                    var target = root.carouselIndexForMonth(selectedMonth);
                    carousel.currentIndex = target;
                    carousel.positionViewAtIndex(target, ListView.Beginning);
                }
            });
        }
    }

    function setPeriod(value) {
        period = value;
        if (value === "month") {
            var current = new Date();
            selectedMonth = selectedYear === current.getFullYear()
                            ? current.getMonth()
                            : 11;
        }
        refresh();
    }

    function changeYear(delta) {
        var currentYear = new Date().getFullYear();
        var next = selectedYear + delta;
        if (next < 2000 || next > currentYear) {
            return;
        }
        selectedYear = next;
        if (period === "month" && selectedYear === currentYear
                && selectedMonth > new Date().getMonth()) {
            selectedMonth = new Date().getMonth();
        }
        refresh();
    }

    function openMonth(index) {
        period = "month";
        selectedMonth = index;
        refresh();
        page.contentY = 0;
    }

    function toggleReview() {
        reviewing = !reviewing;
        if (reviewing && carousel.count > 0) {
            carousel.currentIndex = 0;
            carousel.positionViewAtIndex(0, ListView.Beginning);
        }
    }

    function formatDay(timestamp) {
        if (!timestamp) {
            return "";
        }
        return Qt.formatDateTime(new Date(timestamp * 1000), "dd/MM");
    }

    function changeColor(text) {
        return (text || "").indexOf("-") === 0 ? "#fb7185" : "#34d399";
    }

    onVisibleChanged: {
        if (visible) {
            refresh();
        } else {
            reviewing = false;
        }
    }

    Component.onCompleted: {
        if (visible) {
            refresh();
        }
    }

    Rectangle {
        x: 0
        y: 0
        width: root.width
        height: root.height
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0b0f19" }
            GradientStop { position: 0.55; color: "#0a0e17" }
            GradientStop { position: 1.0; color: "#070a12" }
        }
    }

    Flickable {
        id: page
        objectName: "statsPage"
        x: 24
        y: 18
        width: root.width - 48
        height: root.height - 36
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
            width: page.width - 14
            spacing: 18

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12

                    PeriodTabs {}

                    Item { Layout.fillWidth: true }

                    YearPicker {}

                    ReviewBanner {
                        visible: !root.narrow
                        Layout.preferredWidth: 340
                        Layout.preferredHeight: 54
                    }
                }

                ReviewBanner {
                    visible: root.narrow
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 206
                radius: 24
                border.width: 1
                border.color: "#243044"
                clip: true

                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#141c2b" }
                    GradientStop { position: 0.52; color: "#0f1622" }
                    GradientStop { position: 1.0; color: "#0b1019" }
                }

                Canvas {
                    id: heroArt
                    anchors.fill: parent
                    opacity: 0.9

                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();
                        var w = width;
                        var h = height;
                        if (w <= 0 || h <= 0) {
                            return;
                        }

                        var glow = ctx.createLinearGradient(0, 0, w, h);
                        glow.addColorStop(0, "#4cc9f0");
                        glow.addColorStop(0.55, "#a78bfa");
                        glow.addColorStop(1, "#ff8c42");
                        ctx.globalAlpha = 0.07;
                        ctx.fillStyle = glow;
                        ctx.beginPath();
                        ctx.moveTo(w * 0.42, h);
                        ctx.bezierCurveTo(
                            w * 0.55, h * 0.55, w * 0.72, h * 0.82, w, h * 0.44
                        );
                        ctx.lineTo(w, h);
                        ctx.closePath();
                        ctx.fill();

                        ctx.globalAlpha = 0.14;
                        ctx.strokeStyle = "#4cc9f0";
                        ctx.lineWidth = 1;
                        for (var i = 0; i < 3; i++) {
                            ctx.beginPath();
                            ctx.arc(w - 100, 54, 42 + i * 34, 0, Math.PI * 2);
                            ctx.stroke();
                        }
                        ctx.globalAlpha = 1;
                    }

                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Component.onCompleted: requestPaint()
                }

                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: 30
                    text: root.selectedYear
                    color: "#4cc9f0"
                    opacity: 0.045
                    font.family: "Sora"
                    font.pixelSize: 124
                    font.bold: true
                }

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 24
                    spacing: 6

                    Text {
                        text: Tr.strings["Time Played"]
                        color: "#8b95a5"
                        font.family: "Chakra Petch"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 2.4
                    }

                    Text {
                        text: root.statsData.timeText || "0m"
                        color: "#f8fafc"
                        font.family: "Sora"
                        font.pixelSize: root.narrow ? 48 : 62
                        font.bold: true
                        font.letterSpacing: -1.4
                    }

                    Text {
                        text: root.statsData.periodLabel || ""
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }

                    Flow {
                        Layout.fillWidth: true
                        Layout.topMargin: 10
                        spacing: 16

                        Repeater {
                            model: {
                                var stats = [];
                                if (root.statsData.changeText) {
                                    stats.push({
                                        text: root.statsData.changeText,
                                        color: root.changeColor(root.statsData.changeText)
                                    });
                                }
                                if (root.statsData.daysText) {
                                    stats.push({ text: root.statsData.daysText, color: "#c9d2e0" });
                                }
                                if (root.statsData.streakText) {
                                    stats.push({ text: root.statsData.streakText, color: "#c9d2e0" });
                                }
                                if (root.statsData.sessionsText) {
                                    stats.push({ text: root.statsData.sessionsText, color: "#c9d2e0" });
                                }
                                return stats;
                            }

                            Row {
                                spacing: 7

                                Rectangle {
                                    width: 5
                                    height: 5
                                    radius: 2.5
                                    color: modelData.color
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Text {
                                    text: modelData.text
                                    color: modelData.color
                                    font.family: "Sora"
                                    font.pixelSize: 11
                                }
                            }
                        }
                    }

                    Text {
                        visible: root.statsData.hasData === false
                        text: Tr.strings["No playtime in this period."]
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 11
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    spacing: 2

                    Text {
                        text: Tr.strings["Month by Month"]
                        color: "#f2f5fa"
                        font.family: "Chakra Petch"
                        font.pixelSize: 13
                        font.bold: true
                        font.letterSpacing: 2.0
                    }

                    Text {
                        text: Tr.strings["%1 as a river"].arg(root.selectedYear)
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 10
                    }
                }

                Item { Layout.fillWidth: true }

                Flow {
                    spacing: 12

                    Repeater {
                        model: (root.river.layers || []).slice(0, 5)

                        Row {
                            spacing: 6

                            Rectangle {
                                width: 7
                                height: 7
                                radius: 3.5
                                color: modelData.color
                                anchors.verticalCenter: parent.verticalCenter
                            }

                            Text {
                                text: modelData.name
                                color: "#8b95a5"
                                font.family: "Sora"
                                font.pixelSize: 9
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 246
                radius: 20
                color: "#0e1522"
                border.width: 1
                border.color: "#202b3d"
                clip: true

                Canvas {
                    id: riverChart
                    anchors.fill: parent
                    anchors.margins: 14

                    property var riverData: root.river
                    property var layers: (riverData && riverData.layers)
                                         ? riverData.layers : []
                    property var labels: (riverData && riverData.months)
                                         ? riverData.months : []

                    onRiverDataChanged: requestPaint()
                    onLayersChanged: requestPaint()
                    onLabelsChanged: requestPaint()
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Component.onCompleted: requestPaint()

                    onPaint: {
                        var ctx = getContext("2d");
                        ctx.reset();
                        var w = width;
                        var h = height;
                        if (w <= 0 || h <= 0) {
                            return;
                        }

                        var left = 8;
                        var right = 8;
                        var top = 14;
                        var bottom = 22;
                        var plotW = w - left - right;
                        var plotH = h - top - bottom;
                        var count = labels.length;

                        if (count === 0 || layers.length === 0) {
                            ctx.fillStyle = "#42506a";
                            ctx.font = "11px Sora";
                            ctx.textAlign = "center";
                            ctx.fillText(
                                Tr.strings["No playtime in this period."],
                                w / 2, h / 2
                            );
                            return;
                        }

                        var totals = [];
                        var peak = 1;
                        for (var i = 0; i < count; i++) {
                            var sum = 0;
                            for (var j = 0; j < layers.length; j++) {
                                sum += (layers[j].values[i] || 0);
                            }
                            totals.push(sum);
                            peak = Math.max(peak, sum);
                        }

                        function px(index) {
                            return count === 1
                                   ? left + plotW / 2
                                   : left + plotW * index / (count - 1);
                        }

                        function py(value) {
                            return top + plotH - (value / peak) * plotH;
                        }

                        ctx.strokeStyle = "#1b2638";
                        ctx.lineWidth = 1;
                        for (var line = 0; line <= 3; line++) {
                            var y = top + plotH * line / 3;
                            ctx.beginPath();
                            ctx.moveTo(left, y);
                            ctx.lineTo(w - right, y);
                            ctx.stroke();
                        }

                        function smoothForward(points) {
                            ctx.moveTo(points[0].x, points[0].y);
                            for (var s = 1; s < points.length - 1; s++) {
                                var midX = (points[s].x + points[s + 1].x) / 2;
                                var midY = (points[s].y + points[s + 1].y) / 2;
                                ctx.quadraticCurveTo(
                                    points[s].x, points[s].y, midX, midY
                                );
                            }
                            var lastPoint = points[points.length - 1];
                            ctx.lineTo(lastPoint.x, lastPoint.y);
                        }

                        function smoothReverse(points) {
                            var last = points.length - 1;
                            ctx.lineTo(points[last].x, points[last].y);
                            for (var s = last; s > 0; s--) {
                                var midX = (points[s].x + points[s - 1].x) / 2;
                                var midY = (points[s].y + points[s - 1].y) / 2;
                                ctx.quadraticCurveTo(
                                    points[s].x, points[s].y, midX, midY
                                );
                            }
                            ctx.lineTo(points[0].x, points[0].y);
                        }

                        var cumulative = [];
                        for (var c = 0; c < count; c++) {
                            cumulative.push(0);
                        }

                        for (var layerIndex = 0; layerIndex < layers.length; layerIndex++) {
                            var layer = layers[layerIndex];
                            var lower = [];
                            var upper = [];
                            for (var point = 0; point < count; point++) {
                                lower.push(py(cumulative[point]));
                                cumulative[point] += (layer.values[point] || 0);
                                upper.push(py(cumulative[point]));
                            }

                            var lowerPoints = [];
                            var upperPoints = [];
                            for (var p = 0; p < count; p++) {
                                lowerPoints.push({ x: px(p), y: lower[p] });
                                upperPoints.push({ x: px(p), y: upper[p] });
                            }

                            ctx.beginPath();
                            smoothForward(lowerPoints);
                            smoothReverse(upperPoints);
                            ctx.closePath();
                            ctx.globalAlpha = 0.34;
                            ctx.fillStyle = layer.color;
                            ctx.fill();
                            ctx.globalAlpha = 1;

                            ctx.beginPath();
                            smoothForward(upperPoints);
                            ctx.strokeStyle = layer.color;
                            ctx.lineWidth = 1.5;
                            ctx.stroke();
                        }

                        ctx.fillStyle = "#64748b";
                        ctx.font = "9px Sora";
                        ctx.textAlign = "center";
                        for (var label = 0; label < count; label++) {
                            ctx.fillText(labels[label], px(label), h - 5);
                        }
                    }
                }
            }

            ListView {
                id: carousel
                Layout.fillWidth: true
                Layout.preferredHeight: 448
                orientation: ListView.Horizontal
                spacing: 14
                clip: true
                model: root.months
                boundsBehavior: Flickable.StopAtBounds
                snapMode: ListView.SnapToItem
                cacheBuffer: 900

                ScrollBar.horizontal: ScrollBar {
                    policy: ScrollBar.AsNeeded
                    height: 8
                    background: Item {}
                    contentItem: Rectangle {
                        implicitHeight: 6
                        radius: 3
                        color: "#3a465c"
                    }
                }

                delegate: MonthCard {
                    width: 360
                    height: carousel.height - 10
                    month: modelData
                    monthIndex: modelData.monthIndex !== undefined
                               ? modelData.monthIndex
                               : index
                    active: ListView.isCurrentItem
                }
            }
        }
    }

    Timer {
        id: reviewTimer
        interval: 2800
        repeat: true
        running: root.reviewing && root.months.length > 1
        onTriggered: {
            if (carousel.count > 0) {
                carousel.currentIndex = (carousel.currentIndex + 1)
                                        % carousel.count;
                carousel.positionViewAtIndex(
                    carousel.currentIndex, ListView.Center
                );
            }
        }
    }

    Connections {
        target: Library
        function onPlaytimeChanged() {
            if (root.visible) {
                root.refresh();
            }
        }
    }

    Connections {
        target: Tr
        function onLanguageChanged() {
            if (root.visible) {
                root.refresh();
            }
        }
    }

    component PeriodTabs: Rectangle {
        width: 360
        height: 40
        radius: 20
        color: "#101827"
        border.width: 1
        border.color: "#243044"

        Row {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 2

            Repeater {
                model: [
                    { label: "Week", value: "week" },
                    { label: "Month", value: "month" },
                    { label: "Year", value: "year" },
                    { label: "All time", value: "all" }
                ]

                delegate: Rectangle {
                    readonly property bool selected: root.period === modelData.value
                    width: (parent.width - 6) / 4
                    height: 30
                    radius: 15
                    color: selected ? "#223049" : "transparent"
                    border.width: selected ? 1 : 0
                    border.color: "#3b4f70"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings[modelData.label]
                        color: selected ? "#f2f5fa" : "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 10
                        font.bold: selected
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.setPeriod(modelData.value)
                    }
                }
            }
        }
    }

    component YearPicker: Row {
        readonly property bool canNext: root.selectedYear < new Date().getFullYear()
        height: 40
        spacing: 4

        Rectangle {
            width: 34
            height: 34
            radius: 17
            color: previousArea.containsMouse ? "#1d2737" : "#101827"
            border.width: 1
            border.color: "#243044"

            Text {
                anchors.centerIn: parent
                text: "‹"
                color: "#c9d2e0"
                font.family: "Sora"
                font.pixelSize: 20
            }

            MouseArea {
                id: previousArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.changeYear(-1)
            }
        }

        Text {
            width: 48
            height: 34
            text: root.selectedYear
            color: "#f2f5fa"
            font.family: "Chakra Petch"
            font.pixelSize: 14
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }

        Rectangle {
            width: 34
            height: 34
            radius: 17
            opacity: canNext ? 1 : 0.3
            color: nextArea.containsMouse ? "#1d2737" : "#101827"
            border.width: 1
            border.color: "#243044"

            Text {
                anchors.centerIn: parent
                text: "›"
                color: "#c9d2e0"
                font.family: "Sora"
                font.pixelSize: 20
            }

            MouseArea {
                id: nextArea
                anchors.fill: parent
                enabled: canNext
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.changeYear(1)
            }
        }
    }

    component ReviewBanner: Rectangle {
        radius: 16
        border.width: 1
        border.color: "#2b3b55"
        clip: true

        gradient: Gradient {
            GradientStop { position: 0.0; color: "#17263c" }
            GradientStop { position: 1.0; color: "#101827" }
        }

        Rectangle {
            width: 4
            height: 26
            radius: 2
            x: 14
            anchors.verticalCenter: parent.verticalCenter
            color: "#ff8c42"
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 28
            anchors.rightMargin: 10
            spacing: 10

            Text {
                Layout.fillWidth: true
                text: Tr.strings["Your %1 so far, in review"].arg(root.selectedYear)
                color: "#e8edf5"
                font.family: "Sora"
                font.pixelSize: 11
                font.bold: true
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            Rectangle {
                width: 92
                height: 30
                radius: 15
                color: watchArea.containsMouse ? Qt.lighter("#4cc9f0", 1.08) : "#4cc9f0"

                Row {
                    anchors.centerIn: parent
                    spacing: 7

                    Canvas {
                        width: 12
                        height: 12
                        anchors.verticalCenter: parent.verticalCenter
                        property bool playing: root.reviewing
                        onPlayingChanged: requestPaint()

                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.reset();
                            ctx.fillStyle = "#08131a";
                            if (root.reviewing) {
                                ctx.fillRect(1, 1, 3, 10);
                                ctx.fillRect(8, 1, 3, 10);
                            } else {
                                ctx.beginPath();
                                ctx.moveTo(1, 0);
                                ctx.lineTo(12, 6);
                                ctx.lineTo(1, 12);
                                ctx.closePath();
                                ctx.fill();
                            }
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: Tr.strings["Watch"]
                        color: "#08131a"
                        font.family: "Sora"
                        font.pixelSize: 10
                        font.bold: true
                    }
                }

                MouseArea {
                    id: watchArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.toggleReview()
                }
            }
        }
    }

    component MonthCard: Rectangle {
        id: card
        property var month: ({})
        property int monthIndex: 0
        property bool active: false

        radius: 20
        color: "#101827"
        border.width: 1
        border.color: active
                      ? "#3b82f6"
                      : (cardHover.hovered ? "#334155" : "#243044")

        gradient: Gradient {
            GradientStop { position: 0.0; color: "#141c2b" }
            GradientStop { position: 1.0; color: "#0d131e" }
        }

        HoverHandler { id: cardHover }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Text {
                    text: card.month.number || ""
                    color: Library.accent
                    font.family: "Chakra Petch"
                    font.pixelSize: 11
                    font.bold: true
                    font.letterSpacing: 1.6
                }

                Text {
                    text: card.month.name || ""
                    color: "#f2f5fa"
                    font.family: "Sora"
                    font.pixelSize: 18
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    width: 100
                    height: 28
                    radius: 8
                    color: openArea.containsMouse ? "#1e2c42" : "#121a27"
                    border.width: 1
                    border.color: openArea.containsMouse
                                  ? Library.accent
                                  : "#2a3a52"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings["Open month"]
                        color: openArea.containsMouse
                               ? Library.accent
                               : "#c9d2e0"
                        font.family: "Sora"
                        font.pixelSize: 9
                    }

                    MouseArea {
                        id: openArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.openMonth(card.monthIndex)
                    }
                }
            }

            Text {
                text: card.month.hoursText || "0m"
                color: "#f8fafc"
                font.family: "Sora"
                font.pixelSize: 30
                font.bold: true
                font.letterSpacing: -0.8
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Column {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: Tr.strings["Days played"]
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 8
                    }

                    Text {
                        text: card.month.daysPlayed || 0
                        color: "#dfe6f0"
                        font.family: "Chakra Petch"
                        font.pixelSize: 12
                    }
                }

                Column {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: Tr.strings["Best day"]
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 8
                    }

                    Text {
                        text: card.month.bestDayText || "—"
                        color: "#dfe6f0"
                        font.family: "Chakra Petch"
                        font.pixelSize: 12
                    }

                    Text {
                        text: root.formatDay(card.month.bestDayTimestamp)
                        color: "#64748b"
                        font.family: "Sora"
                        font.pixelSize: 8
                    }
                }

                Column {
                    Layout.fillWidth: true
                    spacing: 2

                    Text {
                        text: Tr.strings["Sessions"]
                        color: "#6f7887"
                        font.family: "Sora"
                        font.pixelSize: 8
                    }

                    Text {
                        text: card.month.sessionsCount || 0
                        color: "#dfe6f0"
                        font.family: "Chakra Petch"
                        font.pixelSize: 12
                    }
                }
            }

            Column {
                Layout.fillWidth: true
                spacing: 8

                Repeater {
                    model: card.month.topGames || []

                    delegate: Column {
                        width: parent.width
                        spacing: 3

                        RowLayout {
                            width: parent.width
                            spacing: 8

                            Text {
                                Layout.fillWidth: true
                                text: modelData.name
                                color: "#cfd6e2"
                                font.family: "Sora"
                                font.pixelSize: 10
                                elide: Text.ElideRight
                            }

                            Text {
                                text: modelData.hoursText
                                color: "#8b95a5"
                                font.family: "Chakra Petch"
                                font.pixelSize: 9
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 4
                            radius: 2
                            color: "#1e293b"

                            Rectangle {
                                width: parent.width * (modelData.percent / 100)
                                height: parent.height
                                radius: 2
                                color: modelData.color
                            }
                        }
                    }
                }

                Text {
                    visible: (card.month.topGames || []).length === 0
                    text: Tr.strings["No playtime in this period."]
                    color: "#5f6a7b"
                    font.family: "Sora"
                    font.pixelSize: 9
                }
            }

            Item { Layout.fillHeight: true }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 6

                Text {
                    text: Tr.strings["Day by day"]
                    color: "#6f7887"
                    font.family: "Sora"
                    font.pixelSize: 8
                }

                Row {
                    Layout.fillWidth: true
                    height: 32
                    spacing: 2

                    Repeater {
                        model: card.month.daily || []

                        Item {
                            width: 7
                            height: 32

                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: Math.max(
                                    2,
                                    28 * ((modelData || 0)
                                          / (card.month.maxDaily || 1))
                                )
                                radius: 1.5
                                color: index === 0
                                       ? Library.accent
                                       : "#4cc9f0"
                                opacity: 0.35 + 0.65 * (modelData
                                             / (card.month.maxDaily || 1))
                            }
                        }
                    }
                }
            }
        }
    }
}
