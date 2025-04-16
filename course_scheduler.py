# course_scheduler.py  – catalog‑agnostic, mode‑aware
"""Generic 4‑Year Scheduler (SQI‑aware + greedy optimiser)

Call
-----
    schedule, sem_credits, df = build_plan(
        catalog_csv=Path(".../my_major.csv"),
        ap_scores={"Calculus BC":5, "Chemistry":4},
        min_cr=12,
        max_cr=17,
        mode="avg"        # or "var" for variance flattening
    )

Returned values
---------------
* **schedule**     list[list[internal_course_id]]
* **sem_credits**  list[int] total credits per term
* **df**            pretty DataFrame ready for Streamlit

The module rebuilds all lookup dicts every time you load a new catalog,
so one import works for any major.
"""
from __future__ import annotations

import pandas as pd
import networkx as nx
import re
from pathlib import Path
from typing import Dict, List, Tuple
from copy import deepcopy

# Constants
DATA_DIR = Path("4_Year_input_Data")
AP_CREDIT_CSV = "4_Year_input_Data/rutgers_ap_credits.csv"
COURSE_RE = re.compile(r"(\d{3}:[0-9xX]{3})", re.IGNORECASE)

DEFAULT_MIN_CR = 12
DEFAULT_MAX_CR = 18
ELECTIVE_START_SEM = 0
SPRINKLE_LAST = 2
NO_MIN_FLOOR_AFTER = 6

# Global variables
cat: pd.DataFrame | None = None
credits_of: Dict[str, int] = {}
sqi_of: Dict[str, float] = {}
display_of: Dict[str, str] = {}
offered_of: Dict[str, str] = {}
prereq_of: Dict[str, str] = {}

# Load Data

def _norm(code: str) -> str:
    m = COURSE_RE.search(str(code))
    return m.group(1).upper() if m else str(code).strip().upper()


def load_catalog(csv_path: Path) -> None:
    """Load a catalog CSV and rebuild global lookup dicts."""
    global cat, credits_of, sqi_of, display_of, offered_of, prereq_of

    raw = pd.read_csv(csv_path, dtype=str).fillna("")
    rows, seen = [], {}
    for _, r in raw.iterrows():
        disp = r["Course Code"].strip().upper()
        if not disp:
            continue
        seen[disp] = seen.get(disp, 0) + 1
        internal = disp if seen[disp] == 1 else f"{disp}#{seen[disp]}"
        cr_match = re.search(r"(\d+)", r["Credits"])
        credits = int(cr_match.group(1)) if cr_match else None
        try:
            sqi = float(r.get("SQI", "").strip()) if r.get("SQI", "").strip() else 3.0
        except ValueError:
            sqi = 3.0
        rows.append({
            "Int": internal,
            "Disp": disp,
            "Name": r.get("Course Name", "").strip(),
            "Credits": credits,
            "Prereq": r.get("Prerequisites", ""),
            "Offered": r.get("Semester Offered", "").lower(),
            "SQI": sqi,
        })

    cat = pd.DataFrame(rows).set_index("Int")
    credits_of = cat["Credits"].to_dict()
    sqi_of = cat["SQI"].to_dict()
    display_of = cat["Disp"].to_dict()
    offered_of = cat["Offered"].to_dict()
    prereq_of = cat["Prereq"].to_dict()

# AP Credit Handler Functions
ap_df = pd.read_csv("./"+AP_CREDIT_CSV, dtype=str)
ap_df["Score"] = pd.to_numeric(ap_df["Score"], errors="coerce")

def ap_fulfilled(ap_scores: Dict[str, int]) -> set[str]:
    done: set[str] = set()
    for exam, sc in ap_scores.items():
        rows = ap_df[(ap_df["AP Exam"].str.lower() == exam.lower()) & (ap_df["Score"] <= sc)]
        for _, row in rows.iterrows():
            for course in str(row["Rutgers Course(s) Granted"]).split("&"):
                done.add(_norm(course))
    return done

# Prerequisite Graph Builder

def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    for code in cat.index:
        G.add_node(code)
        for token in re.split(r",| and | or |;", prereq_of[code]):
            p_disp = _norm(token)
            for ic, d in display_of.items():
                if d == p_disp:
                    G.add_edge(ic, code)
    return G

# Base Schedule Builder

def _baseline(ap_scores: Dict[str, int], min_cr: int, max_cr: int,
              semesters: int = 8):
    fulfilled_disp = ap_fulfilled(ap_scores)
    G = build_graph()

    core, elect = [], []
    for c in nx.topological_sort(G):
        if display_of[c] in fulfilled_disp or credits_of[c] is None:
            continue
        (elect if "ELECTIVE" in cat.loc[c, "Name"].upper() else core).append(c)
    core.sort(key=lambda x: sqi_of[x], reverse=True)
    elect.sort(key=lambda x: sqi_of[x], reverse=True)

    sched: List[List[str]] = [[] for _ in range(semesters)]
    sem_cr = [0] * semesters
    completed_disp = set(fulfilled_disp)

    def met(code, comp):
        return all(display_of[p] in comp for p in G.predecessors(code))

    def offered(code, season):
        return offered_of.get(code, "") in ("", "nan") or season in offered_of[code]

    for sem in range(semesters):
        season = "fall" if sem % 2 == 0 else "spring"
        comp = completed_disp.copy()
        for c in core[:]:
            if met(c, comp) and offered(c, season) and sem_cr[sem] + credits_of[c] <= max_cr:
                sched[sem].append(c); sem_cr[sem] += credits_of[c]; completed_disp.add(display_of[c]); core.remove(c)
        if sem >= ELECTIVE_START_SEM:
            for c in elect[:]:
                if met(c, comp) and offered(c, season) and sem_cr[sem] + credits_of[c] <= max_cr:
                    sched[sem].append(c); sem_cr[sem] += credits_of[c]; completed_disp.add(display_of[c]); elect.remove(c)
        if sem >= ELECTIVE_START_SEM and sem_cr[sem] < min_cr:
            for c in elect[:]:
                if met(c, comp) and offered(c, season) and min_cr <= sem_cr[sem] + credits_of[c] <= max_cr:
                    sched[sem].append(c); sem_cr[sem] += credits_of[c]; completed_disp.add(display_of[c]); elect.remove(c)
                    break

    # sprinkle leftovers
    leftovers = core + elect
    for c in sorted(leftovers, key=lambda x: sqi_of[x], reverse=True):
        for sem in range(semesters - SPRINKLE_LAST, semesters):
            season = "fall" if sem % 2 == 0 else "spring"
            comp = {display_of[x] for s in sched[:sem] for x in s} | fulfilled_disp
            if met(c, comp) and offered(c, season) and min_cr <= sem_cr[sem] + credits_of[c] <= max_cr:
                sched[sem].append(c); sem_cr[sem] += credits_of[c]; break

    return sched, sem_cr, G, fulfilled_disp

#  SQI hill‑climb Optimizer 

def _hill_climb(schedule: List[List[str]], sem_cr: List[int], G: nx.DiGraph,
                fulfilled_disp: set[str], min_cr: int, max_cr: int,
                mode: str = "avg", max_iters: int = 800):
    """Greedy hill‑climb; `mode` = 'avg' or 'var'."""

    def has_floor(sem):
        return sem < NO_MIN_FLOOR_AFTER

    def term_sqi(term):
        return sum(sqi_of[c] for c in term) / len(term) if term else 0.0

    def credit_var():
        mu = sum(sem_cr) / len(sem_cr)
        return sum((c - mu) ** 2 for c in sem_cr)

    def score():
        avgs = [term_sqi(t) for t in schedule if t]
        avg_sqi = sum(avgs) / len(avgs)
        if mode == "avg":
            return avg_sqi
        if mode == "var":
            return -credit_var()  # maximise negative variance
        raise ValueError("mode must be 'avg' or 'var'")

    def met(code, comp):
        return all(display_of[p] in comp for p in G.predecessors(code))

    def season_of(sem):
        return "fall" if sem % 2 == 0 else "spring"

    def completed_before(sem):
        return {display_of[x] for s in schedule[:sem] for x in s} | fulfilled_disp

    def can_insert(code, sem):
        if sem_cr[sem] + credits_of[code] > max_cr:
            return False
        if has_floor(sem) and sem_cr[sem] + credits_of[code] < min_cr:
            return False
        return offered_of.get(code, "") in ("", "nan") or season_of(sem) in offered_of[code] and \
               met(code, completed_before(sem))

    def can_remove(code, sem):
        return not (has_floor(sem) and sem_cr[sem] - credits_of[code] < min_cr)

    def do_move(code, src, dst):
        schedule[src].remove(code)
        schedule[dst].append(code)
        sem_cr[src] -= credits_of[code]
        sem_cr[dst] += credits_of[code]

    best = score()
    iters = 0
    while iters < max_iters:
        improved = False
        # single‑course forward moves
        for src in range(len(schedule) - 1):
            for code in schedule[src][:]:
                if "ELECTIVE" not in cat.loc[code, "Name"].upper() or not can_remove(code, src):
                    continue
                for dst in range(src + 1, len(schedule)):
                    if can_insert(code, dst):
                        do_move(code, src, dst)
                        if score() > best:
                            best = score(); improved = True; break
                        do_move(code, dst, src)
                if improved:
                    break
            if improved:
                break
        if improved:
            iters += 1
            continue
        # pair‑wise swaps
        for a in range(len(schedule)):
            for b in range(a + 1, len(schedule)):
                for ca in schedule[a]:
                    if "ELECTIVE" not in cat.loc[ca, "Name"].upper() or not can_remove(ca, a):
                        continue
                    for cb in schedule[b]:
                        if "ELECTIVE" not in cat.loc[cb, "Name"].upper() or not can_remove(cb, b):
                            continue
                        if can_insert(ca, b) and can_insert(cb, a):
                            do_move(ca, a, b); do_move(cb, b, a)
                            if score() > best:
                                best = score(); improved = True; break
                            do_move(ca, b, a); do_move(cb, a, b)
                    if improved:
                        break
                if improved:
                    break
            if improved:
                break
        if not improved:
            break
        iters += 1

# API

def to_df(schedule: List[List[str]]) -> pd.DataFrame:
    max_len = max(len(s) for s in schedule)
    cols: Dict[str, List[str]] = {}
    for i, sem in enumerate(schedule, 1):
        lines = [f"{display_of[c]} {cat.loc[c,'Name']} (" \
                 f"{credits_of[c]} cr, SQI {sqi_of[c]:.2f})" for c in sem]
        cols[f"Semester {i}"] = lines + [""] * (max_len - len(lines))
    return pd.DataFrame(cols)


def build_plan(catalog_csv: Path,
               ap_scores: Dict[str, int],
               min_cr: int = DEFAULT_MIN_CR,
               max_cr: int = DEFAULT_MAX_CR,
               mode: str = "avg") -> Tuple[List[List[str]], List[int], pd.DataFrame]:
    """Generate schedule, credits list, and DataFrame."""
    load_catalog(catalog_csv)
    sched, sem_cr, G, fulfilled = _baseline(ap_scores, min_cr, max_cr)
    _hill_climb(sched, sem_cr, G, fulfilled, min_cr, max_cr, mode=mode)
    return sched, sem_cr, to_df(sched)

# --------------------------- demo ----------------------------
if __name__ == "__main__":
    demo_catalog = DATA_DIR / "computer_engineering_courses.csv"
    sched, cr, df = build_plan(demo_catalog,
                               {"Calculus BC": 5, "Chemistry": 5},
                               12, 17, mode="var")
    print(df)
