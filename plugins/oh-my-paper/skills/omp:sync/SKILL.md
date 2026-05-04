---
id: omp:sync
name: omp:sync
version: 1.0.0
description: Sync Status - Synchronize project state documents
stages: []
tools: [read_file, write_file, Bash]
---

# omp:sync - Sync Status

Use this skill to sync project state.

## Invocation

```
/omp:sync
```

## Tasks

1. Read all state files
2. Reconcile with actual progress
3. Update project_truth.md
4. Update orchestrator_state.md
5. Update execution_context.md
