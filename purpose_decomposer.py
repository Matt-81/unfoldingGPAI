#!/usr/bin/env python3
"""
purpose_decomposer.py - stepwise, user-guided decomposition of a goal of an AI application
(divide and conquer), ending with the intended-usage goals and, optionally, their risk level
and design-goal status.  Single file, local Ollama model through LangChain.

Theory (N. Prat, "Goal formalization and classification for requirements engineering, fifteen
years later"): a goal is a verb + parameters, each parameter has a semantic function (FUNCTIONS
below, most important first). Specifying a missing parameter is an OR-reduction; splitting a
conjunction or a noun group into its parts is an AND-reduction.

Flow (the code, not the model, drives the structure; the model only answers narrow questions)
  1. goal + context -> the model suggests a more specific goal (if needed); you accept or retype it
  2. the model checks whether the goal can be AND-decomposed (parts that are all needed):
       yes -> one branch per AND sub-goal (you may reject the split)      no -> a single branch
  3. each branch is refined independently:
       a. you choose a semantic function not yet present in the goal
          (Enter = the highest-ranked free one, s = stop: the goal is final)
       b. the model gives up to MAX_OPTIONS alternatives (OR) specifying that function
       c. you select ONE of them (0 = keep the current goal), then back to (a)
       until you stop or no free function is left
  4. the final goal of every branch = an intended-usage goal; with --risks (and --apps) each one
     gets its risk level and design-goal status (from the files, else suggested by the model)
  5. seeing these goals (and their assessment), you may type your own version of the goal
     (Enter = none); with --risks it is assessed like the others and saved under "user_goal" in the JSON

File A (--apps; markdown list "Name | Type", design goals nested below):
    - Radiology assistant | Computer vision
      - Detect tumours in CT scans
File B (--risks; markdown list "goal | risk level"):
    - Recognize the emotions of employees | Unacceptable

Setup:    pip install langchain-ollama      and      ollama pull llama3.1
Usage:    python goal_decomposer.py "Detect tumours" --ai-name "Radiology assistant" \
              --ai-type "Computer vision" --context "used in a public hospital" \
              --apps applications.md --risks risks.md --json out.json
"""
import argparse
import json
import re
import sys

from langchain_ollama import ChatOllama

# =============================== CONFIG (edit me) ===============================
MODEL = "llama3.1"                    # any model you have pulled in Ollama
BASE_URL = "http://localhost:11434"   # Ollama server
TEMPERATURE = 0                       # 0 + fixed seed = reproducible answers
SEED = 0
NUM_CTX = None                        # e.g. 8192 to enlarge the context window (useful for a long file B)
MAX_OPTIONS = 6                       # max sub-goals per reduction (AND parts and OR alternatives)
MIN_OPTIONS = 2                       # fewer distinct sub-goals than this -> reduction dropped
RETRIES = 2                           # extra attempts when the model returns unusable JSON
# ================================================================================

FUNCTIONS = [  # all semantic functions, most important first: (function, group, generic question, generic example)
    ("Obj", "Predicate arguments", "What does the goal act on?", "lung cancer"),
    ("Qual", "Predicate arguments", "Which quality is to be reached?", "high accuracy"),
    ("Res", "Predicate arguments", "Which result is expected?", "reduced time to detect tumours"),
    ("Rec", "Predicate arguments", "Who receives it?", "the radiologist"),
    ("Ref", "Predicate arguments", "Which reference is used?", "existing medical literature"),
    ("Ben", "Level-1 satellites", "Who benefits?", "patients"),
    ("Comp", "Level-1 satellites", "With whom (company)?", "a team of oncologists"),
    ("Mea", "Level-1 satellites", "By which means?", "deep learning on CT images"),
    ("Man", "Level-1 satellites", "In which manner?", "automatically, with human review"),
    ("Spe", "Level-1 satellites", "At which speed?", "in real time"),
    ("Deg", "Level-1 satellites", "To which degree?", "for all suspicious findings"),
    ("So", "Level-1 satellites", "From which source?", "the hospital image archive"),
    ("Dir", "Level-1 satellites", "In which direction?", "from screening to treatment"),
    ("Loc", "Level-2 satellites", "Where?", "in hospital emergency departments"),
    ("Time", "Level-2 satellites", "When?", "during night shifts"),
    ("Freq", "Level-2 satellites", "How often?", "for every scan"),
    ("Dur", "Level-2 satellites", "For how long?", "during the whole treatment"),
]
CODES = {f[0].lower(): f[0] for f in FUNCTIONS}   # case-insensitive lookup: "obj" -> "Obj"
INFO = {f[0]: f for f in FUNCTIONS}

# ----------------------------------- PROMPTS ------------------------------------
SEMANTICS = ("A goal is a VERB in the infinitive followed by PARAMETERS; every parameter has a SEMANTIC FUNCTION "
             "(codes, from MOST to LEAST important):\n"
             + "\n".join("  %s [%s]: %s" % (f, g, q) for f, g, q, _ in FUNCTIONS))
EXPERT = "You are an expert in requirements engineering for AI systems.\n" + SEMANTICS + "\n"
SENTENCE = ("A goal sentence is in English, starts with an infinitive verb (no leading \"To\", no final period), "
            "is atomic, has no negation and no pronouns.")

REFINE_SYSTEM = EXPERT + """
Task: make the goal more specific. If its verb leaves a predicate argument (Obj, Qual, Res, Rec, Ref) unspecified
or vague (generic or indefinite noun group; generic verbs such as support, improve, manage, assist are always
vague), return ONE more specific version of the goal in which EVERY predicate argument the verb needs is
instantiated with a concrete, plausible value for the given context (add satellites only when essential). Keep the
original intent. If the goal is already specific, return an empty string. """ + SENTENCE + """
Answer with ONE JSON object and nothing else: {"specific": "<goal sentence or empty string>"}"""

ANALYZE_SYSTEM = EXPERT + """
Task: analyse ONE goal exactly as written (never improve it, never add information).
1. "parameters": the parameters the goal literally states, each with its semantic function code and the EXACT words
   copied from the goal. The verb is not a parameter; a function the goal does not state is simply absent.
2. "parts": split the goal into AND sub-goals ONLY when ALL of them are needed to achieve it and together they are
   equivalent to it: either the goal is a conjunction of goals ("X and Y"), or one of its noun groups is a definite
   set made of constituent PARTS ("monitor heart rate and blood pressure"). Never split into kinds or alternatives
   (that is an OR) and never invent parts. Each part is a goal sentence identical to the goal except for that part,
   with its own "parameters". """ + SENTENCE + """ If the goal cannot be split, "parts" is an empty list.
Answer with ONE JSON object and nothing else:
{"parameters": [{"function": "<code>", "text": "<words copied from the goal>"}],
 "parts": [{"goal": "<goal sentence>", "parameters": [{"function": "<code>", "text": "<words copied from the part>"}]}]}"""

SPECIFY_SYSTEM = EXPERT + """
Task: OR-reduce the goal by specifying its semantic function %s (%s, e.g. "%s"), which it does not have yet.
Give %d-%d different, realistic alternative values suited to the context (the example only shows the kind of value;
adapt it). Achieving ANY ONE sub-goal achieves the parent. Each sub-goal = the parent goal unchanged + the value,
clearly different from its siblings. """ + SENTENCE + """
If the function cannot sensibly apply to this goal, return an empty list.
Answer with ONE JSON object and nothing else: {"subgoals": ["<goal sentence>", "<goal sentence>"]}"""

ASSESS_SYSTEM = """You are an expert in AI governance and risk assessment (for instance the EU AI Act).
You receive an intended-usage goal of an AI application, a risk catalogue (file B) and the design goals declared
for the application (file A). Two goals describe the same activity when verb and object agree, even if worded differently.
Answer with ONE JSON object and nothing else:
{"risk_match": <number of the catalogue entry describing the same activity, or null>,
 "risk_guess": "<one of the allowed risk levels; always required>",
 "design_match": <number of the declared design goal that covers this goal, or null; null if none are declared>,
 "design_guess": <true if this goal is plausibly a design goal of this kind of application, else false>,
 "reason": "<one sentence>"}"""
# ---------------------------------------------------------------------------------


# ------------------------------- files A and B -----------------------------------
BULLET = re.compile(r"^(\s*)[-*+]\s+(\S.*?)\s*$")


def bullets(path):
    """(line number, indent, text) of every markdown list item; other lines are ignored."""
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            m = BULLET.match(line.expandtabs(4))
            if m:
                yield n, len(m.group(1)), m.group(2)


def split_pair(text, path, n):
    left, sep, right = text.rpartition("|")
    if not sep or not left.strip() or not right.strip():
        raise ValueError("%s:%d: expected '<text> | <value>', got %r" % (path, n, text))
    return left.strip(), right.strip()


def load_applications(path):
    """File A -> {lowercase name: {"name", "type", "goals"}}; deeper bullets are design goals."""
    apps, base, current = {}, None, None
    for n, indent, text in bullets(path):
        base = indent if base is None else base
        if indent <= base:
            name, kind = split_pair(text, path, n)
            current = apps.setdefault(name.lower(), {"name": name, "type": kind, "goals": []})
        else:
            current["goals"].append(text)
    if not apps:
        raise ValueError("%s: no application found" % path)
    return apps


def load_risks(path):
    """File B -> [(goal, risk level)]."""
    risks = [split_pair(text, path, n) for n, _, text in bullets(path)]
    if not risks:
        raise ValueError("%s: no goal found" % path)
    return risks


# --------------------------------- model helpers ---------------------------------
def build_llm(model=MODEL, base_url=BASE_URL, temperature=TEMPERATURE, num_ctx=NUM_CTX):
    """ChatOllama; `format="json"` asks Ollama for JSON output, the fixed seed makes runs reproducible."""
    kwargs = {"model": model, "base_url": base_url, "temperature": temperature, "seed": SEED, "format": "json"}
    if num_ctx:
        kwargs["num_ctx"] = num_ctx
    return ChatOllama(**kwargs)


def parse_json(text):
    """First JSON object in a model reply (tolerates <think> blocks, code fences, chatter)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    text = re.sub(r"^.*?</think>", "", text, flags=re.S | re.I)
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                esc = (c == "\\") and not esc
                if c == '"' and not esc:
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    raise ValueError("no JSON object in model reply")


def ask_json(llm, system, human, verbose=False):
    """One model call -> dict (retries on unusable JSON)."""
    last = None
    for _ in range(RETRIES + 1):
        text = llm.invoke([("system", system), ("human", human)]).content
        if verbose:
            print("--- model reply ---\n%s\n-------------------" % text, file=sys.stderr)
        try:
            data = parse_json(text)
            if isinstance(data, dict):
                return data
            last = ValueError("reply is not a JSON object")
        except ValueError as e:
            last = e
    raise RuntimeError("model gave no usable JSON: %s" % last)


def norm(s):
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return " ".join(re.sub(r"^\s*to\s+", "", s).split())


def clean_goal(s):
    s = " ".join(str(s or "").split()).strip().rstrip(".;")
    if s.lower().startswith("to "):
        s = s[3:]
    return s[:1].upper() + s[1:]


def distinct_goals(items, exclude):
    """Model list (strings or {"goal": ...}) -> cleaned goals, distinct from `exclude` and from each other, max MAX_OPTIONS."""
    seen, out = {norm(exclude)}, []
    for s in items if isinstance(items, list) else []:
        s = clean_goal(s.get("goal", "") if isinstance(s, dict) else s)
        if s and len(s) < 400 and norm(s) not in seen and len(out) < MAX_OPTIONS:
            seen.add(norm(s))
            out.append(s)
    return out


def stated_functions(params, goal):
    """Model [{"function", "text"}] -> codes of the functions whose words really occur in `goal`.
    Grounding the labels in the goal's own text stops the model from echoing the suggested goal or the prompt."""
    text, found = " %s " % norm(goal), set()
    for p in params if isinstance(params, list) else []:
        code = CODES.get(str(p.get("function", "")).strip().lower()) if isinstance(p, dict) else None
        words = norm(str(p.get("text", ""))) if code else ""
        if words and " %s " % words in text:
            found.add(code)
    return found


def ranked(codes):
    """Codes in ranking order, as a readable string."""
    return ", ".join(f[0] for f in FUNCTIONS if f[0] in codes) or "none"


def to_index(value, size):
    """Model answer (1-based number, maybe a string or null) -> 0-based index or None."""
    try:
        i = int(value) - 1
    except (TypeError, ValueError):
        return None
    return i if 0 <= i < size else None


def describe(name, kind, extra):
    return "; ".join(x for x in (" - ".join(y for y in (name, kind) if y), extra) if x) or "not specified"


# ------------------------------- model tasks (steps 1-3) --------------------------
def suggest_specific(llm, goal, context, verbose=False):
    """Step 1: a more specific version of the goal, or '' if the goal is specific enough."""
    data = ask_json(llm, REFINE_SYSTEM, "Context: %s\nGoal: %s" % (context, goal), verbose)
    example = clean_goal(data.get("specific"))
    return "" if norm(example) == norm(goal) else example


def analyze(llm, goal, context, verbose=False):
    """Step 2: -> (functions stated in the goal, [(AND part, functions stated in it)] or [] if not AND-decomposable)."""
    data = ask_json(llm, ANALYZE_SYSTEM, "Context: %s\nGoal: %s" % (context, goal), verbose)
    raw = {clean_goal(p.get("goal")): p for p in data.get("parts", []) if isinstance(p, dict)} \
        if isinstance(data.get("parts"), list) else {}
    parts = [(g, stated_functions(raw[g].get("parameters"), g)) for g in distinct_goals(list(raw.values()), goal)]
    return stated_functions(data.get("parameters"), goal), (parts if len(parts) >= MIN_OPTIONS else [])


def specify(llm, goal, fn, context, verbose=False):
    """Step 3b: up to MAX_OPTIONS OR-alternatives of `goal` that specify function `fn` ([] if unusable)."""
    _, _, question, example = INFO[fn]
    system = SPECIFY_SYSTEM % (fn, question, example, MIN_OPTIONS, MAX_OPTIONS)
    data = ask_json(llm, system, "Context: %s\nGoal: %s" % (context, goal), verbose)
    options = distinct_goals(data.get("subgoals"), goal)
    return options if len(options) >= MIN_OPTIONS else []


# ------------------------------ user interaction (step 3) -------------------------
def ask_function(free):
    """Step 3a: the user's choice among the free functions. Enter = highest ranked, s = stop (None)."""
    print("  Free functions: %s" % ", ".join(free))
    while True:
        answer = input("  Function to specify [Enter = %s (%s), s = stop]: " % (free[0], INFO[free[0]][2])).strip().lower()
        if not answer:
            return free[0]
        if answer in ("s", "stop"):
            return None
        if CODES.get(answer) in free:
            return CODES[answer]
        print("    choose one of the free functions listed above")


def pick(options):
    """Step 3c: the user selects ONE alternative; 0 keeps the current goal (None)."""
    for i, option in enumerate(options, 1):
        print("    %d. %s" % (i, option))
    while True:
        try:
            i = int(input("  Select a goal (1-%d, 0 = keep the current goal): " % len(options)))
            if 0 <= i <= len(options):
                return options[i - 1] if i else None
        except ValueError:
            pass
        print("    enter a number between 0 and %d" % len(options))


def refine_branch(llm, goal, used, context, verbose=False):
    """Step 3: divide and conquer on ONE branch. Returns (final goal, steps).
    Loop: function -> OR-alternatives -> one selected -> next function, until the user stops or none is free.
    `used` holds the functions already present in the goal; each function is consumed once it has been offered."""
    steps = []
    while True:
        free = [f[0] for f in FUNCTIONS if f[0] not in used]
        if not free:
            print("  (all semantic functions are specified)")
            return goal, steps
        fn = ask_function(free)
        if fn is None:
            return goal, steps
        used.add(fn)
        options = specify(llm, goal, fn, context, verbose)
        if not options:
            print("  no usable alternatives for %s, choose another function" % fn)
            continue
        chosen = pick(options)
        steps.append({"function": fn, "alternatives": options, "selected": chosen})
        if chosen:
            goal = chosen
            print("  -> %s" % goal)


# --------------------------- step 4: risk level and design goal ------------------------
def assess(llm, goal, context, app, risks, verbose=False):
    """Risk level from file B, design-goal status from file A; anything missing is suggested by the model."""
    levels = list(dict.fromkeys(level for _, level in risks))
    known = bool(app and app["goals"])  # are the design goals of this application declared?
    human = "AI application: %s\nIntended-usage goal: %s\n\nRisk catalogue (goal | risk level):\n%s\nAllowed risk levels: %s\n\n" \
            "Declared design goals of the application:\n%s" % (
                context, goal,
                "\n".join("%d. %s | %s" % (i, g, lvl) for i, (g, lvl) in enumerate(risks, 1)), ", ".join(levels),
                "\n".join("%d. %s" % (i, g) for i, g in enumerate(app["goals"], 1)) if known
                else "(none: the application is not described in file A)")
    data = ask_json(llm, ASSESS_SYSTEM, human, verbose)

    r = to_index(data.get("risk_match"), len(risks))
    if r is not None:
        risk, risk_src = risks[r][1], 'file B: "%s"' % risks[r][0]
    else:
        risk = {l.lower(): l for l in levels}.get(str(data.get("risk_guess", "")).strip().lower(), "unknown")
        risk_src = "suggested"

    if known:
        d = to_index(data.get("design_match"), len(app["goals"]))
        design = "yes" if d is not None else "no"
        design_src = 'file A: "%s"' % app["goals"][d] if d is not None else "not declared in file A"
    else:
        design = "yes" if str(data.get("design_guess")).strip().lower() in ("true", "yes") else "no"
        design_src = "suggested"
    return {"goal": goal, "risk": risk, "risk_source": risk_src, "design_goal": design,
            "design_source": design_src, "reason": str(data.get("reason", "")).strip()}


def show_assessment(results):
    for r in results:
        print("\n(%d) %s" % (r["n"], r["goal"]))
        if "error" in r:
            print("    ! %s" % r["error"])
            continue
        print("    risk level : %-12s [%s]" % (r["risk"], r["risk_source"]))
        print("    design goal: %-12s [%s]" % (r["design_goal"], r["design_source"]))
        if r["reason"] and "suggested" in (r["risk_source"], r["design_source"]):
            print("    why        : %s" % r["reason"])


# ------------------------------------- CLI ---------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="Stepwise decomposition and risk assessment of goals of an AI application (Ollama + LangChain).")
    ap.add_argument("goal", nargs="*", help="goal statement (asked interactively if omitted)")
    ap.add_argument("--ai-name", default="", help="name of the AI application (looked up in --apps)")
    ap.add_argument("--ai-type", default="", help="type of the AI application (default: the one in --apps)")
    ap.add_argument("--context", default="", help="free-text context (domain, users, constraints...)")
    ap.add_argument("--apps", metavar="FILE", help="file A: AI applications, types and design goals (.md)")
    ap.add_argument("--risks", metavar="FILE", help="file B: goals and risk levels (.md); enables the final assessment")
    ap.add_argument("-m", "--model", default=MODEL)
    ap.add_argument("--base-url", default=BASE_URL)
    ap.add_argument("-t", "--temperature", type=float, default=TEMPERATURE)
    ap.add_argument("--json", metavar="FILE", help="also save everything as JSON")
    ap.add_argument("-v", "--verbose", action="store_true", help="print raw model replies to stderr")
    args = ap.parse_args(argv)

    try:
        apps = load_applications(args.apps) if args.apps else {}
        risks = load_risks(args.risks) if args.risks else []
    except (OSError, ValueError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    app = apps.get(args.ai_name.strip().lower())
    name = app["name"] if app else args.ai_name.strip()
    kind = args.ai_type.strip() or (app["type"] if app else "")

    user_goal = None  # the user's own version of the goal (step 5)

    try:
        # 0. input: goal and context
        goal = " ".join(args.goal).strip()
        if not goal:
            if app and app["goals"]:
                print("Declared design goals of %s:\n%s\n" % (name, "\n".join("  - " + g for g in app["goals"])))
            goal = input("Goal: ").strip()
        if not goal:
            print("no goal given", file=sys.stderr)
            return 2
        goal = clean_goal(goal)
        extra = args.context.strip()
        if not (name or kind or extra):
            extra = input("AI application / context (Enter to skip): ").strip()
        context = describe(name, kind, extra)
        llm = build_llm(args.model, args.base_url, args.temperature)

        # 1. suggest a more specific goal; Enter accepts it, anything typed replaces it
        specific, suggestion = goal, suggest_specific(llm, goal, context, args.verbose)
        if suggestion:
            print("\nMore specific goal suggested:\n  %s" % suggestion)
            specific = clean_goal(input("Goal to use [Enter = accept, or type your own]: ")) or suggestion
        else:
            print("\nThe goal is already specific enough.")

        # 2. AND decomposition: one branch per part, otherwise a single branch (the goal itself)
        present, parts = analyze(llm, specific, context, args.verbose)
        branches = [(specific, present)]
        if parts:
            print("\nThe goal can be AND-decomposed (all parts are needed):")
            for i, (g, _) in enumerate(parts, 1):
                print("  %d. %s" % (i, g))
            if input("Use this decomposition? [Y/n]: ").strip().lower() != "n":
                branches = parts

        # 3. refine every branch independently until the user stops (divide and conquer)
        results = []
        for i, (start, used) in enumerate(branches, 1):
            print("\n=== Branch %d/%d: %s\n  already specified: %s" % (i, len(branches), start, ranked(used)))
            final, steps = refine_branch(llm, start, set(used), context, args.verbose)
            results.append({"n": i, "branch": start, "steps": steps, "goal": final})

        print("\nIntended-usage goals:")
        for r in results:
            print("  (%d) %s" % (r["n"], r["goal"]))

        # 4. risk level and design-goal status of every final goal (only with --risks)
        if risks:
            for r in results:
                try:
                    r.update(assess(llm, r["goal"], context, app, risks, args.verbose))
                except Exception as e:  # keep going with the other goals
                    r["error"] = str(e)
            show_assessment(results)

        # 5. the user may write her own version of the goal, given the identified goals (assessed like the others)
        own = clean_goal(input("\nYour own version of the goal, given the goals above [Enter = none]: "))
        if own:
            user_goal = {"n": len(results) + 1, "branch": None, "steps": [], "goal": own, "user_defined": True}
            if risks:
                try:
                    user_goal.update(assess(llm, own, context, app, risks, args.verbose))
                except Exception as e:
                    user_goal["error"] = str(e)
                show_assessment([user_goal])
            else:
                print("\nYour goal:\n  (%d) %s" % (user_goal["n"], own))
    except (EOFError, KeyboardInterrupt):
        print("\naborted", file=sys.stderr)
        return 130
    except Exception as e:  # e.g. Ollama not running / model missing
        print("error: %s" % e, file=sys.stderr)
        return 1

    if args.json:
        out = {"application": {"name": name, "type": kind}, "context": context, "input_goal": goal,
               "specific_goal": specific, "and_decomposed": len(branches) > 1,
               "branches": results, "user_goal": user_goal}
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        print("\nsaved %s" % args.json, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())