import QtQuick
import QtQuick3D

Item {
    id: root
    objectName: "ds3d"
    property string textureUrl: ""
    property real yaw: -16
    property real pitch: -10

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

            // Solid rounded body: two slabs plus four corner cylinders.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0085, 0.0106, 0.0011)
                materials: [plastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.01, 0.0091, 0.0011)
                materials: [plastic]
            }
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(0.0015, 0.0011, 0.0015)
                position: Qt.vector3d(0.425, 0.455, 0)
                eulerRotation.x: 90
                materials: [plastic]
            }
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(0.0015, 0.0011, 0.0015)
                position: Qt.vector3d(-0.425, 0.455, 0)
                eulerRotation.x: 90
                materials: [plastic]
            }
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(0.0015, 0.0011, 0.0015)
                position: Qt.vector3d(0.425, -0.455, 0)
                eulerRotation.x: 90
                materials: [plastic]
            }
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(0.0015, 0.0011, 0.0015)
                position: Qt.vector3d(-0.425, -0.455, 0)
                eulerRotation.x: 90
                materials: [plastic]
            }

            // Front label (the same art, store strip and meta strip as the 2D card).
            Model {
                source: "#Rectangle"
                scale: Qt.vector3d(0.0078, 0.0086, 0.01)
                position: Qt.vector3d(0, 0, 0.057)
                materials: [label]
            }

            // Notch slot near the top edge.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0032, 0.00022, 0.00008)
                position: Qt.vector3d(0, 0.49, 0.058)
                materials: [dark]
            }

            // Five metallic contacts on the back.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00008)
                position: Qt.vector3d(-0.28, -0.36, -0.058)
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00008)
                position: Qt.vector3d(-0.14, -0.36, -0.058)
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00008)
                position: Qt.vector3d(0, -0.36, -0.058)
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00008)
                position: Qt.vector3d(0.14, -0.36, -0.058)
                materials: [gold]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.0006, 0.0018, 0.00008)
                position: Qt.vector3d(0.28, -0.36, -0.058)
                materials: [gold]
            }

            // Screw on the back.
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(0.00045, 0.0001, 0.00045)
                position: Qt.vector3d(0, 0.36, -0.058)
                eulerRotation.x: 90
                materials: [dark]
            }
        }
    }

    PrincipledMaterial {
        id: plastic
        baseColor: Library.cartridgeColor
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
