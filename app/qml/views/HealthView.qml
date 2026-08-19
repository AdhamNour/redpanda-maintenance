import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

Item {
    id: root

    property var appController

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 24
            anchors.margins: 24

            // Top Header
            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    spacing: 4
                    Text {
                        text: "Cluster Health & Diagnostics"
                        color: "#FFFFFF"
                        font.pixelSize: 20
                        font.bold: true
                    }
                    Text {
                        text: "Real-time partition metrics and cluster diagnostic reporting"
                        color: "#A1A1AA"
                        font.pixelSize: 13
                    }
                }
                Item { Layout.fillWidth: true }
                Button {
                    enabled: appController.isConnected && !appController.isBusy
                    text: "Re-check Health"
                    implicitHeight: 36
                    implicitWidth: 130
                    onClicked: appController.refreshAllClusterData()
                    contentItem: Text {
                        text: "Re-check Health"
                        color: "#FFFFFF"
                        font.bold: true
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    background: Rectangle {
                        radius: 8
                        color: parent.hovered ? "#FF653D" : "#F04D23"
                    }
                }
            }

            // Health Metric Cards Row
            RowLayout {
                Layout.fillWidth: true
                spacing: 16

                // Status Card
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 110
                    radius: 12
                    color: "#16161D"
                    border.color: "#282834"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 8
                        Text {
                            text: "OVERALL STATUS"
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

                // Under-Replicated Partitions Card
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 110
                    radius: 12
                    color: "#16161D"
                    border.color: appController.healthInfo.under_replicated_partitions > 0 ? "#EF4444" : "#282834"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 6
                        Text {
                            text: "UNDER-REPLICATED PARTITIONS"
                            color: "#71717A"
                            font.pixelSize: 11
                            font.bold: true
                        }
                        Text {
                            text: appController.isConnected ? String(appController.healthInfo.under_replicated_partitions || 0) : "-"
                            color: appController.healthInfo.under_replicated_partitions > 0 ? "#F87171" : "#10B981"
                            font.pixelSize: 22
                            font.bold: true
                        }
                    }
                }

                // Leaderless Partitions Card
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 110
                    radius: 12
                    color: "#16161D"
                    border.color: appController.healthInfo.leaderless_partitions > 0 ? "#EF4444" : "#282834"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 6
                        Text {
                            text: "LEADERLESS PARTITIONS"
                            color: "#71717A"
                            font.pixelSize: 11
                            font.bold: true
                        }
                        Text {
                            text: appController.isConnected ? String(appController.healthInfo.leaderless_partitions || 0) : "-"
                            color: appController.healthInfo.leaderless_partitions > 0 ? "#F87171" : "#10B981"
                            font.pixelSize: 22
                            font.bold: true
                        }
                    }
                }

                // Offline Partitions Card
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 110
                    radius: 12
                    color: "#16161D"
                    border.color: appController.healthInfo.offline_partitions > 0 ? "#EF4444" : "#282834"

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 6
                        Text {
                            text: "OFFLINE PARTITIONS"
                            color: "#71717A"
                            font.pixelSize: 11
                            font.bold: true
                        }
                        Text {
                            text: appController.isConnected ? String(appController.healthInfo.offline_partitions || 0) : "-"
                            color: appController.healthInfo.offline_partitions > 0 ? "#F87171" : "#10B981"
                            font.pixelSize: 22
                            font.bold: true
                        }
                    }
                }
            }

            // Raw Output Inspector Container
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 340
                radius: 12
                color: "#131318"
                border.color: "#282834"

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 0

                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 44
                        color: "#181822"
                        radius: 12

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            Text {
                                text: "Diagnostics Output (rpk cluster health)"
                                color: "#FFFFFF"
                                font.bold: true
                                font.pixelSize: 13
                            }
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#282834" }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true

                        TextArea {
                            readOnly: true
                            text: appController.healthInfo.raw_output || (appController.isConnected ? "No diagnostic output available." : "Connect to cluster to view diagnostic health output.")
                            color: "#34D399"
                            font.family: "Cascadia Code, Consolas, monospace"
                            font.pixelSize: 12
                            background: null
                            wrapMode: TextEdit.WrapAnywhere
                            padding: 16
                        }
                    }
                }
            }
        }
    }
}
