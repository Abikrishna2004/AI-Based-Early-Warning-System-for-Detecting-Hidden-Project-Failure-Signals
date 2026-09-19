from typing import Any, Dict, List, Optional, cast
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import RandomizedSearchCV, GroupKFold
from sklearn.base import BaseEstimator, ClassifierMixin

# Dummy dataset for testing hyperparameter tuning
X = pd.DataFrame(np.random.randn(100, 5), columns=[f"f{i}" for i in range(5)])
y = pd.Series(np.random.choice(['Low', 'Medium', 'High'], size=100))
groups = pd.Series(np.repeat(np.arange(10), 10))
weights_list: List[float] = [1.5, 1.0, 1.0]

# Option A: Direct CatBoostClassifier using auto_class_weights='Balanced'
print("--- Testing Option A: Direct CatBoost with auto_class_weights='Balanced' ---")
cb_a = CatBoostClassifier(auto_class_weights='Balanced', random_state=42, verbose=False)
param_distributions: Dict[str, Any] = {
    'depth': [4, 6],
    'learning_rate': [0.05, 0.1],
    'l2_leaf_reg': [1, 3],
    'iterations': [100, 150]
}

gkf = GroupKFold(n_splits=2)
rs_a = RandomizedSearchCV(
    estimator=cast(Any, cb_a),
    param_distributions=param_distributions,
    n_iter=2,
    cv=gkf,
    scoring='f1_macro',
    verbose=1,
    random_state=42
)

try:
    rs_a.fit(X, y, groups=groups)
    print("SUCCESS Option A!")
    print("Best params:", rs_a.best_params_)
except Exception as e:
    print("Option A failed:", e)

# Option B: Custom Scikit-Learn Wrapper for Custom List Class Weights
print("\n--- Testing Option B: Custom Wrapper for Custom Class Weights List ---")
class CatBoostGroupClassifier(BaseEstimator, ClassifierMixin):
    """Custom Scikit-Learn wrapper around CatBoostClassifier for clean hyperparameter tuning."""
    def __init__(
        self,
        iterations: int = 100,
        depth: int = 6,
        learning_rate: float = 0.1,
        l2_leaf_reg: float = 3.0,
        class_weights: Optional[List[float]] = None,
        random_state: int = 42,
        verbose: bool = False
    ) -> None:
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.l2_leaf_reg = l2_leaf_reg
        self.class_weights = class_weights
        self.random_state = random_state
        self.verbose = verbose
        self.model_: Optional[CatBoostClassifier] = None
        self.classes_: Any = None
        
    def fit(self, X: Any, y: Any) -> "CatBoostGroupClassifier":
        self.model_ = CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            l2_leaf_reg=self.l2_leaf_reg,
            class_weights=self.class_weights,
            random_state=self.random_state,
            verbose=self.verbose
        )
        self.model_.fit(X, y)
        self.classes_ = getattr(self.model_, "classes_", None)
        return self

    def predict(self, X: Any) -> Any:
        if self.model_ is None:
            raise RuntimeError("Model is not fitted yet.")
        return self.model_.predict(X)

    def predict_proba(self, X: Any) -> Any:
        if self.model_ is None:
            raise RuntimeError("Model is not fitted yet.")
        return self.model_.predict_proba(X)

cb_wrapper = CatBoostGroupClassifier(class_weights=weights_list, verbose=False)
rs_b = RandomizedSearchCV(
    estimator=cb_wrapper,
    param_distributions=param_distributions,
    n_iter=2,
    cv=gkf,
    scoring='f1_macro',
    verbose=1,
    random_state=42
)

try:
    rs_b.fit(X, y, groups=groups)
    print("SUCCESS Option B!")
    print("Best params:", rs_b.best_params_)
except Exception as e:
    print("Option B failed:", e)
