using Toybox.Graphics as Gfx;
using Toybox.WatchUi as Ui;
using Toybox.Math;

// Reusable drawing primitives implementing the Questline visual language:
// rounded cards, the bolt/stopwatch icons, progress bars, stat cards, level
// rows and pill buttons. Every component supports its required states.
module Components {

    // ---- Background -------------------------------------------------------

    function fillBackground(dc) {
        dc.setColor(Theme.TEXT, Theme.BG);
        dc.clear();
    }

    // ---- Icons ------------------------------------------------------------

    // Lightning bolt (the "energy" mark next to points / XP).
    function drawBolt(dc, cx, cy, size, color) {
        var w = size * 0.5;
        var h = size;
        var pts = [
            [cx + w * 0.10, cy - h * 0.5],
            [cx - w * 0.5,  cy + h * 0.10],
            [cx - w * 0.05, cy + h * 0.10],
            [cx - w * 0.10, cy + h * 0.5],
            [cx + w * 0.5,  cy - h * 0.10],
            [cx + w * 0.05, cy - h * 0.10]
        ];
        dc.setColor(color, Gfx.COLOR_TRANSPARENT);
        dc.fillPolygon(pts);
    }

    // Stopwatch glyph (time / brand). Drawn with a ring, top button and a hand.
    function drawStopwatch(dc, cx, cy, size, color) {
        var r = (size * 0.46).toNumber();
        var pen = (size * 0.10).toNumber();
        if (pen < 2) { pen = 2; }
        dc.setColor(color, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(pen);
        dc.drawCircle(cx, cy, r);
        // top button
        dc.fillRectangle(cx - size * 0.10, cy - r - size * 0.16, size * 0.20, size * 0.16);
        // hand to ~1 o'clock
        dc.drawLine(cx, cy, cx + r * 0.55, cy - r * 0.45);
        dc.setPenWidth(1);
    }

    // Small right-pointing chevron (the "enter this list" affordance).
    function drawChevronRight(dc, cx, cy, size, color) {
        dc.setColor(color, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        dc.drawLine(cx - size * 0.3, cy - size * 0.5, cx + size * 0.3, cy);
        dc.drawLine(cx + size * 0.3, cy, cx - size * 0.3, cy + size * 0.5);
        dc.setPenWidth(1);
    }

    // Side arrows / down arrow used as gesture hints.
    function drawArrow(dc, cx, cy, size, color, dir) {
        // dir: "left" | "right" | "down" | "up"
        dc.setColor(color, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(2);
        var s = size;
        if (dir.equals("left")) {
            dc.drawLine(cx + s * 0.3, cy - s * 0.5, cx - s * 0.3, cy);
            dc.drawLine(cx - s * 0.3, cy, cx + s * 0.3, cy + s * 0.5);
        } else if (dir.equals("right")) {
            dc.drawLine(cx - s * 0.3, cy - s * 0.5, cx + s * 0.3, cy);
            dc.drawLine(cx + s * 0.3, cy, cx - s * 0.3, cy + s * 0.5);
        } else if (dir.equals("down")) {
            dc.drawLine(cx - s * 0.5, cy - s * 0.3, cx, cy + s * 0.3);
            dc.drawLine(cx, cy + s * 0.3, cx + s * 0.5, cy - s * 0.3);
        } else { // up
            dc.drawLine(cx - s * 0.5, cy + s * 0.3, cx, cy - s * 0.3);
            dc.drawLine(cx, cy - s * 0.3, cx + s * 0.5, cy + s * 0.3);
        }
        dc.setPenWidth(1);
    }

    // ---- Progress bar -----------------------------------------------------

    function drawProgressBar(dc, x, y, w, thickness, fraction) {
        var r = thickness / 2;
        dc.setColor(Theme.RAIL, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(x, y, w, thickness, r);
        if (fraction > 0) {
            var fw = (w * fraction).toNumber();
            if (fw < thickness) { fw = thickness; } // keep the rounded cap visible
            dc.setColor(Theme.GREEN, Gfx.COLOR_TRANSPARENT);
            dc.fillRoundedRectangle(x, y, fw, thickness, r);
        }
    }

    // ---- Quest card -------------------------------------------------------

    // Draws a quest card and returns its height. Two zones: text (~3/4) on the
    // left, a darker points panel (bolt + points) on the right. Blue when
    // pending, green when completed; gold border when focused.
    function drawQuestCard(dc, x, y, w, h, quest, focused) {
        var radius = (h * 0.22).toNumber();
        var fill   = quest.completed ? Theme.GREEN : Theme.BLUE_CARD;
        var panel  = quest.completed ? darken(Theme.GREEN) : Theme.BLUE_PANEL;

        // Card body
        dc.setColor(fill, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(x, y, w, h, radius);

        // Right points panel: clip to the panel rect and re-draw a rounded card
        // so only the right rounded corners show (straight left edge).
        var panelW = (w * 0.28).toNumber();
        var panelX = x + w - panelW;
        dc.setClip(panelX, y, panelW, h);
        dc.setColor(panel, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(x, y, w, h, radius);
        dc.clearClip();

        // Bolt + points (lime) centered in the panel.
        var pcx = panelX + panelW / 2;
        drawBolt(dc, pcx, y + h * 0.34, h * 0.30, Theme.LIME);
        dc.setColor(Theme.LIME, Gfx.COLOR_TRANSPARENT);
        dc.drawText(pcx, y + h * 0.52, Fonts.monoTiny(),
                    quest.points.format("%d"),
                    Gfx.TEXT_JUSTIFY_CENTER);

        // Quest text (white), wrapped to up to 2 lines in the left zone.
        var pad = (h * 0.16).toNumber();
        var textW = panelX - x - 2 * pad;
        var font = Fonts.body();
        var lines = TextUtil.wrap(dc, quest.title, font, textW, 2);
        var lineH = dc.getFontHeight(font);
        var totalH = lineH * lines.size();
        var ty = y + (h - totalH) / 2;
        dc.setColor(Theme.TEXT, Gfx.COLOR_TRANSPARENT);
        for (var i = 0; i < lines.size(); i++) {
            dc.drawText(x + pad, ty + i * lineH, font, lines[i], Gfx.TEXT_JUSTIFY_LEFT);
        }

        // Focus ring
        if (focused) {
            dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
            dc.setPenWidth(3);
            dc.drawRoundedRectangle(x, y, w, h, radius);
            dc.setPenWidth(1);
        }
        return h;
    }

    // ---- Stat card (hub) --------------------------------------------------

    function drawStatCard(dc, x, y, w, h, label, value, accent, valueColor, iconType) {
        var radius = (h * 0.18).toNumber();
        dc.setColor(Theme.SURFACE, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(x, y, w, h, radius);
        dc.setColor(Theme.BORDER, Gfx.COLOR_TRANSPARENT);
        dc.setPenWidth(1);
        dc.drawRoundedRectangle(x, y, w, h, radius);

        // Label (small caps, accent color), with icon to its left.
        var iconCx = x + w * 0.22;
        var labelY = y + h * 0.16;
        if (iconType.equals("bolt")) {
            drawBolt(dc, iconCx, labelY + h * 0.06, h * 0.20, accent);
        } else {
            drawStopwatch(dc, iconCx, labelY + h * 0.06, h * 0.22, accent);
        }
        dc.setColor(accent, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x + w * 0.38, labelY, Fonts.label(), label, Gfx.TEXT_JUSTIFY_LEFT);

        // Big value.
        dc.setColor(valueColor, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x + w / 2, y + h * 0.42, Fonts.bigNumber(), value,
                    Gfx.TEXT_JUSTIFY_CENTER);
    }

    // ---- Level row (hub) --------------------------------------------------

    function drawLevelRow(dc, x, y, w, h, name, doneCount, total, streak, focused) {
        if (focused) {
            dc.setColor(Theme.SURFACE, Gfx.COLOR_TRANSPARENT);
            dc.fillRoundedRectangle(x, y, w, h, (h * 0.22).toNumber());
            dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
            dc.setPenWidth(2);
            dc.drawRoundedRectangle(x, y, w, h, (h * 0.22).toNumber());
            dc.setPenWidth(1);
        }
        var pad = (w * 0.05).toNumber();
        // Name (left, white).
        dc.setColor(Theme.TEXT, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x + pad, y + h * 0.10, Fonts.body(), name, Gfx.TEXT_JUSTIFY_LEFT);
        // Streak badge (gold) right after the name when there is one going.
        if (streak > 0) {
            dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
            dc.drawText(x + pad + dc.getTextWidthInPixels(name, Fonts.body()) + pad,
                        y + h * 0.10, Fonts.monoTiny(), streak.format("%d") + "x",
                        Gfx.TEXT_JUSTIFY_LEFT);
        }
        // Counter X/Y (right, mono) leaving room for the chevron.
        dc.setColor(Theme.TEXT_DIM, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x + w - pad - h * 0.4, y + h * 0.10, Fonts.mono(),
                    doneCount.format("%d") + "/" + total.format("%d"),
                    Gfx.TEXT_JUSTIFY_RIGHT);
        // Chevron.
        drawChevronRight(dc, x + w - pad, y + h * 0.30, h * 0.30, Theme.GOLD);
        // Progress bar below.
        var frac = (total > 0) ? (doneCount * 1.0 / total) : 0.0;
        drawProgressBar(dc, x + pad, y + h * 0.72, w - 2 * pad, (h * 0.12).toNumber(), frac);
    }

    // ---- Pill button (detail) --------------------------------------------

    function drawPillButton(dc, cx, y, w, h, text, bg, textColor, focused) {
        var x = cx - w / 2;
        var r = h / 2;
        dc.setColor(bg, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(x, y, w, h, r);
        if (focused) {
            dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
            dc.setPenWidth(3);
            dc.drawRoundedRectangle(x, y, w, h, r);
            dc.setPenWidth(1);
        }
        dc.setColor(textColor, Gfx.COLOR_TRANSPARENT);
        dc.drawText(cx, y + h / 2, Fonts.body(), text,
                    Gfx.TEXT_JUSTIFY_CENTER | Gfx.TEXT_JUSTIFY_VCENTER);
    }

    // ---- Countdown header -------------------------------------------------

    // Level title (left, white bold) + gold stopwatch & countdown (right).
    function drawCountdownHeader(dc, x, y, w, title, countdownText) {
        dc.setColor(Theme.TEXT, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x, y, Fonts.title(), title, Gfx.TEXT_JUSTIFY_LEFT);

        var font = Fonts.mono();
        var tw = dc.getTextWidthInPixels(countdownText, font);
        var iconSize = dc.getFontHeight(font) * 0.9;
        var rightX = x + w;
        dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
        dc.drawText(rightX, y + dc.getFontHeight(Fonts.title()) * 0.4, font,
                    countdownText, Gfx.TEXT_JUSTIFY_RIGHT);
        drawStopwatch(dc, rightX - tw - iconSize * 0.7,
                      y + dc.getFontHeight(Fonts.title()) * 0.4 + dc.getFontHeight(font) / 2,
                      iconSize, Theme.GOLD);
    }

    // ---- Helpers ----------------------------------------------------------

    // Multiply RGB channels by ~0.6 to derive the darker points panel for a
    // completed (green) card.
    function darken(color) {
        var r = (color >> 16) & 0xFF;
        var g = (color >> 8) & 0xFF;
        var b = color & 0xFF;
        r = (r * 6 / 10);
        g = (g * 6 / 10);
        b = (b * 6 / 10);
        return (r << 16) | (g << 8) | b;
    }
}
