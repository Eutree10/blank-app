using Toybox.Time;
using Toybox.Time.Gregorian;

// All date math for period identity, reset detection and deadlines.
//
// Documented design decisions (see README):
//   * Daily   -> calendar day,   resets at local 00:00.
//   * Weekly  -> calendar week,  resets MONDAY 00:00 local (ISO-style week).
//   * Monthly -> calendar month, resets on the 1st at 00:00 local.
//
// A "period id" is a stable integer for the current period. On each launch (and
// periodically) we compare it to the stored id; a difference means the period
// rolled over and that level must be reset.
module Periods {

    const SECS_PER_DAY = 86400;

    // ---- Period identifiers -------------------------------------------------

    function currentId(level) {
        var info = Gregorian.info(Time.now(), Time.FORMAT_SHORT);
        if (level == Levels.DAILY) {
            // YYYYMMDD
            return info.year * 10000 + info.month * 100 + info.day;
        } else if (level == Levels.WEEKLY) {
            // Date integer of the Monday that starts this week.
            var monday = Gregorian.info(weekStart(), Time.FORMAT_SHORT);
            return monday.year * 10000 + monday.month * 100 + monday.day;
        } else {
            // YYYYMM
            return info.year * 100 + info.month;
        }
    }

    // ---- Deadlines (end of the current period) ------------------------------

    function deadline(level) {
        if (level == Levels.DAILY) {
            // Next local midnight.
            return Time.today().add(new Time.Duration(SECS_PER_DAY));
        } else if (level == Levels.WEEKLY) {
            // Monday start + 7 days.
            return weekStart().add(new Time.Duration(7 * SECS_PER_DAY));
        } else {
            return firstOfNextMonth();
        }
    }

    // ---- Helpers ------------------------------------------------------------

    // Local Monday 00:00 of the current week.
    // Gregorian day_of_week is 1=Sunday .. 7=Saturday.
    function weekStart() {
        var today = Time.today();
        var dow = Gregorian.info(today, Time.FORMAT_SHORT).day_of_week;
        var offset = (dow == 1) ? 6 : (dow - 2); // days since Monday
        return today.subtract(new Time.Duration(offset * SECS_PER_DAY));
    }

    // Local 00:00 on the 1st of next month.
    function firstOfNextMonth() {
        var info = Gregorian.info(Time.now(), Time.FORMAT_SHORT);
        var year = info.year;
        var month = info.month + 1;
        if (month > 12) {
            month = 1;
            year += 1;
        }
        return Gregorian.moment({
            :year   => year,
            :month  => month,
            :day    => 1,
            :hour   => 0,
            :minute => 0,
            :second => 0
        });
    }

    // Whole seconds remaining until a deadline, clamped at 0.
    function secondsUntil(deadlineMoment) {
        var secs = deadlineMoment.value() - Time.now().value();
        return (secs > 0) ? secs : 0;
    }
}
