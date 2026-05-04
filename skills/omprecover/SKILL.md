---
id: omprecover
name: recover
version: 1.0.0
description: Recover project state from snapshot to prevent progress loss
stages: [A1, A2, A3, A4, A5, A6, A7, A8, B9, B10, B11, B12, B13, B14, B15, C16, C17, C18, C19, C20, C21, C22, C23]
tools: [read_file, Bash, AskUserQuestion]
tracker: reads snapshots directory; writes to recovered files and recovery_log.md
---

# omp:recover - Snapshot Recovery

Use this skill to recover project state from a snapshot.

## Invocation

```
/omp:recover
```

## Stages

- All stages: A1 through C23

## Tasks

1. Check if snapshots exist
2. List all snapshots
3. Show snapshot list and let user choose
4. Read selected snapshot details
5. Show recovery preview with warnings
6. (Optional) Show diff between snapshot and current files
7. Execute recovery
8. Create recovery log entry

### Snapshot Creation Triggers

Snapshots are automatically created at:
- Before stage transitions (`on-stage-transition` hook)
- Before task completion (`on-task-complete` hook)
- Before key commands (`/omp:write`, `/omp:plan`, etc.)

## Snapshot Info Display

| Field | Description |
|-------|-------------|
| `file` | Filename |
| `timestamp` | Creation time |
| `stage` | Stage at snapshot time |
| `tasks_summary` | Task completion |
| `label` | Snapshot label |

## User Confirmation Flow

1. **Select snapshot** — AskUserQuestion with numbered list
2. **Preview recovery** — Show files to restore + warning
3. **Confirm or view diff** — AskUserQuestion

Options:
- `确认恢复` — Execute recovery
- `查看差异` — Show detailed diff
- `取消` — Cancel recovery

## Tracker Integration

### 读
- `.pipeline/memory/snapshots/` — Snapshot directory

### 写
- `.pipeline/{relPath}` — Recovered files
- `.pipeline/memory/recovery_log.md` — Recovery record appended

## Error Handling

| Error | Handling |
|-------|----------|
| No snapshots | Show message explaining when snapshots are created |
| Corrupted snapshot | Skip and ask user to select another |
| Missing file in snapshot | Skip that file, keep current |
| Write failure | Show error, partial recovery may have occurred |

## Constraints

- MUST use AskUserQuestion for all confirmation steps
- Warn user about overwriting current files
- Never proceed without explicit user confirmation
