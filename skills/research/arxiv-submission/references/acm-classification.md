# ACM classification (CCS 1998)

arXiv's **ACM-class** field is **optional** but worth adding — it aids indexing and signals scope. It
uses the **1998** ACM Computing Classification System (the letter-number codes like `D.2.5`), not the
2012 CCS concept strings.

- **Format**: one line, semicolon-separated leaf codes, most-relevant first, e.g.
  `D.2.5; I.2.6; I.2.11`.
- **How many**: 2–4 codes. One primary "home" code plus a couple that mirror your arXiv cross-lists.
- **Authoritative source**: **https://www.acm.org/publications/computing-classification-system/1998**
  — fetch the specific branch page (e.g., `.../1998/d.2`, `.../1998/i.2`) to confirm a leaf code and
  read its subclasses before committing.

## Derivation procedure

1. Identify the paper's 2–3 core facets (method, subject, application) — usually the same facets that
   drove your arXiv categories.
2. For each facet, walk the tree **top level → second level → leaf**:
   top-level letter (A–K) → `X.n` area → `X.n.k` leaf.
3. Pick the **leaf** (third level) that best matches; verify on the branch page that the leaf's
   description/subclasses fit. Prefer a specific leaf over a `.0 General` or `.m Miscellaneous`.
4. Order codes by relevance; join with `; `.

Map arXiv → ACM intuitively: `cs.SE` → `D.2.*`; `cs.LG`/learning → `I.2.6`; `cs.AI`/agents →
`I.2.11`; NLP → `I.2.7`; `cs.IR` → `H.3.3`; vision → `I.4`/`I.5`; `cs.HC` → `H.5.2`; databases/mining
→ `H.2.8`.

## Top-level tree (1998)

`A` General Literature · `B` Hardware · `C` Computer Systems Organization · `D` Software ·
`E` Data · `F` Theory of Computation · `G` Mathematics of Computing · `H` Information Systems ·
`I` Computing Methodologies · `J` Computer Applications · `K` Computing Milieux

## Common CS leaf codes (quick-reference)

Confirm exact leaves on the branch pages, but these cover most CS/ML/SE papers:

**D.2 Software Engineering**
- `D.2.1` Requirements/Specifications
- `D.2.2` Design Tools and Techniques
- `D.2.4` Software/Program Verification
- `D.2.5` **Testing and Debugging** (incl. regression testing, coverage testing)
- `D.2.8` Metrics
- `D.2.11` Software Architectures
- `D.2.13` Reusable Software

**I.2 Artificial Intelligence**
- `I.2.4` Knowledge Representation Formalisms and Methods
- `I.2.6` **Learning** (ML methods, evaluation of learning systems)
- `I.2.7` Natural Language Processing
- `I.2.8` Problem Solving, Control Methods, and Search
- `I.2.11` **Distributed Artificial Intelligence** (subclasses: Intelligent agents; Multiagent
  systems; Coherence and coordination)

**H — Information Systems** (retrieval / data)
- `H.2.8` Database Applications (incl. data mining)
- `H.3.3` Information Search and Retrieval
- `H.5.2` User Interfaces (HCI)

**Other frequently used**
- `F.2` Analysis of Algorithms and Problem Complexity
- `I.4` Image Processing and Computer Vision · `I.5` Pattern Recognition
- `K.6.3` Software Management

## Worked example

"Who Belongs in the Eval Set?" → `D.2.5; I.2.6; I.2.11`:
- `D.2.5` **Testing and Debugging** — the consolidator curates a **regression** eval set by coverage
  and quality; classic regression-testing / test-suite design (mirrors `cs.SE`).
- `I.2.6` **Learning** — hybrid deterministic + LLM classifier and evaluation methodology for an ML
  system (mirrors `cs.LG`).
- `I.2.11` **Distributed AI** — declarative **agents** with custom actions on an extensibility
  platform (mirrors `cs.AI`; "Intelligent agents" subclass).
- Optional 4th if emphasizing measurement: `D.2.8` **Metrics** (the invocation-quality rater).
