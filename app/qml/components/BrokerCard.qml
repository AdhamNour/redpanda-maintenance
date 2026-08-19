import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var broker: ({})
    property bool isBusy: false
    property int pendingNodeId: -1

    signal enableMaintenanceRequested(int nodeId)
    signal disableMaintenanceRequested(int nodeId)

    implicitWidth: 320
    implicitHeight: 240
    radius: 12
    color: cardMouse.containsMouse ? "#22222C" : "#1B1B22"
    border.color: (broker.ssh_status === "DISCONNECTED") ? "#EF4444" : (broker.is_main ? "#6366F1" : (cardMouse.containsMouse ? "#44445A" : "#2D2D3B"))
    border.width: (broker.ssh_status === "DISCONNECTED" || broker.is_main) ? 2 : 1

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

        // Middle Row 2: SSH Health Heartbeat State
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            ColumnLayout {
                spacing: 2
                Text {
                    text: "SSH HEALTH"
                    color: "#71717A"
                    font.pixelSize: 10
                    font.bold: true
                }
                StatusBadge {
                    label: broker.ssh_status === "DISCONNECTED" ? "SSH LOST" : "SSH ACTIVE"
                    type: broker.ssh_status === "DISCONNECTED" ? "critical" : "healthy"
                }
            }

            Item { Layout.fillWidth: true }

            Text {
                visible: broker.ssh_status === "DISCONNECTED" && broker.ssh_error
                text: "⚠️ Offline"
                color: "#F87171"
                font.pixelSize: 11
                font.bold: true
                Layout.alignment: Qt.AlignVCenter
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
                implicitHeight: 36

                property bool inMaint: (broker.maintenance_state || "").toUpperCase() === "IN MAINTENANCE" || (broker.maintenance_state || "").toUpperCase() === "DRAINING"
                property bool isDraining: root.isBusy && (root.pendingNodeId === broker.id)
                enabled: !maintBtn.isDraining

                contentItem: RowLayout {
                    spacing: 6
                    anchors.centerIn: parent

                    Text {
                        text: maintBtn.isDraining ? "⏳" : (maintBtn.inMaint ? "🟢" : "🛠️")
                        font.pixelSize: 12
                    }

                    Text {
                        text: maintBtn.isDraining
                              ? "Draining partitions..."
                              : (maintBtn.inMaint ? "Exit Maintenance Mode" : "Enter Maintenance Mode")
                        color: maintBtn.isDraining
                               ? "#A1A1AA"
                               : (maintBtn.inMaint ? "#34D399" : "#FFFFFF")
                        font.pixelSize: 12
                        font.bold: true
                    }
                }

                background: Rectangle {
                    radius: 6
                    color: maintBtn.isDraining
                           ? "#1E1E2C"
                           : (maintBtn.down
                              ? "#14141A"
                              : (maintBtn.hovered
                                 ? (maintBtn.inMaint ? "#064E3B" : "#FF653D")
                                 : (maintBtn.inMaint ? "#065F46" : "#F04D23")))
                    border.color: maintBtn.isDraining
                                  ? "#F59E0B"
                                  : (maintBtn.inMaint ? "#10B981" : "#F04D23")
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

