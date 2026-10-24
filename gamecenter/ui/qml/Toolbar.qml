import QtQuick
import QtQuick.Layouts

Item {
    id: root
    height: 54

    signal toastRequested(string message)
    signal addRequested()

    readonly property string heading: {
        if (Library.favoritesOnly) {
            return "FAVORITES";
        }
        var key = Library.sourceFilter;
        if (!key) {
            return "ALL GAMES";
        }
        var options = Library.sourceOptions;
        for (var i = 0; i < options.length; i++) {
            if (options[i].value === key) {
                return options[i].text.toUpperCase();
            }
        }
        return key === "local" ? "LOCAL" : key.toUpperCase();
    }

    readonly property var sourceEntries: {
        var out = [{ text: "All stores", value: "" }, { text: "Local", value: "local" }];
        var options = Library.sourceOptions;
        for (var i = 0; i < options.length; i++) {
            if (options[i].value !== "local") {
                out.push(options[i]);
            }
        }
        return out;
    }

    Connections {
        target: Library
        function onChanged() {
            if (sourceCombo.value !== Library.sourceFilter) {
                sourceCombo.value = Library.sourceFilter;
            }
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 28
        anchors.rightMargin: 28
        spacing: 10

        Text {
            text: root.heading
            color: "#e8edf5"
            font.family: "Chakra Petch"
            font.pixelSize: 14
            font.bold: true
            font.letterSpacing: 3
        }

        Text {
            text: Library.count === 1 ? "1 game" : Library.count + " games"
            color: "#8b95a5"
            font.family: "Sora"
            font.pixelSize: 12
            Layout.alignment: Qt.AlignVCenter
        }

        Item { Layout.fillWidth: true }

        PillCombo {
            id: sourceCombo
            Layout.preferredWidth: 150
            value: Library.sourceFilter
            entries: root.sourceEntries
            onSelected: (chosen) => Library.setSourceFilter(chosen)
        }

        PillCombo {
            id: sortCombo
            Layout.preferredWidth: 186
            value: Library.sortMode
            entries: [
                { text: "Recently Played", value: "recent" },
                { text: "Title", value: "title" },
                { text: "Size", value: "size" }
            ]
            onSelected: (chosen) => Library.setSort(chosen)
        }

        Rectangle {
            width: 34
            height: 34
            radius: 17
            color: Library.favoritesOnly ? "#2a2410" : "#0d0f14"
            border.width: 1
            border.color: Library.favoritesOnly ? "#ffd166" : "#232833"

            Text {
                anchors.centerIn: parent
                text: "★"
                color: Library.favoritesOnly ? "#ffd166" : "#8b95a5"
                font.pixelSize: 14
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: Library.setFavoritesOnly(!Library.favoritesOnly)
            }
        }

        Rectangle {
            width: 34
            height: 34
            radius: 17
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            Grid {
                anchors.centerIn: parent
                columns: 2
                spacing: 3
                Repeater {
                    model: 4
                    Rectangle {
                        width: 6
                        height: 6
                        radius: 1.5
                        color: "#c9d2e0"
                    }
                }
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {}
            }
        }

        Rectangle {
            width: 34
            height: 34
            radius: 17
            color: "#0d0f14"
            border.width: 1
            border.color: "#232833"

            Text {
                anchors.centerIn: parent
                text: "+"
                color: "#c9d2e0"
                font.family: "Sora"
                font.pixelSize: 18
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.addRequested()
            }
        }
    }
}
