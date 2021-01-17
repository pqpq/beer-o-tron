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
    width: 320
    height: 240

    // Scale everything with screen size so it works on large screen during
    // development, and small screen on RPi.
    property int unitOfSize: height / 10
    property int iconSize: unitOfSize
    property int statusIconSpacing: iconSize / 4
    property int statusFontSize: unitOfSize * 3/4
    property int statusFontWeight: Font.Bold

    property int buttonSize: window.width / 8
    property int buttonMargins: buttonSize / 10

    property int listWidth: window.width / 2
    property int listHeight: window.height / 2
    property int textSize: unitOfSize
    property int descriptionTextSize: textSize * 2/3
    property int descriptionMaxWidth: window.width * 3/4

    property int temperatureTextSize: unitOfSize * 3/2
    property int temperatureBackgroundWidth: window.width / 2
    property int temperatureBackgroundHeight: temperatureTextSize * 2

    readonly property string backgroundColor: "lightgrey"
    readonly property real backgroundOpacity: 0.75

    property ListModel presets: ListModel{}

    Messages {
        id: messages
        onReceived: decode(message)
    }

    // Background image. Normally the live temperature graph.
    // Can be a splash screen at startup, etc. etc.
    // Set or refreshed by the "image" message.
    Image {
        id: background
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit

        // Simpler than having per-state PropertyChanges logic for opacity
        opacity: menu.state.endsWith("run") || (menu.state === "top") ? 1 : 0.25
        Behavior on opacity { PropertyAnimation { duration: 200 }}

        // Part transparent rectangle overlaying the background image so we can
        // shade the graph depending on conditions. e.g. red if we're too hot,
        // blue too cold.
        Rectangle {
            id: shade
            anchors.fill: parent
            color: "transparent"
        }
    }

    // We don't need a Row or RowLayout, because we want to position things
    // precisely, and don't want them to move when other item's visibility changes.
    Item {
        id: statusRow
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: temperature.height

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
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            anchors.centerIn: parent
            font.pixelSize: statusFontSize * 1.5
            font.weight: statusFontWeight
            text: "---"
        }
        Text {
            id: degreesSuffix
            anchors.left: temperature.right
            anchors.top: temperature.top
            font.pixelSize: statusFontSize
            font.weight: statusFontWeight
            color: temperature.color
            text: "°C"
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
                duration: 1000
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

            // Normally we toggle between solidHeart and hollowHeart, so the user
            // sees a beating heart, which means comms are live (i.e. things are good).
            // If we loose comms, we switch to problem and the user sees the
            // flashing problem icon.
            readonly property int solidHeart: 0
            readonly property int  hollowHeart: 1
            readonly property int problem: 2
            property int state: problem

            function heartbeat() {
                state = state === solidHeart ? hollowHeart : solidHeart
                setSource()
            }
            function setSource() {
                visible = true
                state = Math.max(state, solidHeart)
                state = Math.min(state, problem)
                const name = ["heart_solid.svg", "heart_border.svg", "problem.svg"][state]
                source = "qrc:/icons/" + name
            }
            function noHeartbeat() {
                state = problem
                setSource()
            }
            Timer {
                id: iconFlasher
                interval: 500
                running: status.state === status.problem
                repeat: true
                onTriggered: status.visible = !status.visible
            }
        }
    }

    // Position 4 buttons along the bottom of the screen to line up with the
    // push buttons on the Adafruit 2315 screen.
    // Dimensions are:
    //
    // |         S  C  R  E  E  N        |
    // +-------------- 45mm -------------+
    // +---+     +---+     +---+     +---+
    // | o |     | o |     | o |     | o |
    // +---+     +---+     +---+     +---+
    // :   :         :     :
    // 6.2mm          6.7mm
    //
    // Button icons, visibility and enablement are set depending on the state.
    //
    // We use RoundButton because the appearance is good, but there's no way
    // to actually press them without a touch screen. Instead "presses" come from
    // GPIO via incoming 'button' messages. We emit signals in onClicked() so we
    // can still test with a mouse while developing.
    Item {
        id: buttons
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: buttonMargins
        height: button1.height
        // Simpler than having per-state PropertyChanges logic for opacity
        opacity: menu.state.endsWith("run") ? 0.5 : 1
        Behavior on opacity { PropertyAnimation { duration: 200 }}

        RoundButton {
            id: button1
            x: 0
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(1)
        }

        RoundButton {
            id: button2
            x: (parent.width - width) * (1/3)
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(2)
        }

        RoundButton {
            id: button3
            x: (parent.width - width) * (2/3)
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(3)
        }

        RoundButton {
            id: button4
            x: parent.width - width
            anchors.bottom: parent.bottom

            visible: icon.source != ""
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(4)
        }

        // A fixed "stop" button which is made visible when needed.
        // This is simpler than changing the colour of button4 depending on state:
        // that caused problems with button appearance not matching the other
        // buttons who had not had their colour changed, when it was disabled.
        RoundButton {
            id: stopButton
            x: parent.width - width
            anchors.bottom: parent.bottom

            visible: false
            icon.source: "qrc:/icons/stop.svg"
            icon.color: "red"
            icon.width: buttonSize
            icon.height: buttonSize
            onClicked: menu.buttonPressed(4)
        }
    }

    Item {
        // Get the posisitioning right once, for this outer Item,
        // then everything else can simply center in it.
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: statusRow.bottom
        anchors.bottom: buttons.top

        Rectangle {
            id: temperatureSetter
            opacity: backgroundOpacity
            color: backgroundColor

            anchors.centerIn: parent
            width: temperatureBackgroundWidth
            height: temperatureBackgroundHeight

            readonly property int decimals: 1
            readonly property real step: 0.1
            property real value: 66.6
            property string valueString: Number(value).toLocaleString(Qt.locale(), 'f', decimals)

            function canDecrease() {
                return value > 20.0
            }
            function decrease() {
                if (canDecrease()) {
                    value -= step
                }
            }

            function canIncrease() {
                return value < (80.0 - step)
            }
            function increase() {
                if (canIncrease()) {
                    value += step
                }
            }

            function set() {
                messages.send("set " + valueString)
            }

            Text {
                anchors.centerIn: parent
                font.pixelSize: temperatureTextSize
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
            preferredHighlightBegin: height / 2 - textSize / 2
            preferredHighlightEnd: preferredHighlightBegin + textSize

            model: presets

            onVisibleChanged: ensureSelectionIsVisible()

            function repopulate() {
                model.clear()
                messages.send("list")
            }

            function canGoDown() {
                return currentIndex < model.count-1
            }
            function down() {
                if (canGoDown())
                    currentIndex++
                ensureSelectionIsVisible()
            }

            function canGoUp() {
                return currentIndex > 0
            }
            function up() {
                if (canGoUp())
                    currentIndex--
                ensureSelectionIsVisible()
            }

            function canSelect() {
                return model.count > 0
            }
            function select() {
                const obj = model.get(currentIndex)
                presetDetails.name = obj.name
                presetDetails.description = obj.description
            }

            function ensureSelectionIsVisible() {
                positionViewAtIndex(currentIndex, ListView.Contain)
            }

            function run() {
                const obj = model.get(currentIndex)
                messages.send("run \"" + obj.id + '"')
            }

            delegate: Text {
                leftPadding: textSize / 2
                rightPadding: textSize / 2
                font.bold: ListView.isCurrentItem
                font.pixelSize: textSize
                width: presetList.width
                elide: Text.ElideRight
                text: name
            }

            Rectangle {
                id: presetListBackground
                opacity: backgroundOpacity
                color: backgroundColor
                anchors.fill: parent
                z: -1
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
                Layout.maximumWidth: descriptionMaxWidth
            }
            Text {
                id: description
                font.pixelSize: descriptionTextSize
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                elide: Text.ElideRight
                Layout.margins: parent.textMargins
                Layout.maximumWidth: descriptionMaxWidth
                Layout.maximumHeight: descriptionTextSize * 5
            }
        }
        Rectangle {
            id: presetDetailsBackground
            visible: presetDetails.visible
            anchors.fill: presetDetails
            opacity: backgroundOpacity
            color: backgroundColor
            z: -1
        }
    }

    Item {
        id: menu
        state: "top"

        states: [
            State {
                name: "top"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/thermometer.svg" }
                PropertyChanges { target: button2; icon.source: "qrc:/icons/timeline.svg"; enabled: true }
                PropertyChanges { target: button3; icon.source: ""; enabled: true } // "qrc:/icons/timeline_add.svg"
                PropertyChanges { target: button4; visible: false }
                PropertyChanges { target: stopButton; visible: true }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }

                readonly property var actions: [menu.noAction, presetList.repopulate, menu.noAction, menu.allStop]
                readonly property var nextStates: ["set.temperature", "preset.choose", "", ""]
            },
            State {
                name: "set.temperature"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/close.svg" }
                PropertyChanges { target: button2; icon.source: "qrc:/icons/remove.svg"; enabled: temperatureSetter.canDecrease() }
                PropertyChanges { target: button3; icon.source: "qrc:/icons/add.svg"; enabled: temperatureSetter.canIncrease()}
                PropertyChanges { target: button4; icon.source: "qrc:/icons/check.svg"; visible: true; enabled: true }
                PropertyChanges { target: stopButton; visible: false }
                PropertyChanges { target: temperatureSetter; visible: true }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }

                readonly property var actions: [menu.idle, temperatureSetter.decrease, temperatureSetter.increase, temperatureSetter.set]
                readonly property var nextStates: ["top", "", "", "set.run"]
            },
            State {
                name: "set.run"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/menu.svg" }
                PropertyChanges { target: button2; icon.source: ""; enabled: true }
                PropertyChanges { target: button3; icon.source: ""; enabled: true }
                PropertyChanges { target: button4; visible: false }
                PropertyChanges { target: stopButton; visible: true }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: false }

                readonly property var actions: [menu.noAction, menu.noAction, menu.noAction, menu.allStop]
                readonly property var nextStates: ["set.temperature", "", "", "top"]
            },
            State {
                name: "preset.choose"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/close.svg" }
                PropertyChanges { target: button2; icon.source: "qrc:/icons/down.svg"; enabled: presetList.canGoDown() }
                PropertyChanges { target: button3; icon.source: "qrc:/icons/up.svg"; enabled: presetList.canGoUp() }
                PropertyChanges { target: button4; icon.source: "qrc:/icons/check.svg"; visible: true; enabled: presetList.canSelect() }
                PropertyChanges { target: stopButton; visible: false }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: true }
                PropertyChanges { target: presetDetails; visible: false }

                readonly property var actions: [menu.noAction, presetList.down, presetList.up, presetList.select]
                readonly property var nextStates: ["top", "", "", "preset.confirm"]
            },
            State {
                name: "preset.confirm"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/back.svg" }
                PropertyChanges { target: button2; icon.source: ""; enabled: true }
                PropertyChanges { target: button3; icon.source: ""; enabled: true}
                PropertyChanges { target: button4; icon.source: "qrc:/icons/check.svg"; visible: true; enabled: true }
                PropertyChanges { target: stopButton; visible: false }
                PropertyChanges { target: temperatureSetter; visible: false }
                PropertyChanges { target: presetList; visible: false }
                PropertyChanges { target: presetDetails; visible: true }

                readonly property var actions: [menu.idle, menu.noAction, menu.noAction, presetList.run]
                readonly property var nextStates: ["preset.choose", "", "", "preset.run"]
            },
            State {
                name: "preset.run"
                PropertyChanges { target: button1; icon.source: "qrc:/icons/menu.svg" }
                PropertyChanges { target: button2; icon.source: "" ; enabled: true}
                PropertyChanges { target: button3; icon.source: ""; enabled: true }
                PropertyChanges { target: button4; visible: false }
                PropertyChanges { target: stopButton; visible: true }
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

        function idle() {
            messages.send("idle")
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
                status.noHeartbeat()
            }
            missed++
            messages.send("heartbeat")
        }

        function gotReply() {
            status.heartbeat()
            missed = 0
        }
    }

    function decode(message) {
        message = message.trim()
        message = message.toLowerCase()

        if (message === "hot") {
            temperature.color = "red"
            shade.color = "#55ff0000"
        }
        if (message === "cold") {
            temperature.color = "blue"
            shade.color = "#550055ff"
        }
        if (message === "ok") {
            temperature.color = "black"
            shade.color = "transparent"
        }
        if (message.startsWith("pump")) {
            pump.visible = parameter(message) === "on"
        }
        if (message.startsWith("heat")) {
            heater.visible = parameter(message) === "on"
        }
        if (message.startsWith("temp")) {
            const degreesC = parseFloat(parameter(message))
            temperature.text = formatTemperature(degreesC)
        }
        if (message.startsWith("time")) {
            const seconds = parseInt(parameter(message))
            time.text = formatTime(seconds)
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
                const newBackgroundImageSource = "file:" + message.slice(indexOfPayload + 1)
                if (background.source === newBackgroundImageSource) {
                    background.source = ""
                }
                background.source = newBackgroundImageSource
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
        return formattedTemperature
    }

    function formatTime(seconds) {
        var formattedTime = "-- s"
        if (!isNaN(seconds)) {
            if (seconds === 0) {
                return ""
            }

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
        let id = ""
        let name = ""
        let description = ""

        const partsAndSpaces = preset.split('"')
        let parts = []
        for (let i in partsAndSpaces) {
            const partOrSpace = partsAndSpaces[i].trim()
            if (partOrSpace !== "") {
                parts.push(partOrSpace)
            }
        }

        if (parts.length > 2) {
            id = parts[1]
            name = parts[2]
        }
        if (parts.length > 3) {
            description = parts[3]
        }

        if (!!id && !!name) {
            presets.append({"id":id, "name":name, "description":description})
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
        if (parts.length === 2) {
            const button = parseInt(parts[1])
            menu.buttonPressed(button)
        }
    }
}
