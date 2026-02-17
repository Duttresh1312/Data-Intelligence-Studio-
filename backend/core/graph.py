from datetime import datetime, timezone

from backend.agents.dataset_summary import DatasetSummaryAgent
from backend.agents.domain_inference import DomainInferenceAgent
from backend.agents.ingestion import DataIngestionAgent
from backend.agents.missing_value_treatment import MissingValueTreatmentAgent
from backend.agents.profiling import ProfilingAgent
from backend.core.state import ConversationMessage, StudioPhase, StudioState


class StudioGraph:
    def __init__(self):
        self.state = StudioState(current_phase=StudioPhase.LANDING)

    def _add_message(self, role: str, content: str) -> None:
        self.state.conversation_history.append(
            ConversationMessage(
                role=role,  # type: ignore[arg-type]
                content=content,
                timestamp=datetime.now(timezone.utc),
            )
        )

    @staticmethod
    def _build_dataset_opening(state: StudioState) -> str:
        profile = state.dataset_profile
        if profile is None:
            return "I've reviewed the dataset profile."

        metric_columns = [name for name, role in profile.column_roles.items() if role.value == "NUMERIC_METRIC"]
        high_missing = [(name, pct) for name, pct in profile.missing_percentage.items() if pct > 10]

        parts: list[str] = []
        if metric_columns:
            parts.append(
                "This dataset appears to contain measurable business metrics such as "
                f"{', '.join(metric_columns[:2])}."
            )
        if profile.datetime_columns:
            parts.append(f"It spans a temporal dimension via {profile.datetime_columns[0]}.")
        if high_missing:
            column, pct = sorted(high_missing, key=lambda item: item[1], reverse=True)[0]
            parts.append(f"{column} has {round(pct, 2)}% missing values, which may affect analysis.")

        if not parts:
            parts.append("The profile shows structured columns with limited explicit metric/time signals.")
        return " ".join(parts)

    def run_ingestion(self, file):
        ingestion_agent = DataIngestionAgent()
        self.state = ingestion_agent.ingest(file)
        self.state.current_phase = StudioPhase.DATA_UPLOADED
        return self.state

    def run_profiling(self):
        if self.state.dataframe is None:
            self.state.errors.append("Dataframe not available for profiling")
            return self.state
        profiling_agent = ProfilingAgent()
        self.state.dataset_profile = profiling_agent.profile(self.state.dataframe)
        self.state.current_phase = StudioPhase.PROFILE_READY
        return self.state

    async def run_upload_pipeline(self, file):
        self.run_ingestion(file)
        if self.state.errors:
            return self.state
        self.run_profiling()
        return self.state

    async def run_start_analysis(self):
        if self.state.dataset_profile is None:
            self.state.errors.append("Dataset profile not available for domain inference")
            return self.state
        domain_agent = DomainInferenceAgent()
        self.state.domain_classification = await domain_agent.infer(
            profile=self.state.dataset_profile,
            column_names=self.state.dataframe_columns or [],
        )
        if self.state.domain_classification is None:
            self.state.errors.append("Domain classification generation failed")
            return self.state

        summary_agent = DatasetSummaryAgent()
        self.state.dataset_summary_report = await summary_agent.generate(
            profile=self.state.dataset_profile,
            domain_classification=self.state.domain_classification,
            include_analysis_guidance=False,
        )
        if self.state.dataset_summary_report is None:
            self.state.errors.append("Dataset summary report generation failed")
            return self.state

        missing_agent = MissingValueTreatmentAgent()
        self.state.missing_value_solutions = missing_agent.suggest(self.state.dataset_profile)
        self.state.last_missing_treatment_result = None

        opening = self._build_dataset_opening(self.state)
        self._add_message("assistant", f"{opening} {self.state.dataset_summary_report.executive_summary}")
        self.state.current_phase = StudioPhase.WAITING_FOR_INTENT
        return self.state

    async def run_chat_turn(self, user_message: str):
        self.state.user_intent = user_message
        self._add_message("user", user_message)

        if self.state.current_phase == StudioPhase.WAITING_FOR_INTENT:
            self._add_message(
                "assistant",
                "Goal captured. I can continue refining insights from this dataset context.",
            )
            return self.state

        self._add_message(
            "assistant",
            f"Current phase is {self.state.current_phase.value}. "
            "Upload data and start analysis before chatting.",
        )
        return self.state
