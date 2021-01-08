import QtQuick 2.12
import QtQuick.Controls 2.5
import QtQuick.Layouts 1.15

import Beer 1.0

ApplicationWindow {
    width: 640
    height: 480
    visible: true
    title: qsTr("Test Stub for Mash-o-matiC")

    property bool respondToHeartbeats: true
    property real temperature: 20
    property int time: 0
    property var startTime: Date.now()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        focus: true

        Text {
            Layout.fillWidth: true
            font.family: "consolas"
            text:
                "Send messages:      H - hot       P - pump      Ctrl-P - pump on\n" +
                "                    C - cold      E - heat      Ctrl-E - heat on\n" +
                "                    K - ok        - / + - change temperature\n" +
                "                    S - stop      [ / ] - change time\n" +
                "                                  < / > - change time by 1 hour\n" +
                "                    L - hard coded list of presets\n" +
                "\n" +
                "  B   - toggle responding to heartbeats\n" +
                "space - toggle auto scroll\n"
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 20
            Button {
                text: "1"
                onPressed: messages.send("button 1 down")
                onReleased: messages.send("button 1 up")
            }
            Button {
                text: "2"
                onPressed: messages.send("button 2 down")
                onReleased: messages.send("button 2 up")
            }
            Button {
                text: "3"
                onPressed: messages.send("button 3 down")
                onReleased: messages.send("button 3 up")
            }
            Button {
                text: "4"
                onPressed: messages.send("button 4 down")
                onReleased: messages.send("button 4 up")
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "cornsilk"

            ListView {
                id: list
                anchors.fill: parent
                clip: true
                model: ListModel {}
                delegate: Text {
                    font.family: "consolas"
                    text: value
                }

                property bool autoScrollToEnd: true
                onAutoScrollToEndChanged: {
                    if (autoScrollToEnd) {
                        positionViewAtEnd()
                    }
                }

                function add(s) {
                    if (s.endsWith('\n')) {
                        s = s.slice(0,-1)
                    }
                    const time = Date.now() - startTime
                    const seconds = time / 1000
                    model.append({value: seconds.toFixed(3) + ' ' + s})
                    if (autoScrollToEnd) {
                        positionViewAtEnd()
                    }
                }
            }
        }

        Keys.onPressed: {
            switch (event.key) {
            case Qt.Key_B:
                respondToHeartbeats = !respondToHeartbeats
                if (respondToHeartbeats) {
                    list.add("Responding to heartbeats.")
                }
                else {
                    list.add("Ignoring heartbeats.")
                }
                event.accepted = true
                break
            case Qt.Key_C:
                messages.send("cold")
                event.accepted = true
                break
            case Qt.Key_E:
                messages.sendOptional("heat", event)
                event.accepted = true
                break
            case Qt.Key_H:
                messages.send("hot")
                event.accepted = true
                break
            case Qt.Key_K:
                messages.send("ok")
                event.accepted = true
                break
            case Qt.Key_L:
                messages.send("preset \"one\" \"blah blah blah\"")
                messages.send("preset \"two\" \"blah blah blah\"")
                messages.send("preset \"three 3\"")
                messages.send("preset \"no closing quote")
                messages.send("preset \"fore\"\"no closing quote and no space separating")
                messages.send("preset noquotes")
                messages.send("preset \"my mash\" \"55' rest\"")
                messages.send("preset \"blah\" \"whatever\"")
                messages.send("preset \"quite a long name\" \"some sort of description\"")
                messages.send("preset \"mash.txt\" \"0934098092357\"")
                event.accepted = true
                break
            case Qt.Key_P:
                messages.sendOptional("pump", event)
                event.accepted = true
                break
            case Qt.Key_S:
                messages.send("stop")
                event.accepted = true
                break
            case Qt.Key_Minus:
                temperature -= 0.1
                messages.send("temp " + temperature)
                event.accepted = true
                break
            case Qt.Key_Plus:
            case Qt.Key_Equal:
                temperature += 0.1
                messages.send("temp " + temperature)
                event.accepted = true
                break
            case Qt.Key_BracketLeft:
                time -= 1
                messages.send("time " + time)
                event.accepted = true
                break
            case Qt.Key_BracketRight:
                time += 1
                messages.send("time " + time)
                event.accepted = true
                break
            case Qt.Key_Less:
            case Qt.Key_Comma:
                time -= 3600
                messages.send("time " + time)
                event.accepted = true
                break
            case Qt.Key_Greater:
            case Qt.Key_Period:
                time += 3600
                messages.send("time " + time)
                event.accepted = true
                break
            case Qt.Key_Space:
                list.autoScrollToEnd = !list.autoScrollToEnd
                event.accepted = true
                break
            }
        }
    }

    Messages {
        id: messages
        onReceived: handle(message)
        onSent: list.add("Tx: " + message)
        onEof: {
            list.add("Rx: EOF")
        }

        function sendOptional(message, event) {
            if (event.modifiers & Qt.ControlModifier) {
                message += " on"
            }
            send(message)
        }
    }

    function handle(message) {
        list.add("Rx: " + message)
        if (message.trim() === "heartbeat" && respondToHeartbeats) {
            messages.send(message)
        }
    }
}
