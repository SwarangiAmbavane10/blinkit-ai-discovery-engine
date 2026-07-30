# AI Product Discovery Engine — Problem Statement

**Organization:** Blinkit  
**Document Type:** Business Problem Definition & Project Scope  
**Version:** 1.0  
**Last Updated:** July 2026

---

## 1. Executive Summary

Blinkit operates in quick commerce, where speed and repeat purchase behavior dominate user journeys. A significant portion of Monthly Active Customers (MAC) repeatedly buy from the same narrow set of categories and SKUs—often staples, beverages, and personal care—while under-exploring adjacent categories that Blinkit already stocks.

This project defines an **AI Product Discovery Engine** whose primary business outcome is to **increase the percentage of Monthly Active Customers who purchase from at least one new category every month**. The engine will synthesize qualitative signals from public and first-party feedback channels to explain *why* discovery stalls, *who* is most likely to experiment, and *where* the highest-leverage product and merchandising opportunities lie.

This document covers the business problem, strategic context, research questions, data scope, deliverable insights, and project boundaries. It does **not** prescribe technical implementation.

---

## 2. Business Context

### 2.1 What Blinkit Is Optimizing For

Quick commerce success depends on two reinforcing loops:

1. **Frequency loop** — Users build habitual reorder patterns for high-velocity items (milk, bread, snacks, household essentials).
2. **Basket expansion loop** — Users gradually add new categories, increasing average order value (AOV), margin mix, and platform stickiness.

Blinkit has largely mastered the frequency loop. The underdeveloped loop is **category exploration**: getting habitual buyers to discover and adopt products outside their established purchase graph.

### 2.2 Why Category Exploration Matters

| Metric | Impact of Low Category Exploration |
|--------|-------------------------------------|
| **AOV** | Repeat SKU purchases cap basket size; new categories unlock cross-sell |
| **Margin** | Staples are often low-margin; specialty, premium, and niche categories improve unit economics |
| **Retention** | Users who expand categories have more reasons to stay vs. switching to competitors |
| **Inventory utilization** | Broad catalog value is unrealized if users never see or trust non-core categories |
| **Marketing efficiency** | Paid acquisition cost is harder to amortize when users only buy 2–3 category types |

### 2.3 The Core Business Tension

Blinkit's product experience is optimized for **speed and certainty**—search, reorder, and known-item checkout. That optimization creates a paradox:

> The same UX patterns that drive repeat purchases may actively suppress experimentation with unfamiliar categories.

Understanding this tension—and resolving it without sacrificing delivery speed or trust—is the central business challenge this project addresses.

---

## 3. Primary Business Goal

### 3.1 North-Star Metric

**Increase the percentage of Monthly Active Customers (MAC) who purchase from at least one new category every month.**

**Definition:**

- **Monthly Active Customer (MAC):** A unique customer who completes at least one delivered order in a calendar month.
- **New category (for a given user in a given month):** A product category the user has **not** purchased in any of the prior **N** months (recommended baseline: N = 6; to be validated with business stakeholders).
- **Category:** Aligned to Blinkit's internal category taxonomy (e.g., Fresh Produce, Dairy, Snacks, Beverages, Personal Care, Household, Baby, Pet, Health & Wellness, Frozen, etc.).

### 3.2 Supporting Metrics (Secondary)

These metrics help diagnose *how* discovery improves, not just *whether* it improves:

| Metric | Purpose |
|--------|---------|
| **Category breadth per MAC** | Average distinct categories purchased per active user per month |
| **Time-to-first-new-category** | Days from signup (or reactivation) to first purchase in a previously untried category |
| **Discovery-attributed conversion** | Orders where at least one SKU came from a category not bought in prior N months |
| **Repeat rate within newly tried categories** | Whether exploration leads to sustained adoption or one-off trials |
| **Segment-level exploration rate** | Exploration broken down by city tier, order frequency, tenure, and demographic proxies |

### 3.3 Success Criteria (Business-Level)

The AI Product Discovery Engine will be considered successful when it consistently produces:

1. **Actionable insight reports** that product, growth, and merchandising teams can act on within a sprint cycle.
2. **Segment-specific discovery profiles** that explain who explores, who doesn't, and why.
3. **Prioritized opportunity backlog** ranked by estimated impact on new-category adoption.
4. **Root-cause narratives** backed by evidence from multiple data sources—not single-channel anecdotes.

---

## 4. Problem Definition

### 4.1 The Problem in One Sentence

**Blinkit users know what they want and reorder it quickly, but the platform provides insufficient motivation, trust, and contextual guidance for them to confidently explore categories beyond their habitual purchase set.**

### 4.2 Observable Symptoms

These symptoms may appear in operational data and qualitative feedback (to be validated during discovery):

- High repeat-SKU concentration among top decile customers
- Search-dominated journeys with low browse-to-purchase conversion outside core categories
- Category landing pages with high exit rates for non-staple categories
- Promo-driven spikes in new-category trials that do not sustain
- Reviews and social discourse citing "I only use Blinkit for X" patterns
- Users unaware that Blinkit stocks categories they currently buy elsewhere

### 4.3 Underlying Hypotheses (To Be Tested)

The engine should treat these as hypotheses, not conclusions:

1. **Habit inertia** — Reorder and "buy again" flows reduce cognitive load but anchor users to prior baskets.
2. **Trust gap** — Users hesitate to try fresh, premium, or unfamiliar categories due to quality, freshness, or substitution concerns.
3. **Discovery blindness** — Users don't encounter relevant categories because the app surfaces what they already buy, not what they might need next.
4. **Intent mismatch** — Quick commerce is associated with urgent, narrow missions; exploratory shopping feels misaligned with the brand promise.
5. **Price and value uncertainty** — Users perceive non-staple categories as overpriced or poor value vs. kirana, supermarket, or specialized retailers.
6. **Social proof absence** — Lack of credible recommendations for categories where taste, brand, or quality preferences vary widely.
7. **Segment divergence** — Some segments (e.g., new parents, health-conscious buyers, premium seekers) are natural experimenters; others are purely transactional.

---

## 5. Strategic Questions the AI Must Answer

The AI Product Discovery Engine exists to answer the following business questions with evidence-backed synthesis.

### 5.1 Why do users repeatedly purchase the same products?

**What we need to understand:**

- Which products and categories dominate repeat purchase cycles?
- Is repetition driven by satisfaction, convenience, risk aversion, or lack of awareness?
- Do users *want* to explore but default to known items under time pressure?
- How do occasion-based needs (weekend cooking, guests, festivals, health goals) interact with repeat behavior?
- What role do household composition, dietary preferences, and local availability play?

**Expected insight types:**

- Repeat purchase driver taxonomy (functional, emotional, situational)
- Category pairs that co-occur vs. categories that never co-occur
- Language patterns in reviews that signal "loyalty" vs. "stuck in a rut"

---

### 5.2 What prevents category exploration?

**What we need to understand:**

- Friction points in the journey from awareness → consideration → trial → repeat
- Category-specific barriers (e.g., produce freshness vs. electronics trust vs. beauty shade matching)
- Mental models: Do users categorize Blinkit as "emergency grocer" vs. "full-shop destination"?
- Competitive substitution: Which categories users buy elsewhere and why
- Failure stories: Wrong substitutions, bad first experiences, or abandoned carts in new categories

**Expected insight types:**

- Barrier map by category cluster
- Severity-ranked friction themes with representative user quotes
- Moments in the user journey where exploration drops off

---

### 5.3 How do users currently discover products?

**What we need to understand:**

- Discovery channels: search, homepage modules, push notifications, influencer content, word-of-mouth, in-app recommendations, deals, seasonal campaigns
- Proactive vs. passive discovery—do users stumble upon products or hunt intentionally?
- Role of external discovery (Instagram, YouTube, Reddit) that later converts on Blinkit
- Differences between first-time category trial and ongoing discovery within a category

**Expected insight types:**

- Discovery pathway map (in-app and out-of-app)
- High-conversion vs. low-conversion discovery touchpoints
- Unmet discovery needs ("I wish Blinkit showed me…")

---

### 5.4 What frustrations exist?

**What we need to understand:**

- Product quality, packaging, delivery timing, substitutions, pricing, stock availability
- Discovery-specific frustrations: irrelevant recommendations, overwhelming choice, poor search results, missing categories
- Post-purchase regret drivers that discourage future experimentation
- Support and refund experiences that erode trust in new categories

**Expected insight types:**

- Frustration theme clusters with frequency and sentiment intensity
- Category-specific complaint profiles
- Frustrations that disproportionately affect first-time category buyers

---

### 5.5 Which user segments experiment?

**What we need to understand:**

- Segment definitions: tenure, order frequency, city tier, basket size, category breadth, promo sensitivity, time-of-order patterns
- Psychographic signals: health-focused, convenience-first, deal hunters, premium upgraders, family planners
- Life-stage triggers: moving homes, new baby, dietary change, festival seasons
- Early adopters vs. laggards within the Blinkit user base

**Expected insight types:**

- Segment personas with exploration behavior profiles
- Triggers and conditions associated with successful category expansion
- Anti-segments: users unlikely to explore without structural intervention

---

### 5.6 What are the root causes?

**What we need to understand:**

Root-cause analysis should move beyond symptoms to systemic drivers across four layers:

| Layer | Example Root-Cause Questions |
|-------|------------------------------|
| **User psychology** | Risk aversion, decision fatigue, status quo bias |
| **Product experience** | Discovery UX, personalization limits, information architecture |
| **Merchandising & supply** | Assortment gaps, pricing, quality consistency in non-core categories |
| **Brand & market context** | Competitive positioning, category perception, quick-commerce mission scope |

**Expected insight types:**

- Root-cause tree linking symptoms → intermediate causes → systemic drivers
- Cross-source validation (e.g., Reddit complaint + App Store review + form response pointing to same cause)
- Confidence scoring based on evidence density and consistency

---

### 5.7 What business opportunities exist?

**What we need to understand:**

- Which categories have high latent demand but low trial rates?
- Which segments are most responsive to nudges (bundles, samples, curated lists, social proof)?
- Which discovery interventions have analogues in user feedback ("I'd buy if…")?
- Quick wins vs. structural bets (UX changes, assortment, pricing, content)

**Expected insight types:**

- Prioritized opportunity list with rationale, target segment, and affected categories
- Estimated impact tier (High / Medium / Low) based on addressable MAC and barrier removability
- Opportunity types: product, merchandising, marketing, CRM, content, partnerships

---

## 6. Data Sources in Scope

The AI Product Discovery Engine will analyze the following qualitative and semi-structured data sources. Each source contributes a distinct lens on user behavior and sentiment.

### 6.1 Google Play Reviews

| Attribute | Detail |
|-----------|--------|
| **Value** | High-volume, longitudinal feedback from Android users; often mentions specific features, delivery, and product quality |
| **Discovery relevance** | Search for patterns around "only order," "wish they had," "found," "discovered," "selection," "variety," category names |
| **Limitations** | Skews Android; review bombing during outages; short-form text |

### 6.2 Apple App Store Reviews

| Attribute | Detail |
|-----------|--------|
| **Value** | iOS user perspective; often overlaps with Play reviews but may differ by demographic |
| **Discovery relevance** | UX and trust signals; premium-user sentiment |
| **Limitations** | Lower volume than Play in India; similar brevity constraints |

### 6.3 Reddit Discussions

| Attribute | Detail |
|-----------|--------|
| **Value** | Unfiltered, contextual conversations; comparative mentions (Swiggy Instamart, Zepto, BigBasket, kirana); use-case storytelling |
| **Discovery relevance** | Organic discovery narratives, category comparisons, recommendation threads, r/india and city subreddits |
| **Limitations** | Non-representative sample; anonymous; requires subreddit and keyword targeting |

### 6.4 Google Form Responses

| Attribute | Detail |
|-----------|--------|
| **Value** | Structured first-party or research-initiated input; can target specific questions on discovery behavior |
| **Discovery relevance** | Direct answers on shopping habits, category willingness, discovery preferences, demographics |
| **Limitations** | Self-selection bias; sample size depends on distribution channel |

### 6.5 Cross-Source Synthesis Requirement

Insights must not be reported in source silos. The engine must:

- **Triangulate** themes that appear across ≥2 sources
- **Flag contradictions** (e.g., App Store praise for selection vs. Reddit complaints about variety)
- **Attribute confidence** based on evidence weight and recency
- **Preserve provenance** so stakeholders can trace insights back to original quotes

---

## 7. Stakeholders & Consumers of Insights

| Stakeholder | Primary Use of Outputs |
|-------------|------------------------|
| **Product Management** | Discovery UX, search, homepage, personalization roadmap |
| **Category & Merchandising** | Assortment gaps, pricing, quality investments by category |
| **Growth & CRM** | Lifecycle campaigns, reactivation, segment-specific nudges |
| **Marketing & Brand** | Positioning, content strategy, seasonal campaigns |
| **Customer Experience / Ops** | Quality and substitution issues blocking repeat in new categories |
| **Leadership** | Strategic bets on catalog breadth vs. depth, segment focus |

---

## 8. Expected Deliverables (Business Outputs)

The following are **business deliverables**, not technical artifacts:

1. **Monthly Discovery Intelligence Report** — Top themes, emerging frustrations, segment shifts, and category opportunity highlights.
2. **Root-Cause Briefs** — Deep dives on 2–3 priority barriers per quarter (e.g., "Why produce trial doesn't repeat").
3. **Segment Exploration Playbooks** — Profiles of high-potential experimenters and recommended intervention angles.
4. **Opportunity Backlog** — Ranked list of business actions with supporting evidence excerpts.
5. **Question-Answer Repository** — Searchable responses to the seven strategic questions (Section 5), updated as new data arrives.
6. **Executive Dashboard Narrative** — Plain-language summary tying qualitative insights to the north-star metric and supporting KPIs.

---

## 9. Project Scope

### 9.1 In Scope

- Business problem framing and success metric definition
- Qualitative analysis of Google Play, App Store, Reddit, and Google Form data
- Thematic extraction aligned to the seven strategic question areas
- User segment characterization based on behavioral and psychographic signals available in source data
- Root-cause synthesis and business opportunity identification
- Cross-source triangulation and confidence assessment
- Periodic insight reporting cadence (recommended: monthly with ad-hoc deep dives)
- Alignment with Blinkit category taxonomy and MAC definitions

### 9.2 Out of Scope

- **Technical implementation** — Architecture, model selection, infrastructure, pipelines, APIs, and deployment
- **Real-time personalization or in-app recommendation serving** — This project informs those systems; it does not operate them
- **Quantitative analytics platform build** — Warehouse design, event tracking, A/B test infrastructure
- **Direct intervention execution** — Campaign launches, UX changes, pricing updates (downstream teams act on insights)
- **Competitive intelligence beyond user-voice mentions** — No proprietary scraping of competitor apps or pricing systems
- **Paid social/listening tools** — Unless explicitly added later; initial scope is the four defined sources
- **Legal/compliance review of data collection** — Assumed to be handled separately; this document assumes compliant access to listed sources

### 9.3 Assumptions

- Blinkit will provide or approve access to Google Form response data and internal category taxonomy.
- Public review and Reddit data is accessible within organizational policy.
- The north-star metric (new category purchase rate among MAC) can be measured internally by Blinkit's analytics team; this engine provides the *why* behind movement in that metric.
- "Category" definitions are stable enough for month-over-month comparison, with a documented mapping for taxonomy changes.

### 9.4 Constraints

- Qualitative sources reflect **stated** preferences and ** vocal** users; silent majority behavior requires triangulation with internal quantitative data (owned by Blinkit, not this project).
- Sentiment and theme analysis must account for **recency** (post-rebrand, post-UI change, post-expansion to new cities).
- Regional and language diversity in India means English-dominant sources may underrepresent certain segments.

### 9.5 Dependencies

| Dependency | Owner | Impact if Missing |
|------------|-------|-------------------|
| Blinkit category taxonomy | Merchandising / Data | Cannot define "new category" consistently |
| MAC and order history definitions | Analytics | Cannot link insights to north-star metric |
| Google Form survey design & distribution | Research / Growth | Limits first-party structured input |
| Stakeholder review cadence | Product Leadership | Insights may not convert to action |

---

## 10. Risks & Mitigations (Business-Level)

| Risk | Mitigation |
|------|------------|
| Insights are interesting but not actionable | Tie every theme to a specific segment, category, and proposed business action |
| Over-indexing on negative reviews | Balance with positive discovery stories; weight by frequency and segment relevance |
| Sample bias from Reddit and app reviews | Explicitly label representativeness limits; seek triangulation with form data |
| Category taxonomy changes break trend analysis | Document taxonomy versioning; maintain mapping tables |
| Insight fatigue | Prioritize ruthlessly; lead with top 5 opportunities per report |
| Conflicting signals across sources | Report contradictions transparently; investigate rather than averaging away |

---

## 11. Phased Business Approach (Non-Technical)

### Phase 1 — Baseline Understanding (Weeks 1–4)

- Ingest and categorize historical feedback from all four sources
- Produce initial answers to the seven strategic questions
- Establish theme taxonomy and segment hypotheses
- Deliver first **Discovery Intelligence Report**

### Phase 2 — Deep Dives (Weeks 5–8)

- Select top 3 barriers and top 3 opportunities from Phase 1
- Produce root-cause briefs with cross-source evidence
- Refine segment exploration profiles

### Phase 3 — Ongoing Intelligence (Month 3+)

- Monthly report cadence with trend detection (new themes, escalating frustrations)
- Quarterly opportunity backlog refresh
- Ad-hoc deep dives triggered by metric shifts or product launches

---

## 12. Open Questions for Stakeholder Alignment

The following decisions require input from Blinkit business owners before insight generation begins:

1. **Lookback window for "new category"** — 3, 6, or 12 months?
2. **Category granularity** — L1 (e.g., Snacks) vs. L2/L3 (e.g., Chips vs. Premium Chips)?
3. **Geographic scope** — Pan-India vs. priority cities first?
4. **Google Form audience** — Existing MAC sample, churned users, or non-users?
5. **Language scope** — English-only initially or include Hindi and regional language sources?
6. **Competitive framing** — How explicitly should Instamart, Zepto, and others be referenced in outputs?
7. **Actionability SLA** — How quickly must insights reach decision-makers after data collection?

---

## 13. Glossary

| Term | Definition |
|------|------------|
| **MAC** | Monthly Active Customer — unique customer with ≥1 delivered order in a calendar month |
| **Category exploration** | Purchasing from a category not bought in the prior N-month lookback window |
| **Discovery** | The process by which a user becomes aware of and considers a product or category they have not habitually purchased |
| **Repeat purchase loop** | Behavioral cycle of reordering the same SKUs/categories due to habit, satisfaction, or convenience |
| **Segment** | A group of users sharing behavioral or psychographic traits relevant to exploration likelihood |
| **Root cause** | Systemic driver (not surface symptom) that explains why a barrier persists across multiple user contexts |
| **Triangulation** | Validating a finding across multiple independent data sources |

---

## 14. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | July 2026 | — | Initial problem statement and scope definition |

---

*This document defines the business problem and project boundaries for the Blinkit AI Product Discovery Engine. Implementation details—including data pipelines, models, tooling, and integration—are intentionally excluded and will be addressed in separate technical specification documents.*
