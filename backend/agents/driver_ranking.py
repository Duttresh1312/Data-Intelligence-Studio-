from __future__ import annotations

from backend.core.state import DriverRanking, StatisticalResult


class DriverRankingEngine:
    @staticmethod
    def _impact_score(result: StatisticalResult) -> float:
        significance = 0.0
        if result.p_value is not None:
            significance = max(0.0, 1.0 - min(result.p_value, 1.0))
        effect = abs(result.effect_size) if result.effect_size is not None else 0.0
        importance = abs(result.feature_importance) if result.feature_importance is not None else 0.0
        magnitude = abs(result.score)
        return (0.4 * significance) + (0.3 * effect) + (0.2 * importance) + (0.1 * magnitude)

    def rank(self, results: list[StatisticalResult]) -> DriverRanking:
        ranked = sorted(results, key=self._impact_score, reverse=True)
        return DriverRanking(ranked_drivers=ranked)
