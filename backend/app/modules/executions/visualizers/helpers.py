from app.modules.executions.visualizations.shared.array_sequences import build_array_visualization
from app.modules.executions.visualizations.shared.structure_extractors import (
    TrackStats as SequenceTrackStats,
)
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_numeric_sequence_map,
    is_numeric,
    resolve_active_indices,
    resolve_matched_indices,
    select_primary_name as resolve_primary_name,
)


def select_primary_sequence_name(execution):
    return resolve_primary_name(
        execution,
        extractor=build_numeric_sequence_map,
        size_of=len,
    )
