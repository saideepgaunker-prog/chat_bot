# Code Health & Technical Debt Metrics

## Overview
Code Health metrics quantify maintainability, complexity, test efficacy, and architectural debt across your repositories.

## Location & Route
Navigate to: **Repositories > [Your Repo] > Metrics > Code Health** (`/repos/:repoId/metrics/health`).
*Required Permission:* `developer`.

## Key Metrics Explained
- **Health Score (0-100)**: Composite index based on test coverage (40%), cyclomatic complexity (30%), code duplication (15%), and security posture (15%).
- **Maintainability Index**: Ranks codebase clean architecture from Grade A (Clean) to Grade F (Refactor Urgently).
- **Test Coverage**: Line and branch coverage percentage. Standard target is > 85%.
- **Technical Debt Ratio**: Estimated engineering hours needed to resolve high-complexity bottlenecks and debt items.
