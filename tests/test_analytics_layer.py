from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine


REQUIRED_VIEWS = {
    # Phase 3A
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

    # Phase 3B
    "v_customer_cohort",
    "v_subscription_health",
    "v_subscription_renewal_risk",
    "v_customer_360",
    "v_product_penetration",
    "v_ai_adoption",
    "v_support_sla_performance",
    "v_support_resolution_percentiles",
}


def scalar(query: str):
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
            OR revenue_share_pct > 100.01
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
            OR frequency_score NOT BETWEEN 1 AND 5
            OR monetary_score NOT BETWEEN 1 AND 5
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
            OR cumulative_revenue_pct > 100.01
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
            OR global_revenue_share_pct > 100.01
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
            OR sla_compliance_pct > 100
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
            OR request_failure_rate_pct > 100
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


# ============================================================
# Phase 3B Tests
# ============================================================


def test_customer_cohort_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cohort
        """
    )

    assert count > 0


def test_cohort_retention_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cohort
        WHERE
            retention_pct < 0
            OR retention_pct > 100
        """
    )

    assert count == 0


def test_subscription_health_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_subscription_health
        """
    )

    assert count > 0


def test_subscription_percentages_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_subscription_health
        WHERE
            active_subscription_pct < 0
            OR active_subscription_pct > 100
            OR auto_renew_pct < 0
            OR auto_renew_pct > 100
        """
    )

    assert count == 0


def test_subscription_risk_score_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_subscription_renewal_risk
        WHERE
            renewal_risk_score < 0
            OR renewal_risk_score > 100
        """
    )

    assert count == 0


def test_subscription_risk_band_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_subscription_renewal_risk
        WHERE renewal_risk_band NOT IN (
            'Low',
            'Medium',
            'High',
            'Critical'
        )
        """
    )

    assert count == 0


def test_customer_360_matches_customer_dimension():

    customer_dimension_count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_customer
        """
    )

    customer_360_count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_360
        """
    )

    assert (
        customer_360_count
        == customer_dimension_count
    )


def test_customer_360_failure_rate_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_360
        WHERE
            request_failure_rate_pct < 0
            OR request_failure_rate_pct > 100
        """
    )

    assert count == 0


def test_product_penetration_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_product_penetration
        WHERE
            customer_penetration_pct < 0
            OR customer_penetration_pct > 100
        """
    )

    assert count == 0


def test_ai_adoption_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_ai_adoption
        WHERE
            ai_adoption_pct < 0
            OR ai_adoption_pct > 100
        """
    )

    assert count == 0


def test_support_sla_performance_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_support_sla_performance
        """
    )

    assert count > 0


def test_support_sla_rates_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_support_sla_performance
        WHERE
            sla_compliance_pct < 0
            OR sla_compliance_pct > 100
            OR reopen_rate_pct < 0
            OR reopen_rate_pct > 100
        """
    )

    assert count == 0


def test_support_percentiles_exist():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_support_resolution_percentiles
        """
    )

    assert count > 0


def test_support_percentile_order():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_support_resolution_percentiles
        WHERE
            p50_resolution_hours
                > p75_resolution_hours

            OR p75_resolution_hours
                > p90_resolution_hours

            OR p90_resolution_hours
                > p95_resolution_hours
        """
    )

    assert count == 0