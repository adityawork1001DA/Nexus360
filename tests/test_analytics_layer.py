from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine


REQUIRED_VIEWS = {
    "v_monthly_revenue",
    "v_yoy_revenue_growth",
    "v_rolling_revenue",
    "v_product_revenue_rank",
    "v_customer_pareto",
    "v_customer_rfm",
    "v_customer_value_tiers",
    "v_regional_performance",
    "v_revenue_anomalies",
    "v_executive_kpis",
}


def scalar(
    query: str,
):
    engine = get_engine()

    with engine.connect() as connection:

        return connection.execute(
            text(query)
        ).scalar_one()


def test_analytics_schema_exists():

    exists = scalar(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.schemata
            WHERE schema_name = 'analytics'
        )
        """
    )

    assert exists is True


def test_required_analytics_views_exist():

    engine = get_engine()

    query = text(
        """
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'analytics'
        """
    )

    with engine.connect() as connection:

        views = {
            row[0]
            for row
            in connection.execute(query)
        }

    missing = REQUIRED_VIEWS - views

    assert not missing, (
        f"Missing analytics views: "
        f"{sorted(missing)}"
    )


def test_monthly_revenue_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_monthly_revenue
        """
    )

    assert count > 0


def test_monthly_revenue_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_monthly_revenue
        WHERE net_revenue_usd < 0
        """
    )

    assert count == 0


def test_executive_kpi_single_row():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_executive_kpis
        """
    )

    assert count == 1


def test_executive_revenue_positive():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_executive_kpis

        WHERE total_revenue_usd <= 0
        """
    )

    assert count == 0


def test_product_revenue_positive():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_product_revenue_rank

        WHERE revenue_usd < 0
        """
    )

    assert count == 0


def test_product_revenue_share_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_product_revenue_rank

        WHERE
            revenue_share_pct < 0

            OR

            revenue_share_pct > 100.01
        """
    )

    assert count == 0


def test_customer_rfm_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_rfm
        """
    )

    assert count > 0


def test_rfm_scores_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_customer_rfm

        WHERE
            recency_score NOT BETWEEN 1 AND 5

            OR frequency_score
               NOT BETWEEN 1 AND 5

            OR monetary_score
               NOT BETWEEN 1 AND 5
        """
    )

    assert count == 0


def test_pareto_percentage_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_customer_pareto

        WHERE
            cumulative_revenue_pct < 0

            OR

            cumulative_revenue_pct > 100.01
        """
    )

    assert count == 0


def test_customer_value_tiers_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_customer_value_tiers

        WHERE customer_value_tier NOT IN (
            'Platinum',
            'Gold',
            'Silver',
            'Bronze'
        )
        """
    )

    assert count == 0


def test_regional_revenue_share_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_regional_performance

        WHERE
            global_revenue_share_pct < 0

            OR

            global_revenue_share_pct > 100.01
        """
    )

    assert count == 0


def test_sla_percentage_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_executive_kpis

        WHERE
            sla_compliance_pct < 0

            OR

            sla_compliance_pct > 100
        """
    )

    assert count == 0


def test_request_failure_rate_valid():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_executive_kpis

        WHERE
            request_failure_rate_pct < 0

            OR

            request_failure_rate_pct > 100
        """
    )

    assert count == 0


def test_anomaly_z_scores_available():

    count = scalar(
        """
        SELECT COUNT(*)

        FROM analytics.v_revenue_anomalies

        WHERE z_score IS NOT NULL
        """
    )

    assert count > 0