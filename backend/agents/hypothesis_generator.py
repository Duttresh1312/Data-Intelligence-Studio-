from __future__ import annotations

from backend.core.state import ColumnRole, DatasetProfile, Hypothesis


class HypothesisGeneratorAgent:
    def generate(
        self,
        dataset_profile: DatasetProfile,
        target_column: str,
        target_type: str,
    ) -> list[Hypothesis]:
        hypotheses: list[Hypothesis] = []
        roles = dataset_profile.column_roles

        numeric_features = [
            col for col, role in roles.items() if role == ColumnRole.NUMERIC_METRIC and col != target_column
        ]
        categorical_features = [
            col
            for col, role in roles.items()
            if role in (ColumnRole.CATEGORICAL_DIMENSION, ColumnRole.BOOLEAN, ColumnRole.TEXT) and col != target_column
        ]

        if target_type == "classification":
            for feature in numeric_features[:8]:
                hypotheses.append(
                    Hypothesis(
                        feature=feature,
                        type="classification_signal",
                        description=f"Variation in {feature} is associated with class shifts in {target_column}.",
                    )
                )
            for feature in categorical_features[:8]:
                hypotheses.append(
                    Hypothesis(
                        feature=feature,
                        type="group_difference",
                        description=f"Category membership in {feature} changes class distribution of {target_column}.",
                    )
                )
        else:
            for feature in numeric_features[:10]:
                hypotheses.append(
                    Hypothesis(
                        feature=feature,
                        type="correlation",
                        description=f"{feature} has measurable correlation with {target_column}.",
                    )
                )
            for feature in categorical_features[:8]:
                hypotheses.append(
                    Hypothesis(
                        feature=feature,
                        type="group_difference",
                        description=f"Mean {target_column} differs across groups in {feature}.",
                    )
                )

        # Ensure deterministic non-empty output when possible.
        if not hypotheses:
            fallback_features = [col for col in roles.keys() if col != target_column][:6]
            for feature in fallback_features:
                hypotheses.append(
                    Hypothesis(
                        feature=feature,
                        type="correlation" if target_type == "regression" else "classification_signal",
                        description=f"{feature} may influence {target_column} and should be statistically tested.",
                    )
                )

        return hypotheses[:20]
