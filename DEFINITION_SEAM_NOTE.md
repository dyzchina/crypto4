# Definitional seam — FIXED in v10.0 (2026-10-23)

**Original status:** identified during a full-manuscript coherence audit; left open in the first v10.0 build, then fixed at the author's instruction the same day.

---

## The seam as it was

The paper's central object was defined by an integral whose integrand was identically zero on its own integration domain.

1. **§2, Definition 1.** A coin is *peg-preserving* over `[0,T]` if `|Ō_i(t) − 1| ≤ ε`, with `ε = 50` bp.
2. **§2, Definition 2 (before).** `M_peg = {(s_1,…,s_N) : s_i peg-preserving ∀i; joint feasibility}` — so every point of the moduli satisfied `|Ō_i − 1| ≤ ε`.
3. **§3, Definition 3.** `Λ_ij(θ) := ∫_{[M_peg]^vir} 1[|Ō_i − 1| > ε] · 1[|Ō_j − 1| > ε] dμ_θ`.

The indicator therefore vanished on the support of the virtual class. `Λ ≡ 0`, the Bernoulli normalisation returned `0/0` off-diagonal, Theorem 2 (local constancy) was trivially true, and Theorem 3 (wall-crossing) had nothing to act on.

---

## The fix (Option A, applied)

Peg preservation was demoted from a *defining restriction on the moduli* to a *constraint cutting a substack out of it*.

| Element | Before | After |
|---|---|---|
| Ambient space | `M_peg` (peg-preserving only) | **`\Mconf`** — configuration moduli, all jointly feasible tuples |
| Peg-preserving set | the moduli itself | **`\Mpeg`** — substack of `\Mconf` (unchanged symbol, narrower role) |
| VFC lives on | `M_peg` | **`M_conf`** |
| `Θ_peg` | `{θ : M_peg(θ) ≠ ∅}` | `{θ : M_peg(θ) ≠ ∅}` — unchanged, now read against the substack |

### Text changed

**Substantive (one definition, one paragraph):**
- `section2_moduli.tex`, Definition 2 — retitled *Basket configuration moduli and its peg-preserving locus*; `\Mconf` defined as all jointly feasible tuples; `\Mpeg ⊂ \Mconf` defined as the substack on which every coin is peg-preserving (Definition 1). Added a short paragraph explaining that peg preservation is a constraint on the ambient space rather than a restriction of what the space may contain, that the atlas and VFC are built on `\Mconf`, and that `\Mpeg` is where the constraint is active.
- `section3_rigidity.tex`, Definition 3 — added the sentence that closes the seam: the integral is over the ambient configuration moduli of Definition 2, on which the indicator has **non-degenerate support** — a configuration with `|Ō_i − 1| > ε` lies outside `\Mpeg` but inside `\Mconf`.

**Wording (3 places in §2):** section preamble, subsection title, and the Theorem 1 statement now say "configuration moduli" rather than "peg-preserving equilibria".

**§3, Definition 5 (wall set):** `Θ_peg` now reads "the open subset under which the peg-preserving locus is non-empty, `\Mpeg(θ) ≠ ∅`", with an explicit note that `\Mconf(θ)` is non-empty throughout `\B`.

**Mechanical symbol substitution:** 56 occurrences of `\Mpeg` → `\Mconf` across §1–§4 and the appendices; `\Mpeg` retained only in the 6 places where the peg-preserving locus is genuinely meant (the new Definition 2, its dimension footnote, the §2 preamble, and the two seam-closing sentences).

### Not changed

- **No theorem statement altered.** Theorems 2–4 are stated in terms of `Σ`, `Λ`, `Θ_peg` and the walls; only the notation of the integration domain changed, not any claim.
- **§5 (the empirical section) untouched** — it contains no `\Mpeg`.
- Wall definitions, Table 1, all figures, all numbers, `numbers.tex`: untouched.

---

## Verification after the fix

- Compiles clean: 40 pages, **0 undefined references**
- 8/8 audits pass: body 8,621 words; refs 34/34 with 0 missing and 0 unused; captions 0 over; figures 0 missing; provenance 0 missing; equations and ref labels clean; sample period clean
- Text extracted from the compiled PDF confirms page 5 carries the new Definition 2 and page 8 carries the seam-closing sentence with `[M]^vir`, `Definition 2`, `M_peg` (locus) and `M` (ambient) all in place

---

## Also fixed in the same audit round

- **Event count.** Four text locations and the Figure 4 title said "seven non-degenerate events"; the data file `data/estimator_vfc_per_event.csv` and the plotted figure contain **eight** events (DAI skipped, UST included). All now read "eight events with a usable pre-event window", and the phrase "non-degenerate" was dropped because §5's own Figure 4 caption states that single-coin blocks *are* metric-degenerate. Figure 4 regenerated.
- **Hard-coded numbers.** The placebo permutation count (`6`), the placebo draw count (`200`), the FTX bootstrap p-value (`0.001`) and the block-metric sum (`-0.108`) were hard-coded where `numbers.tex` macros existed; all four now use `\PLACEBOACONDN`, `\PLACEBOBCONDN`, `\DELTAFTXP` and `\PLACEBOREAL`, so `inject_numbers.py` cannot silently desynchronise the prose from the data.
- **Residual dead macros.** `\PLACEBOMEAN` (−0.013), `\PLACEBOSD` (0.217), `\PLACEBOP` (0.760), `\ESMULT` (43.9) and `\NCOINSSUB` (10) are defined in `numbers.tex` but used nowhere. They appear to be leftovers from an earlier draft that reported an unconditional placebo. Harmless, but they should be wired in or dropped at the next `inject_numbers.py` regeneration.
