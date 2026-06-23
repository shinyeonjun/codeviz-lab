from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate


class _AlgorithmShowcaseTemplate(ExecutionVisualizationTemplate):
    visualization_mode = ""
    showcase_type = ""
    payload: dict

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        line_number = execution.steps[0].line_number if execution.steps else 1
        step_index = execution.steps[0].step_index if execution.steps else 1

        return ExecutionVisualizationRead(
            kind="algorithm-showcase",
            source_variable=self.showcase_type,
            step_states=[
                ExecutionVisualizationStepRead(
                    step_index=step_index,
                    line_number=line_number,
                    payload={
                        "showcaseType": self.showcase_type,
                        **self.payload,
                    },
                    message=None,
                )
            ],
            metadata={"templateMode": self.visualization_mode},
        )


class DijkstraShowcaseExecutionTemplate(_AlgorithmShowcaseTemplate):
    visualization_mode = "showcase-dijkstra"
    showcase_type = "dijkstra"
    payload = {
        "nodes": [
            {"id": "0", "x": 24, "y": 150, "source": True},
            {"id": "1", "x": 105, "y": 170},
            {"id": "2", "x": 95, "y": 92},
            {"id": "3", "x": 214, "y": 92},
            {"id": "4", "x": 148, "y": 24},
            {"id": "5", "x": 36, "y": 44},
        ],
        "edges": [
            {"from": "0", "to": "1", "weight": 7},
            {"from": "0", "to": "2", "weight": 9},
            {"from": "0", "to": "5", "weight": 14},
            {"from": "1", "to": "2", "weight": 10},
            {"from": "1", "to": "3", "weight": 15},
            {"from": "2", "to": "3", "weight": 11},
            {"from": "2", "to": "5", "weight": 2},
            {"from": "3", "to": "4", "weight": 6},
            {"from": "4", "to": "5", "weight": 9},
        ],
        "distances": ["0", "∞", "∞", "∞", "∞", "∞"],
        "stages": [
            {
                "title": "시작 노드 0",
                "description": "0번 노드의 거리를 0으로 두고 탐색을 시작합니다.",
                "distances": ["0", "∞", "∞", "∞", "∞", "∞"],
                "currentNodeId": "0",
                "settledNodeIds": ["0"],
                "activeEdgeIds": [],
                "updatedDistanceIndices": [0],
            },
            {
                "title": "0번에서 이웃 갱신",
                "description": "0번과 연결된 1, 2, 5번 노드의 거리를 갱신합니다.",
                "distances": ["0", "7", "9", "∞", "∞", "14"],
                "currentNodeId": "0",
                "settledNodeIds": ["0"],
                "activeEdgeIds": ["0-1", "0-2", "0-5"],
                "updatedDistanceIndices": [1, 2, 5],
            },
            {
                "title": "가장 가까운 1번 확정",
                "description": "아직 확정되지 않은 노드 중 거리가 가장 짧은 1번을 선택합니다.",
                "distances": ["0", "7", "9", "22", "∞", "14"],
                "currentNodeId": "1",
                "settledNodeIds": ["0", "1"],
                "activeEdgeIds": ["1-3"],
                "updatedDistanceIndices": [3],
            },
            {
                "title": "2번 확정 후 5번 단축",
                "description": "2번을 거쳐 5번으로 가는 경로가 더 짧아집니다.",
                "distances": ["0", "7", "9", "20", "∞", "11"],
                "currentNodeId": "2",
                "settledNodeIds": ["0", "1", "2"],
                "activeEdgeIds": ["2-3", "2-5"],
                "updatedDistanceIndices": [3, 5],
            },
            {
                "title": "5번 확정 후 4번 갱신",
                "description": "5번을 거쳐 4번까지의 최단 거리를 갱신합니다.",
                "distances": ["0", "7", "9", "20", "20", "11"],
                "currentNodeId": "5",
                "settledNodeIds": ["0", "1", "2", "5"],
                "activeEdgeIds": ["5-4"],
                "updatedDistanceIndices": [4],
            },
            {
                "title": "최단 거리 확정",
                "description": "남은 노드까지 확인하여 최단 거리 배열을 완성합니다.",
                "distances": ["0", "7", "9", "20", "20", "11"],
                "currentNodeId": "4",
                "settledNodeIds": ["0", "1", "2", "3", "4", "5"],
                "activeEdgeIds": ["3-4", "5-4"],
                "updatedDistanceIndices": [],
            },
        ],
    }

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        stages = self.payload["stages"]
        step_states: list[ExecutionVisualizationStepRead] = []
        for index, stage in enumerate(stages, start=1):
            line_number = execution.steps[index - 1].line_number if len(execution.steps) >= index else index
            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=index,
                    line_number=line_number,
                    payload={
                        "showcaseType": self.showcase_type,
                        **{key: value for key, value in self.payload.items() if key != "stages"},
                        **stage,
                    },
                    message=stage["description"],
                )
            )

        return ExecutionVisualizationRead(
            kind="algorithm-showcase",
            source_variable=self.showcase_type,
            step_states=step_states,
            metadata={"templateMode": self.visualization_mode},
        )


class MergeSortShowcaseExecutionTemplate(_AlgorithmShowcaseTemplate):
    visualization_mode = "showcase-merge-sort"
    showcase_type = "merge-sort"
    payload = {
        "values": [27, 10, 12, 20, 25, 13, 15, 22],
        "levels": [
            [{"values": [27, 10, 12, 20, 25, 13, 15, 22], "x": 320, "y": 30, "final": False}],
            [
                {"values": [27, 10, 12, 20], "x": 160, "y": 105, "final": False},
                {"values": [25, 13, 15, 22], "x": 480, "y": 105, "final": False},
            ],
            [
                {"values": [27, 10], "x": 95, "y": 180, "final": False},
                {"values": [12, 20], "x": 225, "y": 180, "final": False},
                {"values": [25, 13], "x": 415, "y": 180, "final": False},
                {"values": [15, 22], "x": 545, "y": 180, "final": False},
            ],
            [
                {"values": [27], "x": 70, "y": 255, "final": False},
                {"values": [10], "x": 140, "y": 255, "final": False},
                {"values": [12], "x": 205, "y": 255, "final": False},
                {"values": [20], "x": 275, "y": 255, "final": False},
                {"values": [25], "x": 390, "y": 255, "final": False},
                {"values": [13], "x": 460, "y": 255, "final": False},
                {"values": [15], "x": 525, "y": 255, "final": False},
                {"values": [22], "x": 595, "y": 255, "final": False},
            ],
            [
                {"values": [10, 27], "x": 105, "y": 330, "final": False},
                {"values": [12, 20], "x": 240, "y": 330, "final": False},
                {"values": [13, 25], "x": 425, "y": 330, "final": False},
                {"values": [15, 22], "x": 560, "y": 330, "final": False},
            ],
            [
                {"values": [10, 12, 20, 27], "x": 175, "y": 405, "final": False},
                {"values": [13, 15, 22, 25], "x": 495, "y": 405, "final": False},
            ],
            [{"values": [10, 12, 13, 15, 20, 22, 25, 27], "x": 320, "y": 480, "final": True}],
        ],
    }


class RadixSortShowcaseExecutionTemplate(_AlgorithmShowcaseTemplate):
    visualization_mode = "showcase-radix-sort"
    showcase_type = "radix-sort"
    payload = {
        "input": [8, 2, 7, 3, 5],
        "buckets": [
            [],
            [],
            [2],
            [3],
            [],
            [5],
            [],
            [7],
            [8],
            [],
        ],
        "output": [2, 3, 5, 7, 8],
    }
