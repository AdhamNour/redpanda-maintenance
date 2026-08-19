import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property int selectedProfileId: -1
    property bool isEditing: false

    function loadProfileForm(prof) {
        if (!prof) {
            nameInput.text = "";
            hostInput.text = "";
            portInput.text = "22";
            sshUserInput.text = "";
            sshPassInput.text = "";
            sshKeyInput.text = "";
            authTypeCombo.currentIndex = 0;
            saslUserInput.text = "";
            saslPassInput.text = "";
            saslMechCombo.currentIndex = 0;
            root.selectedProfileId = -1;
            return;
        }

        root.selectedProfileId = prof.id || -1;
        nameInput.text = prof.name || "";
        hostInput.text = prof.host || "";
        portInput.text = String(prof.port || 22);
        sshUserInput.text = prof.ssh_user || "";
        sshPassInput.text = prof.ssh_password || "";
        sshKeyInput.text = prof.ssh_key_path || "";
        authTypeCombo.currentIndex = (prof.ssh_auth_type === "key") ? 1 : 0;
        saslUserInput.text = prof.sasl_user || "";
        saslPassInput.text = prof.sasl_password || "";

        if (prof.sasl_mechanism === "SCRAM-SHA-512") saslMechCombo.currentIndex = 1;
        else if (prof.sasl_mechanism === "PLAIN") saslMechCombo.currentIndex = 2;
        else saslMechCombo.currentIndex = 0;
    }

    Component.onCompleted: {
        if (appController.currentProfile && appController.currentProfile.id) {
            loadProfileForm(appController.currentProfile);
        }
    }

    RowLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24

        // Left Pane: Profiles List
        Rectangle {
            Layout.preferredWidth: 300
            Layout.fillHeight: true
            radius: 12
            color: "#16161D"
            border.color: "#282834"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 12

                RowLayout {
                    Layout.fillWidth: true
                    Text {
                        text: "Saved Clusters"
                        color: "#FFFFFF"
                        font.bold: true
                        font.pixelSize: 15
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "+ New"
                        implicitHeight: 28
                        implicitWidth: 65
                        onClicked: {
                            loadProfileForm(null);
                            nameInput.text = "New Cluster Profile";
                        }
                        contentItem: Text {
                            text: "+ New"
                            color: "#FFFFFF"
                            font.bold: true
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        background: Rectangle {
                            radius: 4
                            color: parent.hovered ? "#FF653D" : "#F04D23"
                        }
                    }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#282834" }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ListView {
                        id: profileList
                        anchors.fill: parent
                        model: appController.profiles
                        spacing: 8

                        delegate: Rectangle {
                            width: profileList.width
                            implicitHeight: 56
                            radius: 8
                            color: root.selectedProfileId === modelData.id ? "#272738" : (profileMouse.containsMouse ? "#20202C" : "#1A1A24")
                            border.color: root.selectedProfileId === modelData.id ? "#F04D23" : "#2E2E3E"

                            MouseArea {
                                id: profileMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    root.loadProfileForm(modelData);
                                    appController.selectProfile(modelData.id);
                                }
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10

                                Rectangle {
                                    width: 32
                                    height: 32
                                    radius: 6
                                    color: "#13131A"
                                    Text {
                                        anchors.centerIn: parent
                                        text: "🐼"
                                        font.pixelSize: 14
                                    }
                                }

                                ColumnLayout {
                                    spacing: 2
                                    Text {
                                        text: modelData.name
                                        color: "#FFFFFF"
                                        font.bold: true
                                        font.pixelSize: 13
                                    }
                                    Text {
                                        text: modelData.host + ":" + modelData.port
                                        color: "#8E8EA0"
                                        font.pixelSize: 11
                                    }
                                }
                            }
                        }
                    }
                }

                Text {
                    text: "Storage: " + appController.databasePath
                    color: "#525266"
                    font.pixelSize: 10
                    wrapMode: Text.WrapAnywhere
                    Layout.fillWidth: true
                }
            }
        }

        // Right Pane: Profile Form
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            radius: 12
            color: "#16161D"
            border.color: "#282834"

            ScrollView {
                anchors.fill: parent
                anchors.margins: 24
                clip: true

                ColumnLayout {
                    width: parent.width
                    spacing: 20

                    Text {
                        text: root.selectedProfileId >= 0 ? "Edit Cluster Profile" : "Create New Cluster Profile"
                        color: "#FFFFFF"
                        font.bold: true
                        font.pixelSize: 18
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#282834" }

                    // General & SSH Details
                    Text { text: "1. GENERAL & SSH CONNECTION"; color: "#F04D23"; font.bold: true; font.pixelSize: 12 }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "Profile Name"; color: "#A1A1AA"; font.pixelSize: 12 }
                            TextField {
                                id: nameInput
                                Layout.fillWidth: true
                                placeholderText: "e.g. US-East Production"
                                color: "#FFFFFF"
                                background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "SSH Remote Host (IP / Hostname)"; color: "#A1A1AA"; font.pixelSize: 12 }
                            TextField {
                                id: hostInput
                                Layout.fillWidth: true
                                placeholderText: "10.0.0.1"
                                color: "#FFFFFF"
                                background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                            }
                        }
                        ColumnLayout {
                            Layout.preferredWidth: 100
                            spacing: 4
                            Text { text: "SSH Port"; color: "#A1A1AA"; font.pixelSize: 12 }
                            TextField {
                                id: portInput
                                Layout.fillWidth: true
                                text: "22"
                                color: "#FFFFFF"
                                background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "SSH Username"; color: "#A1A1AA"; font.pixelSize: 12 }
                            TextField {
                                id: sshUserInput
                                Layout.fillWidth: true
                                placeholderText: "ubuntu / root"
                                color: "#FFFFFF"
                                background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "Auth Type"; color: "#A1A1AA"; font.pixelSize: 12 }
                            ComboBox {
                                id: authTypeCombo
                                Layout.fillWidth: true
                                model: ["Password", "SSH Private Key (.pem / .id_rsa)"]
                            }
                        }
                    }

                    ColumnLayout {
                        visible: authTypeCombo.currentIndex === 0
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "SSH Password"; color: "#A1A1AA"; font.pixelSize: 12 }
                        TextField {
                            id: sshPassInput
                            Layout.fillWidth: true
                            echoMode: TextInput.Password
                            placeholderText: "SSH Password"
                            color: "#FFFFFF"
                            background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                        }
                    }

                    ColumnLayout {
                        visible: authTypeCombo.currentIndex === 1
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "SSH Private Key Absolute Path"; color: "#A1A1AA"; font.pixelSize: 12 }
                        TextField {
                            id: sshKeyInput
                            Layout.fillWidth: true
                            placeholderText: "C:/Users/name/.ssh/id_rsa"
                            color: "#FFFFFF"
                            background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                        }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: "#282834" }

                    // Redpanda SASL Details
                    Text { text: "2. REDPANDA SASL CREDENTIALS"; color: "#F04D23"; font.bold: true; font.pixelSize: 12 }

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "SASL Username"; color: "#A1A1AA"; font.pixelSize: 12 }
                            TextField {
                                id: saslUserInput
                                Layout.fillWidth: true
                                placeholderText: "admin"
                                color: "#FFFFFF"
                                background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 4
                            Text { text: "SASL Password"; color: "#A1A1AA"; font.pixelSize: 12 }
                            TextField {
                                id: saslPassInput
                                Layout.fillWidth: true
                                echoMode: TextInput.Password
                                placeholderText: "SASL Password"
                                color: "#FFFFFF"
                                background: Rectangle { radius: 6; color: "#111116"; border.color: "#343444" }
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Text { text: "SASL Mechanism"; color: "#A1A1AA"; font.pixelSize: 12 }
                        ComboBox {
                            id: saslMechCombo
                            Layout.fillWidth: true
                            model: ["SCRAM-SHA-256", "SCRAM-SHA-512", "PLAIN"]
                        }
                    }

                    Item { Layout.preferredHeight: 10 }

                    // Save / Delete Buttons
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Button {
                            implicitHeight: 40
                            implicitWidth: 140
                            text: "Save Profile"
                            onClicked: {
                                var data = {
                                    "name": nameInput.text || "Untitled Cluster",
                                    "host": hostInput.text,
                                    "port": parseInt(portInput.text) || 22,
                                    "ssh_user": sshUserInput.text,
                                    "ssh_auth_type": authTypeCombo.currentIndex === 1 ? "key" : "password",
                                    "ssh_password": sshPassInput.text,
                                    "ssh_key_path": sshKeyInput.text,
                                    "sasl_user": saslUserInput.text,
                                    "sasl_password": saslPassInput.text,
                                    "sasl_mechanism": saslMechCombo.currentText
                                };

                                if (root.selectedProfileId >= 0) {
                                    appController.updateProfile(root.selectedProfileId, data);
                                } else {
                                    var newId = appController.addProfile(data);
                                    root.selectedProfileId = newId;
                                }
                            }

                            contentItem: Text {
                                text: "Save Profile"
                                color: "#FFFFFF"
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 8
                                color: parent.hovered ? "#FF653D" : "#F04D23"
                            }
                        }

                        Button {
                            visible: root.selectedProfileId >= 0
                            implicitHeight: 40
                            implicitWidth: 120
                            text: "Delete Profile"
                            onClicked: {
                                appController.deleteProfile(root.selectedProfileId);
                                root.loadProfileForm(null);
                            }
                            contentItem: Text {
                                text: "Delete Profile"
                                color: "#F87171"
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            background: Rectangle {
                                radius: 8
                                color: parent.hovered ? "#381313" : "#241515"
                                border.color: "#EF4444"
                            }
                        }
                    }
                }
            }
        }
    }
}
