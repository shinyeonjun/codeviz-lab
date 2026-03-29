from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)


def build_call_stack_visualization(execution: ExecutionRead) -> ExecutionVisualizationRead | None:
    if not execution.steps:
        return None

    stack: list[str] = []
    step_states: list[ExecutionVisualizationStepRead] = []
    observed_functions = {step.function_name for step in execution.steps}
    if len(observed_functions) <= 1:
        return None

    for step in execution.steps:
        if step.call_stack:
            frames = [
                {
                    "depth": depth,
                    "functionName": frame.function_name,
                    "isActive": depth == len(step.call_stack) - 1,
                    "lineNumber": frame.line_number,
                }
                for depth, frame in enumerate(step.call_stack)
            ]
            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    payload={
                        "frames": frames,
                        "activeFunction": step.call_stack[-1].function_name,
                        "eventType": step.event_type,
                        "frameCount": len(frames),
                        "activeDepth": len(frames) - 1 if frames else None,
                    },
                    message=f"{step.call_stack[-1].function_name} ?꾨젅?꾩쓣 異붿쟻?⑸땲??",
                )
            )
            continue

        function_name = step.function_name

        if step.event_type == "line":
            if not stack:
                stack.append(function_name)
            elif stack[-1] == function_name:
                pass
            elif function_name in stack:
                stack = stack[: stack.index(function_name) + 1]
            else:
                stack.append(function_name)
        else:
            if not stack or stack[-1] != function_name:
                if function_name in stack:
                    stack = stack[: stack.index(function_name) + 1]
                else:
                    stack.append(function_name)

        frames = [
            {
                "depth": depth,
                "functionName": name,
                "isActive": depth == len(stack) - 1,
            }
            for depth, name in enumerate(stack)
        ]
        step_states.append(
            ExecutionVisualizationStepRead(
                step_index=step.step_index,
                line_number=step.line_number,
                payload={
                    "frames": frames,
                    "activeFunction": function_name,
                    "eventType": step.event_type,
                    "frameCount": len(frames),
                    "activeDepth": len(frames) - 1 if frames else None,
                },
                message=f"{function_name} 프레임을 추적합니다.",
            )
        )

        if step.event_type in {"return", "exception"} and stack and stack[-1] == function_name:
            stack.pop()

    return ExecutionVisualizationRead(
        kind="call-stack",
        source_variable=None,
        step_states=step_states,
        metadata={"frameCount": max((len(state.payload["frames"]) for state in step_states), default=0)},
    )
