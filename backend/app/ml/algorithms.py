from dataclasses import dataclass, field
from typing import Any

import numpy as np
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier, XGBRegressor


@dataclass
class AlgorithmConfig:
    name: str
    problem_type: str  # classification | regression
    estimator_class: Any
    default_params: dict = field(default_factory=dict)
    param_grid: dict = field(default_factory=dict)


ALGORITHMS: dict[str, AlgorithmConfig] = {
    # Classification
    "logistic_regression": AlgorithmConfig(
        name="Logistic Regression",
        problem_type="classification",
        estimator_class=LogisticRegression,
        default_params={"max_iter": 1000},
        param_grid={"C": [0.01, 0.1, 1, 10], "solver": ["lbfgs", "liblinear"]},
    ),
    "random_forest_classifier": AlgorithmConfig(
        name="Random Forest Classifier",
        problem_type="classification",
        estimator_class=RandomForestClassifier,
        default_params={"n_estimators": 100},
        param_grid={"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10]},
    ),
    "gradient_boosting_classifier": AlgorithmConfig(
        name="Gradient Boosting Classifier",
        problem_type="classification",
        estimator_class=GradientBoostingClassifier,
        default_params={},
        param_grid={"n_estimators": [100, 200], "learning_rate": [0.05, 0.1, 0.2]},
    ),
    "xgboost_classifier": AlgorithmConfig(
        name="XGBoost Classifier",
        problem_type="classification",
        estimator_class=XGBClassifier,
        default_params={"eval_metric": "logloss"},
        param_grid={"n_estimators": [100, 200], "max_depth": [3, 5, 7], "learning_rate": [0.05, 0.1]},
    ),
    "lightgbm_classifier": AlgorithmConfig(
        name="LightGBM Classifier",
        problem_type="classification",
        estimator_class=LGBMClassifier,
        default_params={"verbose": -1},
        param_grid={"n_estimators": [100, 200], "num_leaves": [31, 63]},
    ),
    "svm_classifier": AlgorithmConfig(
        name="SVM Classifier",
        problem_type="classification",
        estimator_class=SVC,
        default_params={"probability": True},
        param_grid={"C": [0.1, 1, 10], "kernel": ["rbf", "linear"]},
    ),
    "knn_classifier": AlgorithmConfig(
        name="KNN Classifier",
        problem_type="classification",
        estimator_class=KNeighborsClassifier,
        default_params={},
        param_grid={"n_neighbors": [3, 5, 7, 11]},
    ),
    # Regression
    "linear_regression": AlgorithmConfig(
        name="Linear Regression",
        problem_type="regression",
        estimator_class=LinearRegression,
        default_params={},
        param_grid={},
    ),
    "ridge": AlgorithmConfig(
        name="Ridge",
        problem_type="regression",
        estimator_class=Ridge,
        default_params={},
        param_grid={"alpha": [0.1, 1.0, 10.0, 100.0]},
    ),
    "lasso": AlgorithmConfig(
        name="Lasso",
        problem_type="regression",
        estimator_class=Lasso,
        default_params={},
        param_grid={"alpha": [0.01, 0.1, 1.0, 10.0]},
    ),
    "random_forest_regressor": AlgorithmConfig(
        name="Random Forest Regressor",
        problem_type="regression",
        estimator_class=RandomForestRegressor,
        default_params={"n_estimators": 100},
        param_grid={"n_estimators": [50, 100, 200], "max_depth": [None, 5, 10]},
    ),
    "xgboost_regressor": AlgorithmConfig(
        name="XGBoost Regressor",
        problem_type="regression",
        estimator_class=XGBRegressor,
        default_params={},
        param_grid={"n_estimators": [100, 200], "max_depth": [3, 5, 7], "learning_rate": [0.05, 0.1]},
    ),
    "lightgbm_regressor": AlgorithmConfig(
        name="LightGBM Regressor",
        problem_type="regression",
        estimator_class=LGBMRegressor,
        default_params={"verbose": -1},
        param_grid={"n_estimators": [100, 200], "num_leaves": [31, 63]},
    ),
}


def get_algorithm(key: str) -> AlgorithmConfig:
    if key not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {key}. Valid: {list(ALGORITHMS)}")
    return ALGORITHMS[key]


def get_algorithms_for_problem(problem_type: str) -> dict[str, AlgorithmConfig]:
    return {k: v for k, v in ALGORITHMS.items() if v.problem_type == problem_type}
