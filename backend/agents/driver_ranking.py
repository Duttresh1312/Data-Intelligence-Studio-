from __future__ import annotations

from backend.core.state import DriverScore, StatisticalFeatureResult, StatisticalResultBundle


class DriverRankingEngine:
    def rank(self, bundle: StatisticalResultBundle) -> list[DriverScore]:
        if not bundle.results:
            return []

        raw_scores: list[tuple[StatisticalFeatureResult, float]] = []
        for result in bundle.results:
            significance = self._significance_score(result.p_value)
            effect = abs(result.effect_size or 0.0)
            corr = abs(result.correlation or 0.0)
            importance = abs(result.feature_importance or 0.0)
            raw = (0.35 * significance) + (0.25 * min(effect, 1.0)) + (0.2 * min(corr, 1.0)) + (0.2 * min(importance, 1.0))
            raw_scores.append((result, raw))

        max_raw = max(score for _, score in raw_scores) or 1.0
        ranked_pairs = sorted(raw_scores, key=lambda item: item[1], reverse=True)

        ranked: list[DriverScore] = []
        for idx, (result, raw) in enumerate(ranked_pairs, start=1):
            normalized = round(raw / max_raw, 4)
            ranked.append(
                DriverScore(
                    feature=result.feature,
                    strength_score=normalized,
                    importance_rank=idx,
                    statistical_significance=self._significance_label(result.p_value),
                    explanation_hint=self._hint(result),
                    p_value=result.p_value,
                    effect_size=result.effect_size,
                    feature_importance=result.feature_importance,
                    correlation=result.correlation,
                )
            )

        return ranked

    @staticmethod
    def _significance_score(p_value: float | None) -> float:
        if p_value is None:
            return 0.4
        if p_value <= 0.001:
            return 1.0
        if p_value <= 0.01:
            return 0.9
        if p_value <= 0.05:
            return 0.75
        if p_value <= 0.1:
            return 0.55
        return 0.25

    @staticmethod
    def _significance_label(p_value: float | None) -> str:
        if p_value is None:
            return "No p-value"
        if p_value <= 0.01:
            return "Strong"
        if p_value <= 0.05:
            return "Moderate"
        return "Weak"

    @staticmethod
    def _hint(result: StatisticalFeatureResult) -> str:
        if result.feature_importance and result.feature_importance > 0.2:
            return "High model contribution"
        if result.correlation and abs(result.correlation) > 0.4:
            return "Meaningful directional relationship"
        if result.effect_size and abs(result.effect_size) > 0.3:
            return "Material segment effect"
        return "Signal present but moderate"
