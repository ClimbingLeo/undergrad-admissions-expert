# EE Outline Review: Finite-State Difference Constraints and Smoothness in Discrete Time Functions

## Overall Assessment

**Short answer: Yes, this topic and direction carry real risks of being too narrow, too mechanistic, and insufficiently analytical for a strong EE — but it is not unsalvageable.**

---

## 1. Is the Research Question Too Simple?

The RQ — "How does restricting the first differences of a discrete time function to a finite set affect its smoothness and stability?" — has several structural problems:

### Conceptual Shallowness
- The answer is almost self-evident from the definitions. If you constrain Δyₜ to {−a, 0, a}, the function is forced to change in only three ways. That the resulting sequence is smoother (or differently-smooth) than an unconstrained one is not a surprising or genuinely open question — it follows directly from the constraint design.
- There is no genuine intellectual tension or discovery arc. A strong EE RQ should be one where the answer is not obvious before the investigation.

### Scope is Very Narrow
- The analysis is essentially: pick three values of a, compute a smoothness metric, observe what changes. This is an algebraic/numerical exercise, not a mathematical investigation with depth.
- The "boundary analysis" (Section 5) covers trivial cases: a=0 locks the sequence; a→∞ becomes unconstrained. These are analytically trivial and can be stated in two lines.

### Stability is Not Actually Analyzed
- The RQ mentions "stability," but the outline only defines a smoothness measure O = (1/(T−2)) Σ |Δ²yₜ|. Stability (in the dynamical systems sense) and smoothness are different concepts. The paper conflates them, which will confuse examiners.

---

## 2. Is the Methodology Sufficient?

### Numerical Investigation is Thin
- Testing a = 3, 6, 12 on "constructed sequences" is essentially a demonstration, not an investigation. IB EE mathematics is expected to show original mathematical reasoning — not just plug values into a formula and tabulate results.
- The gas turbine dataset is used "only as illustration," which means the real-world grounding is superficial.

### The Penalty Function is Borrowed, Not Derived
- L_FS = Σ min[(Δyₜ − sᵢ)²] is taken from the Bielski et al. (2024) paper. If the EE merely applies someone else's penalty function to a few sequences and measures smoothness, the intellectual contribution is minimal.
- Examiners will ask: what did *you* discover that wasn't already in the source paper?

### Only One Reference
- A single academic source is a very thin foundation. This raises the question of whether the topic has enough published literature to support a genuine EE-level discussion, or whether the student is essentially re-demonstrating a niche result from one paper.

---

## 3. What Grade-Level Risks Does This Create?

Under IB EE Mathematics criteria:

| Criterion | Risk |
|---|---|
| Focus and Method (Criterion B) | RQ is answerable by construction — low marks for "investigative" quality |
| Knowledge and Understanding (Criterion C) | Concepts are well-defined but shallow; no engagement with broader mathematical context (e.g., signal processing, Lipschitz conditions, total variation) |
| Critical Thinking (Criterion D) | Outcome is predictable; limited scope for genuine analysis or surprise |
| Engagement (Criterion E) | Narrow numerical experiment may not demonstrate intellectual ownership |

---

## 4. Specific Weaknesses in the Outline

- **Section 3**: The set S = {−a, 0, a} is described as "simplified" in the limitations — but if it is acknowledged as too simple, why is it the core of the paper? Either defend it rigorously or choose a richer constraint set.
- **Section 4**: The smoothness measure O is a mean absolute second difference. This is a reasonable metric, but the EE should justify *why* this measure, compare it to alternatives (e.g., total variation, variance of second differences), and explain its mathematical properties — not just apply it.
- **Section 6**: "Constructed sequences" means the student controls the input. This is a closed loop: you design the sequence, apply the constraint, observe smoothness changes you could have predicted. There is no discovery.
- **Limitations section**: Acknowledging that S is "simplified" and the dataset is "only an illustration" in the limitations section essentially admits the investigation is incomplete. These should be defended as deliberate methodological choices, not apologized for.

---

## 5. How to Strengthen the Topic

If you want to keep this general direction, here are concrete ways to add intellectual depth:

### Option A: Make the Mathematics Richer
- Prove (not just observe numerically) how the choice of a affects an upper bound on |Δ²yₜ|.
- Explore S with more than three states, or asymmetric sets like {−a, 0, b}, and derive how asymmetry affects smoothness analytically.
- Connect to total variation minimization — there is substantial mathematical literature here.

### Option B: Ground It in a Real Problem
- Use the gas turbine dataset as the *primary* source of analysis, not just illustration. Fit the model, compare to unconstrained estimation, analyze residuals, test goodness-of-fit. This turns a math exercise into a genuine applied investigation.

### Option C: Reframe the RQ to Be Genuinely Open
- Instead of: "How does restricting differences to a finite set affect smoothness?" (answerable by construction)
- Try: "For a given time series, what value of a in S = {−a, 0, a} minimizes forecast error while maintaining smoothness?" — this has a non-trivial answer and requires real optimization.
- Or: "Under what conditions does a finite-state constraint outperform L1/L2 regularization in producing smooth discrete functions?" — this requires genuine comparison and mathematical argument.

### Option D: Engage with the Literature More Deeply
- Read more of the signal processing / time series smoothing literature. Total variation denoising (Rudin, Osher, Fatemi 1992) is the mathematical ancestor of this kind of constraint. Situating the EE in that context would add genuine depth.

---

## 6. Summary Verdict

| Dimension | Rating |
|---|---|
| Originality of RQ | Low — outcome is predictable |
| Mathematical depth | Low-Medium — definitions are correct but analysis is shallow |
| Analytical rigor | Low — numerical demonstration only |
| Real-world grounding | Weak — dataset is decorative |
| Overall risk to grade | High if submitted as-is |

**Recommendation**: The topic is not a dead end, but the current outline is essentially a demonstration that "constraining values limits how much a function can change" — which is trivially true. The EE needs either a deeper mathematical question (with proofs or non-trivial derivations) or a richer empirical investigation using real data as a primary source. Revising the RQ to introduce genuine uncertainty, and building the outline around discovering something that is not obvious from the setup, would significantly improve the essay's prospects.
