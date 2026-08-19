import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var broker: ({})
    property bool isBusy: false

    signal enableMaintenanceRequested(int nodeId)
    signal disableMaintenanceRequested(int nodeId)

    implicitWidth: 320
    implicitHeight: 210
    radius: 12
    color: cardMouse.containsMouse ? "#22222C" : "#1B1B22"
    border.color: broker.is_main ? "#6366F1" : (cardMouse.containsMouse ? "#44445A" : "#2D2D3B")
    border.width: broker.is_main ? 2 : 1

    Behavior on color { ColorAnimation { duration: 150 } }
    Behavior on border.color { ColorAnimation { duration: 150 } }

    MouseArea {
        id: cardMouse
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 18
        spacing: 12

        // Top Row: Node ID + Badges
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Rectangle {
                width: 38
                height: 38
                radius: 8
                color: broker.is_main ? "#1E1F3D" : "#131318"
                border.color: broker.is_main ? "#6366F1" : "#2E2E3C"
                border.width: 1

                Text {
                    anchors.centerIn: parent
                    text: broker.id !== undefined ? String(broker.id) : "-"
                    color: broker.is_main ? "#A5B4FC" : "#FFFFFF"
                    font.pixelSize: 16
                    font.bold: true
                }
            }

            ColumnLayout {
                spacing: 2
                Text {
                    text: "Broker " + (broker.id !== undefined ? broker.id : "")
                    color: "#FFFFFF"
                    font.pixelSize: 15
                    font.bold: true
                }
                Text {
                    text: (broker.host || "0.0.0.0") + ":" + (broker.port || "9092")
                    color: "#A1A1AA"
                    font.pixelSize: 12
                    font.family: "Cascadia Code, Consolas, monospace"
                }
            }

            Item { Layout.fillWidth: true }

            StatusBadge {
                visible: broker.is_main === true
                label: "Controller ★"
                type: "controller"
                showDot: false
            }
        }

        // Divider
        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: "#282836"
        }

        // Middle Row: Rack & Maintenance State
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            ColumnLayout {
                spacing: 2
                Text {
                    text: "RACK"
                    color: "#71717A"
                    font.pixelSize: 10
                    font.bold: true
                }
                Text {
                    text: broker.rack && broker.rack !== "N/A" ? broker.rack : "Default (None)"
                    color: "#D4D4D8"
                    font.pixelSize: 12
                }
            }

            Item { Layout.fillWidth: true }

            ColumnLayout {
                spacing: 2
                Layout.alignment: Qt.AlignRight
                Text {
                    text: "MAINTENANCE"
                    color: "#71717A"
                    font.pixelSize: 10
                    font.bold: true
                    Layout.alignment: Qt.AlignRight
                }
                StatusBadge {
                    label: broker.maintenance_state || "ACTIVE"
                    type: {
                        var st = (broker.maintenance_state || "ACTIVE").toUpperCase();
                        if (st === "IN MAINTENANCE") return "warning";
                        if (st === "DRAINING") return "warning";
                        return "healthy";
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        // Action Buttons Footer
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Button {
                id: maintBtn
                Layout.fillWidth: true
                implicitHeight: 34
                enabled: !root.isBusy

                property bool inMaint: (broker.maintenance_state || "").toUpperCase() === "IN MAINTENANCE" || (broker.maintenance_state || "").toUpperCase() === "DRAINING"

                contentItem: Text {
                    text: maintBtn.inMaint ? "Exit Maintenance" : "Enter Maintenance Mode"
                    color: maintBtn.enabled ? (maintBtn.inMaint ? "#10B981" : "#F04D23") : "#666677"
                    font.pixelSize: 12
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    radius: 6
                    color: maintBtn.down ? "#14141A" : (maintBtn.hovered ? "#22222E" : "#17171F")
                    border.color: maintBtn.inMaint ? "#059669" : "#F04D23"
                    border.width: 1
                }

                onClicked: {
                    if (inMaint) {
                        root.disableMaintenanceRequested(broker.id);
                    } else {
                        root.enableMaintenanceRequested(broker.id);
                    }
                }
            }
        }
    }
}
