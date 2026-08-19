import QtQuick

QtObject {
    id: theme

    // Background Colors
    readonly property color bgDark: "#111114"
    readonly property color bgSidebar: "#16161B"
    readonly property color bgCard: "#1B1B22"
    readonly property color bgCardHover: "#23232C"
    readonly property color bgInput: "#131317"
    readonly property color bgDrawer: "#0D0D10"

    // Border Colors
    readonly property color borderSubtle: "#2A2A36"
    readonly property color borderCard: "#323242"
    readonly property color borderFocus: "#F04D23"

    // Brand & Accent Colors (Redpanda Theme)
    readonly property color primary: "#F04D23"
    readonly property color primaryHover: "#FF653D"
    readonly property color primaryPressed: "#D83F17"
    readonly property color primaryDim: "#3D1A14"

    // Status Colors
    readonly property color healthy: "#10B981"
    readonly property color healthyBg: "#0B2B20"
    readonly property color warning: "#F59E0B"
    readonly property color warningBg: "#332206"
    readonly property color critical: "#EF4444"
    readonly property color criticalBg: "#381313"
    readonly property color controller: "#6366F1"
    readonly property color controllerBg: "#191B3A"
    readonly property color info: "#3B82F6"
    readonly property color infoBg: "#11223D"

    // Text Colors
    readonly property color textPrimary: "#FAFAFA"
    readonly property color textSecondary: "#A1A1AA"
    readonly property color textMuted: "#71717A"
    readonly property color textOnPrimary: "#FFFFFF"

    // Sizing & Radii
    readonly property int radiusSm: 6
    readonly property int radiusMd: 10
    readonly property int radiusLg: 14

    // Typography
    readonly property string fontHeading: "Segoe UI, Inter, sans-serif"
    readonly property string fontMono: "Cascadia Code, Consolas, monospace"
}
