using Toybox.Graphics as Gfx;

// Central font registry. The whole UI asks for fonts here, so swapping in
// embedded JetBrains Mono / Fredoka faces is a one-file change
// (see resources/fonts/README.md). For now everything maps to system fonts,
// which keeps the project building on every device with no binary assets.
module Fonts {
    // Rounded sans roles (titles / labels) -> system sans fonts.
    function brand()    { return Gfx.FONT_LARGE; }   // wordmark fallback
    function title()    { return Gfx.FONT_MEDIUM; }  // screen / level titles
    function body()     { return Gfx.FONT_SMALL; }   // quest text
    function label()    { return Gfx.FONT_XTINY; }   // small caps labels

    // Monospaced/data roles (countdown, points, counters, XP).
    // Swap these to the embedded mono face when available.
    function mono()       { return Gfx.FONT_SMALL; }
    function monoTiny()   { return Gfx.FONT_XTINY; }
    function bigNumber()  { return Gfx.FONT_LARGE; }  // hub stat values
}
