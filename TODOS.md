# Implementation Todo List - All Goals

## Phase 1: Unified Extension System (High Priority)

- E1.1: Create `simple_agent/extensions/` framework structure
  - Files: `__init__.py`, `base.py`, `loader.py`, `registry.py`, `manager.py`
  - Tests: `test_extension_loader.py`, `test_extension_registry.py`, `test_runtime_extensions.py`
  - Status: **In Progress**

- E1.2: Implement plugin loading mechanism (YAML/Python file support)
- E1.3: Implement extension registration system with tag-based discovery
- E1.4: Add runtime extension API (load/unload at runtime)
- E1.5: Add extension examples and documentation

## Phase 2: IT/Software Development Optimization (High Priority)

- IT1.1: Git Workflows Integration (worktree, branch, merge strategies)
- IT1.2: CI/CD Integration (GitHub Actions, GitLab CI, Jenkins)
- IT1.3: Testing Framework (pytest, unittest, coverage reporting)
- IT1.4: Code Quality Tools (lint, format, security scanner)
- IT1.5: Add IT tests (`test_git_workflow.py`, `test_ci_cd_integration.py`, `test_code_quality.py`)

## Phase 3: Financial Domain Optimization (Medium Priority)

- F1.1: Financial Data Integration (Yahoo Finance, Alpha Vantage, local cache)
- F1.2: Quantitative Finance Strategies (technical analysis, backtesting)
- F1.3: Risk Management (VaR, stress testing, scenario analysis)
- F1.4: Add Financial tests (`test_finance_data.py`, `test_quant_strategies.py`, `test_risk_management.py`)

## Phase 4: Security Domain Optimization (Medium Priority)

- S1.1: Security Scanning (static analysis, dependency check)
- S1.2: OWASP Integration (top 10 checks, vulnerability patterns)
- S1.3: Vulnerability DB (NVD, CVSS scoring)
- S1.4: Add Security tests (`test_security_scanning.py`, `test_vulnerability_check.py`)

## Phase 5: Runtime Dynamic Extension (Low Priority)

- R1.1: Dynamic Tool Registration (add tools at runtime)
- R1.2: Dynamic Strategy Switching (change策略 without restart)
- R1.3: Hot-plug Agent (add/remove agents during execution)
- R1.4: Add Runtime tests (`test_runtime_tools.py`, `test_dynamic_strategies.py`)

## Phase 6: Documentation & Examples (Medium Priority)

- D1.1: Extension System Guide
- D1.2: Vertical Scenarios Guide (IT, Finance, Security)
- D1.3: Examples (plugin templates, domain adapters)
- D1.4: API Documentation

## High Priority Tasks

- #7: Fix CLI Agent to use StrategyRouter
- #8: Modify EnhancedAgent to support StrategyRouter

---

## Current Status

- Tasks created: 14
- Completed: 1 (test import fixes)
- In Progress: E1.1 (Extension System Framework)

## Next Actions

1. Start with E1.1 - Create extension system framework
2. Implement base Extension class
3. Add loader and registry
4. Add tests for each component
