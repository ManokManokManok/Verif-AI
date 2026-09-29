# Verif-AI Analytics Page: Redesign Spec

Audience: developer/Copilot implementing the redesign of the logged-in **Your Verif-AI Journey** page (React frontend, Django API, MongoDB `analysis_results`).
Scope: redesign of the three sections (Your Checks, Your Activity, Community). The safety summary header, totals, and plain-language AI summary stay unchanged.

## Global design rules

- **Goal of every section:** answer a user question and end with a next step (usually a link to Guidance Mode), not just display numbers.
- **Cards:** one consistent card style (rounded, subtle border, same padding). Section title + one-line question as subtitle.
- **Risk colors (tokens):** green = Not Scam / low, amber = suspicious / medium, red = high risk (`scam_score >= 70`). Never rely on color alone; add icon or text label.
- **Charts:** use the chart library already in the project (Recharts if none). All charts need tooltips, axis labels, and an accessible text summary (`aria-label`).
- **States:** every component needs loading (skeleton), empty (friendly message plus "Analyze a message" button), and low-data (fewer than 3 checks: show "early signal" tag) states.
- **Dates:** group by month/day/weekday in the user's local timezone (client-side or timezone param), not UTC.
- **Mobile:** all two-column layouts stack; carousels become swipeable; tab bars become horizontally scrollable.
- **Privacy:** never display message text. Community data is aggregate only.

=======

## Section 1: Your Checks ("What are you running into?")

**Purpose:** show which scam patterns the user meets most and what to do about them.

### 1.1 Top pattern hero (top of section)
- Full-width highlight card: category name, check count, share of scam checks, trend chip (Rising / Easing / Steady).
- Small line **sparkline** of that category's monthly count (last 6 months).
- Data: `scam_type`, `is_scam`, `created_at` (existing category insight plus monthly bucketing per category).
- Primary button: **"Ask Guidance about this"** opens Guidance Mode with the category preloaded as context.

### 1.2 Pattern explorer (master-detail, desktop two-column)
- **Left: ranked list (max 3, keep as is).** Each row: rank, category, count/share, horizontal meter bar, trend arrow (up = rising, down = easing, flat = steady). Whole row is clickable and shows a selected state.
- **Right: detail panel for the selected pattern.**
  - Stat tiles: share, average scam score, high-risk rate, average type confidence (existing).
  - Movement: "last 30 days vs previous 30 days" mini paired bars (existing counts).
  - **Common red flags:** chips of the most frequent markers for this category. Data: `key_markers` (NEW aggregation; confirm field format).
  - Explanation and safe next step (existing text).
  - Buttons: "Ask Guidance" and "See a checklist" (optional).
- Replace arrows/dots with clickable rows on desktop. On mobile, the detail panel becomes a **swipeable carousel** with dots, one card per pattern.

### 1.3 Recent checks (bottom)
- Layout: short intro on left; on right a **vertical timeline list** of up to 4 grouped rows.
- Each row: category badge, count, latest date, highest score as a colored pill (green/amber/red).
- Row click: opens the most recent result for that group using `ref_id` (the message is not shown here) or "Send to Guidance".
- Data: latest 8 records, grouped by category (existing).

=======

## Section 2: Your Activity ("Is your situation changing?")  [main overhaul]

**Purpose:** show whether the user's exposure is improving or worsening and when scams reach them. This section also serves as the "time in Verif-AI" timeline.

### 2.1 Status row (3 KPI tiles, replaces the single big percentage)
1. **High-risk rate:** large %, with delta chip vs previous 30 days (green down arrow = better, red up arrow = worse).
2. **Trend verdict:** one-line label (Improving / Steady / Rising) plus the existing comparison sentence.
3. **Days since last high-risk message** (or "Checks this month" if none).
- Data: `is_scam`, `scam_score >= 70`, `created_at` (all existing).

### 2.2 Main visual: tabbed chart area (one chart visible at a time, avoids clutter)
Tab bar: **Monthly | Calendar | Weekday**

- **Monthly (default): stacked bar chart**, last 6 active months. X = month, stacked segments = Not Scam (green), Scam under 70 (amber), High risk (red). Tooltip shows counts per segment.
  Data: `created_at`, `is_scam`, `scam_score`.
- **Calendar: heatmap**, last 12 weeks, GitHub-style grid. Cell intensity = checks that day; red outline/dot if a high-risk result occurred. Click a cell to list that day's grouped results.
  Data: `created_at`, `scam_score`, `is_scam`.
- **Weekday: bar chart**, 7 bars (Mon to Sun) showing scam checks per weekday, with insight sentence ("Most scams reach you on Fridays").
  Data: `created_at`, `is_scam`.

### 2.3 Risk mix bar (below chart)
- Single **segmented horizontal bar**: share of checks that were Not Scam / Suspicious (under 70) / High risk. Legend with counts.
- Data: `is_scam`, `scam_score`.

### 2.4 Insight line
- One auto-generated sentence under the chart based on the active tab (rule-based, no AI call), e.g. "Your high-risk checks dropped from 4 to 1 compared with the previous 30 days."
- Small-sample rule: fewer than 5 checks in a window shows "Early signal."

=======

## Section 3: Community ("What is happening around you?")

**Purpose:** put the user's experience in context and warn about rising scams. Aggregate, anonymized, authenticated users only (existing rule).

### 3.1 Header
- Community flagged rate (large %) plus short summary sentence; small badge "Based on N users' checks" (N = count of distinct `user_id`, existing community query).

### 3.2 You vs Community (replaces comparison strip)
- **Grouped horizontal bar chart**: top 5 categories, two bars per category (You vs Community, as % share of scam checks). Categories the user has never seen show a 0 bar.
- Insight sentence: "You see phishing 2x more than the community average."
- Data: user `scam_type` shares (existing) plus community `scam_type` shares (existing).

### 3.3 Rising scams (new list)
- Ranked list of up to 5 categories by month-over-month change: category, % change badge with arrow, mini sparkline.
- Each row has a "Learn more" link that opens Guidance with that category.
- Data: community `scam_type` counts per month (backend has month-over-month insight; per-category monthly series is NEW).

### 3.4 Advice carousel
- Card carousel, auto-rotate every ~8s, pause on hover/touch, arrows and dots, swipeable on mobile.
- Order: advice for the community's top rising category first, then the user's top category, then seasonal message (existing), then general tips.
- Each card: tip text, category tag, "Ask Guidance" button.

### 3.5 Charts (bottom, side by side on desktop, stacked on mobile)
- **Left: ranked horizontal bar chart** of community scam types. Highlight (accent color) the categories the user also has. Toggle: **This month | All time**.
- **Right: line chart with area fill**, monthly confirmed scams. Optional category dropdown (top 5 plus "All") to filter the line.
- Data: `scam_type`, `is_scam`, `created_at`, `user_id` non-empty, `user_deleted` false (existing; category-filtered monthly series is NEW).

### 3.6 Privacy safeguard
- Hide any category or month bucket with fewer than 5 distinct users (show "Not enough data") so individuals cannot be identified. Add a footnote: "Community data is anonymized and aggregated."

=======

## Backend work summary

| Item | Status |
| --- | --- |
| User category insights, 30-day comparisons, monthly counts | Existing |
| Community rate, top categories, monthly confirmed scams, seasonal advice | Existing |
| `key_markers` aggregation per category (user and community) | NEW |
| Monthly counts split by high-risk / scam / not scam | NEW (derive from existing fields) |
| Daily counts (calendar heatmap) and weekday counts | NEW (derive from `created_at`) |
| Community per-category monthly series and MoM % change | NEW |
| Distinct-user counts per category/month (privacy threshold) | NEW |
| Guidance deep link with preloaded category context | NEW (frontend and Guidance route) |