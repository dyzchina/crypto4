# Submission Checklist — v11.2 (ASSUMPTIONS)

## What this bundle is
The build after a full mathematical-correctness audit. The theoretical layer that
earlier versions carried — a virtual fundamental class, a Calabi–Yau hypothesis, a
Kontsevich–Soibelman crossing derivation, a risk-neutral pricing theorem — has been
**removed**, because it did not hold up. What replaces it is three explicit
assumptions (H1)–(H3) plus the results that genuinely follow from them. See
`CHANGELOG.md` for the ten verified findings that forced the change.

**JBF cannot be re-submitted.** Its rejection letter states that revised resubmissions
are detected and carry penalties.

## Gate (all verified on the current build)
- [x] `main.pdf` 31 pp / `main_anon.pdf` 31 pp / `cover_letter.pdf` 2 pp
- [x] 0 undefined references, 0 undefined citations, in both builds
- [x] Word count: **7,037** body words
- [x] Captions over target: 0 · Missing figure files: 0 · Missing raw files: 0 ·
      Undefined labels: 0 · Stale claims: 0 · Self-deprecation: 0
- [x] Abstract: **128 words**
- [x] Anonymised build: 0 identity leaks
- [x] `MANIFEST.sha256` regenerated

## The logic of the paper, in one paragraph
`C(theta)` is the second moment of the peg-deviation vector under a probability
measure (Definition, §3.1) — hence symmetric, positive semidefinite, and estimable.
**(H1)** says `C` is constant within a chamber up to a positive scale; *Theorem*
(§3.3) proves that correlation rigidity then follows exactly, the scale cancelling.
**(H2)** says `C` jumps by a rank-one sum across a wall; *Corollary* (§4.2) proves the
induced correlation jump has zero diagonal; *Remark* derives its three-tier footprint.
**(H3)** says the jump is supported on a wall-affected block. §5 tests the footprint.

## What the paper no longer claims (do not reintroduce)
- No virtual fundamental class, implicit atlas, or Behrend–Fantechi cross-check.
- No Calabi–Yau hypothesis. No dimension formula `d = 3(N-1)`.
- No Kontsevich–Soibelman derivation; the analogy is motivation only, and §4.2 says so.
- No risk-neutral pricing theorem and no basket-derivative decomposition.
- `Omega(gamma)` is a **real signed weight**, not an integer BPS invariant.
- `sigma_W` is **never estimated**; the test is invariant to it only at leading order
  in `a`, which is the order at which the criteria are stated (Appendix C.1).

## Before submitting
- [ ] Choose the target journal, then edit the cover-letter addressee and rebuild it
- [ ] Confirm the abstract limit (128 words clears ≤250 comfortably; not AER/JF ≤100)
- [ ] Confirm whether double-blind; if so upload `main_anon.pdf`
- [ ] Declarations are form fields, not in the PDF

## Known weaknesses (state them, do not let a referee find them)
1. **The three load-bearing properties are assumed, not derived.** §2.3 says so
   explicitly, including the cost. A referee may reasonably ask whether the
   assumptions are interesting without a derivation — that is the paper's central
   exposure and it is disclosed rather than hidden.
2. The test has power on one event. Three events carry a multi-coin block; two have a
   single BLOCK pair.
3. FTX is sign-consistent in 8 of 9 windows but imprecise; FDUSD holds only under a
   30-day pre-window. Both are reported.
4. The block sign condition is `p < 2XY/(X+Y)`; it holds automatically at equal
   variances and is satisfied comfortably on the primary event (max |rho| = 0.20).
