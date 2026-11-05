// @NAME@ top panel (The Linux Workbench theme engine)
// Launcher | gap | Task-Manager | space | clock | space | KVitals | gap | system tray
var THICKNESS = @HEIGHT@;
var STATS = [["CPU", ["cpu/all/usage"]], ["MEM", ["memory/physical/usedPercent"]], ["GPU", ["gpu/gpu0/usage"]], ["NET", ["network/all/download", "network/all/upload"]]];
var KVITALS_PINNED = "cpu/usage,ram/percentage,gpu:gpu0/usage,net/down,net/up";
var GAP = 10;                      // px, fixed spacers

if (typeof locked !== "undefined") { locked = false; }   // widgets must be unlocked to edit panels

// 1. remove: any panel on the top edge of the primary screen (screen 0), plus @NAME@ panels (or another
//    The Linux Workbench theme's)
//    on other screens (marked by us, or built by earlier versions: a top panel holding the
//    same set of widgets), which piled up when a panel landed on the wrong screen.
function hasAll(p, types) {
    for (var i = 0; i < types.length; i++) {
        try { if (p.widgets(types[i]).length === 0) return false; } catch (e) { return false; }
    }
    return true;
}
function isOurs(p) {
    try {
        p.currentConfigGroup = ["General"];
        // ours, or another The Linux Workbench theme's: the same layout, so it is replaced
        for (var i = 0; i < PANEL_KEYS.length; i++)
            if (String(p.readConfig(PANEL_KEYS[i], "")) === "true") return true;
    } catch (e) {}
    return hasAll(p, ["org.kde.plasma.kickoff", "org.kde.plasma.digitalclock", "org.kde.plasma.systemtray"])
        && (hasAll(p, ["org.kde.plasma.kvitals"]) || hasAll(p, ["org.kde.plasma.icontasks", "org.kde.plasma.panelspacer"]));
}
var PANEL_KEYS = @PANEL_KEYS@;
var removed = 0;
// @PREFIX@_ONLY (set by `@COMMAND@ panel --apply --only`): the @NAME@ panel becomes the
// only one on the main screen - Plasma's default bottom panel and any others there go too (they are
// in the backup taken just before, and `@COMMAND@ panel --restore` brings them back)
var ONLY = (typeof @PREFIX@_ONLY !== "undefined" && @PREFIX@_ONLY);
panels().forEach(function (p) {
    if ((p.location === "top" || ONLY) && (p.screen === 0 || isOurs(p))) { p.remove(); removed++; }
});

// 2. new panel, always on the primary screen (Plasma would otherwise put it on whichever
//    screen is active, e.g. the one the terminal is on)
var panel = new Panel;
panel.screen = 0;
panel.location = "top";
panel.currentConfigGroup = ["General"];
panel.writeConfig("@KEY@Panel", "true");
panel.height = THICKNESS;
panel.alignment = "center";
panel.lengthMode = "fill";
panel.hiding = "none";
panel.floating = false;

function spacer() { panel.addWidget("org.kde.plasma.panelspacer"); }   // flexible
function gap(px) {                                                     // fixed width
    var g = panel.addWidget("org.kde.plasma.panelspacer");
    g.currentConfigGroup = ["General"];
    g.writeConfig("expanding", false);
    g.writeConfig("length", px);
}

var launcher = panel.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "@COMMAND@-launcher");   // the @NAME@ mark (installed in the @NAME@ + hicolor icons)
gap(GAP);                               // fixed gap between launcher and task manager
var tasks = panel.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("fill", false);      // size to its icons
// Pinned apps: only ones this system has (Plasma's defaults include apps such as Discover that some
// distributions don't ship, which then show as "?"). Settings, files, the default browser, terminal.
try {
    var pins = [];
    var pin = function (id) { if (applicationExists(id) && pins.indexOf("applications:" + id + ".desktop") < 0) pins.push("applications:" + id + ".desktop"); };
    pin("systemsettings");
    pin("org.kde.dolphin");
    var web = "";
    try { web = String(defaultApplication("browser", true) || ""); } catch (e) {}
    web = web.replace(/^.*\//, "").replace(/\.desktop$/, "");
    if (web && applicationExists(web)) pin(web);
    else ["firefox", "org.mozilla.firefox", "chromium", "brave-browser", "google-chrome"].some(function (b) {
        if (applicationExists(b)) { pin(b); return true; } return false; });
    pin("org.kde.konsole");
    if (pins.length) tasks.writeConfig("launchers", pins.join(","));
} catch (e) {}   // older Plasma without applicationExists(): keep Plasma's own pins
spacer();
var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", false);        // time only
clock.writeConfig("use24hFormat", 0);        // 12-hour with AM/PM (0 = 12 h, 1 = region default, 2 = 24 h)
// Match KVitals' text: KVitals uses a monospace font at the normal desktop size, regular weight.
var fontPt = 10;
try {
    var kg = ConfigFile("kdeglobals", "General");
    var f = String(kg.readEntry("font") || "").split(",");   // e.g. "Noto Sans,10,-1,5,400,..."
    if (f.length > 1 && parseFloat(f[1]) > 0) fontPt = Math.round(parseFloat(f[1]));
} catch (e) {}
clock.writeConfig("autoFontAndSize", false); // fixed size instead of filling the panel height
clock.writeConfig("fontFamily", "monospace");
clock.writeConfig("boldText", false);
clock.writeConfig("italicText", false);
clock.writeConfig("fontWeight", 400);
clock.writeConfig("fontSize", fontPt);
spacer();
// KVitals is the stats widget (no fallback to KDE's System Monitor widgets).
var vitals = false;
if (knownWidgetTypes.indexOf("org.kde.plasma.kvitals") !== -1) {
    var kv = panel.addWidget("org.kde.plasma.kvitals");
    kv.currentConfigGroup = ["General"];
    kv.writeConfig("pinnedMetrics", KVITALS_PINNED);
    kv.writeConfig("gpuEnabled", true);
    kv.writeConfig("netEnabled", true);
    kv.writeConfig("useCustomColors", false);     // follow the @NAME@ colours
    vitals = true;
    gap(GAP);                           // fixed gap between KVitals and the tray
}
panel.addWidget("org.kde.plasma.systemtray");    // far right edge

// Optional: Panel Colorizer with the "@NAME@ Fancy" preset. Only when the caller defines
// @PREFIX@_FANCY (the preset's settings.json), i.e. `@COMMAND@ panel --apply --fancy`.
var fancy = "";
if (typeof @PREFIX@_FANCY !== "undefined" && @PREFIX@_FANCY) {
    if (knownWidgetTypes.indexOf("luisbocanegra.panel.colorizer") !== -1) {
        var pc = panel.addWidget("luisbocanegra.panel.colorizer");
        pc.currentConfigGroup = ["General"];
        pc.writeConfig("globalSettings", JSON.stringify(@PREFIX@_FANCY.globalSettings));
        pc.writeConfig("isEnabled", true);
        pc.writeConfig("hideWidget", true);          // the widget itself stays invisible
        pc.writeConfig("blacklistSpacers", true);    // spacers stay clear: they split the islands
        // Pills: Panel Colorizer's Widget Islands join each group between spacers into one pill
        pc.writeConfig("islandsEnabled", !!(@PREFIX@_FANCY.@KEY@ && @PREFIX@_FANCY.@KEY@.islands));
        pc.writeConfig("islandSeparatorWidget", "org.kde.plasma.panelspacer");
        panel.currentConfigGroup = ["General"];
        // the preset it was built with, and its look: `@COMMAND@ dark|light` restyles it from these
        var style = (typeof @PREFIX@_STYLE_NAME !== "undefined" && @PREFIX@_STYLE_NAME) ? @PREFIX@_STYLE_NAME : "@NAME@ Fancy";
        var look = (typeof @PREFIX@_LOOK !== "undefined" && @PREFIX@_LOOK) ? @PREFIX@_LOOK
                 : style.replace(/^@NAME@ /, "").replace(/ Light$/, "").toLowerCase();
        panel.writeConfig("@KEY@Style", style);
        panel.writeConfig("@KEY@Look", look);
        fancy = " Panel Colorizer: " + style + " applied.";
    } else {
        fancy = " Panel Colorizer is NOT installed - plain panel for now; Panel Colorizer is needed for the @NAME@ look (install it, then run @COMMAND@ panel --apply).";
    }
}

print("@NAME@ panel: removed " + removed + " top panel(s); new " + THICKNESS + " px panel created; "
      + (vitals ? "KVitals added." : "KVitals NOT installed - no stats added (install it, then run @COMMAND@ panel --apply again).") + fancy);
