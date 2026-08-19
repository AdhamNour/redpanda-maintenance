import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Dialog {
    id: root

    property string titleText: "Confirm Action"
    property string messageText: "Are you sure you want to proceed?"
    property string confirmButtonText: "Confirm"
    property bool isDestructive: false

    signal confirmed()
    signal cancelled()

    modal: true
    dim: true
    anchors.centerIn: parent
    implicitWidth: 420
    implicitHeight: 220
    padding: 24

    background: Rectangle {
        radius: 12
        color: "#1B1B22"
        border.color: root.isDestructive ? "#EF4444" : "#F04D23"
        border.width: 1
    }

    contentItem: ColumnLayout {
        spacing: 16

        RowLayout {
            spacing: 10
            Rectangle {
                width: 32
                height: 32
                radius: 16
                color: root.isDestructive ? "#381313" : "#3D1A14"
                Text {
                    anchors.centerIn: parent
                    text: root.isDestructive ? "⚠️" : "ℹ️"
                    font.pixelSize: 14
                }
            }

            Text {
                text: root.titleText
                color: "#FFFFFF"
                font.pixelSize: 16
                font.bold: true
            }
        }

        Text {
            Layout.fillWidth: true
            text: root.messageText
            color: "#D4D4D8"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            lineHeight: 1.3
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Button {
                Layout.fillWidth: true
                implicitHeight: 36
                text: "Cancel"
                onClicked: {
                    root.cancelled();
                    root.close();
                }

                contentItem: Text {
                    text: "Cancel"
                    color: "#A1A1AA"
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color: parent.hovered ? "#282834" : "#1F1F28"
                    border.color: "#3A3A4C"
                }
            }

            Button {
                Layout.fillWidth: true
                implicitHeight: 36
                text: root.confirmButtonText
                onClicked: {
                    root.confirmed();
                    root.close();
                }

                contentItem: Text {
                    text: root.confirmButtonText
                    color: "#FFFFFF"
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color: root.isDestructive ? (parent.hovered ? "#DC2626" : "#EF4444") : (parent.hovered ? "#FF653D" : "#F04D23")
                }
            }
        }
    }

    Shortcut {
        sequence: "Return"
        onActivated: if (root.visible) { root.confirmed(); root.close(); }
    }
    Shortcut {
        sequence: "Enter"
        onActivated: if (root.visible) { root.confirmed(); root.close(); }
    }
    Shortcut {
        sequence: "Escape"
        onActivated: if (root.visible) { root.cancelled(); root.close(); }
    }
}
