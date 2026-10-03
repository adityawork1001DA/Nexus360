from __future__ import annotations

from sqlalchemy import text

from src.database.connection import get_engine


# ============================================================
# NEXUS 360
# Analytics Semantic Layer Tests
#
# Covers:
#   Phase 3A
#   Phase 3B Batch 1
#   Phase 3B Batch 2A
#
# Current analytics assets:
#   Q01 - Q23
# ============================================================


REQUIRED_VIEWS = {
    # --------------------------------------------------------
    # Phase 3A
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # Phase 3B - Batch 1
    # --------------------------------------------------------
    "v_customer_cohort",
    "v_subscription_health",
    "v_subscription_renewal_risk",
    "v_customer_360",
    "v_product_penetration",
    "v_ai_adoption",
    "v_support_sla_performance",
    "v_support_resolution_percentiles",

    # --------------------------------------------------------
    # Phase 3B - Batch 2A
    # --------------------------------------------------------
    "v_cloud_finops",
    "v_customer_cloud_efficiency",
    "v_datacenter_operations",
    "v_cloud_sustainability",
    "v_weather_cloud_correlation",
}


def scalar(query: str):
    """
    Execute a SQL query expected to return
    exactly one scalar value.
    """

    engine = get_engine()

    with engine.connect() as connection:
        return connection.execute(
            text(query)
        ).scalar_one()


# ============================================================
# 1. ANALYTICS SCHEMA
# ============================================================


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
        "Missing analytics views: "
        f"{sorted(missing)}"
    )


# ============================================================
# 2. REVENUE ANALYTICS
# ============================================================


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
# 3. CUSTOMER ANALYTICS
# ============================================================


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


# ============================================================
# 4. COHORT ANALYTICS
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


def test_cohort_month_offset_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cohort
        WHERE months_since_signup < 0
        """
    )

    assert count == 0


# ============================================================
# 5. SUBSCRIPTION ANALYTICS
# ============================================================


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


def test_subscription_contract_values_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_subscription_health
        WHERE
            total_contract_value_usd < 0
            OR active_contract_value_usd < 0
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


# ============================================================
# 6. CUSTOMER 360
# ============================================================


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


def test_customer_360_revenue_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_360
        WHERE lifetime_revenue_usd < 0
        """
    )

    assert count == 0


def test_customer_360_cloud_cost_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_360
        WHERE cloud_cost_usd < 0
        """
    )

    assert count == 0


# ============================================================
# 7. PRODUCT & AI ANALYTICS
# ============================================================


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


def test_product_penetration_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_product_penetration
        """
    )

    assert count > 0


def test_ai_adoption_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_ai_adoption
        """
    )

    assert count > 0


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


# ============================================================
# 8. SUPPORT ANALYTICS
# ============================================================


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


# ============================================================
# 9. CLOUD FINOPS - Q19
# ============================================================


def test_cloud_finops_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_finops
        """
    )

    assert count > 0


def test_cloud_finops_cost_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_finops
        WHERE estimated_cost_usd < 0
        """
    )

    assert count == 0


def test_cloud_finops_failure_rate_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_finops
        WHERE
            request_failure_rate_pct < 0
            OR request_failure_rate_pct > 100
        """
    )

    assert count == 0


def test_cloud_finops_carbon_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_finops
        WHERE carbon_estimate_kg < 0
        """
    )

    assert count == 0


def test_cloud_finops_unit_cost_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_finops
        WHERE
            cost_per_compute_hour_usd < 0
            OR cost_per_million_requests_usd < 0
        """
    )

    assert count == 0


# ============================================================
# 10. CUSTOMER CLOUD EFFICIENCY - Q20
# ============================================================


def test_customer_cloud_efficiency_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cloud_efficiency
        """
    )

    assert count > 0


def test_customer_cloud_efficiency_matches_customers():

    customer_count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_customer
        """
    )

    analytics_count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cloud_efficiency
        """
    )

    assert analytics_count == customer_count


def test_customer_cloud_failure_rate_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cloud_efficiency
        WHERE
            request_failure_rate_pct < 0
            OR request_failure_rate_pct > 100
        """
    )

    assert count == 0


def test_customer_cloud_efficiency_quintile_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cloud_efficiency
        WHERE efficiency_quintile NOT BETWEEN 1 AND 5
        """
    )

    assert count == 0


def test_customer_cloud_efficiency_band_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_customer_cloud_efficiency
        WHERE cloud_efficiency_band NOT IN (
            'Highly Efficient',
            'Efficient',
            'Average',
            'Cost Heavy',
            'Optimization Priority'
        )
        """
    )

    assert count == 0


# ============================================================
# 11. DATACENTER OPERATIONS - Q21
# ============================================================


def test_datacenter_operations_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_datacenter_operations
        """
    )

    assert count > 0


def test_datacenter_operations_matches_dimension():

    datacenter_count = scalar(
        """
        SELECT COUNT(*)
        FROM warehouse.dim_datacenter
        """
    )

    analytics_count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_datacenter_operations
        """
    )

    assert analytics_count == datacenter_count


def test_datacenter_capacity_positive():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_datacenter_operations
        WHERE capacity_mw <= 0
        """
    )

    assert count == 0


def test_datacenter_renewable_percentage_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_datacenter_operations
        WHERE
            renewable_energy_pct < 0
            OR renewable_energy_pct > 100
        """
    )

    assert count == 0


def test_datacenter_failure_rate_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_datacenter_operations
        WHERE
            request_failure_rate_pct < 0
            OR request_failure_rate_pct > 100
        """
    )

    assert count == 0


def test_datacenter_cost_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_datacenter_operations
        WHERE estimated_cost_usd < 0
        """
    )

    assert count == 0


# ============================================================
# 12. SUSTAINABILITY - Q22
# ============================================================


def test_cloud_sustainability_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_sustainability
        """
    )

    assert count > 0


def test_cloud_sustainability_carbon_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_sustainability
        WHERE carbon_estimate_kg < 0
        """
    )

    assert count == 0


def test_cloud_sustainability_renewable_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_sustainability
        WHERE
            renewable_energy_pct < 0
            OR renewable_energy_pct > 100
        """
    )

    assert count == 0


def test_cloud_sustainability_band_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_sustainability
        WHERE renewable_energy_band NOT IN (
            'Renewable Leader',
            'Strong Renewable Mix',
            'Transitioning',
            'Renewable Improvement Priority'
        )
        """
    )

    assert count == 0


def test_cloud_sustainability_carbon_intensity_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_cloud_sustainability
        WHERE carbon_kg_per_compute_hour < 0
        """
    )

    assert count == 0


# ============================================================
# 13. WEATHER × CLOUD - Q23
# ============================================================


def test_weather_cloud_correlation_exists():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        """
    )

    assert count > 0


def test_weather_cloud_observations_exist():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE observation_days <= 0
        """
    )

    assert count == 0


def test_temperature_compute_correlation_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE
            temperature_compute_corr IS NOT NULL
            AND (
                temperature_compute_corr < -1
                OR temperature_compute_corr > 1
            )
        """
    )

    assert count == 0


def test_temperature_cost_correlation_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE
            temperature_cost_corr IS NOT NULL
            AND (
                temperature_cost_corr < -1
                OR temperature_cost_corr > 1
            )
        """
    )

    assert count == 0


def test_temperature_carbon_correlation_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE
            temperature_carbon_corr IS NOT NULL
            AND (
                temperature_carbon_corr < -1
                OR temperature_carbon_corr > 1
            )
        """
    )

    assert count == 0


def test_max_temperature_failure_correlation_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE
            max_temperature_failure_corr IS NOT NULL
            AND (
                max_temperature_failure_corr < -1
                OR max_temperature_failure_corr > 1
            )
        """
    )

    assert count == 0


def test_precipitation_failure_correlation_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE
            precipitation_failure_corr IS NOT NULL
            AND (
                precipitation_failure_corr < -1
                OR precipitation_failure_corr > 1
            )
        """
    )

    assert count == 0


def test_wind_failure_correlation_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_weather_cloud_correlation
        WHERE
            wind_failure_corr IS NOT NULL
            AND (
                wind_failure_corr < -1
                OR wind_failure_corr > 1
            )
        """
    )

    assert count == 0


# ============================================================
# 14. EXECUTIVE / PLATFORM QUALITY
# ============================================================


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


def test_executive_gross_margin_valid():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_executive_kpis
        WHERE gross_margin_pct > 100
        """
    )

    assert count == 0


def test_executive_cloud_cost_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_executive_kpis
        WHERE cloud_estimated_cost_usd < 0
        """
    )

    assert count == 0


def test_executive_carbon_non_negative():

    count = scalar(
        """
        SELECT COUNT(*)
        FROM analytics.v_executive_kpis
        WHERE carbon_estimate_kg < 0
        """
    )

    assert count == 0