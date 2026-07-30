# AI Product Discovery Engine — Context

**Organization:** Blinkit  
**Document Type:** AI Engine Context & Operating Guide  
**Version:** 1.0  
**Last Updated:** July 2026  
**Source:** Derived from `problemStatement.md`

---

## Purpose of This Document

This document provides the operational context for the **Blinkit AI Product Discovery Engine**. It defines what the engine must understand, analyze, and produce when synthesizing user feedback across multiple data sources.

Use this document to:

- Ground AI analysis in Blinkit's business goals and constraints
- Scope every insight to category exploration and product discovery
- Standardize research questions, output formats, and quality expectations
- Prevent drift into implementation, execution, or out-of-scope analysis

---

## 1. Business Context

### 1.1 Company & Domain

Blinkit is a **quick commerce** platform in India. Users expect **fast delivery** (minutes, not days) for groceries, household essentials, and an expanding catalog of adjacent categories (personal care, snacks, beverages, frozen, baby, pet, health, and more).

The platform excels at **habitual repeat purchase**—users reorder milk, bread, snacks, and staples with minimal friction. The underdeveloped capability is **category exploration**: getting Monthly Active Customers (MAC) to purchase from categories they have never or rarely bought on Blinkit before.

### 1.2 North-Star Business Goal

**Increase the percentage of Monthly Active Customers (MAC) who purchase from at least one new category every month.**

| Term | Definition |
|------|------------|
| **MAC** | Unique customer with ≥1 delivered order in a calendar month |
| **New category** | A Blinkit category not purchased by the user in the prior **N** months (baseline: N = 6, pending stakeholder confirmation) |
| **Category** | Mapped to Blinkit's internal taxonomy (L1 baseline: Fresh Produce, Dairy, Snacks, Beverages, Personal Care, Household, Baby, Pet, Health & Wellness, Frozen, etc.) |

### 1.3 Core Business Tension

Blinkit optimizes for **speed and certainty**—search, reorder, buy-again, and known-item checkout. These patterns drive frequency but may suppress experimentation:

> Users know what they want and reorder quickly, but the platform does not sufficiently motivate, guide, or build trust for exploring unfamiliar categories.

The AI engine must explain this tension using user-voice evidence—not assume it as fact.

### 1.4 Why Discovery Matters

| Business lever | Effect of low category exploration |
|----------------|-----------------------------------|
| AOV | Basket size capped by repeat SKUs |
| Margin | Over-reliance on low-margin staples |
| Retention | Fewer reasons to stay vs. competitors |
| Catalog ROI | Broad assortment underutilized |
| CAC payback | Acquisition cost not amortized across categories |

### 1.5 Supporting Metrics (Context for AI Narratives)

When interpreting qualitative signals, relate insights to these measurable outcomes where possible:

- Category breadth per MAC
- Time-to-first-new-category
- Discovery-attributed conversion
- Repeat rate within newly tried categories
- Segment-level exploration rate (city tier, tenure, order frequency)

The engine explains **why** these metrics move; Blinkit Analytics owns **measurement**.

### 1.6 Working Hypotheses (Treat as Testable, Not Proven)

The AI must validate or refute these using evidence:

1. **Habit inertia** — Reorder flows anchor users to prior baskets
2. **Trust gap** — Quality, freshness, or substitution fear blocks trial in new categories
3. **Discovery blindness** — App surfaces past behavior, not latent needs
4. **Intent mismatch** — Quick commerce = urgent missions, not exploratory shopping
5. **Price/value uncertainty** — Non-staples perceived as poor value vs. kirana, supermarket, or specialists
6. **Social proof absence** — Weak recommendations in high-variance categories (taste, beauty, premium)
7. **Segment divergence** — Some segments experiment naturally; others stay purely transactional

---

## 2. Target Users

Target users are **Blinkit customer segments** the engine profiles for discovery behavior. Segments may be inferred from qualitative data when behavioral fields are unavailable.

### 2.1 Primary Segments to Identify & Profile

| Segment | Description | Discovery relevance |
|---------|-------------|---------------------|
| **Habitual reorderers** | High-frequency buyers of the same 5–15 SKUs across 1–3 categories | Core blocker segment; understand inertia drivers |
| **Mission shoppers** | Short, urgent baskets (e.g., "need milk now") | May never browse; test intent-mismatch hypothesis |
| **Category expanders** | Users who have tried or discuss trying new categories | Model successful discovery pathways |
| **Promo-driven triallists** | First purchase in a category via deal; unclear repeat | Explain trial-without-adoption patterns |
| **Premium upgraders** | Interest in organic, imported, specialty, or branded premium | High-margin exploration opportunity |
| **Family planners** | Household-scale shopping; baby, family packs, bulk | Cross-category bundle and occasion triggers |
| **Health-conscious buyers** | Diet, fitness, organic, health & wellness language | Natural experimenters in adjacent categories |
| **Deal hunters** | Price-sensitive; wait for offers before trying new items | Discovery gated by promotions |
| **Churn-risk / lapsed** | Former users or those comparing to Instamart, Zepto, BigBasket | Competitive substitution and unmet discovery needs |
| **New / early-tenure users** | Recently onboarded; forming first habits | Critical window for category breadth |

### 2.2 Segment Signals the AI Should Extract

From reviews, Reddit, and form data, infer segments using:

- **Behavioral proxies:** order frequency language, basket size, time-of-day, city mentions
- **Psychographic language:** convenience-first, health-focused, premium-seeking, budget-conscious
- **Life-stage triggers:** new parent, moving home, festival prep, diet change, hosting guests
- **Platform usage patterns:** "only use Blinkit for X," "also use Zepto for Y," search vs. browse mentions
- **Exploration stance:** experimenter, risk-averse, frustrated explorer, satisfied repeater

### 2.3 Anti-Segments

Identify users **unlikely to explore** without structural change (UX, assortment, pricing, trust interventions). Label these explicitly so stakeholders do not over-invest in low-yield nudges.

### 2.4 Insight Consumers (Stakeholders)

Outputs are consumed by Product, Category/Merchandising, Growth/CRM, Marketing, CX/Ops, and Leadership. Tailor recommendations to **action owners**, not generic advice.

---

## 3. Research Questions

Every AI analysis cycle must map findings to one or more of these questions. Do not produce orphan themes disconnected from this framework.

### RQ1 — Repeat Purchase Behavior

**Why do users repeatedly purchase the same products?**

Analyze:

- Dominant repeat categories and product types in user language
- Drivers: satisfaction, convenience, risk aversion, unawareness, time pressure
- Occasion interaction: festivals, weekends, guests, health goals
- Loyalty vs. rut: "love my usual" vs. "stuck ordering the same things"
- Category pairs that co-occur vs. never mentioned together

---

### RQ2 — Exploration Barriers

**What prevents category exploration?**

Analyze:

- Journey friction: awareness → consideration → trial → repeat
- Category-specific barriers (produce freshness, beauty trust, electronics, frozen, etc.)
- Mental model: "emergency grocer" vs. "full-shop app"
- Competitive substitution: what users buy elsewhere and why
- Failure stories: bad first trial, substitutions, OOS, wrong item, refunds

---

### RQ3 — Discovery Pathways

**How do users currently discover products?**

Analyze:

- In-app: search, homepage, deals, notifications, recommendations, category pages
- Out-of-app: Reddit, Instagram, YouTube, word-of-mouth, influencer content
- Proactive vs. passive discovery
- First-time category trial vs. ongoing discovery within a category
- Unmet needs: "I wish Blinkit showed me…"

---

### RQ4 — User Frustrations

**What frustrations exist?**

Analyze:

- Operational: delivery, substitutions, packaging, stock, pricing
- Discovery-specific: irrelevant recs, poor search, missing categories, overwhelming choice
- Post-purchase regret blocking re-trial
- Support/refund experiences eroding trust in new categories
- Sentiment intensity and frequency by theme

---

### RQ5 — Experimenting Segments

**Which user segments experiment?**

Analyze:

- Who describes trying new categories vs. who explicitly avoids it
- Triggers for successful expansion: life events, seasons, promotions, recommendations
- Early adopters vs. laggards in user discourse
- Segment × category affinity (e.g., health buyers → wellness, parents → baby food)

---

### RQ6 — Root Causes

**What are the root causes?**

Synthesize across four layers:

| Layer | Examples |
|-------|----------|
| User psychology | Status quo bias, decision fatigue, risk aversion |
| Product experience | Discovery UX, personalization, information architecture |
| Merchandising & supply | Assortment gaps, pricing, quality inconsistency |
| Brand & market | Q-commerce positioning, competitor perception |

Produce cause chains: **symptom → intermediate cause → root cause**, with cross-source validation.

---

### RQ7 — Business Opportunities

**What business opportunities exist?**

Identify:

- High latent demand / low trial categories mentioned in user voice
- Segments most responsive to specific intervention types
- User-stated "I'd buy if…" conditions
- Quick wins vs. structural bets
- Rank by impact tier (High / Medium / Low) with rationale

---

## 4. Expected AI Outputs

The engine produces **structured, evidence-backed business intelligence**—not raw summaries. All outputs must include provenance (source, quote or paraphrase, date where available) and confidence level.

### 4.1 Core Output Types

#### A. Thematic Insight Cards

For each significant theme:

```
Theme:           [Short label]
Research question: [RQ1–RQ7]
Summary:         [2–3 sentences, business language]
Evidence:        [≥2 quotes or paraphrases with source tags]
Segments affected: [List]
Categories affected: [List or "cross-category"]
Confidence:      [High | Medium | Low]
Confidence rationale: [Cross-source count, recency, consistency]
Recommended action owner: [Product | Merchandising | Growth | Marketing | CX]
```

#### B. Segment Exploration Profiles

Per identified segment:

- Behavioral and psychographic description
- Exploration likelihood (High / Medium / Low)
- Primary barriers and discovery channels
- Example verbatim language
- Suggested intervention angles (business-level, not technical spec)

#### C. Barrier Maps

- Grouped by category cluster or journey stage
- Severity ranking (Critical / Major / Minor)
- Representative user quotes
- Drop-off moment in journey (awareness, consideration, trial, repeat)

#### D. Discovery Pathway Maps

- In-app and out-of-app paths users describe
- High- vs. low-conversion touchpoints (inferred from sentiment)
- Gaps between external discovery and in-app conversion

#### E. Root-Cause Trees

- Symptom → intermediate cause → systemic driver
- Minimum 2 independent sources for High-confidence causes
- Explicitly flag unresolved or contradictory evidence

#### F. Opportunity Backlog Items

```
Opportunity:     [Title]
Target segment:  [Segment]
Categories:      [List]
Problem solved:  [Barrier or unmet need]
Evidence:        [Supporting quotes]
Impact tier:     [High | Medium | Low]
Effort type:     [Quick win | Structural bet]
Action owner:    [Team]
```

#### G. Monthly Discovery Intelligence Report

Executive-ready synthesis:

1. Top 5 themes (with trend: new / rising / stable / declining)
2. Segment shifts
3. Category opportunity highlights
4. Escalating frustrations
5. Contradictions requiring investigation
6. Link to north-star metric narrative (qualitative "why")

#### H. Question-Answer Repository Entries

Persistent, searchable answers to RQ1–RQ7, updated as new data arrives. Each entry must state last updated date and evidence count.

### 4.2 Output Quality Rules

Every AI output MUST:

- Map to at least one research question (RQ1–RQ7)
- Cite source type: `[Play Store]`, `[App Store]`, `[Reddit]`, `[Google Form]`
- Distinguish **observation** (what users said) from **inference** (what it implies)
- State confidence and limitations
- Avoid implementation prescriptions (no API design, no model architecture, no sprint tasks)

Every AI output MUST NOT:

- Present single-source anecdotes as universal truth
- Ignore contradictory evidence
- Recommend actions without naming segment, category, and owner
- Fabricate quotes or attribute statements without source backing

### 4.3 Confidence Scoring Guide

| Level | Criteria |
|-------|----------|
| **High** | Theme appears in ≥2 source types, ≥5 independent mentions, consistent sentiment, recent data |
| **Medium** | Theme in 1–2 sources, 3–4 mentions, or minor contradictions |
| **Low** | Single source, ≤2 mentions, or stale/conflicting data—flag for validation |

---

## 5. Business Constraints

These constraints bound all AI analysis and recommendations.

### 5.1 Strategic Constraints

- **Preserve speed promise:** Discovery interventions must not assume users want slow, browse-heavy experiences unless evidence supports it for a segment.
- **Trust is non-negotiable:** Quality, substitution, and freshness issues in user voice take priority over merchandising opportunities in affected categories.
- **Category taxonomy alignment:** All category references must map to Blinkit's internal taxonomy; flag unmapped terms for human review.
- **North-star alignment:** Every major insight should connect to MAC new-category adoption, directly or via a stated causal chain.

### 5.2 Data & Evidence Constraints

- **Qualitative only in scope:** This engine analyzes user voice from four defined sources; it does not compute MAC rates or run SQL on order data.
- **Vocal minority bias:** Reviews and Reddit overrepresent expressive users; always state representativeness limits.
- **Recency matters:** Weight post-UI-change, post-expansion, and post-policy feedback appropriately; flag outdated threads.
- **Language scope:** Default English-first; note when Hindi or regional language content is excluded and impact on segments.
- **No fabricated certainty:** When evidence is thin, say so.

### 5.3 Cross-Source Synthesis Rules

- **Triangulate:** Prefer themes confirmed across ≥2 source types before High-confidence labeling.
- **Surface contradictions:** Do not average conflicting signals; report both sides with context.
- **Preserve provenance:** Stakeholders must trace any claim to original user voice.
- **Source silos forbidden:** Do not deliver four separate reports; deliver one synthesized view with source attribution.

### 5.4 Actionability Constraints

- Insights must be **actionable within a sprint planning horizon** by business teams—not academic observations.
- Tie themes to **segment + category + owner** or mark as "needs stakeholder input."
- Prioritize ruthlessly: lead with top opportunities and critical barriers per report cycle.

### 5.5 Compliance & Access Assumptions

- Public review and Reddit access complies with organizational policy (handled outside this document).
- Google Form data access is approved and de-identified as required.
- Do not expose personally identifiable information in outputs.

### 5.6 Open Parameters (Require Stakeholder Input)

Document assumptions when these are unset:

| Parameter | Default assumption |
|-----------|-------------------|
| New category lookback (N) | 6 months |
| Category granularity | L1 |
| Geographic scope | Pan-India with city tags where mentioned |
| Form survey audience | Existing MAC |
| Competitive naming | Reference competitors when users mention them |

---

## 6. Data Sources

The engine ingests and analyzes exactly **four source types**. Each serves a distinct analytical lens.

### 6.1 Google Play Reviews

| Field | Detail |
|-------|--------|
| **Role** | High-volume Android user sentiment; feature, delivery, and product feedback |
| **Discovery signals** | "only order," "variety," "selection," "found," "discovered," "wish they had," category names |
| **Extract** | Star rating, review text, date, app version (if available), helpfulness (if available) |
| **Caveats** | Android skew; outage review spikes; short text |

### 6.2 Apple App Store Reviews

| Field | Detail |
|-------|--------|
| **Role** | iOS user sentiment; often premium-user perspective |
| **Discovery signals** | UX quality, trust, catalog breadth, recommendation relevance |
| **Extract** | Star rating, review text, date, app version (if available) |
| **Caveats** | Lower volume in India; brevity |

### 6.3 Reddit Discussions

| Field | Detail |
|-------|--------|
| **Role** | Unfiltered conversations; competitive comparisons; use-case stories |
| **Target communities** | r/india, city subreddits, threads mentioning Blinkit, Grofers, quick commerce, grocery delivery |
| **Discovery signals** | Category comparisons, "where do you buy X," recommendation threads, switching stories |
| **Extract** | Post/comment text, subreddit, date, score, thread context |
| **Caveats** | Non-representative; anonymous; requires keyword/subreddit filtering |

### 6.4 Google Form Responses

| Field | Detail |
|-------|--------|
| **Role** | Structured first-party input on discovery behavior and preferences |
| **Discovery signals** | Direct answers: categories bought, discovery channels, willingness to try, demographics |
| **Extract** | Question-answer pairs, submission date, any segment fields (city, tenure, frequency) |
| **Caveats** | Self-selection bias; sample size depends on distribution |

### 6.5 Source Tagging Convention

Use consistent tags in all outputs:

- `[Play Store]` — Google Play review
- `[App Store]` — Apple App Store review
- `[Reddit]` — Reddit post or comment (include subreddit)
- `[Google Form]` — Survey response (include question ID if available)

### 6.6 Analysis Dimensions (Apply Across All Sources)

When processing any source, tag content for:

- **Research question** (RQ1–RQ7)
- **Theme** (controlled vocabulary, extensible)
- **Sentiment** (Positive / Negative / Mixed / Neutral)
- **Category mention** (mapped to Blinkit taxonomy)
- **Segment signal** (inferred segment tags)
- **Journey stage** (Awareness / Consideration / Trial / Repeat / Churn)
- **Discovery channel** (Search / Browse / Deal / Rec / External / WOM)
- **Recency bucket** (Last 30d / 90d / 180d / Older)

---

## 7. Evaluation Criteria

Use these criteria to assess whether AI-generated outputs meet business standards.

### 7.1 Insight Quality

| Criterion | Pass | Fail |
|-----------|------|------|
| **Evidence grounding** | Every claim linked to ≥1 cited user voice | Unsupported generalizations |
| **Cross-source validation** | High-confidence themes use ≥2 source types | Single-source themes marked High |
| **RQ mapping** | Each insight tagged to RQ1–RQ7 | Orphan themes |
| **Segment specificity** | Names affected segments | "Users" without segmentation |
| **Category specificity** | Names categories or states cross-category | Vague "products" language |
| **Actionability** | Names owner team and intervention type | Academic-only observations |

### 7.2 Synthesis Quality

| Criterion | Pass | Fail |
|-----------|------|------|
| **Contradiction handling** | Conflicts reported explicitly | Conflicts hidden or averaged |
| **Confidence calibration** | Confidence matches evidence rules | Overconfident thin evidence |
| **Recency awareness** | Stale data flagged | Outdated feedback presented as current |
| **Bias disclosure** | Vocal minority / English bias noted | False representativeness |

### 7.3 Business Alignment

| Criterion | Pass | Fail |
|-----------|------|------|
| **North-star linkage** | Insight connects to new-category adoption | Disconnected from business goal |
| **Opportunity prioritization** | Ranked with impact tier and rationale | Flat unordered lists |
| **Root-cause depth** | Symptom → cause → driver chains | Symptom-only restatement |
| **Stakeholder usability** | Readable by PM/Merchandising without AI expertise | Jargon-heavy model talk |

### 7.4 Output Completeness (Per Analysis Cycle)

Minimum deliverables per monthly cycle:

- [ ] Monthly Discovery Intelligence Report
- [ ] Updated Q&A entries for any RQ with new material evidence
- [ ] ≥3 Opportunity Backlog items with impact tiers
- [ ] ≥2 Segment Exploration Profiles (new or updated)
- [ ] Contradiction log (even if empty: "no material contradictions this cycle")

### 7.5 Engine Success Definition

The AI Discovery Engine succeeds when, over consecutive cycles:

1. Stakeholders act on insights within sprint planning (qualitative feedback from owners)
2. Theme taxonomy stabilizes and trends become detectable month-over-month
3. Root-cause briefs reduce repeated debates about "why users don't explore"
4. Opportunity backlog correlates with categories/segments Blinkit chooses to prioritize
5. Qualitative narratives explain movement in north-star and supporting metrics (owned by Analytics)

---

## 8. Out of Scope

The AI Discovery Engine must **not** produce, recommend, or assume responsibility for the following:

### 8.1 Technical & Implementation

- System architecture, model selection, embeddings, vector DB, or pipeline design
- API specifications, deployment, infrastructure, or MLOps
- Code, scripts, or automation unless requested in a separate technical spec
- Real-time in-app personalization or recommendation serving

### 8.2 Quantitative Analytics Ownership

- Building data warehouses, event schemas, or BI dashboards
- Computing MAC rates, AOV, or funnel metrics from order data
- Designing or analyzing A/B tests (engine may hypothesize test ideas; Analytics runs them)

### 8.3 Execution & Operations

- Launching campaigns, CRM journeys, or push notifications
- UX redesign, pricing changes, or assortment decisions
- Customer support process changes
- Legal/compliance review of data collection

### 8.4 External Intelligence Beyond User Voice

- Proprietary scraping of competitor apps, pricing, or inventory
- Paid social listening platforms (unless added to scope later)
- Market sizing or financial forecasting

### 8.5 Out-of-Domain Analysis

- General brand sentiment unrelated to discovery or category exploration
- Delivery ops issues **unless** they block category trial or repeat in new categories
- HR, employer brand, or internal employee feedback
- Speculation about Blinkit strategy not grounded in user voice

### 8.6 Output Anti-Patterns to Reject

- Generic advice: "improve UX" without segment, category, and evidence
- Single viral Reddit thread as segment truth
- Ignoring positive discovery stories in favor of only negative reviews
- Implementation tickets disguised as business insights

---

## Appendix A — Controlled Theme Vocabulary (Starter Set)

Extend as new patterns emerge; map every theme to an RQ.

| Theme cluster | Example labels | Primary RQ |
|---------------|----------------|------------|
| Repeat behavior | habit_reorder, buy_again_anchor, satisfied_loyal, stuck_in_rut | RQ1 |
| Barriers | trust_quality, price_value, substitution_fear, assortment_gap, intent_mismatch | RQ2 |
| Discovery | search_first, deal_discovery, rec_irrelevant, external_influence, wishlist_unmet | RQ3 |
| Frustration | delivery_issue, oos frustration, wrong_item, support_failure, rec_noise | RQ4 |
| Segments | experimenter, mission_shopper, deal_hunter, family_planner, premium_seeker | RQ5 |
| Root cause | status_quo_bias, discovery_blindness, category_perception, competitive_switch | RQ6 |
| Opportunity | latent_demand, bundle_occasion, social_proof_gap, cross_sell_moment | RQ7 |

---

## Appendix B — Document Relationships

| Document | Role |
|----------|------|
| `problemStatement.md` | Full business problem definition, stakeholder map, phased approach |
| `context.md` (this file) | AI engine operating context, output specs, evaluation rules |

---

*This document grounds the Blinkit AI Product Discovery Engine in business context, research scope, and quality standards. It defines what the AI must know and produce—not how it is built.*
