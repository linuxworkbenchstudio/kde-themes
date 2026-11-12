import QtQuick

// @NAME@ splash (@VARIANT@). Uses core QtQuick only.
// The logo in the centre, the name below it, and a progress bar near the bottom with a percentage.
// KSplash sets `stage` from 1 to 6 as the session starts, so the bar moves in steps.
Rectangle {
    id: root
    color: "@BG@"
    property int stage
    readonly property real progress: Math.min(1, Math.max(0, (stage - 1) / 5))

    onStageChanged: {
        if (stage === 2) {
            introAnimation.running = true
        }
    }

    Item {
        id: content
        anchors.fill: parent
        opacity: 0

        Image {
            id: art
            anchors.fill: parent
            source: "images/background.jpg"
            fillMode: Image.PreserveAspectCrop
            smooth: true
            asynchronous: false
        }

        // the @NAME@ logo (images/logo.png), in the centre
        Image {
            id: logo
            source: "images/logo.png"
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
            height: Math.round(parent.height * 0.17)
            width: height
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -Math.round(parent.height * 0.04)
        }

        // the name (images/wordmark.png), below the logo
        Image {
            id: wordmark
            source: "images/wordmark.png"
            fillMode: Image.PreserveAspectFit
            smooth: true
            mipmap: true
            height: Math.round(parent.height * 0.032)
            width: height * sourceSize.width / Math.max(1, sourceSize.height)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: logo.bottom
            anchors.topMargin: Math.round(parent.height * 0.035)
        }

        // progress bar near the bottom, with the percentage under it
        Rectangle {
            id: track
            width: Math.round(parent.width * 0.2)
            height: Math.max(3, Math.round(parent.height * 0.0035))
            radius: height / 2
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Math.round(parent.height * 0.12)
            color: Qt.rgba(1, 1, 1, 0.18)

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                height: parent.height
                radius: parent.radius
                color: "@LINE@"
                width: parent.width * root.progress
                Behavior on width {
                    NumberAnimation { duration: 450; easing.type: Easing.OutCubic }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: track.bottom
            anchors.topMargin: Math.round(parent.height * 0.014)
            text: Math.round(root.progress * 100) + "%"
            color: "@TEXT@"
            opacity: 0.8
            font.pixelSize: Math.max(12, Math.round(parent.height * 0.016))
            font.weight: Font.Medium
        }
    }

    OpacityAnimator {
        id: introAnimation
        target: content
        from: 0
        to: 1
        duration: 600
        easing.type: Easing.InOutQuad
    }
}
