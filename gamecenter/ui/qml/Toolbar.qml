import QtQuick
import QtQuick.Layouts

Item {
    id: root
    height: 54

    signal toastRequested(string message)

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 28
        anchors.rightMargin: 28
        spacing: 10

        Text {
            text: "ALL GAMES"
            color: "#e8edf5"
            font.family: "Chakra Petch"
            font.pixelSize: 14
            font.bold: true
            font.letterSpacing: 3
        }

        Text {
            text: Library.total === 1 ? "1 game" : Library.total + " games"
            color: "#8b95a5"
            font.family: "Sora"
            font.pixelSize: 12
            Layout.alignment: Qt.AlignVCenter
        }

        Item { Layout.fillWidth: true }

        PillCombo {
            id: sourceCombo
            Layout.preferredWidth: 150
            value: ""
            entries: {
                var out = [{ text: "All stores", value: "" }];
                for (var i = 0; i < Library.sources.length; i++) {
                    var s = Library.sources[i];
                    out.push({ text: s.charAt(0).toUpperCase() + s.slice(1), value: s });
                }
                return out;
            }
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
                onClicked: root.toastRequested("Adding games comes in v0.2")
            }
        }
    }
}
