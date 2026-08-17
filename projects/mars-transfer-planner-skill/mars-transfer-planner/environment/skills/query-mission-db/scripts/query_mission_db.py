"""Query the PostgreSQL mission planning database with data quality filtering."""

import psycopg2
import psycopg2.extras


class MissionDB:
    def __init__(self, dbname="mission_db", user="postgres", host="localhost"):
        self.conn = psycopg2.connect(dbname=dbname, user=user, host=host)

    def run(self, query_name, **kwargs):
        queries = {
            "get_planet": "SELECT * FROM planets WHERE name = %(name)s",
            "get_all_planets": "SELECT * FROM planets ORDER BY orbital_radius_au",
            "get_available_spacecraft": (
                "SELECT * FROM spacecraft WHERE available = TRUE "
                "AND reliability_rating >= %(min_reliability)s "
                "ORDER BY reliability_rating DESC"
            ),
            "get_all_spacecraft": "SELECT * FROM spacecraft ORDER BY name",
            "get_launch_windows": (
                "SELECT * FROM launch_windows "
                "WHERE EXTRACT(YEAR FROM open_date) = %(target_year)s "
                "AND deprecated = FALSE "
                "ORDER BY alignment_quality DESC"
            ),
            "get_all_launch_windows": (
                "SELECT * FROM launch_windows "
                "WHERE deprecated = FALSE "
                "ORDER BY open_date"
            ),
            "get_fuel_providers": (
                "SELECT * FROM fuel_providers "
                "WHERE reliability_rating >= %(min_reliability)s "
                "AND status = 'active' "
                "ORDER BY cost_per_kg_usd ASC"
            ),
            "get_all_fuel_providers": (
                "SELECT * FROM fuel_providers "
                "WHERE status = 'active' "
                "ORDER BY cost_per_kg_usd"
            ),
            "get_mission_constraints": (
                "SELECT * FROM mission_constraints "
                "WHERE constraint_name = %(constraint_name)s"
            ),
            "get_all_mission_constraints": "SELECT * FROM mission_constraints ORDER BY constraint_name",
            "get_spacecraft_by_name": "SELECT * FROM spacecraft WHERE name = %(name)s",
            "get_suitable_spacecraft": (
                "SELECT * FROM spacecraft "
                "WHERE available = TRUE "
                "AND reliability_rating >= %(min_reliability)s "
                "AND max_payload_kg >= %(min_payload)s "
                "ORDER BY dry_mass_kg ASC"
            ),
            "get_fuel_provider_by_name": (
                "SELECT * FROM fuel_providers "
                "WHERE provider_name = %(provider_name)s "
                "AND status = 'active'"
            ),
            "get_compatible_fuel_types": (
                "SELECT fuel_type FROM spacecraft_fuel_compatibility "
                "WHERE spacecraft_name = %(spacecraft_name)s "
                "AND certified = TRUE "
                "AND (certification_expiry IS NULL OR certification_expiry > '2026-01-01')"
            ),
            "get_compatible_providers": (
                "SELECT fp.* FROM fuel_providers fp "
                "JOIN spacecraft_fuel_compatibility sfc "
                "ON fp.fuel_type = sfc.fuel_type "
                "WHERE sfc.spacecraft_name = %(spacecraft_name)s "
                "AND sfc.certified = TRUE "
                "AND (sfc.certification_expiry IS NULL OR sfc.certification_expiry > '2026-01-01') "
                "AND fp.status = 'active' "
                "AND fp.reliability_rating >= %(min_reliability)s "
                "ORDER BY fp.cost_per_kg_usd ASC"
            ),
            "custom": None,
        }

        if query_name == "custom":
            sql = kwargs.pop("sql")
        else:
            sql = queries.get(query_name)
            if sql is None:
                raise ValueError(
                    f"Unknown query: {query_name}. Available: {list(queries.keys())}"
                )

        cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql, kwargs)
        rows = cur.fetchall()
        cur.close()
        return [dict(row) for row in rows]

    def close(self):
        self.conn.close()
