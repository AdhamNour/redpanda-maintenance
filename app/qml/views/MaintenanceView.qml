import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: root

    property int wizardStep: 1
    property int selectedNodeId: -1

    signal requestEnableMaintenance(int nodeId)
    signal requestDisableMaintenance(int nodeId)

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 24
            anchors.margins: 24

            // Header
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 4
                    Text {
                        text: "Cluster Maintenance & Rolling Upgrades"
                        color: "#FFFFFF"
                        font.pixelSize: 20
                        font.bold: true
                    }
                    Text {
                        text: "Monitor partition draining and safely orchestrate node maintenance without downtime"
                        color: "#A1A1AA"
                        font.pixelSize: 13
                    }
                }
            }

            // Section 1: Maintenance Status Matrix
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: matrixCol.implicitHeight + 36
                radius: 12
                color: "#16161D"
                border.color: "#282834"

                ColumnLayout {
                    id: matrixCol
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "Node Maintenance Matrix (rpk cluster maintenance status)"
                            color: "#FFFFFF"
                            font.pixelSize: 15
                            font.bold: true
                        }
                    }

                    // Table Header
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 32
                        color: "#1F1F2A"
                        radius: 6

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            spacing: 12

                            Text { text: "NODE ID"; color: "#71717A"; font.bold: true; font.pixelSize: 11; Layout.preferredWidth: 80 }
                            Text { text: "DRAINING"; color: "#71717A"; font.bold: true; font.pixelSize: 11; Layout.preferredWidth: 100 }
                            Text { text: "FINISHED"; color: "#71717A"; font.bold: true; font.pixelSize: 11; Layout.preferredWidth: 100 }
                            Text { text: "STATUS"; color: "#71717A"; font.bold: true; font.pixelSize: 11; Layout.preferredWidth: 120 }
                            Item { Layout.fillWidth: true }
                            Text { text: "ACTION"; color: "#71717A"; font.bold: true; font.pixelSize: 11; Layout.preferredWidth: 140 }
                        }
                    }

                    // Empty placeholder
                    Text {
                        visible: !appController.isConnected || appController.maintenanceList.length === 0
                        text: appController.isConnected ? "No maintenance data received." : "Connect to cluster to view maintenance status matrix."
                        color: "#71717A"
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignHCenter
                    }

                    // Table Rows
                    Repeater {
                        model: appController.maintenanceList
                        delegate: Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 40
                            color: index % 2 === 0 ? "#181822" : "#14141B"
                            radius: 4

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 16
                                anchors.rightMargin: 16
                                spacing: 12

                                Text {
                                    text: "Node " + modelData.node_id
                                    color: "#FFFFFF"
                                    font.bold: true
                                    font.pixelSize: 12
                                    Layout.preferredWidth: 80
                                }

                                Text {
                                    text: modelData.draining ? "Yes" : "No"
                                    color: modelData.draining ? "#FBBF24" : "#A1A1AA"
                                    font.pixelSize: 12
                                    Layout.preferredWidth: 100
                                }

                                Text {
                                    text: modelData.finished ? "Yes" : "No"
                                    color: modelData.finished ? "#34D399" : "#A1A1AA"
                                    font.pixelSize: 12
                                    Layout.preferredWidth: 100
                                }

                                StatusBadge {
                                    label: modelData.status
                                    type: modelData.status === "ACTIVE" ? "healthy" : "warning"
                                    Layout.preferredWidth: 120
                                }

                                Item { Layout.fillWidth: true }

                                Button {
                                    Layout.preferredWidth: 150
                                    implicitHeight: 30
                                    enabled: !appController.isBusy
                                    onClicked: {
                                        if (modelData.status === "ACTIVE") {
                                            root.requestEnableMaintenance(modelData.node_id);
                                        } else {
                                            root.requestDisableMaintenance(modelData.node_id);
                                        }
                                    }
                                    contentItem: Text {
                                        text: appController.isBusy
                                              ? "⏳ Working..."
                                              : (modelData.status === "ACTIVE" ? "Enter Maintenance" : "Exit Maintenance")
                                        color: appController.isBusy
                                               ? "#A1A1AA"
                                               : "#FFFFFF"
                                        font.bold: true
                                        font.pixelSize: 11
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
                                    background: Rectangle {
                                        radius: 4
                                        color: appController.isBusy
                                               ? "#242432"
                                               : (modelData.status === "ACTIVE"
                                                  ? (parent.hovered ? "#FF653D" : "#F04D23")
                                                  : (parent.hovered ? "#059669" : "#10B981"))
                                        border.color: modelData.status === "ACTIVE" ? "#F04D23" : "#059669"
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Section 2: Guided Rolling Maintenance Wizard
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: wizardCol.implicitHeight + 36
                radius: 12
                color: "#16161D"
                border.color: "#282834"

                ColumnLayout {
                    id: wizardCol
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 16

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "🛠️ Guided Rolling Maintenance Assistant"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Item { Layout.fillWidth: true }
                        Text {
                            text: "Step " + root.wizardStep + " of 3"
                            color: "#F04D23"
                            font.bold: true
                            font.pixelSize: 12
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#282834" }

                    // Step 1: Pre-flight Health Check
                    ColumnLayout {
                        visible: root.wizardStep === 1
                        Layout.fillWidth: true
                        spacing: 12

                        Text {
                            text: "Step 1: Health Pre-Check"
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 14
                        }
                        Text {
                            text: "Before draining a broker, ensure there are no under-replicated or offline partitions to avoid data loss."
                            color: "#A1A1AA"
                            font.pixelSize: 13
                        }

                        RowLayout {
                            spacing: 12
                            StatusBadge {
                                label: appController.healthInfo.is_healthy ? "Pre-check Passed (Cluster Healthy)" : "Warning: Cluster Degraded"
                                type: appController.healthInfo.is_healthy ? "healthy" : "critical"
                            }
                        }

                        Button {
                            implicitHeight: 36
                            implicitWidth: 160
                            text: "Proceed to Node Select"
                            enabled: appController.isConnected
                            onClicked: root.wizardStep = 2
                            contentItem: Text {
                                text: "Proceed to Step 2 ➔"
                                color: "#FFFFFF"
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 6
                                color: parent.hovered ? "#FF653D" : "#F04D23"
                            }
                        }
                    }

                    // Step 2: Select Node
                    ColumnLayout {
                        visible: root.wizardStep === 2
                        Layout.fillWidth: true
                        spacing: 12

                        Text {
                            text: "Step 2: Select Broker Node to Drain"
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 14
                        }

                        ComboBox {
                            id: nodeCombo
                            Layout.fillWidth: true
                            implicitHeight: 40
                            model: appController.brokers
                            textRole: "id"
                            displayText: currentText !== "" ? "Broker Node " + currentText : "Select Node..."
                            onCurrentIndexChanged: {
                                if (currentIndex >= 0 && currentIndex < appController.brokers.length) {
                                    root.selectedNodeId = appController.brokers[currentIndex].id;
                                }
                            }
                        }

                        RowLayout {
                            spacing: 12
                            Button {
                                text: "Back"
                                implicitHeight: 36
                                implicitWidth: 80
                                onClicked: root.wizardStep = 1
                            }
                            Button {
                                text: "Drain & Enter Maintenance"
                                implicitHeight: 36
                                implicitWidth: 200
                                enabled: root.selectedNodeId >= 0 && !appController.isBusy
                                onClicked: {
                                    root.requestEnableMaintenance(root.selectedNodeId);
                                    root.wizardStep = 3;
                                }
                                contentItem: Text {
                                    text: "Drain & Enter Maintenance ➔"
                                    color: "#FFFFFF"
                                    font.bold: true
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 6
                                    color: parent.hovered ? "#FF653D" : "#F04D23"
                                }
                            }
                        }
                    }

                    // Step 3: Complete Maintenance & Recovery
                    ColumnLayout {
                        visible: root.wizardStep === 3
                        Layout.fillWidth: true
                        spacing: 12

                        Text {
                            text: "Step 3: Maintenance & Return to Cluster"
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 14
                        }
                        Text {
                            text: "Perform your server update / reboot now. Once finished, exit maintenance to return the node to active service."
                            color: "#A1A1AA"
                            font.pixelSize: 13
                        }

                        RowLayout {
                            spacing: 12
                            Button {
                                text: "Exit Maintenance on Node " + root.selectedNodeId
                                implicitHeight: 36
                                implicitWidth: 220
                                enabled: !appController.isBusy
                                onClicked: {
                                    root.requestDisableMaintenance(root.selectedNodeId);
                                    root.wizardStep = 1;
                                }
                                contentItem: Text {
                                    text: "Complete & Exit Maintenance"
                                    color: "#FFFFFF"
                                    font.bold: true
                                    horizontalAlignment: Text.AlignHCenter
                                    verticalAlignment: Text.AlignVCenter
                                }
                                background: Rectangle {
                                    radius: 6
                                    color: parent.hovered ? "#059669" : "#10B981"
                                }
                            }
                            Button {
                                text: "Reset Wizard"
                                implicitHeight: 36
                                implicitWidth: 120
                                onClicked: root.wizardStep = 1
                            }
                        }
                    }
                }
            }
        }
    }
}
