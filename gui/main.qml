import QtQuick 2.12
import QtQuick.Controls 2.4
import QtQuick.Layouts 1.3
import QtQuick.Window 2.12

import Beer 1.0

Window {
    id: window
    visible: true

    visibility: "FullScreen"
    flags: Qt.FramelessWindowHint

    title: qsTr("Beer-o-tron")

    Messages {
        id: messages
        onReceived: label.text = message
    }

    Rectangle {
        anchors.fill: parent
        color: "lightseagreen"
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

    Rectangle {
        anchors.centerIn: parent
        color: "red"
        width: 200
        height: 100

        Text {
            id: label
            anchors.centerIn: parent
        }
    }
}
