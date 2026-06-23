param(
    [string]$BoardId = "uXjVGojeCfM=",
    [string]$AccessToken = $env:MIRO_ACCESS_TOKEN,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Usage:
#   $env:MIRO_ACCESS_TOKEN = "<Miro access token with boards:write scope>"
#   .\docs\database\push-hohyun-db-design-to-miro.ps1
#
# Dry run:
#   .\docs\database\push-hohyun-db-design-to-miro.ps1 -DryRun

$tables = @(
    @{
        Key = "users"; Status = "current"; X = -1120; Y = -520; Width = 300; Height = 180
        Fields = @("id PK", "email UK", "password_hash", "name", "created_at")
    },
    @{
        Key = "auth_sessions"; Status = "current"; X = -1120; Y = -260; Width = 300; Height = 150
        Fields = @("id PK", "token_hash UK", "user_id FK", "created_at", "expires_at")
    },
    @{
        Key = "lesson_progress"; Status = "planned"; X = -1120; Y = 0; Width = 300; Height = 170
        Fields = @("id PK", "user_id FK", "lesson_id FK", "status", "best_score", "completed_at")
    },
    @{
        Key = "learning_categories"; Status = "planned"; X = -520; Y = -540; Width = 330; Height = 145
        Fields = @("id PK", "name", "description", "sort_order", "is_active")
    },
    @{
        Key = "learning_lessons"; Status = "planned"; X = -520; Y = -270; Width = 330; Height = 220
        Fields = @("id PK", "category_id FK", "visualization_template_id FK", "title", "language", "difficulty", "tags")
    },
    @{
        Key = "lesson_contents"; Status = "planned"; X = -520; Y = 30; Width = 330; Height = 160
        Fields = @("lesson_id PK/FK", "summary", "concept_points JSON", "walkthrough_code")
    },
    @{
        Key = "lesson_exercises"; Status = "planned"; X = -520; Y = 280; Width = 330; Height = 170
        Fields = @("id PK", "lesson_id FK", "prompt", "starter_code", "function_name", "checkpoints JSON")
    },
    @{
        Key = "exercise_test_cases"; Status = "planned"; X = -520; Y = 520; Width = 330; Height = 140
        Fields = @("id PK", "exercise_id FK", "case_order", "input JSON", "expected JSON", "is_hidden")
    },
    @{
        Key = "visualization_templates"; Status = "planned"; X = 120; Y = -520; Width = 330; Height = 170
        Fields = @("id PK", "base_mode", "display_name", "supported_languages JSON", "required_trace_features JSON", "is_active")
    },
    @{
        Key = "execution_runs"; Status = "current"; X = 120; Y = -240; Width = 330; Height = 220
        Fields = @("id PK", "user_id FK nullable", "lesson_id FK planned", "language", "visualization_mode", "status", "source_code", "step_count")
    },
    @{
        Key = "execution_steps"; Status = "current"; X = 120; Y = 70; Width = 330; Height = 230
        Fields = @("id PK", "run_id FK", "step_index", "line_number", "function_name", "locals_snapshot JSON", "globals_snapshot JSON", "call_stack JSON")
    },
    @{
        Key = "exam_sessions"; Status = "planned"; X = 760; Y = -520; Width = 330; Height = 170
        Fields = @("id PK", "user_id FK", "category_id FK", "question_count", "status", "started_at", "completed_at")
    },
    @{
        Key = "exam_session_questions"; Status = "planned"; X = 760; Y = -260; Width = 330; Height = 150
        Fields = @("id PK", "session_id FK", "lesson_id FK", "question_order")
    },
    @{
        Key = "exam_attempts"; Status = "current"; X = 760; Y = 0; Width = 330; Height = 210
        Fields = @("id PK", "user_id FK nullable", "session_question_id FK planned", "lesson_id", "question_id", "source_code", "status", "score", "result_payload JSON")
    },
    @{
        Key = "exam_case_results"; Status = "planned"; X = 760; Y = 300; Width = 330; Height = 160
        Fields = @("id PK", "attempt_id FK", "case_id", "passed", "expected JSON", "actual JSON", "message")
    }
)

$relations = @(
    @{ From = "users"; To = "auth_sessions"; Label = "owns" },
    @{ From = "users"; To = "execution_runs"; Label = "runs" },
    @{ From = "users"; To = "exam_attempts"; Label = "submits" },
    @{ From = "users"; To = "lesson_progress"; Label = "tracks" },
    @{ From = "execution_runs"; To = "execution_steps"; Label = "records" },
    @{ From = "visualization_templates"; To = "execution_runs"; Label = "selected_by_ai" },
    @{ From = "learning_categories"; To = "learning_lessons"; Label = "groups" },
    @{ From = "visualization_templates"; To = "learning_lessons"; Label = "default_template" },
    @{ From = "learning_lessons"; To = "lesson_contents"; Label = "has" },
    @{ From = "learning_lessons"; To = "lesson_exercises"; Label = "has" },
    @{ From = "lesson_exercises"; To = "exercise_test_cases"; Label = "checks" },
    @{ From = "learning_lessons"; To = "lesson_progress"; Label = "completed_by" },
    @{ From = "learning_lessons"; To = "execution_runs"; Label = "practice_run" },
    @{ From = "exam_sessions"; To = "exam_session_questions"; Label = "contains" },
    @{ From = "learning_lessons"; To = "exam_session_questions"; Label = "asked_as" },
    @{ From = "exam_session_questions"; To = "exam_attempts"; Label = "answered_by" },
    @{ From = "exam_attempts"; To = "exam_case_results"; Label = "case_results" }
)

function ConvertTo-HtmlLine {
    param([string]$Value)
    return [System.Net.WebUtility]::HtmlEncode($Value)
}

function New-TableContent {
    param(
        [string]$Name,
        [string]$Status,
        [string[]]$Fields
    )
    $statusText = if ($Status -eq "current") { "CURRENT" } else { "PLANNED" }
    $fieldText = ($Fields | ForEach-Object { ConvertTo-HtmlLine $_ }) -join "<br/>"
    return "<p><strong>$(ConvertTo-HtmlLine $Name)</strong></p><p><em>$statusText</em></p><p>$fieldText</p>"
}

function New-ShapePayload {
    param([hashtable]$Table)

    $isCurrent = $Table.Status -eq "current"
    $fillColor = if ($isCurrent) { "#EFF6FF" } else { "#F8FAFC" }
    $borderColor = if ($isCurrent) { "#2563EB" } else { "#94A3B8" }

    return @{
        data = @{
            shape = "round_rectangle"
            content = New-TableContent -Name $Table.Key -Status $Table.Status -Fields $Table.Fields
        }
        style = @{
            fillColor = $fillColor
            fillOpacity = "1.0"
            borderColor = $borderColor
            borderOpacity = "1.0"
            borderWidth = if ($isCurrent) { "2.0" } else { "1.5" }
            color = "#0F172A"
            fontFamily = "arial"
            fontSize = "14"
            textAlign = "left"
            textAlignVertical = "top"
        }
        position = @{
            origin = "center"
            x = $Table.X
            y = $Table.Y
        }
        geometry = @{
            width = $Table.Width
            height = $Table.Height
        }
    }
}

function New-ConnectorPayload {
    param(
        [string]$StartItemId,
        [string]$EndItemId,
        [string]$Label
    )

    return @{
        startItem = @{
            id = $StartItemId
            snapTo = "auto"
        }
        endItem = @{
            id = $EndItemId
            snapTo = "auto"
        }
        shape = "straight"
        captions = @(
            @{
                content = $Label
                position = "50%"
            }
        )
        style = @{
            strokeColor = "#64748B"
            strokeWidth = "1.5"
        }
    }
}

$preview = @{
    boardId = $BoardId
    shapes = $tables | ForEach-Object { New-ShapePayload -Table $_ }
    relations = $relations
}

if ($DryRun) {
    $preview | ConvertTo-Json -Depth 12
    exit 0
}

if ([string]::IsNullOrWhiteSpace($AccessToken)) {
    throw "Set MIRO_ACCESS_TOKEN or pass -AccessToken before writing to Miro."
}

$encodedBoardId = [uri]::EscapeDataString($BoardId)
$apiRoot = "https://api.miro.com/v2/boards/$encodedBoardId"
$headers = @{
    Accept = "application/json"
    Authorization = "Bearer $AccessToken"
    "Content-Type" = "application/json"
}

$itemIds = @{}

foreach ($table in $tables) {
    $payload = New-ShapePayload -Table $table
    $body = $payload | ConvertTo-Json -Depth 12
    $response = Invoke-RestMethod -Method Post -Uri "$apiRoot/shapes" -Headers $headers -Body $body
    $itemIds[$table.Key] = $response.id
    Write-Host "shape created: $($table.Key) -> $($response.id)"
}

foreach ($relation in $relations) {
    if (-not $itemIds.ContainsKey($relation.From) -or -not $itemIds.ContainsKey($relation.To)) {
        Write-Warning "connector skipped: $($relation.From) -> $($relation.To)"
        continue
    }

    $payload = New-ConnectorPayload `
        -StartItemId $itemIds[$relation.From] `
        -EndItemId $itemIds[$relation.To] `
        -Label $relation.Label
    $body = $payload | ConvertTo-Json -Depth 12
    $response = Invoke-RestMethod -Method Post -Uri "$apiRoot/connectors" -Headers $headers -Body $body
    Write-Host "connector created: $($relation.From) -> $($relation.To) -> $($response.id)"
}

Write-Host "hohyun DB design has been pushed to Miro."
