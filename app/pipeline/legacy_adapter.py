"""Legacy adapter for backward compatibility with DataStateMachine consumers.

Usage goal:
    from app.pipeline.legacy_adapter import LegacyStateMachineAdapter as DataStateMachine
    adapter = LegacyStateMachineAdapter(context, mode='full_auto', ...)
    adapter.process()

For now we keep the old `python_scripts.state_machine.DataStateMachine` intact
because tests import it directly. This adapter is an intermediate step: once
call sites migrate we can alias or replace the old class.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.domain.models import ProjectContext
from app.pipeline.orchestrator import DataPipelineOrchestrator
from app.infrastructure.logging_sinks import LogSink
from app.infrastructure.deprecation import DeprecationEmitter

DEPRECATION_MESSAGE = (
    "DataStateMachine is deprecated; use DataPipelineOrchestrator (or access via LegacyStateMachineAdapter)."
)


@dataclass
class LegacyStateMachineAdapter:
    """Wraps pipeline orchestrator but mimics subset of DataStateMachine interface.

    Parameters mirror the legacy usage so existing code can be switched over
    incrementally. Only `process()` is provided (loop semantics handled by orchestrator).
    """
    context: ProjectContext
    mode: str = 'full_auto'
    output_type: str = 'raw'
    processes: Optional[list] = None
    processed_data_save_path: Optional[str] = None
    visualization_params: Optional[Dict[str, Any]] = None
    log_sink: LogSink | None = None
    _orchestrator: DataPipelineOrchestrator | None = field(init=False, default=None)

    def __post_init__(self):  # noqa: D401
        if self.log_sink is not None:
            DeprecationEmitter.emit(
                key='legacy.state_machine',
                sink=self.log_sink,
                message=DEPRECATION_MESSAGE,
                extra={'adapter': 'legacy_state_machine'}
            )

    # Backward compatible method name
    def process(self):
        """Execute the pipeline and return final dataframe (legacy contract)."""
        if self._orchestrator is None:
            self._orchestrator = DataPipelineOrchestrator(
                self.context,
                mode=self.mode,
                output_type=self.output_type,
                processes=self.processes,
                processed_data_save_path=self.processed_data_save_path,
                visualization_params=self.visualization_params,
                log_sink=self.log_sink,
            )
        return self._orchestrator.run()

    # Alias for symmetry with old API if some code used run()
    def run(self):  # pragma: no cover - trivial delegator
        return self.process()

__all__ = ["LegacyStateMachineAdapter", "DEPRECATION_MESSAGE"]
