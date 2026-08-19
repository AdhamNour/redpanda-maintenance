import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "views"

ApplicationWindow {
    id: window
    visible: true
    width: 1140
    height: 780
    minimumWidth: 960
    minimumHeight: 640
    title: "PandaPilot - Redpanda Cluster Maintenance Cockpit"
    color: "#0E0E12"

    // Local log list for the LogDrawer
    property var logItems: []

    // State for ConfirmDialog
    property int pendingMaintenanceNodeId: -1
    property bool pendingIsEnable: true

    // State for floating Maintenance Toast Banner
    property string toastMessage: ""
    property string toastIp: ""
    property bool toastVisible: false
    property bool toastCopied: false

    Timer {
        id: toastTimer
        interval: 8000
        onTriggered: window.toastVisible = false
    }

    Connections {
        target: appController
        function onLogAppended(timestamp, level, message) {
            var newArr = window.logItems.slice();
            newArr.push({ "timestamp": timestamp, "level": level, "message": message });
            if (newArr.length > 500) newArr.shift();
            window.logItems = newArr;
        }
        function onMaintenanceSucceeded(nodeId, brokerHost) {
            window.toastMessage = "Node " + nodeId + " is in maintenance mode.";
            window.toastIp = brokerHost;
            window.toastCopied = false;
            window.toastVisible = true;
            toastTimer.restart();
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ==========================================
        // TOP HEADER BAR
        // ==========================================
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 64
            color: "#16161D"
            border.color: "#282834"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 16

                // Brand Logo & Title
                RowLayout {
                    spacing: 10
                    Image {
                        Layout.preferredWidth: 36
                        Layout.preferredHeight: 36
                        sourceSize.width: 36
                        sourceSize.height: 36
                        source: "../resources/icon.png"
                        mipmap: true
                        smooth: true
                        fillMode: Image.PreserveAspectFit
                    }
                    ColumnLayout {
                        spacing: 0
                        Text {
                            text: "PandaPilot"
                            color: "#FFFFFF"
                            font.pixelSize: 16
                            font.bold: true
                        }
                        Text {
                            text: "Redpanda Cluster Maintenance"
                            color: "#F04D23"
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                }

                Rectangle { width: 1; height: 32; color: "#2E2E3E" }

                // Active Profile Dropdown
                RowLayout {
                    spacing: 8
                    Text {
                        text: "Cluster:"
                        color: "#A1A1AA"
                        font.pixelSize: 12
                    }

                    ComboBox {
                        id: profilePicker
                        implicitWidth: 220
                        implicitHeight: 34
                        model: appController.profiles
                        textRole: "name"
                        currentIndex: {
                            for (var i = 0; i < appController.profiles.length; i++) {
                                if (appController.profiles[i].id === appController.currentProfile.id) return i;
                            }
                            return 0;
                        }
                        onActivated: {
                            var prof = appController.profiles[index];
                            if (prof) appController.selectProfile(prof.id);
                        }

                        contentItem: Text {
                            leftPadding: 12
                            rightPadding: profilePicker.indicator.width + 12
                            text: profilePicker.displayText
                            font.bold: true
                            font.pixelSize: 12
                            color: "#FFFFFF"
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
                        }

                        background: Rectangle {
                            radius: 6
                            color: profilePicker.hovered ? "#222230" : "#181822"
                            border.color: profilePicker.visualFocus ? "#F04D23" : "#343446"
                            border.width: 1
                        }

                        popup: Popup {
                            y: profilePicker.height + 4
                            width: profilePicker.width
                            implicitHeight: contentItem.implicitHeight + 12
                            padding: 6

                            contentItem: ListView {
                                clip: true
                                implicitHeight: contentHeight
                                model: profilePicker.popup.visible ? profilePicker.delegateModel : null
                                currentIndex: profilePicker.highlightedIndex
                                ScrollIndicator.vertical: ScrollIndicator { }
                            }

                            background: Rectangle {
                                radius: 8
                                color: "#161622"
                                border.color: "#343448"
                                border.width: 1
                            }
                        }

                        delegate: ItemDelegate {
                            width: profilePicker.width - 12
                            implicitHeight: 32
                            highlighted: profilePicker.highlightedIndex === index

                            contentItem: Text {
                                text: modelData.name
                                color: highlighted ? "#F04D23" : "#FFFFFF"
                                font.bold: highlighted
                                font.pixelSize: 12
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }

                            background: Rectangle {
                                radius: 4
                                color: highlighted ? "#262638" : "transparent"
                            }
                        }
                    }
                }

                // Connect / Disconnect Action Button
                Button {
                    id: connectBtn
                    implicitHeight: 34
                    implicitWidth: 110
                    enabled: !appController.isBusy

                    contentItem: RowLayout {
                        spacing: 6
                        anchors.centerIn: parent
                        Text {
                            text: appController.isConnected ? "🔌" : "⚡"
                            font.pixelSize: 11
                        }
                        Text {
                            text: appController.isConnected ? "Disconnect" : "Connect"
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 12
                        }
                    }

                    background: Rectangle {
                        radius: 6
                        color: appController.isConnected
                               ? (parent.hovered ? "#381313" : "#241515")
                               : (parent.hovered ? "#FF653D" : "#F04D23")
                        border.color: appController.isConnected ? "#EF4444" : "#F04D23"
                    }

                    onClicked: {
                        if (appController.isConnected) {
                            appController.disconnectSSH();
                        } else {
                            appController.connectCurrentProfile();
                        }
                    }
                }

                // Status Indicator Pill
                StatusBadge {
                    label: appController.connectionStatus
                    type: appController.isConnected ? "healthy" : (appController.isBusy ? "warning" : "muted")
                }

                Item { Layout.fillWidth: true }

                // Busy Activity Spinner / Text
                RowLayout {
                    visible: appController.isBusy
                    spacing: 8
                    BusyIndicator {
                        implicitWidth: 22
                        implicitHeight: 22
                        running: appController.isBusy
                    }
                    Text {
                        text: appController.busyMessage || "Working..."
                        color: "#FBBF24"
                        font.pixelSize: 12
                        font.bold: true
                    }
                }
            }
        }

        // ==========================================
        // MAIN BODY (SIDEBAR + VIEWS)
        // ==========================================
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Navigation Sidebar
            Rectangle {
                Layout.preferredWidth: 210
                Layout.fillHeight: true
                color: "#131318"
                border.color: "#282834"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 6

                    // Navigation Buttons
                    Repeater {
                        model: [
                            { name: "Dashboard", icon: "📊", viewIndex: 0 },
                            { name: "Cluster Health", icon: "🩺", viewIndex: 1 },
                            { name: "Maintenance", icon: "🛠️", viewIndex: 2 },
                            { name: "Profiles (DB)", icon: "⚙️", viewIndex: 3 }
                        ]

                        delegate: Rectangle {
                            Layout.fillWidth: true
                            implicitHeight: 44
                            radius: 8
                            color: viewStack.currentIndex === modelData.viewIndex ? "#242432" : (navMouse.containsMouse ? "#1C1C24" : "transparent")
                            border.color: viewStack.currentIndex === modelData.viewIndex ? "#F04D23" : "transparent"

                            MouseArea {
                                id: navMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: viewStack.currentIndex = modelData.viewIndex
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 14
                                anchors.rightMargin: 14
                                spacing: 10

                                Text {
                                    text: modelData.icon
                                    font.pixelSize: 15
                                }

                                Text {
                                    text: modelData.name
                                    color: viewStack.currentIndex === modelData.viewIndex ? "#FFFFFF" : "#A1A1AA"
                                    font.bold: viewStack.currentIndex === modelData.viewIndex
                                    font.pixelSize: 13
                                }
                            }
                        }
                    }

                    Item { Layout.fillHeight: true }

                    // Database Storage Footer
                    Rectangle {
                        Layout.fillWidth: true
                        implicitHeight: 50
                        color: "#181822"
                        radius: 6

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 8
                            spacing: 2
                            Text {
                                text: "SQLite Database"
                                color: "#A1A1AA"
                                font.bold: true
                                font.pixelSize: 10
                            }
                            Text {
                                text: "pandapilot.db"
                                color: "#34D399"
                                font.pixelSize: 10
                            }
                        }
                    }
                }
            }

            // View Stack Container
            StackLayout {
                id: viewStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: 0

                DashboardView {
                    onRequestEnableMaintenance: function(nodeId) {
                        window.pendingMaintenanceNodeId = nodeId;
                        window.pendingIsEnable = true;
                        confirmDlg.titleText = "Enable Maintenance Mode";
                        confirmDlg.messageText = "Node " + nodeId + " will be placed into maintenance mode. Redpanda will drain partition leadership to other brokers before safely returning.";
                        confirmDlg.confirmButtonText = "Drain & Enable";
                        confirmDlg.isDestructive = false;
                        confirmDlg.open();
                    }
                    onRequestDisableMaintenance: function(nodeId) {
                        window.pendingMaintenanceNodeId = nodeId;
                        window.pendingIsEnable = false;
                        confirmDlg.titleText = "Disable Maintenance Mode";
                        confirmDlg.messageText = "Node " + nodeId + " will exit maintenance mode and rejoin active cluster replication.";
                        confirmDlg.confirmButtonText = "Exit Maintenance";
                        confirmDlg.isDestructive = false;
                        confirmDlg.open();
                    }
                }

                HealthView {}

                MaintenanceView {
                    onRequestEnableMaintenance: function(nodeId) {
                        window.pendingMaintenanceNodeId = nodeId;
                        window.pendingIsEnable = true;
                        confirmDlg.titleText = "Enable Maintenance Mode";
                        confirmDlg.messageText = "Node " + nodeId + " will be drained with --wait.";
                        confirmDlg.confirmButtonText = "Enable";
                        confirmDlg.isDestructive = false;
                        confirmDlg.open();
                    }
                    onRequestDisableMaintenance: function(nodeId) {
                        window.pendingMaintenanceNodeId = nodeId;
                        window.pendingIsEnable = false;
                        confirmDlg.titleText = "Disable Maintenance Mode";
                        confirmDlg.messageText = "Node " + nodeId + " will resume cluster operations.";
                        confirmDlg.confirmButtonText = "Disable";
                        confirmDlg.isDestructive = false;
                        confirmDlg.open();
                    }
                }

                ProfilesView {}
            }
        }

        // ==========================================
        // BOTTOM LOG DRAWER
        // ==========================================
        LogDrawer {
            id: logDrawer
            Layout.fillWidth: true
            logModel: window.logItems
            onClearRequested: window.logItems = []
        }
    }

    // Global Keyboard Shortcuts
    Shortcut {
        sequence: "Ctrl+R"
        onActivated: {
            if (appController.isConnected && !appController.isBusy) {
                appController.refreshAllClusterData();
            }
        }
    }
    Shortcut {
        sequence: "F5"
        onActivated: {
            if (appController.isConnected && !appController.isBusy) {
                appController.refreshAllClusterData();
            }
        }
    }
    Shortcut {
        sequence: "Ctrl+L"
        onActivated: logDrawer.isExpanded = !logDrawer.isExpanded
    }
    Shortcut {
        sequence: "Ctrl+1"
        onActivated: viewStack.currentIndex = 0
    }
    Shortcut {
        sequence: "Ctrl+2"
        onActivated: viewStack.currentIndex = 1
    }
    Shortcut {
        sequence: "Ctrl+3"
        onActivated: viewStack.currentIndex = 2
    }
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: viewStack.currentIndex = 3
    }

    // Floating Maintenance Success Toast Banner
    Rectangle {
        id: toastBanner
        visible: window.toastVisible
        anchors.top: parent.top
        anchors.topMargin: window.toastVisible ? 76 : -80
        anchors.horizontalCenter: parent.horizontalCenter
        implicitWidth: Math.min(parent.width - 40, 520)
        implicitHeight: 52
        radius: 10
        color: "#181824"
        border.color: "#10B981"
        border.width: 1
        z: 999

        Behavior on anchors.topMargin {
            NumberAnimation { duration: 250; easing.type: Easing.OutCubic }
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 16
            spacing: 12

            Text {
                text: "🛠️"
                font.pixelSize: 16
            }

            ColumnLayout {
                spacing: 1
                Text {
                    text: window.toastMessage
                    color: "#FFFFFF"
                    font.bold: true
                    font.pixelSize: 13
                }
                Text {
                    text: "IP: " + window.toastIp + (window.toastCopied ? " (Copied to clipboard!)" : "")
                    color: "#34D399"
                    font.pixelSize: 11
                    font.family: "Cascadia Code, Consolas, monospace"
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                implicitHeight: 30
                implicitWidth: 90
                onClicked: {
                    appController.copyToClipboard(window.toastIp);
                    window.toastCopied = true;
                }
                contentItem: Text {
                    text: window.toastCopied ? "✓ Copied" : "📋 Copy IP"
                    color: window.toastCopied ? "#34D399" : "#FFFFFF"
                    font.bold: true
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color: parent.hovered ? "#2D2D3E" : "#222230"
                    border.color: window.toastCopied ? "#10B981" : "#45455E"
                }
            }

            Button {
                implicitHeight: 26
                implicitWidth: 26
                onClicked: window.toastVisible = false
                contentItem: Text {
                    text: "✕"
                    color: "#A1A1AA"
                    font.bold: true
                    font.pixelSize: 11
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 13
                    color: parent.hovered ? "#333344" : "transparent"
                }
            }
        }
    }

    // Safety Confirmation Dialog
    ConfirmDialog {
        id: confirmDlg
        onConfirmed: {
            if (window.pendingMaintenanceNodeId >= 0) {
                if (window.pendingIsEnable) {
                    appController.enableMaintenance(window.pendingMaintenanceNodeId);
                } else {
                    appController.disableMaintenance(window.pendingMaintenanceNodeId);
                }
            }
        }
    }
}
