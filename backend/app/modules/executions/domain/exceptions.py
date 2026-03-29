class ExecutionNotFoundError(Exception):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"실행 결과를 찾을 수 없습니다: {run_id}")
        self.run_id = run_id


class ExecutionInputLimitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
