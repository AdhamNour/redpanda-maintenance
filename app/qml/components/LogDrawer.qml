import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property bool isExpanded: false
    property var logModel: []
    property string activeFilter: "ALL" // ALL, ERROR, SUCCESS, INFO
    property bool allCopied: false

    signal clearRequested()

    Timer {
        id: copyTimer
        interval: 2000
        onTriggered: root.allCopied = false
    }

    function getAllLogsText() {
        var text = "";
        for (var i = 0; i < root.logModel.length; i++) {
            var item = root.logModel[i];
            if (root.activeFilter !== "ALL" && item.level !== root.activeFilter) continue;
            text += "[" + item.timestamp + "] [" + item.level + "] " + item.message + "\n";
        }
        return text;
    }

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

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 16
                anchors.rightMargin: 16
                spacing: 12

                // Expand/Collapse toggle area
                MouseArea {
                    Layout.preferredWidth: titleRow.implicitWidth + 24
                    Layout.fillHeight: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.isExpanded = !root.isExpanded

                    RowLayout {
                        id: titleRow
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 8

                        Text {
                            text: root.isExpanded ? "▼" : "▲"
                            color: "#F04D23"
                            font.pixelSize: 11
                        }

                        Text {
                            text: "Execution Console"
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
                    }
                }

                // Filter Chips (visible when expanded)
                RowLayout {
                    visible: root.isExpanded
                    spacing: 6

                    // All Chip
                    Rectangle {
                        implicitWidth: 38
                        implicitHeight: 22
                        radius: 4
                        color: root.activeFilter === "ALL" ? "#F04D23" : (allMouse.containsMouse ? "#282836" : "#1B1B24")
                        border.color: root.activeFilter === "ALL" ? "#F04D23" : "#343446"

                        MouseArea {
                            id: allMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activeFilter = "ALL"
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "All"
                            color: "#FFFFFF"
                            font.pixelSize: 10
                            font.bold: root.activeFilter === "ALL"
                        }
                    }

                    // Errors Chip
                    Rectangle {
                        implicitWidth: 62
                        implicitHeight: 22
                        radius: 4
                        color: root.activeFilter === "ERROR" ? "#7F1D1D" : (errMouse.containsMouse ? "#282836" : "#1B1B24")
                        border.color: root.activeFilter === "ERROR" ? "#EF4444" : "#343446"

                        MouseArea {
                            id: errMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activeFilter = "ERROR"
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "🚨 Errors"
                            color: root.activeFilter === "ERROR" ? "#FCA5A5" : "#D4D4D8"
                            font.pixelSize: 10
                            font.bold: root.activeFilter === "ERROR"
                        }
                    }

                    // Success Chip
                    Rectangle {
                        implicitWidth: 70
                        implicitHeight: 22
                        radius: 4
                        color: root.activeFilter === "SUCCESS" ? "#064E3B" : (succMouse.containsMouse ? "#282836" : "#1B1B24")
                        border.color: root.activeFilter === "SUCCESS" ? "#10B981" : "#343446"

                        MouseArea {
                            id: succMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activeFilter = "SUCCESS"
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "✅ Success"
                            color: root.activeFilter === "SUCCESS" ? "#6EE7B7" : "#D4D4D8"
                            font.pixelSize: 10
                            font.bold: root.activeFilter === "SUCCESS"
                        }
                    }

                    // Info Chip
                    Rectangle {
                        implicitWidth: 52
                        implicitHeight: 22
                        radius: 4
                        color: root.activeFilter === "INFO" ? "#1E3A8A" : (infoMouse.containsMouse ? "#282836" : "#1B1B24")
                        border.color: root.activeFilter === "INFO" ? "#3B82F6" : "#343446"

                        MouseArea {
                            id: infoMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: root.activeFilter = "INFO"
                        }
                        Text {
                            anchors.centerIn: parent
                            text: "ℹ️ Info"
                            color: root.activeFilter === "INFO" ? "#93C5FD" : "#D4D4D8"
                            font.pixelSize: 10
                            font.bold: root.activeFilter === "INFO"
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                // Copy All Button
                Button {
                    visible: root.isExpanded
                    implicitHeight: 26
                    implicitWidth: root.allCopied ? 75 : 85
                    onClicked: {
                        var allTxt = root.getAllLogsText();
                        if (allTxt) {
                            appController.copyToClipboard(allTxt);
                            root.allCopied = true;
                            copyTimer.restart();
                        }
                    }
                    contentItem: Text {
                        text: root.allCopied ? "✓ Copied" : "📋 Copy All"
                        color: root.allCopied ? "#34D399" : "#A1A1AA"
                        font.pixelSize: 11
                        font.bold: root.allCopied
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 4
                        color: parent.hovered ? "#282834" : "#1C1C24"
                        border.color: root.allCopied ? "#10B981" : "#383848"
                    }
                }

                // Clear Button
                Button {
                    text: "Clear"
                    implicitHeight: 26
                    implicitWidth: 55
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
                    Qt.callLater(function() {
                        logListView.positionViewAtEnd();
                    });
                }

                delegate: RowLayout {
                    width: logListView.width - 32
                    spacing: 8
                    visible: root.activeFilter === "ALL" || modelData.level === root.activeFilter
                    height: visible ? implicitHeight : 0

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
