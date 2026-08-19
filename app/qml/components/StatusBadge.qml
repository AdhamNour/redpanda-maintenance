import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root

    property string label: ""
    property string type: "healthy" // healthy, warning, critical, controller, info, muted
    property bool showDot: true

    implicitHeight: 26
    implicitWidth: badgeRow.implicitWidth + 18
    radius: 13

    // Computed colors based on type
    color: {
        switch(type) {
            case "healthy": return "#0B2B20"
            case "warning": return "#332206"
            case "critical": return "#381313"
            case "controller": return "#191B3A"
            case "info": return "#11223D"
            default: return "#22222B"
        }
    }

    border.color: {
        switch(type) {
            case "healthy": return "#10B981"
            case "warning": return "#F59E0B"
            case "critical": return "#EF4444"
            case "controller": return "#818CF8"
            case "info": return "#3B82F6"
            default: return "#404052"
        }
    }
    border.width: 1

    RowLayout {
        id: badgeRow
        anchors.centerIn: parent
        spacing: 6

        Rectangle {
            visible: root.showDot
            width: 6
            height: 6
            radius: 3
            color: root.border.color
        }

        Text {
            text: root.label
            color: {
                switch(root.type) {
                    case "healthy": return "#34D399"
                    case "warning": return "#FBBF24"
                    case "critical": return "#F87171"
                    case "controller": return "#A5B4FC"
                    case "info": return "#60A5FA"
                    default: return "#A1A1AA"
                }
            }
            font.pixelSize: 11
            font.bold: true
            font.family: "Segoe UI, sans-serif"
        }
    }
}
