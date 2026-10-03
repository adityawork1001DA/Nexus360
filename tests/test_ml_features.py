import numpy as np

from src.ml.customer_features import (
    CustomerFeatureBuilder,
)


def build_bundle():
    return CustomerFeatureBuilder().build()


def test_customer_features_exist():

    bundle = build_bundle()

    assert not bundle.features.empty


def test_customer_features_unique_customer():

    bundle = build_bundle()

    assert (
        bundle.features[
            "customer_id"
        ].is_unique
    )


def test_customer_features_have_model_columns():

    bundle = build_bundle()

    assert len(
        bundle.feature_columns
    ) > 0

    assert set(
        bundle.feature_columns
    ).issubset(
        bundle.features.columns
    )


def test_customer_numeric_features_finite():

    bundle = build_bundle()

    values = (
        bundle.features[
            bundle.numeric_features
        ]
        .to_numpy(
            dtype=float
        )
    )

    assert np.isfinite(
        values
    ).all()


def test_customer_gross_margin_finite():

    bundle = build_bundle()

    assert np.isfinite(
        bundle.features[
            "gross_margin_pct"
        ]
    ).all()


def test_customer_subscription_percentage_valid():

    bundle = build_bundle()

    values = bundle.features[
        "active_subscription_pct"
    ]

    assert (
        values >= 0
    ).all()

    assert (
        values <= 100
    ).all()


def test_customer_sla_breach_percentage_valid():

    bundle = build_bundle()

    values = bundle.features[
        "sla_breach_rate_pct"
    ]

    assert (
        values >= 0
    ).all()

    assert (
        values <= 100
    ).all()


def test_customer_failed_request_percentage_valid():

    bundle = build_bundle()

    values = bundle.features[
        "failed_request_rate_calculated_pct"
    ]

    assert (
        values >= 0
    ).all()

    assert (
        values <= 100
    ).all()