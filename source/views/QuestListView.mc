using Toybox.WatchUi as Ui;
using Toybox.Graphics as Gfx;
using Toybox.Lang;

// One level's quest list: a countdown header, a vertically scrolling list of
// quest cards (pending first, then a "COMPLETED" divider, then the completed
// cards for the current period), side arrows hinting left/right level switching,
// and a scroll indicator.
class QuestListView extends Ui.View {

    public var level;
    private var _focusIndex;     // index into the flat quest list
    private var _scrollY;        // pixel scroll offset within the content

    // Cached per-frame layout.
    private var _flat;           // pending quests followed by completed quests
    private var _pendingCount;
    private var _cardY;          // content-space top y per flat index
    private var _cardH;
    private var _gap;
    private var _dividerY;
    private var _dividerH;
    private var _contentH;
    private var _viewTop;
    private var _viewH;

    function initialize(levelIn) {
        View.initialize();
        level = levelIn;
        _focusIndex = 0;
        _scrollY = 0;
    }

    function onShow() {
        var app = getApp();
        if (app.service != null) {
            app.service.load();
        }
    }

    // Switch this view to another level in place (used by the level menu on
    // button devices). Resets focus and scroll.
    function setLevel(levelIn) {
        level = levelIn;
        _focusIndex = 0;
        _scrollY = 0;
        Ui.requestUpdate();
    }

    // ---- Layout -----------------------------------------------------------

    function buildLayout(dc) {
        var service = getApp().service;
        var all = service.questsFor(level);

        // Split into pending then completed, preserving order.
        var pending = [];
        var done = [];
        for (var i = 0; i < all.size(); i++) {
            if (all[i].completed) { done.add(all[i]); } else { pending.add(all[i]); }
        }
        _pendingCount = pending.size();
        _flat = [];
        for (var i = 0; i < pending.size(); i++) { _flat.add(pending[i]); }
        for (var i = 0; i < done.size(); i++)    { _flat.add(done[i]); }

        var h = dc.getHeight();
        _cardH = (h * 0.21).toNumber();
        _gap   = (h * 0.03).toNumber();
        _dividerH = (h * 0.11).toNumber();
        _viewTop = (Layout.isRound() ? h * 0.21 : h * 0.16).toNumber();
        _viewH   = h - _viewTop;

        _cardY = new [_flat.size()];
        var y = (_gap / 2).toNumber();
        for (var i = 0; i < _pendingCount; i++) {
            _cardY[i] = y;
            y += _cardH + _gap;
        }
        // Divider for the Completed section (shown whenever the list is non-empty).
        _dividerY = y;
        if (_flat.size() > 0) { y += _dividerH; }
        for (var i = _pendingCount; i < _flat.size(); i++) {
            _cardY[i] = y;
            y += _cardH + _gap;
        }
        _contentH = y;
    }

    // ---- Drawing ----------------------------------------------------------

    function onUpdate(dc) {
        var service = getApp().service;
        Components.fillBackground(dc);
        buildLayout(dc);

        var w      = dc.getWidth();
        var h      = dc.getHeight();
        var margin = Layout.sideMargin(dc);
        var cw     = w - 2 * margin;

        // Header: level title + gold stopwatch & countdown.
        var title = Ui.loadResource(Levels.shortNameResource(level));
        var cd    = Format.countdown(service.secondsLeft(level));
        Components.drawCountdownHeader(dc, margin, (h * 0.04).toNumber(), cw, title, cd);

        // Empty state.
        if (_flat.size() == 0) {
            dc.setColor(Theme.TEXT_DIM, Gfx.COLOR_TRANSPARENT);
            dc.drawText(w / 2, h / 2, Fonts.body(),
                        Ui.loadResource(Rez.Strings.EmptyLevel),
                        Gfx.TEXT_JUSTIFY_CENTER | Gfx.TEXT_JUSTIFY_VCENTER);
            drawSideArrows(dc);
            return;
        }

        clampScroll();

        // Scrolling content, clipped to the viewport.
        dc.setClip(0, _viewTop, w, _viewH);
        for (var i = 0; i < _flat.size(); i++) {
            var sy = _viewTop + _cardY[i] - _scrollY;
            if (sy + _cardH >= _viewTop && sy <= _viewTop + _viewH) {
                Components.drawQuestCard(dc, margin, sy, cw, _cardH,
                                         _flat[i], i == _focusIndex);
            }
        }
        // "COMPLETED" divider.
        var dy = _viewTop + _dividerY - _scrollY;
        if (dy + _dividerH >= _viewTop && dy <= _viewTop + _viewH) {
            drawDivider(dc, margin, dy, cw, _flat.size() - _pendingCount);
        }
        dc.clearClip();

        drawSideArrows(dc);
        drawScrollIndicator(dc);
    }

    function drawDivider(dc, x, y, w, completedCount) {
        var cy = y + _dividerH / 2;
        var label = Ui.loadResource(Rez.Strings.CompletedLink) +
                    " (" + completedCount.format("%d") + ")";
        var tw = dc.getTextWidthInPixels(label, Fonts.label());
        dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
        dc.drawText(x + w / 2, cy, Fonts.label(), label,
                    Gfx.TEXT_JUSTIFY_CENTER | Gfx.TEXT_JUSTIFY_VCENTER);
        Components.drawArrow(dc, x + w / 2 + tw / 2 + 14, cy, _dividerH * 0.3,
                             Theme.GOLD, "down");
    }

    function drawSideArrows(dc) {
        var w = dc.getWidth();
        var h = dc.getHeight();
        var s = (h * 0.05).toNumber();
        Components.drawArrow(dc, (w * 0.04).toNumber(), h / 2, s, Theme.GOLD, "left");
        Components.drawArrow(dc, (w * 0.96).toNumber(), h / 2, s, Theme.GOLD, "right");
    }

    function drawScrollIndicator(dc) {
        if (_contentH <= _viewH) { return; }
        var w = dc.getWidth();
        var trackX = w - 4;
        var thumbH = (_viewH * _viewH / _contentH).toNumber();
        var maxScroll = _contentH - _viewH;
        var thumbY = _viewTop + ((_viewH - thumbH) * _scrollY / maxScroll).toNumber();
        dc.setColor(Theme.RAIL, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(trackX, _viewTop, 3, _viewH, 1);
        dc.setColor(Theme.GOLD, Gfx.COLOR_TRANSPARENT);
        dc.fillRoundedRectangle(trackX, thumbY, 3, thumbH, 1);
    }

    // ---- Navigation helpers ----------------------------------------------

    function clampScroll() {
        var maxScroll = _contentH - _viewH;
        if (maxScroll < 0) { maxScroll = 0; }
        if (_scrollY > maxScroll) { _scrollY = maxScroll; }
        if (_scrollY < 0) { _scrollY = 0; }
    }

    // Ensure the focused card is fully visible.
    function ensureVisible() {
        if (_focusIndex < 0 || _focusIndex >= _cardY.size()) { return; }
        var top = _cardY[_focusIndex];
        var bottom = top + _cardH;
        if (top - _scrollY < 0) {
            _scrollY = top;
        } else if (bottom - _scrollY > _viewH) {
            _scrollY = bottom - _viewH;
        }
    }

    function focusNext() {
        if (_flat == null || _flat.size() == 0) { return; }
        if (_focusIndex < _flat.size() - 1) { _focusIndex += 1; }
        ensureVisible();
        Ui.requestUpdate();
    }

    function focusPrev() {
        if (_flat == null || _flat.size() == 0) { return; }
        if (_focusIndex > 0) { _focusIndex -= 1; }
        ensureVisible();
        Ui.requestUpdate();
    }

    function focusedQuest() {
        if (_flat == null || _focusIndex < 0 || _focusIndex >= _flat.size()) {
            return null;
        }
        return _flat[_focusIndex];
    }

    // Map a screen coordinate to a quest (touch). Returns the Quest or null.
    function questAt(px, py) {
        if (_flat == null) { return null; }
        for (var i = 0; i < _flat.size(); i++) {
            var sy = _viewTop + _cardY[i] - _scrollY;
            if (py >= sy && py <= sy + _cardH && py >= _viewTop) {
                _focusIndex = i;
                return _flat[i];
            }
        }
        return null;
    }
}
