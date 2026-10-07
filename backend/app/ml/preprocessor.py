"""Preprocessing Pipeline Module

Constructs robust Scikit-learn ColumnTransformer and Pipelines for numeric scaling,
missing-value imputation, and categorical encoding.
"""

from typing import List, Tuple
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from app.ml.features import (
    BASE_NUMERIC_FEATURES,
    ENGINEERED_FEATURES,
    CATEGORICAL_FEATURES
)

ALL_NUMERIC_FEATURES = BASE_NUMERIC_FEATURES + ENGINEERED_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """Creates a Scikit-learn ColumnTransformer for full dataset preprocessing.

    Architecture:
    - Numerical Pipeline: Median imputation -> Standard scaling (zero mean, unit variance)
    - Categorical Pipeline: One-hot encoding with handle_unknown='ignore'
    """
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, ALL_NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES)
        ],
        remainder="drop"
    )

    return preprocessor
