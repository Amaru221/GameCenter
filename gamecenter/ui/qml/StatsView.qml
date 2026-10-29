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
    property string currentView: "stats"
    signal reviewRequested(int year)
    signal viewRequested(string view)

    readonly property bool narrow: width < 1080
    // The header row needs a little more room than the rest of the view: with
    // the period tabs, the view switch, the year and the 340 px review banner
    // the full row only fits above this width.
    readonly property bool compactHeader: width < 1170
    // Newest bucket first: months, weeks or days depending on the period.
    readonly property var months: {
        var list = (statsData.buckets || statsData.months || []).slice();
        list.reverse();
        return list;
    }
    readonly property string bucketsKind: statsData.bucketsKind || "month"
    readonly property bool canOpenBucket: bucketsKind === "month"
    readonly property var river: statsData.river || ({})
    readonly property var topGame: statsData.topGame || ({})
    readonly property var highlights: statsData.highlights || []

    function refresh() {
        statsData = Library.stats(
            period,
            selectedYear,
            period === "month" ? selectedMonth : -1
        );
    }

    function focusStart() {
        Qt.callLater(function() {
            if (carousel.count > 0) {
                carousel.currentIndex = 0;
                carousel.positionViewAtIndex(0, ListView.Beginning);
            }
        });
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
        focusStart();
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
        page.contentY = 0;
        focusStart();
    }

    function openMonth(index) {
        period = "month";
        selectedMonth = index;
        refresh();
        page.contentY = 0;
        focusStart();
    }

    function formatDay(timestamp) {
        if (!timestamp) {
            return "";
        }
        return Qt.formatDateTime(new Date(timestamp * 1000), "dd/MM");
    }

    function durationText(seconds) {
        var total = Math.max(0, Number(seconds) || 0);
        if (total <= 0) {
            return "0 min";
        }
        var minutes = Math.max(1, Math.round(total / 60));
        if (minutes < 60) {
            return minutes + " min";
        }
        var hours = Math.floor(minutes / 60);
        var rest = minutes % 60;
        return rest > 0 ? hours + " h " + rest + " min" : hours + " h";
    }

    function changeColor(text) {
        return (text || "").indexOf("-") === 0 ? "#fb7185" : "#34d399";
    }

    function bucketTitle() {
        if (bucketsKind === "day") {
            return Tr.strings["Day by Day"];
        }
        if (bucketsKind === "week") {
            return Tr.strings["Week by Week"];
        }
        return Tr.strings["Month by Month"];
    }

    function tintColor(hex, alpha) {
        var value = String(hex || "#facc15");
        if (value.length !== 7) {
            return Qt.rgba(0.98, 0.8, 0.08, alpha);
        }
        return Qt.rgba(
            parseInt(value.substring(1, 3), 16) / 255,
            parseInt(value.substring(3, 5), 16) / 255,
            parseInt(value.substring(5, 7), 16) / 255,
            alpha
        );
    }

    function reviewText() {
        return Tr.strings["Your %1 in review"].arg(selectedYear);
    }

    function riverSubtitle() {
        // All time keeps the annual month breakdown, so name the year here.
        var label = period === "all"
                    ? selectedYear
                    : (statsData.periodLabel || selectedYear);
        return Tr.strings["%1 as a river"].arg(label);
    }

    onVisibleChanged: {
        if (visible) {
            refresh();
            focusStart();
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
                    spacing: 10

                    PeriodTabs {}

                    Item { Layout.fillWidth: true }

                    ViewTabs {}

                    YearPicker {}

                    ReviewBanner {
                        objectName: "statsReviewBanner"
                        visible: !root.compactHeader
                        Layout.preferredWidth: 340
                        Layout.preferredHeight: 54
                    }
                }

                ReviewBanner {
                    visible: root.compactHeader
                    Layout.fillWidth: true
                    Layout.preferredHeight: 54
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 286
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
                    objectName: "statsYearWatermark"
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

                // The most played game lives inside the time-played block, next
                // to the hours, so it never covers the year watermark.
                ColumnLayout {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
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
                        color: "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 0.3
                    }

                    Rectangle {
                        id: topGamePanel
                        objectName: "topGamePanel"
                        visible: root.topGame
                                 && (root.topGame.name || "") !== ""
                        Layout.preferredWidth: root.narrow ? 240 : 300
                        Layout.preferredHeight: 84
                        radius: 14
                        color: "#0b111b"
                        border.width: 1
                        border.color: "#26374d"
                        clip: true

                        Rectangle {
                            anchors.fill: parent
                            radius: 14
                            gradient: Gradient {
                                GradientStop {
                                    position: 0.0
                                    color: Qt.rgba(
                                        Library.accent.r,
                                        Library.accent.g,
                                        Library.accent.b,
                                        0.10
                                    )
                                }
                                GradientStop { position: 1.0; color: "#0b111b" }
                            }
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10

                            Item {
                                Layout.preferredWidth: 44
                                Layout.preferredHeight: 62

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 7
                                    color: "#070a10"
                                    border.width: 1
                                    border.color: "#2b3b53"
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 2
                                    radius: 5
                                    color: "#182234"
                                    clip: true

                                    Image {
                                        anchors.fill: parent
                                        source: root.topGame.cover || ""
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                        cache: true
                                    }
                                }
                            }

                            ColumnLayout {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                spacing: 2

                                Text {
                                    text: Tr.strings["Most played"]
                                    color: Library.accent
                                    font.family: "Chakra Petch"
                                    font.pixelSize: 8
                                    font.bold: true
                                    font.letterSpacing: 1.2
                                }

                                Text {
                                    Layout.fillWidth: true
                                    text: root.topGame.name || ""
                                    color: "#f2f5fa"
                                    font.family: "Sora"
                                    font.pixelSize: 13
                                    font.bold: true
                                    wrapMode: Text.WordWrap
                                    maximumLineCount: 2
                                    elide: Text.ElideRight
                                }

                                Item { Layout.fillHeight: true }

                                Row {
                                    spacing: 8

                                    Text {
                                        text: root.topGame.hoursText || ""
                                        color: "#facc15"
                                        font.family: "Sora"
                                        font.pixelSize: 12
                                        font.bold: true
                                    }

                                    Text {
                                        text: root.statsData.periodLabel || ""
                                        color: "#7d8798"
                                        font.family: "Sora"
                                        font.pixelSize: 8
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }
                        }
                    }

                    Flow {
                        Layout.fillWidth: true
                        Layout.topMargin: 10
                        spacing: 8

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

                            StatChip {
                                label: modelData.text
                                tint: modelData.color
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

            // Period highlights: longest session, busiest day/month, average
            // and favourite weekday. They are recomputed on every refresh.
            RowLayout {
                objectName: "statsHighlights"
                Layout.fillWidth: true
                visible: root.highlights.length > 0
                spacing: 12

                Repeater {
                    model: root.highlights

                    delegate: HighlightTile {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 76
                        item: modelData
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                ColumnLayout {
                    spacing: 2

                    Text {
                        text: root.bucketTitle()
                        color: "#f2f5fa"
                        font.family: "Chakra Petch"
                        font.pixelSize: 13
                        font.bold: true
                        font.letterSpacing: 2.0
                    }

                    Text {
                        text: root.riverSubtitle()
                        color: "#7d8798"
                        font.family: "Sora"
                        font.pixelSize: 10
                        font.letterSpacing: 0.2
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
                id: chartCard
                objectName: "riverChartCard"
                Layout.fillWidth: true
                Layout.preferredHeight: 246
                radius: 20
                color: "#0e1522"
                border.width: 1
                border.color: hoverIndex >= 0 ? "#33507a" : "#202b3d"
                clip: true

                property int hoverIndex: -1
                property real hoverX: 0

                readonly property var hoverInfo: {
                    var info = { total: 0, rows: [], extra: 0, label: "" };
                    var labels = (root.river && root.river.labels)
                                 ? root.river.labels : [];
                    var layers = (root.river && root.river.layers)
                                 ? root.river.layers : [];
                    var index = hoverIndex;
                    if (index < 0 || index >= labels.length) {
                        return info;
                    }
                    info.label = labels[index];
                    var rows = [];
                    for (var i = 0; i < layers.length; i++) {
                        var value = layers[i].values[index] || 0;
                        info.total += value;
                        if (value > 0) {
                            rows.push({
                                name: layers[i].name,
                                color: layers[i].color,
                                value: value
                            });
                        }
                    }
                    rows.sort(function(a, b) { return b.value - a.value; });
                    info.extra = Math.max(0, rows.length - 4);
                    info.rows = rows.slice(0, 4);
                    return info;
                }

                function indexAt(x) {
                    var labels = (root.river && root.river.labels)
                                 ? root.river.labels : [];
                    var count = labels.length;
                    if (count === 0) {
                        return -1;
                    }
                    var plotWidth = Math.max(1, riverChart.width - 16);
                    var ratio = (x - 8) / plotWidth;
                    return Math.max(
                        0,
                        Math.min(count - 1, Math.round(ratio * (count - 1)))
                    );
                }

                Canvas {
                    id: riverChart
                    anchors.fill: parent
                    anchors.margins: 14

                    property var riverData: root.river
                    property var layers: (riverData && riverData.layers)
                                         ? riverData.layers : []
                    property var labels: (riverData && riverData.labels)
                                         ? riverData.labels
                                         : ((riverData && riverData.months)
                                            ? riverData.months : [])
                    property int hover: chartCard.hoverIndex

                    onRiverDataChanged: requestPaint()
                    onLayersChanged: requestPaint()
                    onLabelsChanged: requestPaint()
                    onHoverChanged: requestPaint()
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
                            ctx.fillStyle = label === hover
                                            ? "#dfe6f0" : "#64748b";
                            ctx.fillText(labels[label], px(label), h - 5);
                        }

                        // Hover guide: a dashed vertical line plus a dot on
                        // every stack boundary, so the tooltip has context.
                        if (hover >= 0 && hover < count) {
                            var hx = px(hover);
                            ctx.save();
                            ctx.strokeStyle = "rgba(166, 190, 220, 0.35)";
                            ctx.lineWidth = 1;
                            ctx.setLineDash([3, 4]);
                            ctx.beginPath();
                            ctx.moveTo(hx, top - 6);
                            ctx.lineTo(hx, h - bottom + 6);
                            ctx.stroke();
                            ctx.restore();

                            var acc = 0;
                            for (var li = 0; li < layers.length; li++) {
                                acc += (layers[li].values[hover] || 0);
                                var dy = py(acc);
                                ctx.beginPath();
                                ctx.arc(hx, dy, 3.4, 0, Math.PI * 2);
                                ctx.fillStyle = layers[li].color;
                                ctx.fill();
                                ctx.lineWidth = 1.6;
                                ctx.strokeStyle = "#0e1522";
                                ctx.stroke();
                            }
                        }
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    anchors.margins: 14
                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton
                    cursorShape: Qt.CrossCursor

                    onPositionChanged: (mouse) => {
                        chartCard.hoverX = mouse.x + 14;
                        chartCard.hoverIndex = chartCard.indexAt(mouse.x);
                    }
                    onExited: chartCard.hoverIndex = -1
                }

                Rectangle {
                    id: chartTip
                    objectName: "riverTooltip"
                    visible: chartCard.hoverIndex >= 0
                    width: 238
                    height: tipColumn.implicitHeight + 20
                    radius: 12
                    x: Math.max(
                        10,
                        Math.min(chartCard.width - width - 10,
                                 chartCard.hoverX - width / 2)
                    )
                    y: 10
                    color: "#111a2a"
                    border.width: 1
                    border.color: "#31445f"
                    opacity: visible ? 1 : 0
                    Behavior on opacity { NumberAnimation { duration: 110 } }

                    Column {
                        id: tipColumn
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 6

                        Row {
                            width: parent.width

                            Text {
                                text: chartCard.hoverInfo.label
                                color: Library.accent
                                font.family: "Chakra Petch"
                                font.pixelSize: 11
                                font.bold: true
                                font.letterSpacing: 1.4
                            }

                            Item { width: parent.width - 96; height: 1 }

                            Text {
                                text: root.durationText(chartCard.hoverInfo.total)
                                color: "#f8fafc"
                                font.family: "Chakra Petch"
                                font.pixelSize: 11
                                font.bold: true
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: "#243349"
                        }

                        Repeater {
                            model: chartCard.hoverInfo.rows

                            Item {
                                width: tipColumn.width
                                height: 15

                                Rectangle {
                                    width: 7
                                    height: 7
                                    radius: 3.5
                                    color: modelData.color
                                    anchors.verticalCenter: parent.verticalCenter
                                }

                                Text {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 14
                                    anchors.right: tipValue.left
                                    anchors.rightMargin: 8
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: modelData.name
                                    color: "#b7c2d2"
                                    font.family: "Sora"
                                    font.pixelSize: 10
                                    elide: Text.ElideRight
                                }

                                Text {
                                    id: tipValue
                                    anchors.right: parent.right
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: root.durationText(modelData.value)
                                    color: "#8fa3bd"
                                    font.family: "Chakra Petch"
                                    font.pixelSize: 9
                                }
                            }
                        }

                        Text {
                            visible: chartCard.hoverInfo.extra > 0
                            text: "+" + chartCard.hoverInfo.extra
                            color: "#6f7887"
                            font.family: "Chakra Petch"
                            font.pixelSize: 9
                        }
                    }
                }
            }

            ListView {
                id: carousel
                objectName: "monthCarousel"
                Layout.fillWidth: true
                Layout.preferredHeight: 540
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
        objectName: "statsPeriodTabs"
        width: 340
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
        objectName: "statsYearPicker"
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
                text: root.reviewText()
                color: "#e8edf5"
                font.family: "Sora"
                font.pixelSize: 11
                font.bold: true
                wrapMode: Text.WordWrap
                maximumLineCount: 2
                elide: Text.ElideRight
            }

            Rectangle {
                width: 112
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

                        onPaint: {
                            var ctx = getContext("2d");
                            ctx.reset();
                            ctx.fillStyle = "#08131a";
                            ctx.beginPath();
                            ctx.moveTo(1, 0);
                            ctx.lineTo(12, 6);
                            ctx.lineTo(1, 12);
                            ctx.closePath();
                            ctx.fill();
                        }
                    }

                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: Tr.strings["Review year"]
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
                    onClicked: root.reviewRequested(root.selectedYear)
                }
            }
        }
    }

    component StatChip: Rectangle {
        id: chip
        property string label: ""
        property color tint: "#c9d2e0"

        height: 24
        width: chipRow.implicitWidth + 18
        radius: 12
        color: Qt.rgba(chip.tint.r, chip.tint.g, chip.tint.b, 0.10)
        border.width: 1
        border.color: Qt.rgba(chip.tint.r, chip.tint.g, chip.tint.b, 0.28)

        Row {
            id: chipRow
            anchors.centerIn: parent
            spacing: 6

            Rectangle {
                width: 5
                height: 5
                radius: 2.5
                color: chip.tint
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: chip.label
                color: Qt.lighter(chip.tint, 1.12)
                font.family: "Sora"
                font.pixelSize: 10
                font.bold: true
                font.letterSpacing: 0.2
            }
        }
    }

    component HighlightPill: Rectangle {
        id: pill
        property string valueText: ""
        property color tint: "#facc15"
        property int valueSize: 12
        property bool large: false

        height: pill.large ? 42 : 22
        width: pillRow.implicitWidth + (pill.large ? 28 : 18)
        radius: height / 2
        color: "#0f1622"
        border.width: 1
        border.color: Qt.rgba(pill.tint.r, pill.tint.g, pill.tint.b, 0.56)

        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: Qt.rgba(pill.tint.r, pill.tint.g, pill.tint.b, 0.22)
            }
            GradientStop { position: 1.0; color: "#0d131e" }
        }

        Rectangle {
            anchors.fill: parent
            anchors.margins: -3
            radius: parent.radius + 3
            color: "transparent"
            border.width: 1
            border.color: Qt.rgba(pill.tint.r, pill.tint.g, pill.tint.b, 0.16)
        }

        Row {
            id: pillRow
            anchors.centerIn: parent
            spacing: pill.large ? 8 : 5

            Rectangle {
                width: pill.large ? 7 : 5
                height: pill.large ? 7 : 5
                radius: 1
                rotation: 45
                color: pill.tint
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: pill.valueText
                color: Qt.lighter(pill.tint, 1.16)
                font.family: "Sora"
                font.pixelSize: pill.valueSize
                font.bold: true
                font.letterSpacing: pill.large ? -0.6 : 0
            }
        }
    }

    component MonthCard: Rectangle {
        id: card
        objectName: "monthCard"
        property var month: ({})
        property int monthIndex: 0
        property bool active: false

        readonly property var topGames: month.topGames || []
        readonly property var banner: month.banner || ({})
        readonly property string kind: month.kind || "month"
        readonly property bool hasData: (month.sessionsCount || 0) > 0

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
            spacing: 10

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
                    font.pixelSize: card.kind === "month" ? 18 : 16
                    font.bold: true
                    elide: Text.ElideRight
                }

                // Cover of the most played game of the bucket.
                Item {
                    id: mostPlayedCover
                    objectName: "monthPlayedCover"
                    visible: !!(card.month.mostPlayed
                                && card.month.mostPlayed.cover)
                    Layout.preferredWidth: 26
                    Layout.preferredHeight: 34
                    Layout.leftMargin: 2

                    Rectangle {
                        anchors.fill: parent
                        radius: 6
                        color: "#0a1019"
                        border.width: 1
                        border.color: "#2c3b52"
                    }

                    Rectangle {
                        anchors.fill: parent
                        anchors.margins: 2
                        radius: 4
                        color: "#182234"
                        clip: true

                        Image {
                            anchors.fill: parent
                            source: card.month.mostPlayed
                                    ? (card.month.mostPlayed.cover || "")
                                    : ""
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                            cache: true
                        }
                    }

                    HoverHandler { id: coverHover }

                    ToolTip.visible: coverHover.hovered
                    ToolTip.delay: 250
                    ToolTip.text: Tr.strings["Most played game"] + ": "
                                  + (card.month.mostPlayedName || "")
                                  + (card.month.mostPlayedHours
                                     ? " · " + card.month.mostPlayedHours
                                     : "")
                }

                Item { Layout.fillWidth: true }

                Rectangle {
                    visible: root.canOpenBucket && card.kind === "month"
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

            // Diamond + number in the same container, in the value position.
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 44

                HighlightPill {
                    objectName: "topHoursPill"
                    visible: card.month.topHours === true
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    large: true
                    valueText: card.month.hoursText || "0m"
                    tint: "#facc15"
                    valueSize: 28
                }

                Text {
                    visible: card.month.topHours !== true
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: card.month.hoursText || "0m"
                    color: "#f8fafc"
                    font.family: "Sora"
                    font.pixelSize: 30
                    font.bold: true
                    font.letterSpacing: -0.8
                }
            }

            // One unique highlight for this card.
            Rectangle {
                objectName: "cardBanner"
                visible: (card.banner.label || "") !== "" && card.hasData
                Layout.fillWidth: true
                Layout.preferredHeight: visible ? 44 : 0
                radius: 11
                color: root.tintColor(card.banner.tint, 0.10)
                border.width: 1
                border.color: root.tintColor(card.banner.tint, 0.38)

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 12
                    spacing: 9

                    Rectangle {
                        width: 3
                        height: parent.height - 16
                        radius: 1.5
                        color: card.banner.tint || "#facc15"
                    }

                    Column {
                        Layout.fillWidth: true
                        spacing: 1

                        Text {
                            text: card.banner.label || ""
                            color: card.banner.tint || "#facc15"
                            font.family: "Chakra Petch"
                            font.pixelSize: 9
                            font.bold: true
                            font.letterSpacing: 0.9
                        }

                        Text {
                            text: card.banner.value || ""
                            color: "#f2f5fa"
                            font.family: "Sora"
                            font.pixelSize: 14
                            font.bold: true
                        }
                    }

                    Text {
                        text: card.banner.detail || ""
                        color: "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 9
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                MetricColumn {
                    Layout.fillWidth: true
                    label: Tr.strings["Days played"]
                    value: String(card.month.daysPlayed || 0)
                    highlighted: card.month.topDays === true
                    pillObjectName: "topDaysPill"
                    tint: "#34d399"
                }

                MetricColumn {
                    Layout.fillWidth: true
                    label: Tr.strings["Playtime"]
                    value: card.month.bestDayText || "—"
                    detail: root.formatDay(card.month.bestDayTimestamp)
                }

                MetricColumn {
                    Layout.fillWidth: true
                    label: Tr.strings["Sessions"]
                    value: String(card.month.sessionsCount || 0)
                    highlighted: card.month.topSessions === true
                    pillObjectName: "topSessionsPill"
                    tint: "#a78bfa"
                }
            }

            RowLayout {
                objectName: "cardHighlights"
                Layout.fillWidth: true
                visible: (card.month.highlights || []).length > 0
                spacing: 10

                Repeater {
                    model: card.month.highlights || []

                    delegate: MiniStat {
                        Layout.fillWidth: true
                        item: modelData
                    }
                }
            }

            Column {
                Layout.fillWidth: true
                spacing: 7

                Repeater {
                    model: card.topGames

                    delegate: Column {
                        width: parent.width
                        spacing: 3

                        RowLayout {
                            width: parent.width
                            spacing: 7

                            Text {
                                Layout.preferredWidth: 18
                                text: (index + 1 < 10 ? "0" : "") + (index + 1)
                                color: "#64748b"
                                font.family: "Chakra Petch"
                                font.pixelSize: 10
                                font.bold: true
                            }

                            Item {
                                Layout.preferredWidth: 20
                                Layout.preferredHeight: 26

                                Rectangle {
                                    anchors.fill: parent
                                    radius: 4
                                    color: "#0a1019"
                                    border.width: 1
                                    border.color: "#2a3a52"
                                }

                                Rectangle {
                                    anchors.fill: parent
                                    anchors.margins: 1.5
                                    radius: 3
                                    color: "#182234"
                                    clip: true

                                    Image {
                                        anchors.fill: parent
                                        source: modelData.cover || ""
                                        fillMode: Image.PreserveAspectCrop
                                        asynchronous: true
                                        cache: true
                                    }
                                }
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

                        Rectangle {
                            x: 25
                            width: parent.width - 25
                            height: 3
                            radius: 1.5
                            color: "#1e293b"

                            Rectangle {
                                width: parent.width * (modelData.percent / 100)
                                height: parent.height
                                radius: 1.5
                                color: modelData.color
                            }
                        }
                    }
                }

                RowLayout {
                    visible: card.month.hasOtherGames === true
                    width: parent.width
                    spacing: 7

                    Text {
                        Layout.preferredWidth: 18
                        text: "—"
                        color: "#64748b"
                        font.family: "Chakra Petch"
                        font.pixelSize: 10
                        font.bold: true
                    }

                    Text {
                        Layout.fillWidth: true
                        text: card.month.otherGamesText || Tr.strings["Other games"]
                        color: "#8b95a5"
                        font.family: "Sora"
                        font.pixelSize: 10
                        font.italic: true
                        elide: Text.ElideRight
                    }

                    Text {
                        text: card.month.otherHoursText || ""
                        color: "#cfd6e2"
                        font.family: "Sora"
                        font.pixelSize: 10
                        font.bold: true
                    }
                }

                Text {
                    visible: !card.hasData
                    text: Tr.strings["No playtime in this period."]
                    color: "#5f6a7b"
                    font.family: "Sora"
                    font.pixelSize: 9
                }
            }

            Item { Layout.fillHeight: true }

            ColumnLayout {
                visible: card.kind !== "day"
                Layout.fillWidth: true
                spacing: 5

                Text {
                    text: Tr.strings["Day by day"]
                    color: "#7d8798"
                    font.family: "Sora"
                    font.pixelSize: 9
                    font.letterSpacing: 0.35
                }

                Row {
                    id: dayChart
                    Layout.fillWidth: true
                    height: 30
                    spacing: 2

                    readonly property int barCount: (card.month.daily || []).length
                    readonly property real barWidth: barCount > 0
                                                     ? Math.min(
                                                           10,
                                                           Math.max(
                                                               2,
                                                               (width - (barCount - 1) * 2)
                                                               / barCount
                                                           )
                                                       )
                                                     : 4

                    Repeater {
                        model: card.month.daily || []

                        Item {
                            width: dayChart.barWidth
                            height: 30

                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: Math.max(
                                    2,
                                    26 * ((modelData || 0)
                                          / (card.month.maxDaily || 1))
                                )
                                radius: 1.5
                                color: index === dayChart.barCount - 1
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

    component ViewTabs: Rectangle {
        objectName: "statsViewTabs"
        width: 270
        height: 38
        radius: 19
        color: "#0d0f14"
        border.width: 1
        border.color: "#232833"

        Row {
            anchors.fill: parent
            anchors.margins: 4
            spacing: 2

            Repeater {
                model: [
                    { label: "LIBRARY", value: "library" },
                    { label: "STATS", value: "stats" },
                    { label: "STORE", value: "store" }
                ]

                delegate: Rectangle {
                    readonly property bool selected: root.currentView === modelData.value
                    width: (parent.width - 4) / 3
                    height: 30
                    radius: 15
                    color: selected ? "#232936" : "transparent"

                    Text {
                        anchors.centerIn: parent
                        text: Tr.strings[modelData.label]
                        color: selected ? "#f2f5fa" : "#7b8494"
                        font.family: "Chakra Petch"
                        font.pixelSize: 11
                        font.bold: true
                        font.letterSpacing: 1.4
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.viewRequested(modelData.value)
                    }
                }
            }
        }
    }

    component HighlightTile: Rectangle {
        id: tile
        property var item: ({})

        radius: 14
        color: root.tintColor(tile.item.tint, 0.08)
        border.width: 1
        border.color: root.tintColor(tile.item.tint, 0.28)

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 2

            Text {
                Layout.fillWidth: true
                text: tile.item.label || ""
                color: tile.item.tint || "#8b95a5"
                font.family: "Chakra Petch"
                font.pixelSize: 9
                font.bold: true
                font.letterSpacing: 0.9
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: tile.item.value || "—"
                color: "#f8fafc"
                font.family: "Sora"
                font.pixelSize: 18
                font.bold: true
                elide: Text.ElideRight
            }

            Text {
                Layout.fillWidth: true
                text: tile.item.detail || ""
                color: "#8b95a5"
                font.family: "Sora"
                font.pixelSize: 9
                elide: Text.ElideRight
            }
        }
    }

    component MetricColumn: Column {
        id: metric
        property string label: ""
        property string value: ""
        property string detail: ""
        property bool highlighted: false
        property string pillObjectName: ""
        property color tint: "#facc15"

        spacing: 2

        Text {
            text: metric.label
            color: "#7d8798"
            font.family: "Sora"
            font.pixelSize: 9
            font.letterSpacing: 0.35
        }

        Item {
            width: parent.width
            height: 22

            HighlightPill {
                objectName: metric.pillObjectName
                visible: metric.highlighted
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                valueText: metric.value
                tint: metric.tint
                valueSize: 12
            }

            Text {
                visible: !metric.highlighted
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: metric.value
                color: "#dfe6f0"
                font.family: "Sora"
                font.pixelSize: 13
                font.bold: true
            }
        }

        Text {
            text: metric.detail
            color: "#64748b"
            font.family: "Sora"
            font.pixelSize: 8
            height: 11
        }
    }

    component MiniStat: ColumnLayout {
        id: mini
        property var item: ({})

        spacing: 1

        Text {
            Layout.fillWidth: true
            text: mini.item.label || ""
            color: mini.item.tint || "#7d8798"
            font.family: "Chakra Petch"
            font.pixelSize: 8
            font.bold: true
            font.letterSpacing: 0.7
            elide: Text.ElideRight
        }

        Text {
            Layout.fillWidth: true
            text: mini.item.value || "—"
            color: "#f2f5fa"
            font.family: "Sora"
            font.pixelSize: 12
            font.bold: true
            elide: Text.ElideRight
        }

        Text {
            Layout.fillWidth: true
            text: mini.item.detail || ""
            color: "#64748b"
            font.family: "Sora"
            font.pixelSize: 8
            elide: Text.ElideRight
        }
    }
}
