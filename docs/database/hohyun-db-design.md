# hohyun DB 설계

이 문서는 CodeViz 현재 구현 DB와 다음 단계에서 DB로 옮기는 것이 좋은 학습/시험 데이터를 함께 정리한 설계안이다.

## 현재 실제 구현된 테이블

현재 SQLAlchemy 모델과 Alembic 기준으로 실제 DB에 존재하는 핵심 테이블은 다음 5개다.

| 테이블 | 역할 | 핵심 관계 |
| --- | --- | --- |
| `users` | 로그인 사용자 | `auth_sessions`, `execution_runs`, `exam_attempts`의 기준 |
| `auth_sessions` | 세션 토큰 저장 | `users.id`를 `CASCADE`로 참조 |
| `execution_runs` | 코드 실행 1회 기록 | `users.id`를 nullable `SET NULL`로 참조 |
| `execution_steps` | trace 단계별 스냅샷 | `execution_runs.id`를 `CASCADE`로 참조 |
| `exam_attempts` | 시험 제출/채점 결과 | `users.id`를 nullable `SET NULL`로 참조 |

## DB로 옮기는 것이 좋은 확장 영역

현재 학습 카테고리와 lesson은 JSON 카탈로그에 있고, 시험 문제도 lesson의 exercise를 기반으로 런타임 생성된다. 운영/관리 화면까지 생각하면 아래 테이블로 분리하는 편이 낫다.

| 영역 | 권장 테이블 |
| --- | --- |
| 학습 카탈로그 | `learning_categories`, `learning_lessons`, `lesson_contents` |
| 실습/자동채점 | `lesson_exercises`, `exercise_test_cases` |
| 시각화 템플릿 | `visualization_templates` |
| 사용자 진도 | `lesson_progress` |
| 시험 세션 | `exam_sessions`, `exam_session_questions` |
| 오답/케이스 결과 | `exam_case_results` |

## 설계 원칙

- 학습 콘텐츠는 `learning_lessons`를 중심으로 잡고, 긴 본문과 예제 코드는 `lesson_contents`로 분리한다.
- 자동채점은 `lesson_exercises`와 `exercise_test_cases`로 분리해서 문제 수정과 테스트케이스 추가를 쉽게 한다.
- 실행 trace는 데이터 양이 커질 수 있으므로 `execution_runs`와 `execution_steps`를 분리한다.
- 시험은 랜덤 출제 흐름을 복원할 수 있게 `exam_sessions`와 `exam_session_questions`를 별도로 둔다.
- `exam_attempts`는 현재 구현과 호환되게 유지하되, 다음 단계에서 `session_question_id`를 nullable FK로 추가하는 방식이 안전하다.
- 시각화 템플릿은 코드 렌더러 자체를 DB에 넣지 않고, 템플릿 ID/지원 언어/필요 trace feature 같은 메타데이터만 저장한다.

## 관계 요약

- `users` 1:N `auth_sessions`
- `users` 1:N `execution_runs`
- `users` 1:N `exam_attempts`
- `users` 1:N `lesson_progress`
- `execution_runs` 1:N `execution_steps`
- `learning_categories` 1:N `learning_lessons`
- `learning_lessons` 1:1 `lesson_contents`
- `learning_lessons` 1:0..1 `lesson_exercises`
- `lesson_exercises` 1:N `exercise_test_cases`
- `exam_sessions` 1:N `exam_session_questions`
- `exam_session_questions` 1:N `exam_attempts`
- `exam_attempts` 1:N `exam_case_results`

## Miro 반영 메모

보드 제목은 `hohyun DB 설계`로 두고, 다이어그램은 네 영역으로 배치한다.

1. 인증/사용자: `users`, `auth_sessions`, `lesson_progress`
2. 학습 카탈로그: `learning_categories`, `learning_lessons`, `lesson_contents`, `lesson_exercises`, `exercise_test_cases`
3. 실행/Trace: `execution_runs`, `execution_steps`, `visualization_templates`
4. 시험/피드백: `exam_sessions`, `exam_session_questions`, `exam_attempts`, `exam_case_results`

Miro MCP로 최종 ERD를 생성했다.

- 최종본: `https://miro.com/app/board/uXjVGojeCfM=/?moveToWidget=3458764672338137698`
- 제목: `hohyun DB Design ERD`
- 구성: 15개 테이블, 17개 관계

## Miro API 자동 반영

보드 편집 권한과 `boards:write` scope가 있는 Miro access token이 있으면 아래 스크립트로 shape/connector를 직접 생성할 수 있다.

```powershell
$env:MIRO_ACCESS_TOKEN = "<Miro access token>"
.\docs\database\push-hohyun-db-design-to-miro.ps1
```

미리 생성될 payload만 확인하려면 다음처럼 실행한다.

```powershell
.\docs\database\push-hohyun-db-design-to-miro.ps1 -DryRun
```
