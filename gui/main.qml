import QtQuick 2.12
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3
import QtQuick.Window 2.12

import Beer 1.0

Window {
    id: window
    visible: true

    ////////////////////////////////////////////////
    // Just for testing
    //visibility: "FullScreen"
    width: 640
    height: 480
    ///////////////////////////////////////////////

    flags: Qt.FramelessWindowHint

    title: qsTr("Beer-o-tron")

    Messages {
        id: messages
        onReceived: handle(message)
    }

    // Background image. Normally the live temperature graph.
    // Can be a splash screen at startup, etc. etc.
    Image {
        id: background
        anchors.fill: parent
        source: "file:./../data/graph.png"
    }

    // Part transparent rectangle overlaying the background image so we can
    // shade the graph depending on conditions. e.g. red if we're too hot,
    // blue too cold.
    Rectangle {
        id: shade
        anchors.fill: parent
        color: "transparent"

        property color c
        onCChanged: {
            if (c == "#00000000")
                color = "transparent"
            else
                color = Qt.rgba(c.r, c.g, c.b, 0.33)
        }
    }

    // Allow a press and hold anywhere on the screen to trigger an action,
    // e.g emergency stop, or mode change
    MouseArea {
        id: wholeScreen
        anchors.fill: parent
        onPressAndHold: rect.toggle()
    }

    RowLayout {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        anchors.horizontalCenter: parent.horizontalCenter

        spacing: 20

        Button {
            text: "A"
            onPressed: messages.send("a 9")
        }

        Button {
            text: "B"
            onPressed: messages.send("b 4.2")
        }

        Button {
            text: "quit"
            onPressed: {
                messages.send("bye")
                Qt.quit()
            }
        }
    }

    /// @todo remove later - for testing
    Rectangle {
        id: rect
        anchors.centerIn: parent
        color: "red"
        width: 200
        height: 100

        function toggle() {
            if (color == "#0000ff")
                color = "plum"
            else
                color = "blue"
        }

        Text {
            id: label
            anchors.centerIn: parent
        }
    }

    function handle(message) {
        message = message.trim()

        label.text = message
        if (message === "hot") {
            shade.c = "red"
        }
        if (message === "cold") {
            shade.c = /*"cyan"*/ "blue" /*"skyblue"*/
        }
        if (message === "ok") {
            shade.c = "transparent"
        }
        if (message === "quit") {
            Qt.quit()
        }
    }
}
