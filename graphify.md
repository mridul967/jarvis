# Graphify Workflow Guide for Jarvis

`graphify` is an AST and knowledge-graph engine built specifically for AI coding agents and complex codebases. Instead of relying on blind `grep` searches or dumping thousands of tokens of raw code into an LLM context window, it builds a complete symbol and dependency graph (call flows, imports, types, and architecture relationships).

Here is how you can use it to immediately improve your workflow in **Jarvis**:

---

### 1. Direct Antigravity IDE Integration (Biggest Win)
Notice the command in the help output:
```bash
graphify antigravity install
```
Because this workspace is running inside **Google Antigravity**, running this command automatically registers `graphify` rules, workflows, and skills into your `.agents/` directory. 
* **The Benefit:** When you ask the agent to refactor code, debug an algorithm, or trace a function, the agent will query the graph first to see all callers and dependencies across both the backend and frontend. This directly prevents issues like the one you had earlier (where moving `backend/core` broke 25+ files because callers weren't known up front).

---

### 2. Generate a Local AST Knowledge Graph (Zero API Cost)
You can index your entire repository locally using tree-sitter without spending any API tokens:
```bash
graphify extract . --code-only
```
* **The Benefit:** It scans your Python files (FastAPI, PyTorch GAT models, QPSO/QACO scripts) and TypeScript/Next.js frontend into a unified graph (`graphify-out/graph.json`). It maps which UI components call which API endpoints, and which backend routers call which optimizer algorithms.

---

### 3. Generate Interactive Architecture & Call-Flow Visualizations (For SIH Deliverables)
Your problem statement for SIH 2026 (Deliverables 1, 4, & 5) requires demonstrating graph-based network modeling and architecture clarity. You can export interactive visualizations of your codebase instantly:

* **Interactive D3 Hierarchy Tree:**
  ```bash
  graphify tree --output graphify-out/ARCHITECTURE_TREE.html
  ```
* **Mermaid Architecture & Call-Flow HTML:**
  ```bash
  graphify export callflow-html --output graphify-out/CALLFLOW.html
  ```
* **Interactive Graph Explorer:**
  ```bash
  graphify export html
  ```
Opening these HTML files in a browser gives you an interactive map of how your data flows from the Next.js UI -> FastAPI routers -> GAT / QPSO / QACO engines -> SQLite/NetworkX.

---

### 4. Safe Refactoring & Impact Analysis
Whenever you are about to modify a core algorithm (like changing `qrg_update`, modifying GAT attention dimensions, or refactoring the routing contract):
* You can check exactly which files and functions depend on that symbol before touching any code.
* It eliminates guesswork when decoupling research scripts (`research/converted/...`) into clean backend modules.

---

### 5. Automated Updates via Git Hooks
To ensure the graph doesn't go stale as you write code:
```bash
graphify hook install
```
This adds a lightweight post-commit hook that incrementally updates the dependency graph whenever you commit changes.

---

### Recommended 3-Step Setup to Run in Terminal:
1. **Connect to Antigravity:**
   ```bash
   graphify antigravity install
   ```
2. **Build the local codebase index:**
   ```bash
   graphify extract . --code-only
   ```
3. **Generate the interactive architecture map:**
   ```bash
   graphify tree
   ```
