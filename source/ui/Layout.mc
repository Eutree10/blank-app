using Toybox.System;
using Toybox.Graphics as Gfx;

// Runtime layout adaptation. Because the UI is custom-drawn, one code path
// serves round, semi-round and rectangular watches: we just compute safe
// margins from the screen shape and size and center content.
module Layout {

    // Horizontal safe inset (px) for the given dc. Round screens need a bigger
    // inset so cards don't clip on the curved edges.
    function sideMargin(dc) {
        var w = dc.getWidth();
        var shape = System.getDeviceSettings().screenShape;
        if (shape == System.SCREEN_SHAPE_ROUND) {
            return (w * 0.11).toNumber();
        }
        return (w * 0.06).toNumber();
    }

    // Content width between the side margins.
    function contentWidth(dc) {
        return dc.getWidth() - 2 * sideMargin(dc);
    }

    function centerX(dc) { return dc.getWidth() / 2; }

    // True for round screens, where headers/footers should be pulled inward
    // vertically too.
    function isRound() {
        return System.getDeviceSettings().screenShape == System.SCREEN_SHAPE_ROUND;
    }

    // Top inset for the first row of content.
    function topInset(dc) {
        return isRound() ? (dc.getHeight() * 0.10).toNumber() : (dc.getHeight() * 0.04).toNumber();
    }

    // A scale factor (~1.0 on a 240px watch) to nudge sizes on big/small screens.
    function scale(dc) {
        return dc.getHeight() / 240.0;
    }
}
