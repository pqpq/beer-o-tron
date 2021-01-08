// Where are we going to show the name of the pre-set we're running?
// When you press a button, when its idle (but running).
// This should also bring up the option to do an emergency stop, as well as whatever else.

import QtQuick 2.12
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3
import QtQuick.Window 2.12

import Beer 1.0     // always a good idea!

// Expected QQmlContext properties:
// bool testing : whether we're windowed, for testing, or full screen
// string pathToGraph : the path to the background image

Window {
    id: window
    visible: true

    visibility: testing ? "Windowed" : "FullScreen"
    width: 640
    height: 480

    flags: testing ? Qt.Window : Qt.FramelessWindowHint

    title: qsTr("Mash-o-MatiC")

    // scale everything with screen size so it works on large screen during
    // development, and small screen on RPi.
    property int iconSize: height / 10
    property int statusIconSpacing: iconSize / 4
    property int menuIconSpacing: iconSize / 2
    property int statusFontSize: iconSize * 2/3
    property int statusFontWeight: Font.Bold

    Messages {
        id: messages
        onReceived: handle(message)
    }

    /// @todo need a mechanism to update this.
    /// Timer? Message? QFileSystemWatcher ?

    // Background image. Normally the live temperature graph.
    // Can be a splash screen at startup, etc. etc.
    Image {
        id: background
        anchors.fill: parent
        source: pathToGraph
    }

    // Part transparent rectangle overlaying the background image so we can
    // shade the graph depending on conditions. e.g. red if we're too hot,
    // blue too cold.
    Rectangle {
        id: shade
        anchors.fill: parent
        color: "transparent"

        property color col
        onColChanged: {
            if (col == "#00000000")
                color = "transparent"
            else
                color = Qt.rgba(col.r, col.g, col.b, 0.33)
        }
    }

    /* not using a touch screen any more
    // Allow a press and hold anywhere on the screen to trigger an action,
    // e.g emergency stop, or mode change
    MouseArea {
        id: wholeScreen
        anchors.fill: parent
        onPressAndHold: menu.screenPress()
    }
    */

    Row {
        id: rightStatus
        anchors.right: parent.right
        anchors.rightMargin: statusIconSpacing
        anchors.top: parent.top
        anchors.topMargin: statusIconSpacing
        spacing: statusIconSpacing

        Image {
            id: heater
            height: iconSize
            width: iconSize
            source: "qrc:/icons/flame.svg"
            visible: false
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
            visible: false
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
            visible: text
        }

        Image {
            id: status
            height: iconSize
            width: iconSize

            // Normally we toggle between 0 and 1, so the user sees a constantly
            // changing heart, which is a good sign.
            // If we loose comms, we switch to 2 (problem) and the user sees the
            // flashing problem icon.
            // 0 = solid heart
            // 1 = hollow heart
            // 2 = problem
            property int state: 0

            function heartbeat() {
                state = state === 0 ? 1 : 0
                setSource()
            }
            function setSource() {
                opacity = 1
                if (state === 0) {
                    source = "qrc:/icons/heart_solid.svg"
                }
                else if (state === 1) {
                    source = "qrc:/icons/heart_border.svg"
                }
                else {
                    source = "qrc:/icons/problem.svg"
                }
            }
            function problem() {
                if (state !== 2) {
                    state = 2
                    setSource()
                }
            }
            Timer {
                interval: 500
                running: status.state === 2
                repeat: true
                onTriggered: status.opacity = status.opacity ? 0 : 1
            }
            onStateChanged: console.log("state=", state)
        }
    }

    Row {
        id: leftStatus
        anchors.left: parent.left
        anchors.leftMargin: statusIconSpacing
        anchors.top: parent.top
        anchors.topMargin: statusIconSpacing
        spacing: statusIconSpacing

        Text {
            id: temperature
            font.pixelSize: statusFontSize
            font.weight: statusFontWeight
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            text: "---"
        }
    }

    RowLayout {
        id: topLevelMenu
        anchors.centerIn: parent
        spacing: window.menuIconSpacing

        RoundButton {
            icon.source: "qrc:/icons/thermometer.svg"
            icon.width: window.iconSize
            icon.height: window.iconSize
            onPressed: {
                console.log("set temperature")
                menu.state = "set.change"
            }
        }
        RoundButton {
            icon.source: "qrc:/icons/timeline.svg"
            icon.width: window.iconSize
            icon.height: window.iconSize
            onPressed: console.log("profiles")
        }
        RoundButton {
            icon.source: "qrc:/icons/timeline_add.svg"
            icon.width: window.iconSize
            icon.height: window.iconSize
            onPressed: console.log("create profile")
        }
        RoundButton {
            icon.source: "qrc:/icons/power.svg"
            icon.width: window.iconSize
            icon.height: window.iconSize
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

        SpinBox {
            id: temperatureSpinner
            from: 20 * 10
            value: 666
            to: 100 * 10
            stepSize: 1

            onValueChanged: console.log("temperatureSpinner value=", value)

            /// @todo remember value when made visible, so cancel can work.
            property int decimals: 1
            property real realValue: value / 10
            property real previousValue: 0

            onVisibleChanged: {
                console.log("temperatureSpinner visible=", visible)
                previousValue = realValue
                value = realValue * 10
            }

            function cancel() {
                realValue = previousValue
            }

            function accept() {
                previousValue = realValue
            }

            validator: DoubleValidator {
                bottom: Math.min(temperatureSpinner.from, temperatureSpinner.to)
                top:  Math.max(temperatureSpinner.from, temperatureSpinner.to)
            }

            textFromValue: function(value, locale) {
                return Number(value / 10).toLocaleString(locale, 'f', temperatureSpinner.decimals)
            }

            valueFromText: function(text, locale) {
                return Number.fromLocaleString(locale, text) * 10
            }
        }

        RoundButton {
            icon.source: "qrc:/icons/check.svg"
            onPressed: {
                console.log("OK", temperatureSpinner.realValue)
                temperatureSpinner.accept()
                menu.state = "set.run"
                messages.send("set " + temperatureSpinner.realValue.toString())
            }
        }
        RoundButton {
            icon.source: "qrc:/icons/close.svg"
            onPressed: {
                console.log("X")
                temperatureSpinner.cancel()

                // this needs to go to setMenu if we're running
                menu.state = "top"
            }
        }
    }

    ColumnLayout {
        id: setMenu
        anchors.centerIn: parent
        RoundButton {
            icon.source: "qrc:/icons/settings.svg"
            onPressed: {
                console.log("Change temperature")
                menu.state = "set.change"
            }
        }
        RoundButton {
            icon.source: "qrc:/icons/menu.svg"
            onPressed: {
                console.log("Main menu")
                menu.state = "top"
            }
        }
        Button {
            text: "EMERGENCY STOP"
            onPressed: {
                console.log("STOP")
                messages.send("stop")
                menu.state = "top"
            }
            background: Rectangle { color: "red" }
        }
    }

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
                status.problem()
            }
            missed++
            messages.send("heartbeat")
        }

        function gotReply() {
            status.heartbeat()
            missed = 0
        }
    }

    function handle(message) {
        message = message.trim()
        message = message.toLowerCase()

        if (message === "hot") {
            shade.col = "red"
        }
        if (message === "cold") {
            shade.col = "blue"
        }
        if (message === "ok") {
            shade.col = "transparent"
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
        if (message === "stop") {
            time.text = ""
        }
        if (message === "heartbeat") {
            heartbeat.gotReply()
        }

        // Why? What can we do? This is a full screen app on an embedded
        // system. Should it ever quit? Maybe not.
        if (message === "quit") {
            Qt.quit()
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
