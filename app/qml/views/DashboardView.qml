import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: root

    signal requestEnableMaintenance(int nodeId)
    signal requestDisableMaintenance(int nodeId)

    // Tracks which node is actively being put into maintenance (-1 = none)
    property int pendingMaintenanceNodeId: -1

    Connections {
        target: appController
        function onOperationFinished(operation, success, message) {
            if (operation === "enable_maintenance" || operation === "disable_maintenance") {
                root.pendingMaintenanceNodeId = -1;
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 24
            anchors.margins: 24

            // Top Stats / Summary Header
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 90
                radius: 12
                color: "#16161D"
                border.color: "#282834"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 20

                    // Total Brokers Stat
                    RowLayout {
                        spacing: 12
                        Rectangle {
                            width: 44
                            height: 44
                            radius: 8
                            color: "#20202C"
                            Text {
                                anchors.centerIn: parent
                                text: "🖥️"
                                font.pixelSize: 18
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: "TOTAL BROKERS"
                                color: "#71717A"
                                font.pixelSize: 11
                                font.bold: true
                            }
                            Text {
                                text: appController.isConnected ? String(appController.brokers.length) : "-"
                                color: "#FFFFFF"
                                font.pixelSize: 20
                                font.bold: true
                            }
                        }
                    }

                    Rectangle { width: 1; height: 40; color: "#282834" }

                    // Controller Node Stat
                    RowLayout {
                        spacing: 12
                        Rectangle {
                            width: 44
                            height: 44
                            radius: 8
                            color: "#1B1C33"
                            Text {
                                anchors.centerIn: parent
                                text: "★"
                                color: "#818CF8"
                                font.pixelSize: 20
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: "CONTROLLER NODE"
                                color: "#71717A"
                                font.pixelSize: 11
                                font.bold: true
                            }
                            Text {
                                text: appController.isConnected && appController.controllerBroker.id !== undefined
                                      ? "Node " + appController.controllerBroker.id
                                      : "None"
                                color: "#818CF8"
                                font.pixelSize: 18
                                font.bold: true
                            }
                        }
                    }

                    Rectangle { width: 1; height: 40; color: "#282834" }

                    // Cluster Health Stat
                    RowLayout {
                        spacing: 12
                        Rectangle {
                            width: 44
                            height: 44
                            radius: 8
                            color: appController.healthInfo.is_healthy ? "#0B2B20" : "#381313"
                            Text {
                                anchors.centerIn: parent
                                text: appController.healthInfo.is_healthy ? "✅" : "⚠️"
                                font.pixelSize: 18
                            }
                        }
                        ColumnLayout {
                            spacing: 2
                            Text {
                                text: "CLUSTER HEALTH"
                                color: "#71717A"
                                font.pixelSize: 11
                                font.bold: true
                            }
                            StatusBadge {
                                label: appController.isConnected ? (appController.healthInfo.status_text || "HEALTHY") : "DISCONNECTED"
                                type: appController.isConnected ? (appController.healthInfo.is_healthy ? "healthy" : "critical") : "muted"
                            }
                        }
                    }

                    Item { Layout.fillWidth: true }

                    // Refresh Button
                    Button {
                        enabled: appController.isConnected && !appController.isBusy
                        implicitHeight: 38
                        implicitWidth: 120
                        onClicked: appController.refreshAllClusterData()

                        contentItem: RowLayout {
                            spacing: 6
                            anchors.centerIn: parent
                            Text {
                                text: "🔄"
                                font.pixelSize: 12
                            }
                            Text {
                                text: "Refresh Data"
                                color: "#FFFFFF"
                                font.bold: true
                                font.pixelSize: 12
                            }
                        }
                        background: Rectangle {
                            radius: 8
                            color: parent.hovered ? "#FF653D" : "#F04D23"
                        }
                    }
                }
            }

            // Section Title
            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Cluster Brokers & Nodes"
                    color: "#FFFFFF"
                    font.pixelSize: 18
                    font.bold: true
                }
                Item { Layout.fillWidth: true }
                Text {
                    visible: appController.isConnected
                    text: "Click a node action to enter/exit maintenance"
                    color: "#71717A"
                    font.pixelSize: 12
                }
            }

            // Disconnected / Empty Placeholder
            Rectangle {
                visible: !appController.isConnected || appController.brokers.length === 0
                Layout.fillWidth: true
                implicitHeight: 280
                radius: 12
                color: "#16161D"
                border.color: "#282834"

                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 12

                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: appController.isConnected ? "📡" : "🔌"
                        font.pixelSize: 40
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: appController.isConnected ? "No brokers discovered yet." : "Not Connected to Redpanda Cluster"
                        color: "#FFFFFF"
                        font.pixelSize: 16
                        font.bold: true
                    }
                    Text {
                        Layout.alignment: Qt.AlignHCenter
                        text: appController.isConnected
                              ? "Click 'Refresh Data' to query rpk cluster info."
                              : "Select a profile from the top bar and click 'Connect' to manage the cluster."
                        color: "#A1A1AA"
                        font.pixelSize: 13
                    }
                }
            }

            // Broker Cards Grid
            Flow {
                visible: appController.isConnected && appController.brokers.length > 0
                Layout.fillWidth: true
                spacing: 18

                Repeater {
                    model: appController.brokers
                    delegate: BrokerCard {
                        broker: modelData
                        isBusy: appController.isBusy
                        pendingNodeId: root.pendingMaintenanceNodeId

                        onEnableMaintenanceRequested: {
                            root.pendingMaintenanceNodeId = nodeId;
                            root.requestEnableMaintenance(nodeId);
                        }
                        onDisableMaintenanceRequested: {
                            root.pendingMaintenanceNodeId = nodeId;
                            root.requestDisableMaintenance(nodeId);
                        }
                    }
                }
            }
        }
    }
}
