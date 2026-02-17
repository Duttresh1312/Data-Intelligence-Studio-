from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, f_oneway, pearsonr
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from backend.core.state import HypothesisSet, IntentType, StatisticalResult


class StatisticalTestEngine:
    def run(
        self,
        dataframe: pd.DataFrame,
        hypotheses: HypothesisSet,
        intent_type: IntentType,
    ) -> list[StatisticalResult]:
        results: list[StatisticalResult] = []
        df = dataframe.copy()

        for hypothesis in hypotheses.hypotheses:
            predictor = hypothesis.predictor_column
            target = hypothesis.target_column
            if predictor not in df.columns:
                continue
            if target and target not in df.columns:
                continue

            if intent_type == IntentType.PREDICTIVE and target:
                predictive = self._predictive_test(df, predictor, target)
                if predictive is not None:
                    results.append(predictive)
                continue

            if target is None:
                continue
            result = self._pairwise_test(df, predictor, target)
            if result is not None:
                results.append(result)

        return results

    def _pairwise_test(self, df: pd.DataFrame, predictor: str, target: str) -> Optional[StatisticalResult]:
        x = df[predictor]
        y = df[target]
        numeric_x = pd.api.types.is_numeric_dtype(x)
        numeric_y = pd.api.types.is_numeric_dtype(y)

        if numeric_x and numeric_y:
            pair = pd.DataFrame({"x": x, "y": y}).dropna()
            if pair.shape[0] < 5:
                return None
            corr, p_value = pearsonr(pair["x"], pair["y"])
            return StatisticalResult(
                predictor=predictor,
                target=target,
                test_type="pearson",
                score=float(corr),
                p_value=float(p_value),
                effect_size=float(corr * corr),
            )

        if (not numeric_x) and numeric_y:
            pair = pd.DataFrame({"x": x.astype(str), "y": y}).dropna()
            grouped = [grp["y"].values for _, grp in pair.groupby("x")]
            if len(grouped) < 2:
                return None
            stat, p_value = f_oneway(*grouped)
            grand_mean = pair["y"].mean()
            ss_between = sum(len(group) * (group.mean() - grand_mean) ** 2 for group in grouped)
            ss_total = ((pair["y"] - grand_mean) ** 2).sum()
            eta_sq = float(ss_between / ss_total) if ss_total > 0 else 0.0
            return StatisticalResult(
                predictor=predictor,
                target=target,
                test_type="anova",
                score=float(stat),
                p_value=float(p_value),
                effect_size=eta_sq,
            )

        if (not numeric_x) and (not numeric_y):
            table = pd.crosstab(x.astype(str), y.astype(str))
            if table.shape[0] < 2 or table.shape[1] < 2:
                return None
            chi2, p_value, _, _ = chi2_contingency(table)
            n = table.to_numpy().sum()
            min_dim = min(table.shape) - 1
            cramers_v = float(np.sqrt((chi2 / n) / min_dim)) if n > 0 and min_dim > 0 else 0.0
            return StatisticalResult(
                predictor=predictor,
                target=target,
                test_type="chi_square",
                score=float(chi2),
                p_value=float(p_value),
                effect_size=cramers_v,
            )

        if numeric_x and (not numeric_y):
            # Symmetry: treat categorical target as predictor for compatible test naming.
            return self._pairwise_test(df, target, predictor)
        return None

    def _predictive_test(self, df: pd.DataFrame, predictor: str, target: str) -> Optional[StatisticalResult]:
        if target not in df.columns or predictor not in df.columns:
            return None
        subset = df[[predictor, target]].dropna()
        if subset.shape[0] < 20:
            return None

        X = pd.get_dummies(subset[[predictor]], drop_first=True)
        if X.empty:
            return None
        y = subset[target]
        is_numeric_target = pd.api.types.is_numeric_dtype(y)

        if is_numeric_target and y.nunique() > 10:
            model = RandomForestRegressor(n_estimators=120, random_state=42)
        else:
            y = y.astype("category").cat.codes
            model = RandomForestClassifier(n_estimators=120, random_state=42)

        model.fit(X, y)
        importance = float(np.mean(model.feature_importances_))
        return StatisticalResult(
            predictor=predictor,
            target=target,
            test_type="random_forest_importance",
            score=importance,
            p_value=None,
            effect_size=importance,
            feature_importance=importance,
        )
