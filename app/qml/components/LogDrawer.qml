import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property bool isExpanded: false
    property var logModel: []

    signal clearRequested()

    implicitHeight: isExpanded ? 240 : 40
    color: "#0E0E12"
    border.color: "#282834"
    border.width: 1

    Behavior on implicitHeight {
        NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header bar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 40
            color: "#16161C"

            MouseArea {
                anchors.fill: parent
                onClicked: root.isExpanded = !root.isExpanded
                cursorShape: Qt.PointingHandCursor
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 10

                Text {
                    text: root.isExpanded ? "▼" : "▲"
                    color: "#F04D23"
                    font.pixelSize: 12
                }

                Text {
                    text: "Execution Console & Output Stream"
                    color: "#FFFFFF"
                    font.pixelSize: 13
                    font.bold: true
                }

                Rectangle {
                    implicitWidth: countText.implicitWidth + 12
                    implicitHeight: 20
                    radius: 10
                    color: "#242430"

                    Text {
                        id: countText
                        anchors.centerIn: parent
                        text: logListView.count + " lines"
                        color: "#A1A1AA"
                        font.pixelSize: 11
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "Clear"
                    implicitHeight: 26
                    implicitWidth: 60
                    onClicked: root.clearRequested()

                    contentItem: Text {
                        text: "Clear"
                        color: "#A1A1AA"
                        font.pixelSize: 11
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 4
                        color: parent.hovered ? "#282834" : "#1C1C24"
                        border.color: "#383848"
                    }
                }
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#22222E"
            visible: root.isExpanded
        }

        // Log output list
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: root.isExpanded
            clip: true

            ListView {
                id: logListView
                anchors.fill: parent
                model: root.logModel
                spacing: 4
                topMargin: 8
                bottomMargin: 8
                leftMargin: 16
                rightMargin: 16

                onCountChanged: {
                    // Auto scroll to bottom
                    Qt.callLater(function() {
                        logListView.positionViewAtEnd();
                    });
                }

                delegate: RowLayout {
                    width: logListView.width - 32
                    spacing: 8

                    Text {
                        text: "[" + modelData.timestamp + "]"
                        color: "#606070"
                        font.family: "Cascadia Code, Consolas, monospace"
                        font.pixelSize: 11
                    }

                    Text {
                        text: "[" + modelData.level + "]"
                        color: {
                            if (modelData.level === "SUCCESS") return "#34D399";
                            if (modelData.level === "ERROR") return "#F87171";
                            return "#60A5FA";
                        }
                        font.bold: true
                        font.family: "Cascadia Code, Consolas, monospace"
                        font.pixelSize: 11
                    }

                    Text {
                        Layout.fillWidth: true
                        text: modelData.message
                        color: modelData.level === "ERROR" ? "#FCA5A5" : "#E4E4E7"
                        font.family: "Cascadia Code, Consolas, monospace"
                        font.pixelSize: 11
                        wrapMode: Text.WrapAnywhere
                    }
                }
            }
        }
    }
}
