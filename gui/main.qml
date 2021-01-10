// NEXT:

// Disable up and down buttons when list ends are reached.
// Disable + and - buttons when temperature limits are reached


import QtQuick 2.12
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3
import QtQuick.Window 2.12

import Beer 1.0     // always a good idea!


Window {
    id: window
    visible: true

    // The 'runWindowed' QQmlContext property must come from main.cpp
    flags: runWindowed ? Qt.Window : Qt.FramelessWindowHint
    visibility: runWindowed ? "Windowed" : "FullScreen"

    title: qsTr("Mash-o-MatiC")
    width: 320//640
    height: 240//480

    // Scale everything with screen size so it works on large screen during
    // development, and small screen on RPi.
    property int unitOfSize: height / 10
    property int iconSize: unitOfSize
    property int statusIconSpacing: iconSize / 4
    property int statusFontSize: unitOfSize * 3/4
    property int statusFontWeight: Font.Bold

    property int buttonSize: window.width / 8
    property int buttonBottomMargin: buttonSize / 8

    property int listWidth: window.width / 2
    property int listHeight: window.height / 2
    property int textSize: unitOfSize
    property int descriptionTextSize: textSize * 2/3

    property ListModel presets: ListModel{}

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
        fillMode: Image.PreserveAspectFit
        opacity: menu.state.endsWith("run") ? 1 : 0.33
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

    // We don't need a Row or RowLayout, because we want to position things
    // precisely, and don't want them to move when other item's visibility changes.
    Item {
        id: statusRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: iconSize

        Text {
            id: time
            font.pixelSize: statusFontSize
            font.weight: statusFontWeight
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            anchors.left: parent.left
            visible: text
        }

        Text {
            id: temperature
            font.pixelSize: statusFontSize
            font.weight: statusFontWeight
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            anchors.centerIn: parent
            text: "---"
        }

        Image {
            id: heater
            height: iconSize
            width: iconSize
            sourceSize.width: iconSize
            source: "qrc:/icons/flame.svg"
            anchors.right: pump.left
            visible: false
        }

        Image {
            id: pump
            height: iconSize
            width: iconSize
            sourceSize.width: iconSize
            source: "qrc:/icons/pump.svg"
            anchors.right: status.left
            visible: false

            RotationAnimator on rotation {
                from: 0
                to: 360
                duration: 2000
                loops: Animation.Infinite
                running: pump.visible
            }
        }

        Image {
            id: status
            anchors.right: parent.right
            height: iconSize
            width: iconSize
            sourceSize.width: iconSize

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
                state = Math.max(state, 0)
                state = Math.min(state, 2)
                source = ["qrc:/icons/heart_solid.svg", "qrc:/icons/heart_border.svg", "qrc:/icons/problem.svg"][state]
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
            //onStateChanged: console.log("state=", state)
        }
    }

    // Position 4 buttons along the bottom of the screen to line up with the
    // push buttons on the Adafruit 2315 screen.
    // Icons are set depending on the state.
    // We use RoundButton because the appearance is good, but there's no way
    // to press them without a touch screen. Presses are simulated by linking
    // to incoming messages. We emit signals in onClicked() so we can test
    // with a mouse.
    Item {
        id: buttons
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.bottomMargin: buttonBottomMargin
        height: button1.height
        opacity: menu.state.endsWith("run") ? 0.5 : 1

        RoundButton {
            id: button1
            x: parent.width * (1/8) - width / 2
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(1)
        }

        RoundButton {
            id: button2
            x: parent.width * (3/8) - width / 2
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(2)
        }

        RoundButton {
            id: button3
            x: parent.width * (5/8) - width / 2
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(3)
        }

        RoundButton {
            id: button4
            x: parent.width * (7/8) - width / 2
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(4)
        }
    }

    Item {
        // Get the posisitioning right once, for this outer Item, then everything
        // else can simply center in it.
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: statusRow.bottom
        anchors.bottom: buttons.top

        Rectangle {
            id: temperatureSetter

            anchors.centerIn: parent

            property int decimals: 1
            property real value: 66.6
            readonly property real step: 0.1
            property string valueString: Number(value).toLocaleString(Qt.locale(), 'f', decimals)

            function decrease() {
                if (value > 20.0) {
                    value -= step
                }
            }

            function increase() {
                if (value < (80.0 - step)) {
                    value += step
                }
            }

            function set() {
                messages.send("set " + valueString)
            }

            Text {
                anchors.centerIn: parent
                font.pixelSize: textSize * 1.5
                font.bold: true
                text: parent.valueString + "°C"
            }
        }

        ListView {
            id: presetList

            anchors.centerIn: parent
            width: listWidth
            height: listHeight
            clip: true

            // Keep the selected item in the middle of the list
            highlightRangeMode: ListView.StrictlyEnforceRange
            preferredHighlightBegin: height/2 - textSize / 2
            preferredHighlightEnd: height/2 + textSize / 2

            model: presets

            onVisibleChanged: ensureSelectionIsVisible()

            function repopulate() {
                model.clear()
                messages.send("list")
            }
            function down() {
                if (currentIndex < model.count-1)
                    currentIndex++
                ensureSelectionIsVisible()
            }
            function up() {
                if (currentIndex > 0)
                    currentIndex--
                ensureSelectionIsVisible()
            }
            function select() {
                let obj = model.get(currentIndex)
                messages.send("run \"" + obj.name + '"')
                presetDetails.name = obj.name
                presetDetails.description = obj.description
            }
            function ensureSelectionIsVisible() {
                positionViewAtIndex(currentIndex, ListView.Contain)
            }

            delegate: Text {
                leftPadding: textSize / 2
                rightPadding: textSize / 2
                font.bold: ListView.isCurrentItem
                font.pixelSize: textSize
                elide: Text.ElideRight
                text: name
            }

            // To debug the size, but also gives a bit of contrast and makes it
            // obvious there's somethine there, even if there are few/no entries.
            Rectangle {
                anchors.fill: parent
                z: -1
                color: "lightgrey"
                opacity: 0.5
            }
        }

        ColumnLayout {
            id: presetDetails
            anchors.centerIn: parent

            property int textMargins: textSize / 4

            property alias name: name.text
            property alias description: description.text

            Text {
                id: name
                font.bold: true
                font.pixelSize: textSize
                elide: Text.ElideRight
                Layout.margins: parent.textMargins
                Layout.bottomMargin: 0
                Layout.maximumWidth: window.width * 0.75
                //Rectangle {
                //    anchors.fill: parent
                //    color: "red"
                //    z: -0.5
                //}
            }
            Text {
                id: description
                font.pixelSize: descriptionTextSize
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                elide: Text.ElideRight
                Layout.margins: parent.textMargins
                Layout.maximumWidth: window.width * 0.75
                Layout.maximumHeight: descriptionTextSize * 5
                //Rectangle {
                //    anchors.fill: parent
                //    color: "blue"
                //    z: -0.5
                //}
            }
        }
        Rectangle {
            id: presetDetailsBackground
            anchors.fill: presetDetails
            visible: presetDetails.visible
            z: -1
            color: "lightgrey"
            opacity: 0.5
        }
    }

    Item {
        id: menu
        state: "top"

        onStateChanged: console.log("menu.state=", state)

        states: [
            State {
                name: "top"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/thermometer.svg" }
                PropertyChanges { target: button2; icon.source: "qrc:/icons/timeline.svg" }
                PropertyChanges { target: button3; icon.source: "" } // "qrc:/icons/timeline_add.svg"
                PropertyChanges { target: button4; icon.source: "qrc:/icons/stop.svg"; icon.color: "red" }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }

                readonly property var actions: [menu.noAction, presetList.repopulate, menu.noAction, menu.allStop]
                readonly property var nextStates: ["set.temperature", "preset.choose", "", ""]
            },
            State {
                name: "set.temperature"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/close.svg" }
                PropertyChanges { target: button2; icon.source: "qrc:/icons/remove.svg" }
                PropertyChanges { target: button3; icon.source: "qrc:/icons/add.svg"}
                PropertyChanges { target: button4; icon.source: "qrc:/icons/check.svg"; icon.color: "transparent" }
                PropertyChanges { target: temperatureSetter; visible: true }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }

                readonly property var actions: [menu.noAction, temperatureSetter.decrease, temperatureSetter.increase, temperatureSetter.set]
                readonly property var nextStates: ["top", "", "", "set.run"]
            },
            State {
                name: "set.run"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/menu.svg" }
                PropertyChanges { target: button2; icon.source: "" }
                PropertyChanges { target: button3; icon.source: "" }
                PropertyChanges { target: button4; icon.source: "qrc:/icons/stop.svg"; icon.color: "red" }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }
                readonly property var actions: [menu.noAction, menu.noAction, menu.noAction, menu.allStop]
                readonly property var nextStates: ["set.temperature", "", "", "top"]
            },
            State {
                name: "preset.choose"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/close.svg" }
                PropertyChanges { target: button2; icon.source: "qrc:/icons/down.svg" }
                PropertyChanges { target: button3; icon.source: "qrc:/icons/up.svg"}
                PropertyChanges { target: button4; icon.source: "qrc:/icons/check.svg"; icon.color: "transparent" }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: true }
                PropertyChanges { target: presetDetails; visible: false }
                readonly property var actions: [menu.noAction, presetList.down, presetList.up, presetList.select]
                readonly property var nextStates: ["top", "", "", "preset.confirm"]
            },
            State {
                name: "preset.confirm"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/back.svg" }
                PropertyChanges { target: button2; icon.source: "" }
                PropertyChanges { target: button3; icon.source: ""}
                PropertyChanges { target: button4; icon.source: "qrc:/icons/check.svg"; icon.color: "transparent" }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: true }
                readonly property var nextStates: ["preset.choose", "", "", "preset.run"]
            },
            State {
                name: "preset.run"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/menu.svg" }
                PropertyChanges { target: button2; icon.source: "" }
                PropertyChanges { target: button3; icon.source: "" }
                PropertyChanges { target: button4; icon.source: "qrc:/icons/stop.svg"; icon.color: "red" }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }
                readonly property var actions: [menu.noAction, menu.noAction, menu.noAction, menu.allStop]
                readonly property var nextStates: ["preset.confirm", "", "", "top"]
            }
        ]

        function getCurrentStateObject() {
            for (let i = 0; i < states.length; ++i) {
                if (menu.states[i].name === menu.state) {
                    return menu.states[i]
                }
            }
            console.error("Couldn't find the current state for '"+menu.state+"'!")
            return menu.states[0]   // top
        }

        function buttonPressed(button) {
            //console.log("buttonPressed(" + button + ")")

            if (button < 1 || button > 4)
                return

            let state = getCurrentStateObject()

            if (typeof state.actions !== "undefined") {
                state.actions[button - 1]()
            }

            let nextState = ""
            if (typeof state.nextStates !== "undefined") {
                // fixed state change logic can be looked up in a table
                nextState = state.nextStates[button - 1]
            }
            else {
                // complex logic is encapsulated in a function
                nextState = state.nextStateForButtonPress(button)
            }
            if (nextState !== "") {
                menu.state = nextState
            }
        }

        function noAction() {}

        function allStop() {
            messages.send("allstop")
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
        if (message.startsWith("button")) {
            parseButton(message)
        }
        if (message.startsWith("preset")) {
            parsePreset(message)
        }
        if (message.startsWith("image")) {
            const indexOfPayload = message.indexOf(" ")
            if (indexOfPayload > 0) {
                background.source = "file:" + message.slice(indexOfPayload + 1)
            }
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

    function parsePreset(preset) {
        //console.log("parsePreset(" + preset + ")")

        let name = ""
        let description = ""

        const parts = preset.split('"')
        if (parts.length > 1) {
            name = parts[1]
        }
        if (parts.length > 3) {
            description = parts[3]
        }

        if (!!name) {
            presets.append({"name":name, "description":description})
        }
    }

    Timer {
        id: buttonPressAndHoldTimer
        interval: 100
        running: false
        repeat: true

        //onRunningChanged: console.log("buttonPressAndHoldTimer running=", running)

        property var counts: [0,0,0,0]
        property var pressed: [false, false, false, false]

        function buttonUpdate(button, isPressed) {
            //console.log("buttonPressAndHoldTimer.buttonUpdate(" + button + ", " + isPressed + ")")
            if (0 < button && button < 5) {
                pressed[button-1] = isPressed
                counts[button-1] = 0
                if (isPressed) {
                    menu.buttonPressed(button)
                    start()
                }
                else {
                    const anyPressed = pressed[0] || pressed[1] || pressed[2] || pressed[3]
                    if (!anyPressed) {
                        stop()
                    }
                }
            }

            //for (let i = 0; i < 4; i++) {
            //    console.log("  ", i, pressed[i], counts[i])
            //}
        }

        onTriggered: {
            //console.log("buttonPressAndHoldTimer.onTriggered()")
            for (let i = 0; i < 4; i++) {
                if (pressed[i]) {
                    counts[i]++

                    // auto repeat
                    if (counts[i] > 5) {
                        menu.buttonPressed(i+1)
                    }

                    // increase speed of autorepeat after 2 seconds
                    if (counts[i] > (2 * 1000/interval)) {
                        menu.buttonPressed(i+1)
                        menu.buttonPressed(i+1)
                        menu.buttonPressed(i+1)
                        menu.buttonPressed(i+1)
                    }
                }
                //console.log("  ", i, pressed[i], counts[i])
            }
        }
    }

    function parseButton(message) {
        const parts = message.split(' ')
        if (parts.length === 3) {
            const button = parseInt(parts[1])
            const isPressed = parts[2] === "down"
            buttonPressAndHoldTimer.buttonUpdate(button, isPressed)
        }
    }
}
