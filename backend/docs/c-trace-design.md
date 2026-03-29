# C 언어 trace 설계안

## 배경

현재 플랫폼은 Python에 대해 `sys.settrace` 기반 줄 단위 trace를 제공한다.

C 언어는 인터프리터가 아니라 컴파일된 바이너리로 실행되기 때문에, Python처럼 런타임에서 바로 줄 단위 후킹을 할 수 없다. 따라서 C trace는 `컴파일 단계`와 `디버거 단계`를 별도로 설계해야 한다.

## 왜 Python 방식이 C에 그대로 안 되는가

- Python: 인터프리터가 각 줄 실행 이벤트를 노출한다.
- C: `gcc/clang`가 소스 코드를 바이너리로 바꾼 뒤 실행한다.
- 따라서 C는 실행 전에 디버그 심볼을 넣고, 실행 중에는 `gdb` 같은 디버거로 현재 줄/스택/변수를 읽어야 한다.

## 공식 근거

- GCC는 `-g`로 디버그 정보를 생성하고, `-fvar-tracking`, `-fvar-tracking-assignments`로 변수 위치 추적 품질을 높일 수 있다.
- GDB/MI는 자동화용 인터페이스를 제공하고, `-exec-next`, `-stack-list-locals`, `-data-evaluate-expression` 같은 명령으로 스텝/로컬 변수/식 평가를 할 수 있다.

참고:
- GCC Debugging Options: https://gcc.gnu.org/onlinedocs/gcc-14.1.0/gcc/Debugging-Options.html
- GDB/MI File Commands: https://sourceware.org/gdb/current/onlinedocs/gdb.html/GDB_002fMI-File-Commands.html
- GDB 공식 문서 PDF: https://sourceware.org/gdb/download/onlinedocs/gdb.pdf

## 목표

### 1차 목표

- C 코드를 안전하게 컴파일/실행한다.
- 컴파일 에러와 런타임 에러를 보여준다.
- trace가 없는 경우에도 실행 결과와 stdout/stderr를 제공한다.

### 2차 목표

- 단일 스레드, 단일 소스 파일 기준 줄 단위 trace를 수집한다.
- 현재 함수명, 현재 줄 번호, 지역 변수 값을 step 형태로 저장한다.
- Python `steps[]`와 최대한 비슷한 응답으로 맞춘다.

### 3차 목표

- 배열/포인터/구조체를 더 잘 읽어서 시각화 품질을 높인다.
- 스택 프레임, 재귀, 포인터 이동을 보조 데이터로 제공한다.

## 추천 아키텍처

```text
executions/
  infrastructure/
    runners/
      languages/
        python/
        c/
          local_runner.py
          docker_runner.py
          c_execute_runner.py
          c_trace_runner.py
          gdb_mi_client.py
          parsers/
            gdb_mi_parser.py
            c_value_parser.py
```

## 권장 구현 전략

### 단계 1. 현재 구조 유지

현재 구현:

- `c_execute_runner.py`
- `LocalCExecutionRunner`
- `DockerCExecutionRunner`

이 단계는 유지한다. C를 완전히 trace하기 전까지는 `실행 + 컴파일 에러 확인`이 fallback 역할을 해야 한다.

### 단계 2. GDB 기반 trace 추가

새 파일:

- `c_trace_runner.py`
- `gdb_mi_client.py`

컴파일 방식:

```text
gcc -std=c11 -O0 -g -fvar-tracking -fvar-tracking-assignments main.c -o main.out
```

이유:

- `-O0`: 최적화를 끄면 source line과 변수 위치가 덜 뒤틀린다.
- `-g`: 디버그 심볼 생성
- `-fvar-tracking`, `-fvar-tracking-assignments`: GDB가 변수 상태를 더 잘 복원할 수 있게 도움

### 단계 3. GDB/MI 제어 흐름

권장 방식은 일반 CLI 출력 파싱보다 `GDB/MI`를 쓰는 것이다.

예상 흐름:

1. `gdb --interpreter=mi2 ./main.out` 실행
2. `-file-exec-and-symbols ./main.out`
3. `-break-insert main`
4. `-exec-run`
5. 프로그램이 멈출 때마다
   - 현재 위치 확인
   - `-stack-list-frames`
   - `-stack-list-locals 1`
   - 필요 시 `-data-evaluate-expression 변수명`
6. `-exec-next` 또는 `-exec-step`
7. 종료 시까지 반복

## step 데이터 매핑

목표 응답은 Python과 최대한 맞춘다.

```json
{
  "line_number": 12,
  "event_type": "line",
  "function_name": "main",
  "locals_snapshot": {
    "i": 2,
    "sum": 10
  },
  "stdout_snapshot": "",
  "error_message": null
}
```

### 필드별 수집 방법

- `line_number`
  - GDB stop event의 `frame.line`
- `function_name`
  - GDB stop event의 `frame.func`
- `locals_snapshot`
  - `-stack-list-locals 1`
  - 값이 안 나오는 경우 `-data-evaluate-expression`
- `stdout_snapshot`
  - subprocess stdout 누적 버퍼
- `error_message`
  - signal, crash, compile failure, gdb 에러 메시지

## 범위 제한이 꼭 필요한 이유

C trace는 케이스가 많아서 처음부터 다 받으면 망한다.

1차 지원 범위는 아래로 제한하는 게 맞다.

- 단일 C 파일
- `main` 함수 시작
- 단일 스레드
- 표준 라이브러리 위주
- 지역 변수 중심
- 기본 scalar와 1차원 배열 일부만

처음부터 제외할 것:

- 멀티 파일 프로젝트
- pthread
- 매크로 복잡한 코드
- 구조체 포인터 깊은 중첩
- 함수 포인터
- 동적 라이브러리 디버깅

## 자료구조/시각화와의 연결

### 1차

- C trace 결과도 기존 `steps[]` 형식으로 저장
- 시각화 선택은 일단 `none`, `array-bars`, `array-cells` 정도로 제한

### 2차

- `locals_snapshot`에서 배열/인덱스 패턴을 추출
- 현재 Python 시각화 추출기와 최대한 공용화

### 3차

- 포인터 이동
- 메모리 주소
- 구조체 필드
- call stack

## 추천 구현 우선순위

### Phase A

- 현재 C 실행기 안정화
- 언어 선택 UI 연결
- C는 `visualizationMode=none` 허용

### Phase B

- `c_trace_runner.py`
- `gdb_mi_client.py`
- `main`, `for`, `while`, `if`가 있는 단순 예제에서 줄 단위 trace

### Phase C

- `locals_snapshot` 품질 개선
- 배열 추출
- `array-bars`, `array-cells` 연결

### Phase D

- 함수 호출과 재귀
- call stack 시각화
- 포인터/구조체 고도화

## 왜 GDB를 우선 추천하는가

대안도 있다.

### 1. 소스 코드 계측

- C 코드를 파싱해서 줄마다 `printf`를 삽입
- 구현은 쉬워 보이지만 안정성이 낮다.
- 전처리기, 매크로, 문자열, 중첩 블록에서 쉽게 깨진다.

### 2. clang AST 기반 계측

- 더 정확하지만 구현량이 많다.
- 교육용 플랫폼 MVP에는 무겁다.

### 3. GDB/MI

- 이미 검증된 디버거를 쓴다.
- 공식 인터페이스가 있다.
- 줄/함수/스택/지역 변수 정보를 비교적 일관되게 얻을 수 있다.

따라서 현재 프로젝트에는 `GDB/MI`가 가장 현실적이다.

## 지금 당장 코드로 바꿔야 할 것

### 바로 해도 되는 것

- `languages/c` 구조 유지
- `c_trace_runner.py` 골격 추가
- `gdb_mi_client.py` 골격 추가
- 설정 추가
  - `RUNNER_C_TRACE_ENABLED`
  - `RUNNER_DOCKER_C_TRACE_IMAGE`

### 아직 미루는 게 맞는 것

- C용 AI 템플릿 자동 선택 고도화
- 구조체/포인터 전용 시각화
- Java 동시 추가

## 최종 판단

- C trace는 가능하다.
- 하지만 Python처럼 쉽게 되진 않는다.
- 현재 프로젝트에서는 `GDB/MI 기반 점진 도입`이 가장 현실적이다.
- 순서는 `실행 -> 줄 단위 trace -> 변수 품질 -> 시각화 고도화`로 가야 한다.
