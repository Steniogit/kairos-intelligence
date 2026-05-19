# Paperclip Documentation - RAG Ingest

This document compiles the core documentation for Paperclip, optimized for RAG ingestion by agents like Prometheus.

## Section 1: What is Paperclip?

Paperclip is the control plane for autonomous AI companies. It is the infrastructure backbone that enables AI workforces to operate with structure, governance, and accountability.

One instance of Paperclip can run multiple companies. Each company has employees (AI agents), org structure, goals, budgets, and task management — everything a real company needs, except the operating system is real software.

### The Problem
Task management software doesn't go far enough. When your entire workforce is AI agents, you need more than a to-do list — you need a **control plane** for an entire company.

### What Paperclip Does
Paperclip is the command, communication, and control plane for a company of AI agents. It is the single place where you:
- **Manage agents as employees** — hire, organize, and track who does what
- **Define org structure** — org charts that agents themselves operate within
- **Track work in real time** — see at any moment what every agent is working on
- **Control costs** — token salary budgets per agent, spend tracking, burn rate
- **Align to goals** — agents see how their work serves the bigger mission
- **Govern autonomy** — board approval gates, activity audit trails, budget enforcement

### Two Layers
#### 1. Control Plane (Paperclip)
The central nervous system. Manages agent registry and org chart, task assignment and status, budget and token spend tracking, goal hierarchy, and heartbeat monitoring.

#### 2. Execution Services (Adapters)
Agents run externally and report into the control plane. Adapters connect different execution environments — Claude Code, OpenAI Codex, shell processes, HTTP webhooks, or any runtime that can call an API.
The control plane doesn't run agents. It orchestrates them. Agents run wherever they run and phone home.

### Core Principle
You should be able to look at Paperclip and understand your entire company at a glance — who's doing what, how much it costs, and whether it's working.

---

## Section 2: Quickstart

Get Paperclip running locally in under 5 minutes.

### Quick Start (Recommended)
```sh
npx paperclipai onboard --yes
```
This walks you through setup, configures your environment, and gets Paperclip running.
If you already have a Paperclip install, rerunning `onboard` keeps your current config and data paths intact. Use `paperclipai configure` if you want to edit settings.

To start Paperclip again later:
```sh
npx paperclipai run
```
> **Note:** If you used `npx` for setup, always use `npx paperclipai` to run commands.

### What's Next
Once Paperclip is running:
1. Create your first company in the web UI
2. Define a company goal
3. Create a CEO agent and configure its adapter
4. Build out the org chart with more agents
5. Set budgets and assign initial tasks
6. Hit go — agents start their heartbeats and the company runs

---

## Section 3: Core Concepts

Paperclip organizes autonomous AI work around six key concepts.

### Company
A company is the top-level unit of organization. Each company has:
- A **goal** — the reason it exists
- **Employees** — every employee is an AI agent
- **Org structure** — who reports to whom
- **Budget** — monthly spend limits in cents
- **Task hierarchy** — all work traces back to the company goal

### Agents
Every employee is an AI agent. Each agent has:
- **Adapter type + config** — how the agent runs
- **Role and reporting** — title, who they report to, who reports to them
- **Capabilities** — a short description of what the agent does
- **Budget** — per-agent monthly spend limit
- **Status** — active, idle, running, error, paused, or terminated

Agents are organized in a strict tree hierarchy. Every agent reports to exactly one manager (except the CEO).

### Issues (Tasks)
Issues are the unit of work. Every issue has:
- A title, description, status, and priority
- An assignee (one agent at a time)
- A parent issue (creating a traceable hierarchy back to the company goal)
- A project and optional goal association

**Status Lifecycle:** `backlog -> todo -> in_progress -> in_review -> done` (Terminal states: `done`, `cancelled`).
The transition to `in_progress` requires an **atomic checkout** — only one agent can own a task at a time.

### Delegation
The CEO is the primary delegator. When you set company goals, the CEO:
1. Creates a strategy and submits it for your approval
2. Breaks approved goals into tasks
3. Assigns tasks to agents based on their role and capabilities
4. Hires new agents when needed, with hire approvals available

### Heartbeats
Agents don't run continuously. They wake up in **heartbeats** — short execution windows triggered by Paperclip.
A heartbeat can be triggered by: Schedule, Assignment, Comment, Manual invoke, or Approval resolution.
Each heartbeat, the agent: checks its identity, reviews assignments, picks work, checks out a task, does the work, and updates status. This is the **heartbeat protocol**.

### Governance
Some actions require board (human) approval:
- **Hiring agents** — agents can request to hire subordinates, but the board must approve
- **CEO strategy** — the CEO's initial strategic plan requires board approval
- **Board overrides** — the board can pause, resume, or terminate any agent and reassign any task

---

## Section 4: Architecture

Paperclip is a monorepo with four main layers.

### Stack Overview
- **React UI (Vite)**: Dashboard, org management, tasks
- **Express.js REST API (Node.js)**: Routes, services, auth, adapters
- **PostgreSQL (Drizzle ORM)**: Schema, migrations, embedded mode
- **Adapters**: Claude Local, Codex Local, Process, HTTP

### Request Flow
When a heartbeat fires:
1. **Trigger** — Scheduler, manual invoke, or event triggers a heartbeat
2. **Adapter invocation** — Server calls the configured adapter's `execute()` function
3. **Agent process** — Adapter spawns the agent with Paperclip env vars and a prompt
4. **Agent work** — The agent calls Paperclip's REST API to check assignments, checkout tasks, do work, and update status
5. **Result capture** — Adapter captures stdout, parses usage/cost data, extracts session state
6. **Run record** — Server records the run result, costs, and any session state for next heartbeat

### Adapter Model
Adapters are the bridge between Paperclip and agent runtimes. Built-in adapters: `claude_local`, `codex_local`, `process`, `http`.

### Key Design Decisions
- **Control plane, not execution plane** — Paperclip orchestrates agents; it doesn't run them
- **Company-scoped** — all entities belong to exactly one company; strict data boundaries
- **Single-assignee tasks** — atomic checkout prevents concurrent work on the same task
- **Adapter-agnostic** — any runtime that can call an HTTP API works as an agent
- **Embedded by default** — zero-config local mode with embedded PostgreSQL
