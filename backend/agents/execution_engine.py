from __future__ import annotations

import asyncio
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from fastapi import WebSocket

from backend.agents.driver_ranking import DriverRankingEngine
from backend.agents.hypothesis_generator import HypothesisGeneratorAgent
from backend.agents.insight_synthesis import InsightSynthesisAgent
from backend.agents.statistical_engine import StatisticalTestEngine
from backend.core.state import (
    AnalysisPlan,
    ExecutionResult,
    IntentType,
    OperationType,
    StudioPhase,
    StudioState,
)


class ExecutionEngineAgent:
    async def _send_event(
        self,
        websocket: WebSocket | None,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        if websocket is None:
            return
        try:
            await websocket.send_json({"type": event_type, "payload": payload})
        except Exception:
            return

    async def execute_plan(
        self,
        plan: AnalysisPlan,
        state: StudioState,
        websocket: WebSocket | None = None,
    ) -> list[ExecutionResult]:
        if state.dataframe is None:
            raise ValueError("Dataframe is not available for execution.")

        df = state.dataframe.copy()
        state.execution_results = []
        context: dict[str, Any] = {}

        for step in plan.steps:
            await self._send_event(
                websocket,
                "step_started",
                {"step_id": step.step_id, "operation_type": step.operation_type.value},
            )
            await asyncio.sleep(0)
            try:
                op = step.operation_type
                if op == OperationType.SUMMARY:
                    result = self._run_summary(step.step_id, df)
                elif op == OperationType.GROUPBY:
                    result = self._run_groupby(step.step_id, df, step.parameters)
                elif op == OperationType.CORRELATION:
                    result = self._run_correlation(step.step_id, df)
                elif op == OperationType.TREND:
                    result = self._run_trend(step.step_id, df, step.parameters)
                elif op == OperationType.TRAIN_MODEL:
                    result = self._run_train_model(step.step_id, df, step.parameters, context)
                elif op == OperationType.EVALUATE_MODEL:
                    result = self._run_evaluate_model(step.step_id, context)
                elif op == OperationType.CLEAN_DATA:
                    result, df = self._run_clean_data(step.step_id, df, step.parameters)
                else:
                    raise ValueError(f"Unknown operation_type: {step.operation_type}")

                state.execution_results.append(result)
                await self._send_event(
                    websocket,
                    "step_completed",
                    {
                        "step_id": result.step_id,
                        "status": result.status,
                        "summary": result.result_summary,
                        "metrics": result.metrics,
                    },
                )
            except Exception as exc:
                failed = ExecutionResult(
                    step_id=step.step_id,
                    status="FAILED",
                    result_summary=f"{step.operation_type.value} failed: {exc}",
                    metrics=None,
                )
                state.execution_results.append(failed)
                await self._send_event(
                    websocket,
                    "step_failed",
                    {
                        "step_id": step.step_id,
                        "error": str(exc),
                    },
                )

        state.current_phase = StudioPhase.COMPLETED
        await self._run_driver_analysis(state, df, websocket)
        await self._send_event(
            websocket,
            "analysis_completed",
            {
                "phase": state.current_phase.value,
                "execution_results": [result.model_dump() for result in state.execution_results],
                "driver_ranking": state.driver_ranking.model_dump() if state.driver_ranking else None,
                "driver_insight_report": (
                    state.driver_insight_report.model_dump() if state.driver_insight_report else None
                ),
            },
        )
        return state.execution_results

    async def _run_driver_analysis(
        self,
        state: StudioState,
        dataframe: pd.DataFrame,
        websocket: WebSocket | None,
    ) -> None:
        if state.intent_classification is None or state.dataset_profile is None:
            return
        await self._send_event(
            websocket,
            "step_started",
            {"step_id": "driver_analysis", "operation_type": "DRIVER_DISCOVERY"},
        )
        try:
            hypothesis_agent = HypothesisGeneratorAgent()
            hypothesis_set = await hypothesis_agent.generate(
                intent_classification=state.intent_classification,
                dataset_profile=state.dataset_profile,
            )
            state.hypothesis_set = hypothesis_set

            stats_engine = StatisticalTestEngine()
            statistical_results = stats_engine.run(
                dataframe=dataframe,
                hypotheses=hypothesis_set,
                intent_type=state.intent_classification.intent_type,
            )
            state.statistical_results = statistical_results

            ranking_engine = DriverRankingEngine()
            state.driver_ranking = ranking_engine.rank(statistical_results)

            top_target = None
            if state.driver_ranking.ranked_drivers:
                top_target = state.driver_ranking.ranked_drivers[0].target

            insight_agent = InsightSynthesisAgent()
            state.driver_insight_report = await insight_agent.synthesize(
                ranked_drivers=state.driver_ranking,
                intent_type=state.intent_classification.intent_type,
                sample_size=int(dataframe.shape[0]),
                target_variable=top_target,
            )

            await self._send_event(
                websocket,
                "step_completed",
                {
                    "step_id": "driver_analysis",
                    "status": "SUCCESS",
                    "summary": "Generated ranked drivers and synthesized analytical interpretation.",
                    "metrics": {
                        "hypotheses": len(hypothesis_set.hypotheses),
                        "statistical_results": len(statistical_results),
                    },
                },
            )
        except Exception as exc:
            await self._send_event(
                websocket,
                "step_failed",
                {"step_id": "driver_analysis", "error": str(exc)},
            )

    def execute(self, dataframe: pd.DataFrame, plan: AnalysisPlan) -> list[ExecutionResult]:
        df = dataframe.copy()
        results: list[ExecutionResult] = []
        context: dict[str, Any] = {}

        for step in plan.steps:
            try:
                op = step.operation_type
                if op == OperationType.SUMMARY:
                    result = self._run_summary(step.step_id, df)
                elif op == OperationType.GROUPBY:
                    result = self._run_groupby(step.step_id, df, step.parameters)
                elif op == OperationType.CORRELATION:
                    result = self._run_correlation(step.step_id, df)
                elif op == OperationType.TREND:
                    result = self._run_trend(step.step_id, df, step.parameters)
                elif op == OperationType.TRAIN_MODEL:
                    result = self._run_train_model(step.step_id, df, step.parameters, context)
                elif op == OperationType.EVALUATE_MODEL:
                    result = self._run_evaluate_model(step.step_id, context)
                elif op == OperationType.CLEAN_DATA:
                    result, df = self._run_clean_data(step.step_id, df, step.parameters)
                else:
                    raise ValueError(f"Unknown operation_type: {step.operation_type}")
                results.append(result)
            except Exception as exc:
                results.append(
                    ExecutionResult(
                        step_id=step.step_id,
                        status="FAILED",
                        result_summary=f"{step.operation_type.value} failed: {exc}",
                        metrics=None,
                    )
                )
        return results

    def _run_summary(self, step_id: str, df: pd.DataFrame) -> ExecutionResult:
        summary = df.describe(include="all").fillna("").to_dict()
        return ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary="Generated dataframe summary statistics.",
            metrics={
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "summary": summary,
            },
        )

    def _run_groupby(self, step_id: str, df: pd.DataFrame, parameters: dict[str, Any]) -> ExecutionResult:
        group_by = parameters.get("group_by")
        target_column = parameters.get("target_column")
        agg = parameters.get("agg", "mean")
        if not group_by or group_by not in df.columns:
            raise ValueError("Valid group_by column is required.")
        if not target_column or target_column not in df.columns:
            raise ValueError("Valid target_column is required.")
        grouped = df.groupby(group_by)[target_column].agg(agg).sort_values(ascending=False)
        return ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary=f"Computed {agg} by {group_by} for {target_column}.",
            metrics={"groupby_result": grouped.head(20).to_dict()},
        )

    def _run_correlation(self, step_id: str, df: pd.DataFrame) -> ExecutionResult:
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] < 2:
            raise ValueError("At least two numeric columns are required for correlation.")
        corr = numeric.corr(numeric_only=True)
        flattened = corr.where(~np.eye(corr.shape[0], dtype=bool)).stack()
        top_pair = flattened.abs().idxmax() if not flattened.empty else None
        top_value = float(flattened[top_pair]) if top_pair else None
        return ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary="Computed correlation matrix for numeric columns.",
            metrics={
                "correlation_matrix": corr.round(4).to_dict(),
                "strongest_pair": list(top_pair) if top_pair else None,
                "strongest_value": top_value,
            },
        )

    def _run_trend(self, step_id: str, df: pd.DataFrame, parameters: dict[str, Any]) -> ExecutionResult:
        datetime_column = parameters.get("datetime_column")
        target_column = parameters.get("target_column")
        if not datetime_column or datetime_column not in df.columns:
            raise ValueError("Valid datetime_column is required.")
        temp = df.copy()
        temp[datetime_column] = pd.to_datetime(temp[datetime_column], errors="coerce")
        temp = temp.dropna(subset=[datetime_column])
        if temp.empty:
            raise ValueError("No parseable datetime values for trend analysis.")
        if target_column and target_column in temp.columns and pd.api.types.is_numeric_dtype(temp[target_column]):
            trend = (
                temp.set_index(datetime_column)[target_column]
                .resample("ME")
                .mean()
                .dropna()
            )
            label = f"Monthly mean trend for {target_column}"
        else:
            trend = temp.set_index(datetime_column).resample("ME").size()
            label = "Monthly row-count trend"
        return ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary=label,
            metrics={"trend_points": {str(k.date()): float(v) for k, v in trend.items()}},
        )

    def _run_train_model(
        self,
        step_id: str,
        df: pd.DataFrame,
        parameters: dict[str, Any],
        context: dict[str, Any],
    ) -> ExecutionResult:
        target_column = parameters.get("target_column")
        if not target_column or target_column not in df.columns:
            raise ValueError("TRAIN_MODEL requires a valid target_column.")

        y = df[target_column]
        X = df.drop(columns=[target_column])
        X = pd.get_dummies(X, drop_first=True)
        valid_mask = ~(y.isna() | X.isna().any(axis=1))
        X = X.loc[valid_mask]
        y = y.loc[valid_mask]
        if X.empty or y.empty:
            raise ValueError("No valid rows after filtering missing values.")

        is_classification = not pd.api.types.is_numeric_dtype(y) or y.nunique() <= 10
        if is_classification and y.dtype == "object":
            y = y.astype("category").cat.codes

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        if is_classification:
            model = LogisticRegression(max_iter=1000)
            task_type = "classification"
        else:
            model = LinearRegression()
            task_type = "regression"
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        context["model"] = model
        context["task_type"] = task_type
        context["y_test"] = y_test
        context["y_pred"] = y_pred

        return ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary=f"Trained baseline {task_type} model on target '{target_column}'.",
            metrics={
                "task_type": task_type,
                "target_column": target_column,
                "train_rows": int(X_train.shape[0]),
                "test_rows": int(X_test.shape[0]),
                "feature_count": int(X_train.shape[1]),
            },
        )

    def _run_evaluate_model(self, step_id: str, context: dict[str, Any]) -> ExecutionResult:
        if "model" not in context:
            raise ValueError("No trained model available for evaluation.")
        y_test = context["y_test"]
        y_pred = context["y_pred"]
        task_type = context["task_type"]

        if task_type == "classification":
            metrics = {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision_weighted": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
                "recall_weighted": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
                "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
            }
        else:
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            metrics = {
                "mae": float(mean_absolute_error(y_test, y_pred)),
                "rmse": rmse,
                "r2": float(r2_score(y_test, y_pred)),
            }

        return ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary=f"Evaluated {task_type} model performance.",
            metrics=metrics,
        )

    def _run_clean_data(
        self,
        step_id: str,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> tuple[ExecutionResult, pd.DataFrame]:
        operations = parameters.get(
            "operations",
            ["drop_duplicates", "fill_numeric_median", "fill_categorical_mode"],
        )
        cleaned = df.copy()
        metrics: dict[str, Any] = {
            "rows_before": int(df.shape[0]),
            "missing_before": int(df.isna().sum().sum()),
        }

        if "drop_duplicates" in operations:
            before = cleaned.shape[0]
            cleaned = cleaned.drop_duplicates()
            metrics["duplicates_removed"] = int(before - cleaned.shape[0])

        if "fill_numeric_median" in operations:
            for column in cleaned.select_dtypes(include=[np.number]).columns:
                cleaned[column] = cleaned[column].fillna(cleaned[column].median())

        if "fill_categorical_mode" in operations:
            cat_cols = cleaned.select_dtypes(exclude=[np.number]).columns
            for column in cat_cols:
                mode = cleaned[column].mode(dropna=True)
                fill_value = mode.iloc[0] if not mode.empty else "UNKNOWN"
                cleaned[column] = cleaned[column].fillna(fill_value)

        if "remove_outliers_iqr" in operations:
            numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                q1 = cleaned[col].quantile(0.25)
                q3 = cleaned[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                cleaned = cleaned[(cleaned[col] >= lower) & (cleaned[col] <= upper)]

        metrics["rows_after"] = int(cleaned.shape[0])
        metrics["missing_after"] = int(cleaned.isna().sum().sum())

        result = ExecutionResult(
            step_id=step_id,
            status="SUCCESS",
            result_summary="Applied deterministic data cleaning operations.",
            metrics=metrics,
        )
        return result, cleaned
