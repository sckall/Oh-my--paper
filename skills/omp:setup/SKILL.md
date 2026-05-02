---
id: omp:setup
name: omp:setup
version: 1.0.0
description: A1 TOPIC_INIT - Initialize research project with topic, venue, and goals
stages: [A1]
tools: [read_file, write_file, Bash]
---

# omp:setup - Project Initialization

Use this skill to initialize a new research project.

## Invocation

```
/omp:setup
```

## Stage

A1 - TOPIC_INIT

## Tasks

1. Create `.pipeline/` directory structure
2. Generate `project_truth.md` with research topic
3. Create `research_brief.json` with venue and goals
4. Initialize task tracking in `tasks.json`
