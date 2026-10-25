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

    // The back 0.010 is a separate shell layer. That lets the contact pocket
    // sit two steps below the outer back surface instead of on top of it.
    readonly property real backLayer: 0.010
    readonly property real frontDepth: bodyDepth - backLayer
    readonly property real frontZ: backLayer / 2
    readonly property real backZ: -bodyDepth / 2 + backLayer / 2
    readonly property real backSurfaceZ: -bodyDepth / 2
    readonly property real levelOneZ: backSurfaceZ + 0.004
    readonly property real levelTwoZ: backSurfaceZ + 0.008
    readonly property real pocketFloorZ: backSurfaceZ + backLayer
    readonly property real innerRingZ: levelTwoZ - 0.001

    // Eighteen contacts. The two ends and the centre-most pad are slightly
    // longer, as on a real game card.
    readonly property int contactCount: 18
    readonly property real contactWidth: 0.028
    readonly property real contactGap: 0.014
    readonly property real contactStep: contactWidth + contactGap
    readonly property real contactStart: -((contactCount - 1) * contactStep) / 2
    readonly property real contactBottom: -0.520
    readonly property real contactShortHeight: 0.135
    readonly property real contactLongHeight: 0.150
    readonly property real contactDepth: 0.002
    readonly property real contactZ: levelTwoZ + contactDepth / 2
    readonly property real dividerZ: levelOneZ
    readonly property real dividerHeight: 0.190
    readonly property real dividerBottom: -0.530

    property color cartridgeColor: Library.cartridgeColor

    signal playRequested()

    function contactIsLong(index) {
        return index === 0 || index === 8 || index === contactCount - 1;
    }

    function contactHeight(index) {
        return contactIsLong(index) ? contactLongHeight : contactShortHeight;
    }

    function contactX(index) {
        return contactStart + index * contactStep;
    }

    function contactY(index) {
        return contactBottom + contactHeight(index) / 2;
    }

    function dividerX(index) {
        return contactStart + (index + 0.5) * contactStep;
    }

    function dividerY() {
        return dividerBottom + dividerHeight / 2;
    }

    // Small tangential boxes that give the back layer its rounded bottom-left
    // corner without a square step.
    readonly property int arcSegments: 5

    function arcAngle(index) {
        return Math.PI + (index + 0.5) * (Math.PI / 2) / arcSegments;
    }

    function arcX(index) {
        return -bodyWidth / 2 + cornerRadius + 0.080 * Math.cos(arcAngle(index));
    }

    function arcY(index) {
        return -bodyHeight / 2 + cornerRadius + 0.080 * Math.sin(arcAngle(index));
    }

    function arcRotation(index) {
        return arcAngle(index) * 180 / Math.PI + 90;
    }

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
            eulerRotation.x: 22
            eulerRotation.y: 160
            brightness: 0.90
        }

        DirectionalLight {
            eulerRotation.x: -18
            eulerRotation.y: 180
            brightness: 1.40
            castsShadow: true
            shadowFactor: 0.65
        }

        Node {
            id: cartridge
            eulerRotation.x: root.pitch
            eulerRotation.y: root.yaw

            // Front shell: main slab, bottom strip and the rounded corner.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(
                    root.bodyWidth / 100,
                    (root.bodyHeight - root.cornerRadius) / 100,
                    root.frontDepth / 100
                )
                position: Qt.vector3d(0, root.cornerRadius / 2, root.frontZ)
                materials: [plastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(
                    (root.bodyWidth - root.cornerRadius) / 100,
                    root.cornerRadius / 100,
                    root.frontDepth / 100
                )
                position: Qt.vector3d(
                    root.cornerRadius / 2,
                    -root.bodyHeight / 2 + root.cornerRadius / 2,
                    root.frontZ
                )
                materials: [plastic]
            }
            Model {
                source: "#Cylinder"
                scale: Qt.vector3d(
                    root.cornerRadius * 2 / 100,
                    root.frontDepth / 100,
                    root.cornerRadius * 2 / 100
                )
                position: Qt.vector3d(
                    -root.bodyWidth / 2 + root.cornerRadius,
                    -root.bodyHeight / 2 + root.cornerRadius,
                    root.frontZ
                )
                eulerRotation.x: 90
                materials: [plastic]
            }

            // Back shell: a U-shaped frame, open at the bottom centre where the
            // contact pocket meets the cartridge edge.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(
                    root.bodyWidth / 100,
                    0.86 / 100,
                    root.backLayer / 100
                )
                position: Qt.vector3d(0, 0.10, root.backZ)
                materials: [plastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.08 / 100, 0.11 / 100, root.backLayer / 100)
                position: Qt.vector3d(-0.46, -0.385, root.backZ)
                materials: [plastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.08 / 100, 0.20 / 100, root.backLayer / 100)
                position: Qt.vector3d(0.46, -0.43, root.backZ)
                materials: [plastic]
            }

            // Back layer of the rounded bottom-left corner.
            Repeater3D {
                model: root.arcSegments
                delegate: Model {
                    required property int index
                    source: "#Cube"
                    scale: Qt.vector3d(
                        0.032 / 100,
                        0.020 / 100,
                        (root.backLayer + 0.0004) / 100
                    )
                    position: Qt.vector3d(
                        root.arcX(index),
                        root.arcY(index),
                        root.backZ - 0.0002 + (index % 2) * 0.00008
                    )
                    eulerRotation.z: root.arcRotation(index)
                    materials: [plastic]
                }
            }

            // Stepped plastic frame around the pocket: middle and inner rings.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.84 / 100, 0.01 / 100, 0.002 / 100)
                position: Qt.vector3d(0, -0.335, root.levelOneZ)
                materials: [framePlastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.01 / 100, 0.19 / 100, 0.002 / 100)
                position: Qt.vector3d(-0.415, -0.435, root.levelOneZ)
                materials: [framePlastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.01 / 100, 0.19 / 100, 0.002 / 100)
                position: Qt.vector3d(0.415, -0.435, root.levelOneZ)
                materials: [framePlastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.82 / 100, 0.01 / 100, 0.002 / 100)
                position: Qt.vector3d(0, -0.345, root.innerRingZ)
                materials: [framePlastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.01 / 100, 0.18 / 100, 0.002 / 100)
                position: Qt.vector3d(-0.405, -0.44, root.innerRingZ)
                materials: [framePlastic]
            }
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.01 / 100, 0.18 / 100, 0.002 / 100)
                position: Qt.vector3d(0.405, -0.44, root.innerRingZ)
                materials: [framePlastic]
            }

            // Dark floor of the pocket, so the two recess levels read clearly.
            Model {
                source: "#Cube"
                scale: Qt.vector3d(0.80 / 100, 0.19 / 100, 0.000002)
                position: Qt.vector3d(0, -0.43, root.pocketFloorZ - 0.0001)
                materials: [dark]
            }

            // Eighteen gold pads, sitting on the second recess level.
            Repeater3D {
                model: root.contactCount
                delegate: Model {
                    required property int index
                    source: "#Cube"
                    scale: Qt.vector3d(
                        root.contactWidth / 100,
                        root.contactHeight(index) / 100,
                        root.contactDepth / 100
                    )
                    position: Qt.vector3d(
                        root.contactX(index),
                        root.contactY(index),
                        root.contactZ
                    )
                    materials: [gold]
                }
            }

            // Plastic separators at the middle layer, down to the bottom edge.
            Repeater3D {
                model: root.contactCount - 1
                delegate: Model {
                    required property int index
                    source: "#Cube"
                    scale: Qt.vector3d(
                        root.contactGap / 100,
                        root.dividerHeight / 100,
                        root.contactDepth / 100
                    )
                    position: Qt.vector3d(
                        root.dividerX(index),
                        root.dividerY(),
                        root.dividerZ
                    )
                    materials: [framePlastic]
                }
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
        id: framePlastic
        baseColor: Qt.lighter(root.cartridgeColor, 2.0)
        roughness: 0.35
        metalness: 0.08
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
        baseColor: "#f0c14b"
        metalness: 0.25
        roughness: 0.28
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
