import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.model_selection import RandomizedSearchCV, GroupKFold
from sklearn.base import BaseEstimator, ClassifierMixin

# Create dummy data
X = pd.DataFrame(np.random.randn(100, 5), columns=[f"f{i}" for i in range(5)])
y = pd.Series(np.random.choice(['Low', 'Medium', 'High'], size=100))
groups = pd.Series(np.repeat(np.arange(10), 10))

class CatBoostGroupClassifier(BaseEstimator, ClassifierMixin):
    """Custom Scikit-Learn wrapper around CatBoostClassifier to ensure compatibility with sklearn clone() and RandomizedSearchCV."""
    def __init__(self, iterations=100, depth=6, learning_rate=0.1, l2_leaf_reg=3, class_weights=None, random_state=42, verbose=False):
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.l2_leaf_reg = l2_leaf_reg
        self.class_weights = class_weights
        self.random_state = random_state
        self.verbose = verbose
        
    def fit(self, X, y):
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
        self.classes_ = self.model_.classes_
        return self

    def predict(self, X):
        return self.model_.predict(X)

    def predict_proba(self, X):
        return self.model_.predict_proba(X)

cb_wrapper = CatBoostGroupClassifier(class_weights=[1.5, 1.0, 1.0], random_state=42, verbose=False)

param_distributions = {
    'depth': [4, 6],
    'learning_rate': [0.05, 0.1],
    'l2_leaf_reg': [1, 3],
    'iterations': [100, 150]
}

gkf = GroupKFold(n_splits=2)
rs = RandomizedSearchCV(
    estimator=cb_wrapper,
    param_distributions=param_distributions,
    n_iter=2,
    cv=gkf,
    scoring='f1_macro',
    verbose=1,
    random_state=42
)

try:
    rs.fit(X, y, groups=groups)
    print("SUCCESS: RandomizedSearchCV fit successfully!")
    print("Best params:", rs.best_params_)
except Exception as e:
    print("ERROR:", e)

