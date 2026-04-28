# AGENTS.md

## Project overview
WorkoutAgent is an LLM-powered application for workout planning, coaching, and related agent workflows.
Primary goals:
- correctness
- reliable structured outputs
- low hallucination rate
- predictable prompt behavior
- reasonable token efficiency

## Tech stack
- Language: [Python/TypeScript/etc.]
- Main framework(s): [list]
- LLM/provider(s): [list]
- Key entrypoints:
  - [example: src/agent.py]
  - [example: src/prompts/]
  - [example: src/tools/]

## Working rules
- Prefer minimal, targeted changes over broad refactors.
- Do not scan or rewrite unrelated files unless necessary.
- Preserve existing public interfaces unless a change is required.
- When changing prompts or agent logic, explain expected impact on accuracy, latency, and token use.
- When uncertain, inspect code first and state assumptions clearly.

## Review priorities
When reviewing this codebase, focus on:
1. bugs and correctness issues
2. prompt quality and instruction conflicts
3. structured output reliability
4. tool-calling robustness
5. token/performance inefficiencies
6. opportunities to reduce hallucinations

## Prompt/LLM guidelines
- Prefer explicit schemas and deterministic output formats where possible.
- Flag prompts that are vague, conflicting, too long, or redundant.
- Flag unnecessary context that may hurt accuracy or token usage.
- Check for missing validation, retries, fallbacks, and guardrails.
- Check for prompt injection risks if external/user content is passed into prompts.

## Code change guidelines
- Show diffs or minimal edits when possible.
- Avoid rewriting whole files for small fixes.
- Keep business logic separate from prompt text where practical.
- Add or update tests when modifying core behavior.

## Validation
Before finishing, try to:
- run relevant tests only
- run lint/type checks only if relevant
- avoid expensive full-repo commands unless needed

## High-risk areas
Pay extra attention to:
- prompt assembly
- message history handling
- retrieval/context injection
- tool invocation and parsing
- JSON/schema validation
- fallback behavior on model failure
- memory/state management

## Scope guardrails
To reduce unnecessary token usage:
- Do not analyze the entire repository unless explicitly asked.
- Start with the smallest relevant set of files.
- For reviews, prioritize likely hot paths first.
- Prefer patch-style recommendations over full rewrites.

## Architecture notes
[Briefly explain your agent flow here:
user input -> planner/prompt builder -> LLM call -> tool execution -> validation -> final response]

## MCP/A2A guidance
When evaluating MCP or A2A:
- first identify existing tool boundaries
- then identify separable agent roles
- prefer minimal integration over full architectural rewrite
- call out blockers clearly