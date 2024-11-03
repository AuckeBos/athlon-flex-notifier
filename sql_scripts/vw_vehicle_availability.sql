CREATE OR REPLACE VIEW
    public.vw_vehicle_availability AS (
        WITH
            -- has_gap_with_previous_row: wheter active_to from prev equals active_from from cur
            -- if true, the vehicle has been deleted between cur and prev
            gaps as (
                SELECT
                    key_hash,
                    make,
                    model,
                    active_from,
                    active_to,
                    LAG(active_to, 1, active_from) OVER vehicle < active_from as has_gap_with_previous_row
                FROM
                    vehicle
                WINDOW
                    vehicle AS (
                        PARTITION BY
                            key_hash
                        ORDER BY
                            active_from
                    )
            ),
            -- availability_group: all consecutive rows of a vehicle have the same group
            -- each group will be grouped into one availability. the vehicle wasn't deleted during this group
            availability_groups AS (
                SELECT
                    key_hash,
                    make,
                    model,
                    active_from as active_from,
                    active_to AS active_to,
                    SUM(has_gap_with_previous_row::int) OVER vehicle AS availability_group
                FROM
                    gaps
                WINDOW
                    vehicle AS (
                        PARTITION BY
                            key_hash
                        ORDER BY
                            active_from
                    )
            ),
            -- active_from: first active_from of this group
            -- active_to: last active_to of this group, or null (means still available)
            availabilities AS (
                SELECT
                    key_hash,
                    MIN(make) AS make,
                    MIN(model) AS model,
                    MIN(active_from) AS active_from,
                    CASE
                        WHEN (COUNT(active_to) = COUNT(*)) THEN MAX(active_to)
                        -- Handle null as MAX
                        ELSE Null
                    END AS active_to
                FROM
                    availability_groups
                GROUP BY
                    key_hash,
                    availability_group
            )
        SELECT
            key_hash AS vehicle_key_hash,
            make AS make,
            model AS model,
            active_from AS available_since,
            active_to AS available_until
        FROM
            availabilities
        ORDER BY
            vehicle_key_hash,
            available_since DESC
    );