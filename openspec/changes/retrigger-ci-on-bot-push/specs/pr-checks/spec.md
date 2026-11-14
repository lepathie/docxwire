# Spec Delta

## Purpose

Ensures every pull request to `main` has its CI check runs (lint, test, check-specs, check-deps, PR title lint) reported in the PR's checks view for the PR's head commit, including after the PR Orchestrator pushes an auto-fix to the PR branch, so the checks a maintainer sees are the complete, current CI result and required-checks gating works.

## ADDED Requirements

### Requirement: CI checks are visible in the PR checks view
For every non-fork pull request targeting `main`, the system SHALL report the CI check runs for the PR's head commit in the PR's checks view, such that the view reflects the complete CI result (lint, test, check-specs, check-deps, and PR title lint) for that head commit.

#### Scenario: PR without an auto-fix
- **WHEN** a non-fork PR is opened against `main` and the orchestrator determines no fix is needed
- **THEN** the CI pipeline is re-triggered on the PR branch
- **AND** the CI check runs for the PR head are visible in the PR's checks view

#### Scenario: PR after an auto-fix push
- **WHEN** the orchestrator pushes an auto-fix to the PR branch and the resulting `synchronize` event starts a new orchestrator run for the new head commit
- **THEN** that run re-triggers the CI pipeline on the PR branch
- **AND** the CI check runs for the new head commit are visible in the PR's checks view

### Requirement: Exactly one CI re-trigger per PR head
The system SHALL re-trigger the CI pipeline exactly once per PR head commit, and SHALL perform the re-trigger in the last orchestrator run for that head commit.

#### Scenario: Run that pushed a fix does not re-trigger
- **WHEN** an orchestrator run pushes an auto-fix to the PR branch
- **THEN** that run does not re-trigger the CI pipeline
- **AND** the re-trigger for the new head commit is performed by the orchestrator run triggered by that push

#### Scenario: Run for the bot's fix push re-triggers
- **WHEN** an orchestrator run is started by the bot's own fix push on a non-fork PR
- **THEN** the run re-triggers the CI pipeline on the PR branch

#### Scenario: In-sync run re-triggers
- **WHEN** an orchestrator run applies no fix
- **THEN** the run re-triggers the CI pipeline on the PR branch

### Requirement: Fix-loop guard
The system SHALL NOT commit or push any auto-fix in an orchestrator run triggered by the bot's own fix push, preventing an infinite push loop.

#### Scenario: Bot push run applies no fix
- **WHEN** an orchestrator run's triggering actor is the bot account used for fix pushes
- **THEN** the run commits and pushes no auto-fix

### Requirement: Fork PRs are excluded
The system SHALL NOT apply auto-fixes or re-trigger the CI pipeline for pull requests from forks, whose tokens lack the required write permissions.

#### Scenario: Fork PR
- **WHEN** a PR from a fork is opened, synchronized, or reopened against `main`
- **THEN** no auto-fix is pushed and no CI re-trigger is performed for that PR
