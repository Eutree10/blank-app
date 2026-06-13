using Toybox.Graphics as Gfx;
using Toybox.Lang;

// Small text helpers (Monkey C strings have no split/wrap of their own).
module TextUtil {

    // Splits on single spaces into a list of words (empties dropped).
    function words(text) {
        var result = [];
        var start = 0;
        var n = text.length();
        for (var i = 0; i <= n; i++) {
            if (i == n || text.substring(i, i + 1).equals(" ")) {
                if (i > start) { result.add(text.substring(start, i)); }
                start = i + 1;
            }
        }
        return result;
    }

    // Greedy word-wrap into at most `maxLines` lines fitting `maxWidth`.
    // The last line is ellipsized if text remains.
    function wrap(dc, text, font, maxWidth, maxLines) {
        var ws = words(text);
        var lines = [];
        var current = "";
        for (var i = 0; i < ws.size(); i++) {
            var word = ws[i];
            var trial = current.equals("") ? word : current + " " + word;
            if (dc.getTextWidthInPixels(trial, font) <= maxWidth) {
                current = trial;
            } else {
                if (current.equals("")) {
                    // A single word wider than the line: hard-clip it.
                    current = clip(dc, word, font, maxWidth);
                }
                lines.add(current);
                current = word;
                if (lines.size() == maxLines) {
                    // No room left; ellipsize the final line and stop.
                    lines[maxLines - 1] = ellipsize(dc, lines[maxLines - 1], font, maxWidth);
                    return lines;
                }
            }
        }
        if (!current.equals("") && lines.size() < maxLines) {
            lines.add(current);
        }
        return lines;
    }

    // Truncate to fit width (used for an over-long single word).
    function clip(dc, text, font, maxWidth) {
        var s = text;
        while (s.length() > 1 && dc.getTextWidthInPixels(s, font) > maxWidth) {
            s = s.substring(0, s.length() - 1);
        }
        return s;
    }

    // Append "…" while trimming to fit width.
    function ellipsize(dc, text, font, maxWidth) {
        var s = text;
        while (s.length() > 0 && dc.getTextWidthInPixels(s + "…", font) > maxWidth) {
            s = s.substring(0, s.length() - 1);
        }
        return s + "…";
    }
}
