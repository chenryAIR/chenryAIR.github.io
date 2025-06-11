--Created by Chad Henry
--Created 6.4.2025
--Last modified 6.11.2025
--Purpose: Prepare the data for the Airbnb analysis and dashboard.



-- Step 1: Identify consecutive blocks of availability or bookings for each listing
WITH bookings AS (
    SELECT
        listing_id,
        date,
        available,
        -- Create a "consecutive group" ID using the difference of row numbers technique
        -- This groups consecutive dates with the same 'available' value
        ROW_NUMBER() OVER (PARTITION BY listing_id ORDER BY date) -
        ROW_NUMBER() OVER (PARTITION BY listing_id, available ORDER BY date) AS consecutive
    FROM airbnb_calendar
),

-- Step 2: Keep only booking/availability streaks of 14 days or less, or availability blocks
realbookings AS (
    SELECT
        listing_id,
        consecutive,
        available,
        MIN(date) AS min_date  -- Track the start date of the consecutive block
    FROM bookings
    GROUP BY listing_id, consecutive, available
    HAVING COUNT(*) <= 14 OR available = true
    -- Logic: we keep short booking windows (≤ 14 days) or all availability streaks
),

-- Step 3: Count days booked or available per month per listing
daycount AS (
    SELECT 
        r.listing_id,
        b.available,
        TO_CHAR(date, 'YYYY-MM') AS year_month,
        COUNT(*) AS book_days
    FROM realbookings AS r
    JOIN bookings AS b
        ON r.listing_id = b.listing_id
        AND r.consecutive = b.consecutive
        AND r.available = b.available
    GROUP BY r.listing_id, year_month, b.available
),

-- Step 4: Pivot data to get monthly booking stats per listing
longwide AS (
    SELECT
        listing_id,
        -- April 2025: count of days not booked (available = true)
        MAX(CASE WHEN available = true AND year_month = '2025-04' THEN book_days ELSE 0 END) AS not_booked,
        -- April 2025: count of days booked (available = false)
        MAX(CASE WHEN available = false AND year_month = '2025-04' THEN book_days ELSE 0 END) AS booked,
        -- March 2025: prior month, same structure
        MAX(CASE WHEN available = true AND year_month = '2025-03' THEN book_days ELSE 0 END) AS prior_not_booked,
        MAX(CASE WHEN available = false AND year_month = '2025-03' THEN book_days ELSE 0 END) AS prior_booked
    FROM daycount
    WHERE year_month <= '2025-04'  -- Only keep months up to April 2025
    GROUP BY listing_id
)

-- Step 5: Join with listings metadata and calculate review timing & binary flags
SELECT 
    *,
    -- Days since last review, as of April 1st, 2025
    '2025-04-01'::date - last_review AS days_since_last_review,

    -- Booking outcome: 1 if booked at least once in April, else 0
    CASE WHEN booked > 0 THEN 1 ELSE 0 END AS booked_yes,

    -- Time-based review flags for independent variable
    CASE WHEN '2025-04-01'::date - last_review <= 30 THEN 1 ELSE 0 END AS days_since_last_review30,
    CASE WHEN '2025-04-01'::date - last_review <= 60 THEN 1 ELSE 0 END AS days_since_last_review60,
    CASE WHEN '2025-04-01'::date - last_review <= 90 THEN 1 ELSE 0 END AS days_since_last_review90,

    -- Total days available in April (booked + not booked)
    j.not_booked + j.booked AS total_avail

FROM longwide AS j
JOIN airbnb_listings AS l
    ON j.listing_id = l.id
    AND l.last_review IS NOT NULL  -- Only keep listings that have been reviewed

WHERE j.not_booked + j.booked > 0  -- Remove listings with no availability in April
;
