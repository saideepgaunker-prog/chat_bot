# Agent Orchestration & Multi-Agent Coordination

## Overview
The Developer Control Tower employs autonomous AI agents that operate across repositories. The Orchestrator manages agent schedules, triggers, and collaboration.

## Location & Route
Navigate to: **Control Tower > Agents > Orchestration Config** (`/agents/orchestration/config`).
*Required Permission:* `maintainer`.

## Active Agents
- **Code Reviewer Agent**: Analyzes ASTs, identifies security anti-patterns, checks style guidelines, and posts inline review comments on Pull Requests.
- **CI/CD Orchestrator Agent**: Monitors build matrices, analyzes test failure logs, and suggests automated fixes for flaky tests.
- **Security Scanner Agent**: Conducts continuous SAST and dependency audits, flagging vulnerabilities and secret leaks.
- **Release Summarizer Agent**: Aggregates merged PRs into formatted release notes and semver suggestions.

## Configuration Options
- **Trigger Strategy**: `On-Commit`, `On-PR-Open`, or `Cron-Nightly`.
- **Concurrency Limit**: Max simultaneous agent workers per tenant (Default: 8).
- **Auto-Fix PR Generation**: Allows agents to open draft PRs with proposed code fixes.
