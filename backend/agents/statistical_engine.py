from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, f_oneway, mannwhitneyu, pearsonr, spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from backend.core.state import Hypothesis, StatisticalFeatureResult, StatisticalResultBundle


class StatisticalTestEngine:
    def run(
        self,
        dataframe: pd.DataFrame,
        hypotheses: list[Hypothesis],
        target_column: str,
        target_type: str,
    ) -> StatisticalResultBundle:
        df = dataframe.copy()
        quality_flags: list[str] = []
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' is not present in dataframe.")

        if df[target_column].isna().any():
            quality_flags.append("Target column contains missing values; pairwise rows were dropped per test.")

        results: list[StatisticalFeatureResult] = []
        for hypothesis in hypotheses:
            feature = hypothesis.feature
            if feature not in df.columns or feature == target_column:
                continue
            row = self._run_single(df, feature, target_column, target_type)
            if row is not None:
                results.append(row)

        model_type_used = "random_forest_classifier" if target_type == "classification" else "random_forest_regressor"
        importances = self._feature_importance(df, [r.feature for r in results], target_column, target_type)

        for result in results:
            if result.feature in importances:
                result.feature_importance = importances[result.feature]
            result.confidence_score = self._confidence(result)

        return StatisticalResultBundle(
            target_column=target_column,
            target_type="classification" if target_type == "classification" else "regression",
            model_type_used=model_type_used,
            data_quality_flags=quality_flags,
            results=results,
        )

    def _run_single(
        self,
        df: pd.DataFrame,
        feature: str,
        target: str,
        target_type: str,
    ) -> StatisticalFeatureResult | None:
        subset = df[[feature, target]].dropna()
        if subset.shape[0] < 12:
            return None

        x = subset[feature]
        y = subset[target]
        x_numeric = pd.api.types.is_numeric_dtype(x)

        if target_type == "classification":
            y_codes = y.astype("category").cat.codes
            n_classes = int(pd.Series(y_codes).nunique())
            if n_classes < 2:
                return None

            if x_numeric and n_classes == 2:
                group0 = x[y_codes == 0]
                group1 = x[y_codes == 1]
                if len(group0) < 3 or len(group1) < 3:
                    return None
                stat, p_value = mannwhitneyu(group0, group1, alternative="two-sided")
                effect = self._cohens_d(group0.to_numpy(dtype=float), group1.to_numpy(dtype=float))
                return StatisticalFeatureResult(
                    feature=feature,
                    test_type="mann_whitney_u",
                    p_value=float(p_value),
                    effect_size=abs(effect),
                    correlation=None,
                    feature_importance=None,
                )

            if x_numeric and n_classes > 2:
                groups = [x[y_codes == label].to_numpy(dtype=float) for label in sorted(pd.Series(y_codes).unique())]
                groups = [g for g in groups if len(g) >= 3]
                if len(groups) < 2:
                    return None
                f_stat, p_value = f_oneway(*groups)
                effect = self._eta_squared(groups)
                return StatisticalFeatureResult(
                    feature=feature,
                    test_type="anova_multi_class",
                    p_value=float(p_value),
                    effect_size=float(effect),
                )

            table = pd.crosstab(x.astype(str), y.astype(str))
            if table.shape[0] < 2 or table.shape[1] < 2:
                return None
            chi2, p_value, _, _ = chi2_contingency(table)
            n = float(table.to_numpy().sum())
            min_dim = min(table.shape) - 1
            cramers_v = math.sqrt((chi2 / n) / min_dim) if n > 0 and min_dim > 0 else 0.0
            return StatisticalFeatureResult(
                feature=feature,
                test_type="chi_square",
                p_value=float(p_value),
                effect_size=float(cramers_v),
            )

        # Regression target
        y_num = pd.to_numeric(y, errors="coerce")
        if y_num.isna().all():
            return None

        if x_numeric:
            x_num = pd.to_numeric(x, errors="coerce")
            pair = pd.DataFrame({"x": x_num, "y": y_num}).dropna()
            if pair.shape[0] < 12:
                return None
            pearson_corr, pearson_p = pearsonr(pair["x"], pair["y"])
            spearman_corr, _ = spearmanr(pair["x"], pair["y"])
            return StatisticalFeatureResult(
                feature=feature,
                test_type="pearson_spearman",
                p_value=float(pearson_p),
                effect_size=abs(float(pearson_corr)),
                correlation=float(spearman_corr) if np.isfinite(spearman_corr) else float(pearson_corr),
            )

        groups = []
        for _, grp in pd.DataFrame({"x": x.astype(str), "y": y_num}).dropna().groupby("x"):
            if grp.shape[0] >= 3:
                groups.append(grp["y"].to_numpy(dtype=float))
        if len(groups) < 2:
            return None
        f_stat, p_value = f_oneway(*groups)
        effect = self._eta_squared(groups)
        return StatisticalFeatureResult(
            feature=feature,
            test_type="anova",
            p_value=float(p_value),
            effect_size=float(effect),
            correlation=None,
        )

    def _feature_importance(
        self,
        df: pd.DataFrame,
        features: list[str],
        target_column: str,
        target_type: str,
    ) -> dict[str, float]:
        if not features:
            return {}

        subset = df[features + [target_column]].dropna()
        if subset.shape[0] < 20:
            return {}

        X = subset[features]
        y = subset[target_column]

        numeric_features = [col for col in features if pd.api.types.is_numeric_dtype(X[col])]
        categorical_features = [col for col in features if col not in numeric_features]

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", "passthrough", numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ],
            remainder="drop",
        )

        if target_type == "classification":
            y_model = y.astype("category").cat.codes
            model = RandomForestClassifier(n_estimators=180, random_state=42)
        else:
            y_model = pd.to_numeric(y, errors="coerce")
            mask = y_model.notna()
            X = X.loc[mask]
            y_model = y_model.loc[mask]
            if X.empty:
                return {}
            model = RandomForestRegressor(n_estimators=180, random_state=42)

        pipeline = Pipeline([("prep", preprocessor), ("model", model)])
        pipeline.fit(X, y_model)

        rf_model = pipeline.named_steps["model"]
        importances = rf_model.feature_importances_

        transformed_feature_names: list[str] = []
        transformed_feature_names.extend(numeric_features)
        if categorical_features:
            encoder = pipeline.named_steps["prep"].named_transformers_["cat"]
            encoded_names = encoder.get_feature_names_out(categorical_features).tolist()
            transformed_feature_names.extend(encoded_names)

        aggregated: dict[str, float] = {feature: 0.0 for feature in features}
        for name, importance in zip(transformed_feature_names, importances):
            matched = next((feature for feature in features if name == feature or name.startswith(f"{feature}_")), None)
            if matched is not None:
                aggregated[matched] += float(importance)

        return aggregated

    @staticmethod
    def _cohens_d(group_a: np.ndarray, group_b: np.ndarray) -> float:
        mean_diff = float(np.mean(group_a) - np.mean(group_b))
        var_a = float(np.var(group_a, ddof=1)) if len(group_a) > 1 else 0.0
        var_b = float(np.var(group_b, ddof=1)) if len(group_b) > 1 else 0.0
        pooled = np.sqrt(((len(group_a) - 1) * var_a + (len(group_b) - 1) * var_b) / max(1, len(group_a) + len(group_b) - 2))
        if pooled == 0:
            return 0.0
        return mean_diff / float(pooled)

    @staticmethod
    def _eta_squared(groups: list[np.ndarray]) -> float:
        all_values = np.concatenate(groups)
        grand_mean = float(np.mean(all_values))
        ss_between = sum(len(group) * (float(np.mean(group)) - grand_mean) ** 2 for group in groups)
        ss_total = float(np.sum((all_values - grand_mean) ** 2))
        if ss_total == 0:
            return 0.0
        return float(ss_between / ss_total)

    @staticmethod
    def _confidence(result: StatisticalFeatureResult) -> float:
        p_component = 0.0
        if result.p_value is not None:
            p_component = max(0.0, min(1.0, 1.0 - result.p_value))
        effect_component = min(1.0, abs(result.effect_size or 0.0))
        corr_component = min(1.0, abs(result.correlation or 0.0))
        imp_component = min(1.0, abs(result.feature_importance or 0.0))
        return round((0.35 * p_component) + (0.25 * effect_component) + (0.2 * corr_component) + (0.2 * imp_component), 4)
