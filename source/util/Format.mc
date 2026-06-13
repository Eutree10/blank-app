using Toybox.Lang;

// Pure formatting helpers for the on-screen data. All countdown output is
// UPPERCASE and changes granularity with how much time is left.
module Format {

    // Countdown formatting from seconds remaining:
    //   >= 1 day   -> "6D 09H" / "22D 09H"
    //   < 1 day    -> "09H 24M"
    //   < 1 hour   -> "24M 30S"
    function countdown(secondsRemaining) {
        var s = secondsRemaining;
        if (s < 0) { s = 0; }

        var days  = s / 86400;
        var hours = (s % 86400) / 3600;
        var mins  = (s % 3600) / 60;
        var secs  = s % 60;

        if (days >= 1) {
            return days.format("%d") + "D " + hours.format("%02d") + "H";
        } else if (hours >= 1) {
            return hours.format("%02d") + "H " + mins.format("%02d") + "M";
        } else {
            return mins.format("%02d") + "M " + secs.format("%02d") + "S";
        }
    }

    // Abbreviated XP for the hub:
    //   < 1000           -> "740"
    //   1000 .. 9999     -> "1.7K"
    //   10000 .. 999999  -> "42K"
    //   >= 1,000,000     -> "1.3M"
    function abbreviate(value) {
        var v = value;
        if (v < 0) { v = 0; }
        if (v < 1000) {
            return v.format("%d");
        } else if (v < 10000) {
            // One decimal, e.g. 1700 -> "1.7K". Strip a trailing ".0".
            var k = v / 1000.0;
            var str = k.format("%.1f");
            if (str.substring(str.length() - 2, str.length()).equals(".0")) {
                str = str.substring(0, str.length() - 2);
            }
            return str + "K";
        } else if (v < 1000000) {
            return (v / 1000).format("%d") + "K";
        } else {
            var m = v / 1000000.0;
            var str = m.format("%.1f");
            if (str.substring(str.length() - 2, str.length()).equals(".0")) {
                str = str.substring(0, str.length() - 2);
            }
            return str + "M";
        }
    }
}
