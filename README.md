# Purpose Decomposer

A small, interactive command-line tool that helps specify, decompose and assess the **purposes (goals)** of an AI application.
It runs with a **local LLM** (through [Ollama](https://ollama.com/) and [LangChain](https://docs.langchain.com/oss/python/langchain/overview)), so no data leaves your machine.

> **Research context.** This code is the prototype accompanying a research paper submitted to the **2027 CAiSE conference**. It illustrates how a conceptual model of AI purpose can support the governance and regulation of general-purpose AI (GPAI), for example against the EU AI Act.

## What it does

Starting from a goal such as *"Scan CVs of applicants"*, the script guides you step by step:

1. **Specification.** The model suggests a more specific version of the goal. You accept it or type your own.
2. **AND-decomposition.** If the goal is made of parts that are all needed, it is split into one branch per part.
3. **OR-refinement.** For each branch you choose a *semantic function* the goal does not state yet (result, manner, recipient, location, ...). The model proposes alternatives and you select one. Repeat until you stop.
4. **Assessment** (optional). Each final goal, called an *intended-usage goal*, gets a **risk level** and a **design-goal status** (is it among the purposes declared for the application?). Values come from your input files, and the model suggests them when the files have no match.
5. **Your own version.** At the end, you can write your own version of the goal, given the goals identified. It is assessed like the others.

The code, not the model, drives the structure of the process. The model only answers narrow questions and returns JSON. The goal formalisation is based on N. Prat, *"Goal formalization and classification for requirements engineering, fifteen years later"*.

## Installation

Requirements: Python 3.9+ and [Ollama](https://ollama.com/download).

```bash
pip install langchain-ollama
ollama pull llama3.1
```

Make sure the Ollama server is running (it listens on `http://localhost:11434` by default). The model, server URL, temperature and other settings can be edited in the `CONFIG` block at the top of `goal_decomposer.py`. They can also be set with command-line options (`-m`, `--base-url`, `-t`).

## Input files

Both files are simple markdown lists.

**File A (`applications.md`, `--apps`)**: AI applications, their type, and their declared design goals (proper purposes), nested below.

```markdown
- Recruiting assistant | Decision support
  - Rank job candidates for recruiters
  - Summarize candidate CVs
```

**File B (`risks.md`, `--risks`)**: purposes and their risk level.

```markdown
- Recognize the emotions of employees | Unacceptable
```

Both files are optional. Without file A the design-goal status is suggested by the model. Without file B the assessment step is skipped.

## Usage

```bash
python purpose_decomposer.py "Detect tumours" \
  --ai-name "Radiology assistant" --ai-type "Computer vision" \
  --context "used in a public hospital" \
  --apps applications.md --risks risks.md --json out.json
```

| Option | Meaning |
|---|---|
| `goal` | Goal statement (asked interactively if omitted) |
| `--ai-name`, `--ai-type` | Application name (looked up in `--apps`) and type |
| `--context` | Free-text context (domain, users, constraints) |
| `--apps FILE`, `--risks FILE` | Files A and B |
| `-m`, `--base-url`, `-t` | Ollama model, server URL, temperature |
| `--json FILE` | Save the whole session as JSON |
| `-v` | Print raw model replies (debugging) |

At each prompt, **Enter** accepts the default, `s` stops refining a branch, and `0` keeps the current goal.

## Demonstration: scanning CVs of applicants

A borderline use case: an HR employee of a mid-sized EU company wants an LLM to scan CVs. Summarising CVs is a declared purpose of the application. Ranking candidates is also declared, but it is high-risk under the AI Act. Rejecting applicants automatically is not declared at all.

1. Save the following as `risks.md`. The levels are illustrative and loosely based on the AI Act, so check them before reusing them.

   ```markdown
   - Rank job candidates for recruiters | High
   - Reject job applicants automatically on the basis of their CVs | High
   - Filter job applicants according to their CVs | High
   - Summarize candidate CVs | Limited
   - Recognize the emotions of employees | Unacceptable
   - Answer customer questions about invoices | Minimal
   ```

2. Run:

   ```bash
   python goal_decomposer.py "Scan CVs of applicants" \
     --ai-name "Recruiting assistant" \
     --context "HR department of a mid-sized company in the EU" \
     --apps applications.md --risks risks.md --json demo.json
   ```

3. Follow the prompts:
   - Accept the suggested more specific goal (**Enter**).
   - If an AND-split is proposed, accept it.
   - Choose **`Res`** (expected result) and select the alternative producing a ranked shortlist. On another branch, select the one producing a summary.
   - Choose **`Man`** (manner) and select the *automatically* alternative. Then type **`s`** to stop.
   - Read the assessment: summarising is within the declared purposes and rated *Limited*. Ranking is declared but *High*.
   - At the last prompt, type `Reject applicants automatically on the basis of their CVs`. It is *High* risk and **not** a declared design goal, which is the borderline drift the demonstration is meant to show.

The alternatives are generated by the model, so wording can differ between models. With temperature 0 and a fixed seed, runs are reproducible for a given model.

## Files

| File | Description |
|---|---|
| `goal_decomposer.py` | The script (single file) |
| `applications.md` | Example file A with several AI applications |
| `purpose_model.mmd` | Conceptual model (Mermaid source) |

## Citation

If you use this code, please cite the paper once it is published. *(Reference to be added after the review process.)*

## License

*(To be added.)*
