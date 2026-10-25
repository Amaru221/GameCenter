import QtQuick
import QtQuick3D

Item {
    id: root
    objectName: "ds3d"
    property string textureUrl: ""
    property real yaw: -16
    property real pitch: -10

    // Real DS game cards are almost square but slightly taller and thin, with
    // three pointed corners and a rounded bottom-left corner.
    readonly property real bodyWidth: 1.0
    readonly property real bodyHeight: 1.06
    readonly property real bodyDepth: 0.075
    readonly property real cornerRadius: 0.09
    property color cartridgeColor: Library.cartridgeColor

    signal playRequested()

    View3D {
        anchors.fill: parent

        environment: SceneEnvironment {
            clearColor: "transparent"
            backgroundMode: SceneEnvironment.Transparent
            antialiasingMode: SceneEnvironment.MSAA
            antialiasingQuality: SceneEnvironment.High
        }

        camera: camera

        PerspectiveCamera {
            id: camera
            position: Qt.vector3d(0, 0, 2.2)
            fieldOfView: 34
            clipNear: 0.05
            clipFar: 50
        }

        DirectionalLight {
            eulerRotation.x: -28
            eulerRotation.y: -24
            brightness: 1.15
        }

        DirectionalLight {
            eulerRotation.x: 18
            eulerRotation.y: 155
            brightness: 0.45
        }

        Node {
            id: cartridge
            eulerRotation.x: root.pitch
            eulerRotation.y: root.yaw

            // Main slab, down to the tangent of the rounded corner.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(
                    root.bodyWidth / 100,
                    (root.bodyHeight - root.cornerRadius) / 100,
                    root.bodyDepth / 100
                )
                position: Qt.vector3d(0, root.cornerRadius / 2, 0)
                materials: [plastic]
            }
            // Bottom strip, from the rounded corner to the right edge.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(
                    (root.bodyWidth - root.cornerRadius) / 100,
                    root.cornerRadius / 100,
                    root.bodyDepth / 100
                )
                position: Qt.vector3d(
                    root.cornerRadius / 2,
                    -root.bodyHeight / 2 + root.cornerRadius / 2,
                    0
                )
                materials: [plastic]
            }
            // Rounded bottom-left corner, tangent to both slabs.
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(
                    root.cornerRadius * 2 / 100,
                    root.bodyDepth / 100,
                    root.cornerRadius * 2 / 100
                )
                position: Qt.vector3d(
                    -root.bodyWidth / 2 + root.cornerRadius,
                    -root.bodyHeight / 2 + root.cornerRadius,
                    0
                )
                eulerRotation.x: 90
                materials: [plastic]
            }

            // Front label (the same art, store strip and meta strip as the 2D card).
            Model {
                source: "#Rectangle"
                scale: Qt.vector3d(0.0086, 0.0094, 0.01)
                position: Qt.vector3d(0, 0, root.bodyDepth / 2 + 0.001)
                materials: [label]
            }

            // Notch slot near the top edge.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0020, 0.00014, 0.00002)
                position: Qt.vector3d(0, 0.505, root.bodyDepth / 2 + 0.001)
                materials: [dark]
            }

            // Five metallic contacts on the back.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00002)
                position: Qt.vector3d(-0.28, -0.36, -(root.bodyDepth / 2 + 0.001))
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00002)
                position: Qt.vector3d(-0.14, -0.36, -(root.bodyDepth / 2 + 0.001))
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00002)
                position: Qt.vector3d(0, -0.36, -(root.bodyDepth / 2 + 0.001))
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00002)
                position: Qt.vector3d(0.14, -0.36, -(root.bodyDepth / 2 + 0.001))
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00002)
                position: Qt.vector3d(0.28, -0.36, -(root.bodyDepth / 2 + 0.001))
                materials: [gold]
            }

            // Screw on the back.
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(0.00045, 0.00002, 0.00045)
                position: Qt.vector3d(0, 0.36, -(root.bodyDepth / 2 + 0.001))
                eulerRotation.x: 90
                materials: [dark]
            }
        }
    }

    PrincipledMaterial {
        id: plastic
        baseColor: root.cartridgeColor
        roughness: 0.55
        metalness: 0.05
        cullMode: Material.NoCulling
    }

    PrincipledMaterial {
        id: label
        baseColorMap: Texture {
            source: root.textureUrl
        }
        roughness: 0.45
        cullMode: Material.NoCulling
    }

    PrincipledMaterial {
        id: gold
        baseColor: "#e2b54a"
        metalness: 0.35
        roughness: 0.35
    }

    PrincipledMaterial {
        id: dark
        baseColor: "#0b0d10"
        roughness: 0.7
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: dragging ? Qt.ClosedHandCursor : Qt.OpenHandCursor

        property real lastX: 0
        property real lastY: 0
        property bool dragging: false

        onPressed: (mouse) => {
            lastX = mouse.x;
            lastY = mouse.y;
            dragging = true;
        }
        onPositionChanged: (mouse) => {
            if (!dragging) {
                return;
            }
            root.yaw += (mouse.x - lastX) * 0.55;
            root.pitch = Math.max(-50, Math.min(50, root.pitch - (mouse.y - lastY) * 0.4));
            lastX = mouse.x;
            lastY = mouse.y;
        }
        onReleased: dragging = false
        onDoubleClicked: root.playRequested()
    }
}
