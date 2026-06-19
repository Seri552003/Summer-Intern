# An Agentic LLM-Based Intelligent Process Planning System for Manufacturing with Multi-Objective Optimization and Sequence Validation

Integrating Large Language Models, Multi-Objective Optimization, FSM Validation, and Self-Correction for Automated Process Planning.

**Summer Internship Project** · Manufacturing AI · CAPP (Computer-Aided Process Planning)

---

## 📌 Project Status

**Weeks 1–3 Complete** | 6-Week Roadmap | 21/21 Tests Passing

| Week | Module | Status |
|------|--------|--------|
| Week 1 | Feature Extraction & Tokenization | ✅ Complete |
| Week 2 | LLM Process Planner Development | ✅ Complete |
| Week 3 | Multi-Agent Evaluation System | ✅ Complete |
| Week 4 | NSGA-II Optimization & FSM Validation | 🔜 Upcoming |
| Week 5 | Error Detection & Self-Correction Loop | 🔜 Upcoming |
| Week 6 | Testing, Demo & Documentation | 🔜 Upcoming |

---

## 🎯 Objective

Manual process planning in manufacturing is time-consuming, experience-dependent, and prone to sequencing errors. This project builds an AI-driven system that **automatically generates, evaluates, validates, and self-corrects** manufacturing process plans — converting raw part specifications (material, geometry, tolerance, batch size) into an optimized, machine-ready process route.

---

## 🏗️ System Architecture (Built So Far)

```
  Part Input (JSON)
        │
        ▼
┌───────────────────┐
│  WEEK 1            │   Validates input, converts features/material/
│  Tokenizer         │   tolerance/batch size into numeric Token IDs
└─────────┬──────────┘
          ▼
┌───────────────────┐
│  WEEK 2            │   LLM (HuggingFace) interprets tokens and
│  LLM Process       │   generates a candidate process plan; route
│  Planner           │   selected from the manufacturing route library
└─────────┬──────────┘
          ▼
┌───────────────────┐
│  WEEK 3            │   4 agents — Time ⏱, Cost 💰, Energy ⚡,
│  Multi-Agent       │   Efficiency 📊 — score every candidate route
│  Evaluation        │   and the best route is selected
└─────────┬──────────┘
          ▼
   Optimized Process Plan
   (Route + Time + Cost + Energy + Efficiency Score)
```

All three modules are connected through `week3/run_pipeline.py`, which runs the entire flow end-to-end on a batch of parts in a single command.

---

## 📂 Repository Structure

```
INTERN-PROJECT/
│
├── week1/                      Feature Extraction & Tokenization
│   ├── feature_vocab.py        10 manufacturing geometry features
│   ├── material_tokens.py      7 materials, tolerance & batch categories
│   ├── token_map.json          Master Token ID mapping (100s/200s/300s/400s)
│   ├── parser.py                JSON input validator
│   ├── tokenizer.py            Main: input → token sequence
│   ├── tests/test_tokenizer.py  6 unit tests
│   └── README.md
│
├── week2/                      LLM Process Planner Development
│   ├── llm_planner.py          HuggingFace LLM-based plan generation
│   ├── routes.py               Manufacturing route library (Route A/B/C)
│   ├── planner.py              Token-based route selection logic
│   └── tests/test_planner.py    5 unit tests
│
├── week3/                      Multi-Agent Evaluation System
│   ├── agents.py                Time, Cost, Energy, Efficiency agents
│   ├── multi_agent_eval.py     Compares all routes, selects the best
│   ├── run_pipeline.py         ⭐ End-to-end pipeline (Week 1→2→3)
│   └── tests/test_agents.py     10 unit tests
│
├── data/                       Synthetic Dataset
│   ├── generate_dataset.py     Dataset generator script
│   ├── parts_dataset.json      50 synthetic manufacturing parts
│   ├── parts_dataset.csv       Same dataset, CSV format
│   └── pipeline_results.json   Output of the full pipeline run
│
└── README.md                   This file
```

---

## ⚙️ How to Run

**Run the full pipeline on all 50 dataset parts:**
```bash
cd week3
python run_pipeline.py
```

**Run each week's module individually:**
```bash
cd week1 && python tokenizer.py
cd week2 && python planner.py
cd week3 && python multi_agent_eval.py
```

**Run all tests (21 total):**
```bash
cd week1 && python -m pytest tests/ -v   # 6 tests
cd week2 && python -m pytest tests/ -v   # 5 tests
cd week3 && python -m pytest tests/ -v   # 10 tests
```

---

## 🧪 Why a Synthetic Dataset?

Publicly available manufacturing process-planning datasets are scarce — this is a documented constraint in the project's problem statement. To validate the system across diverse conditions, a **50-part synthetic dataset** was generated covering 7 materials, 10 geometry features, 6 tolerance levels, and batch sizes from prototype (5 units) to mass production (5000 units). This allows the Week 1→2→3 pipeline to be tested at scale rather than on isolated examples.

---

## 📊 Example: End-to-End Run

**Input:**
```json
{
  "material": "Aluminum",
  "features": ["Hole", "Slot"],
  "tolerance": "0.02mm",
  "batch_size": 500
}
```

**Pipeline Output:**
```
Tokens          : [201, 101, 102, 303, 403]
Best Route      : Route_A (Facing → Drilling → Reaming → Inspection)
Time            : 25.0 min
Cost            : $46.00
Energy          : 1.3 kWh
Efficiency Score: 71.23 / 100
```

---

## 🔬 Test Summary

| Module | Tests | Status |
|--------|-------|--------|
| Week 1 — Tokenizer | 6 | ✅ All Passing |
| Week 2 — Planner | 5 | ✅ All Passing |
| Week 3 — Multi-Agent Eval | 10 | ✅ All Passing |
| **Total** | **21** | **✅ All Passing** |

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **LLM:** HuggingFace Transformers (`falcon-rw-1b`)
- **Testing:** pytest
- **Data:** JSON, CSV
- **Version Control:** Git & GitHub

---

## 🔜 Next Steps (Week 4 onward)

- **Week 4:** Implement NSGA-II for true multi-objective Pareto optimization across the synthetic dataset; build an FSM (Finite State Machine) to validate operation sequences against manufacturing precedence rules.
- **Week 5:** Build a self-correction loop so the LLM can automatically repair sequences rejected by the FSM.
- **Week 6:** Final integration testing, live demo, and complete documentation.

---

## 🔗 Repository

[github.com/Radhana123/LLM-CAPP-Project_Summer_Intern](https://github.com/Radhana123/LLM-CAPP-Project_Summer_Intern)