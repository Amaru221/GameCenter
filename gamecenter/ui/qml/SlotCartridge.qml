import QtQuick

// The cartridge resting in the dock slot while its game is running. The item is
// clipped at the dock edge so only the protruding top of the cartridge shows.
Item {
    id: root
    objectName: "slotCartridge"
    width: 100
    height: 44
    clip: true

    property var game: ({})
    readonly property real cardScale: 0.34

    readonly property bool active: !!(game && game.title)

    visible: opacity > 0
    opacity: active ? 1 : 0
    z: 19

    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

    Cartridge {
        width: 208
        height: 288
        x: (root.width - width) / 2
        y: -(height - height * root.cardScale) / 2
        scale: root.cardScale
        transformOrigin: Item.Center
        interactive: false
        showTitle: false
        style: Library.cartridgeStyle
        gameTitle: root.game.title || ""
        gameSource: root.game.source || ""
        gameMeta: root.game.meta || ""
        coverUrl: root.game.cover || ""
        gameInstalled: root.game.installed !== false
        cartridgeColor: root.game.cartridgeColor || Library.cartridgeColor
    }
}
