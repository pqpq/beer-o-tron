import QtQuick 2.12
import QtQuick.Controls 2.5
import QtQuick.Layouts 1.15

import Beer 1.0

ApplicationWindow {
    width: 640
    height: 480
    visible: true
    title: qsTr("Mash-o-matiC Test Stub")

    property bool sendHeartbeats: true
    property real temperature: 20
    property int time: 0

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10
        focus: true

        Text {
            Layout.fillWidth: true
            font.family: "consolas"
            text:
                "Send messages:    H - hot       P - pump      Ctrl-P - pump on\n" +
                "                  C - cold      E - heat      Ctrl-E - heat on\n" +
                "                  K - ok        - / + - change temperature\n" +
                "                  S - stop      [ / ] - change time\n" +
                "                  Q - quit\n" +
                "B - toggle sending heartbeats   space - toggle auto scroll\n"
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
                    text: index + ' ' + value
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
                    model.append({value:s})
                    if (autoScrollToEnd) {
                        positionViewAtEnd()
                    }
                }
            }
        }

        Keys.onPressed: {
            switch (event.key) {
            case Qt.Key_B:
                sendHeartbeats = !sendHeartbeats
                if (sendHeartbeats) {
                    list.add("Sending heartbeats.")
                }
                else {
                    list.add("Not sending heartbeats.")
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
            case Qt.Key_P:
                messages.sendOptional("pump", event)
                event.accepted = true
                break
            case Qt.Key_Q:
                messages.send("quit")
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

        function sendOptional(message, event) {
            if (event.modifiers & Qt.ControlModifier) {
                message += " on"
            }
            send(message)
        }
    }

    Timer {
        id: heartbeat
        interval: 1000
        repeat: true
        running: sendHeartbeats

        onTriggered: messages.send("heartbeat")
    }

    function handle(message) {
        list.add("Rx: " + message)
        //message = message.trim()
        //message = message.toLowerCase()
    }

}
