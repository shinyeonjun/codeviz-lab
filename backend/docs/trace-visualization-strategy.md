# Trace 기반 시각화 전략

CodeViz의 시각화는 언어별 디버거 결과를 공통 Trace IR로 모은 뒤, 프론트엔드 템플릿은 언어와 무관하게 같은 구조를 읽는 방식으로 간다.

## 언어별 trace 수집

| 언어 | 방식 | 수집 데이터 | 비고 |
| --- | --- | --- | --- |
| Python | `sys.settrace` | line, locals, globals, stdout, call stack | CPython에서 디버거/프로파일러 구현용으로 제공되는 tracing hook 사용 |
| C | GDB + Python API | line breakpoint, locals, globals, stdout, backtrace | `-g -O0` 컴파일 후 내부 breakpoint에서 snapshot 생성 |
| Java | JDB | line breakpoint, locals, 배열 dump, call stack | JPDA 계열 디버거를 사용하고, JDB가 없으면 실행 결과만 fallback |

## 공통 IR

모든 runner는 아래 정보를 `TraceExecutionResult`로 반환한다.

- `line_number`
- `event_type`
- `function_name`
- `locals_snapshot`
- `globals_snapshot`
- `stdout_snapshot`
- `call_stack`
- `metadata`

프론트엔드 시각화 템플릿은 Python/C/Java 원본 문법을 직접 보지 않고 이 IR만 사용한다. 그래서 `array-bars`, `dp-table`, `graph-node-edge`, `call-stack` 같은 템플릿을 언어별로 다시 만들지 않아도 된다.

## 템플릿 선택 순서

`visualizationMode: auto`일 때는 다음 순서로 결정한다.

1. 실행 결과에 trace step이 없으면 `none`
2. trace snapshot에서 자료구조를 감지해 템플릿 선택
3. trace만으로 모호하면 기존 source-code selector로 fallback
4. OpenAI selector는 이후 정밀한 tie-breaker나 설명 생성용으로 확장

현재 trace selector가 감지하는 주요 구조는 다음과 같다.

- 숫자 배열: `array-bars`
- 일반 배열/문자열: `array-cells`
- `left`/`right` 포인터: `palindrome-pointers`
- 2차원 DP/거리 테이블: `dp-table`
- graph/adj/visited/queue 기반 탐색: `graph-bfs-traversal` 또는 `graph-node-edge`
- graph/stack/재귀 기반 탐색: `graph-dfs-traversal` 또는 `graph-node-edge`
- stack/top/push/pop: `stack-vertical`
- queue/front/rear: `queue-horizontal`
- call stack 깊이 2 이상 또는 재귀: `call-stack`

## 참고한 공식 문서

- Python `sys.settrace`: https://docs.python.org/3/library/sys.html#sys.settrace
- GDB Python breakpoint API: https://sourceware.org/gdb/current/onlinedocs/gdb.html/Breakpoints-In-Python.html
- GDB debugging manual: https://sourceware.org/gdb/current/onlinedocs/gdb
- Java JPDA: https://docs.oracle.com/en/java/javase/24/docs/specs/jpda/jpda.html
- Java JPDA 구조 개요: https://docs.oracle.com/en/java/javase/17/docs/specs/jpda/architecture.html
