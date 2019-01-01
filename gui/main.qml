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

    //flags: Qt.FramelessWindowHint

    title: qsTr("Beer-o-tron")

    // scale everything with screen size so it works on large screen during
    // development, and small screen on RPi.
    property int iconSize: height / 10
    property int iconSpacing: iconSize / 4
    property int statusFontSize: iconSize * 2/3
    property int statusFontWeight: Font.Bold

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
        onPressAndHold: menu.screenPress()
    }

    Row {
        id: rightStatus
        anchors.right: parent.right
        anchors.rightMargin: iconSpacing
        anchors.top: parent.top
        anchors.topMargin: iconSpacing
        spacing: iconSpacing

        Image {
            id: heater
            height: iconSize
            width: iconSize
            source: "qrc:/icons/flame.svg"
        }
        Item {
            id: heaterSpacer
            height: iconSize
            width: iconSize
            visible: !heater.visible
        }

        Image {
            id: pump
            height: iconSize
            width: iconSize
            source: "qrc:/icons/pump.svg"
            RotationAnimator on rotation {
                from: 0
                to: 360
                duration: 2000
                loops: Animation.Infinite
                running: pump.visible
            }
        }
        Item {
            id: pumpSpacer
            height: iconSize
            width: iconSize
            visible: !pump.visible
        }

        Text {
            id: time
            font.pixelSize: statusFontSize
            font.weight: statusFontWeight
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
            text: "???"
        }
    }

    Row {
        id: leftStatus
        anchors.left: parent.left
        anchors.leftMargin: iconSpacing
        anchors.top: parent.top
        anchors.topMargin: iconSpacing
        spacing: iconSpacing

        Text {
            id: temperature
            font.pixelSize: statusFontSize
            font.weight: statusFontWeight
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            text: "---"
        }
    }

    /*
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
    */

    ColumnLayout {
        id: topLevelMenu
        anchors.centerIn: parent
        Button {
            text: "Set temperature"
            onPressed: {
                console.log("set temperature")
                menu.state = "set.change"
            }
        }
        Button {
            text: "Profiles"
            onPressed: console.log("profiles")
        }
        Button {
            text: "Create profile"
            onPressed: console.log("create profile")
        }
        Button {
            text: "Quit"
            onPressed: {
                messages.send("bye")
                console.log("quit")
                Qt.quit()
            }
        }
    }

    ColumnLayout {
        id: setChangeMenu
        anchors.centerIn: parent
        Button {
            text: "temperature"
            onPressed: console.log("temperature")
        }
        Button {
            text: "{tick}"
            onPressed: {
                console.log("OK")
                menu.state = "set.run"
                messages.send("set 14.3")
            }
        }
        Button {
            text: "X"
            onPressed: {
                console.log("X")

                // this needs to go to setMenu if we're running
                menu.state = "top"
            }
        }
    }

    ColumnLayout {
        id: setMenu
        anchors.centerIn: parent
        Button {
            text: "Change temperature"
            onPressed: {
                console.log("Change temperature")
                menu.state = "set.change"
            }
        }
        Button {
            text: "Main menu"
            onPressed: {
                console.log("Main menu")
                menu.state = "top"
            }
        }
        Button {
            text: "STOP"
            onPressed: {
                console.log("STOP")
                messages.send("stop")
                menu.state = "top"
            }
        }
    }
    /*
    /// @todo remove later - for testing
    Rectangle {
        id: rect
        anchors.centerIn: parent
        color: "red"
        width: parent.width/3
        height: parent.height/3

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
    */

    Item {
        id: menu
        state: "top"
        states: [
            State {
                name: "top"
                PropertyChanges { target: topLevelMenu; visible: true }
                PropertyChanges { target: setChangeMenu; visible: false }
                PropertyChanges { target: setMenu; visible: false }
            },

            State {
                name: "set.change"
                PropertyChanges { target: topLevelMenu; visible: false }
                PropertyChanges { target: setChangeMenu; visible: true }
                PropertyChanges { target: setMenu; visible: false }
            },
            State {
                name: "set.run"
                PropertyChanges { target: topLevelMenu; visible: false }
                PropertyChanges { target: setChangeMenu; visible: false }
                PropertyChanges { target: setMenu; visible: false }
            },
            State {
                name: "set.menu"
                PropertyChanges { target: topLevelMenu; visible: false }
                PropertyChanges { target: setChangeMenu; visible: false }
                PropertyChanges { target: setMenu; visible: true }
            }
        ]

        function screenPress() {
            //rect.toggle()
            if (state == "set.run")
                state = "set.menu"
        }
    }

    Timer {
        id: heartbeat
        interval: 1000
        repeat: true
        running: true

        property int missed: 0
        onTriggered: {
            if (missed > 4) {
                /// @todo Do something more serious.
                console.error("Hearbeat failed!")
            }
            missed++
            messages.send("heartbeat")
        }

        function gotReply() {
            missed = 0
        }
    }

    function handle(message) {
        message = message.trim()
        message = message.toLowerCase()

        label.text = message
        if (message === "hot") {
            shade.c = "red"
        }
        if (message === "cold") {
            shade.c = "blue"
        }
        if (message === "ok") {
            shade.c = "transparent"
        }
        if (message === "quit") {
            Qt.quit()
        }
        if (message.startsWith("pump")) {
            pump.visible = parameter(message) === "on"
        }
        if (message.startsWith("heat")) {
            heater.visible = parameter(message) === "on"
        }
        if (message.startsWith("temp")) {
            var degreesC = parseFloat(parameter(message))
            temperature.text = formatTemperature(degreesC)
        }
        if (message.startsWith("time")) {
            var seconds = parseInt(parameter(message))
            time.text = formatTime(seconds)
        }
        if (message === "heartbeat") {
            heartbeat.gotReply()
        }
    }

    function parameter(message) {
        return message.slice(message.lastIndexOf(" ") + 1)
    }

    function formatTemperature(degreesC) {
        var formattedTemperature = "--"
        if (!isNaN(degreesC))
            formattedTemperature = degreesC.toPrecision(3)
        return formattedTemperature + "°C"
    }

    function formatTime(seconds) {
        var formattedTime = "-- s"
        if (!isNaN(seconds)) {
            var h = Math.floor(seconds/3600)
            var m = Math.floor((seconds - h*3600)/60)
            var s = seconds % 60

            if (h) {
                formattedTime = parseInt(h) + 'h'
                if (m < 10)
                    formattedTime += '0'
                formattedTime += parseInt(m)
            }
            else if (m) {
                formattedTime = parseInt(m) + 'm'
                if (s < 10)
                    formattedTime += '0'
                formattedTime += parseInt(s)
            }
            else {
                formattedTime = parseInt(s) + 's'
            }
        }

        return formattedTime
    }
}
