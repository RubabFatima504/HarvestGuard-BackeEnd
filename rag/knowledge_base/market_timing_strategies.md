# Market Timing Strategies: Mango Price Patterns

This document summarizes observed seasonal price patterns for Chaunsa mango in Punjab, drawn directly from AMIS Punjab wholesale price data collected across the 2026 season (early July through late August), rather than from general theory. This is the one dataset in HarvestGuard's knowledge base built from primary, self-collected market observation rather than published literature.

## What the Data Shows: Prices Rose Through the Season, Not Fell

Conventional expectation is that prices are highest early in a harvest season (low supply) and fall as the season reaches peak volume, before rising again as the season winds down. **The 2026 Chaunsa data does not follow this pattern.** Tracking the Fair Quality Price (FQP) at Lahore mandi across the season:

| Date | Lahore FQP (Rs/quintal) |
|---|---|
| 5 July | 24,100 |
| 8-9 July | 25,200 |
| 10 July | 26,100 |
| 1 August | 27,750 |
| 2-5 August | 33,750-34,750 |
| 23 August | ~25,000 (mixed, high variance) |

Prices climbed steadily and then jumped sharply in early August — a roughly 44% increase in FQP between 5 July and 5 August — rather than declining into what should be peak season. This appears consistent with 2026-specific supply conditions: industry reporting from the same period noted that Pakistan's mango crop outlook was revised down 20-30% compared to the prior season due to weather-related disruption to flowering and fruit set. A smaller-than-usual crop this season likely kept supply tight even during what is normally the peak arrival period, pushing prices up rather than down.

**The takeaway for advisory logic is not "prices always rise in August"** — that would be over-fitting to one season's weather anomaly. The takeaway is that **seasonal price assumptions should be treated as defaults to be overridden by current-season signals**, not fixed rules. HarvestGuard's live AMIS price fetches should always be weighted more heavily than any static seasonal-pattern assumption baked into advisory logic.

## Regional Price Variation Is Significant

Not all markets moved together. Lahore's FQP roughly doubled its early-July premium over the season, while Sahiwal's FQP stayed comparatively flat (around Rs 27,500-28,000/quintal) across the same July-August window. This means a farmer near Sahiwal deciding "should I wait for a better price" would have seen a very different answer than a farmer near Lahore, even though both are Punjab mandis trading the same crop in the same weeks.

Practical implication: **market timing advice needs to be market-specific, not just crop-specific.** A single "wait N days for better prices" recommendation that ignores which mandi a farmer is targeting risks being wrong in either direction.

## General Principles (Where Season-Specific Data Isn't Available)

Where live or recent AMIS data isn't available for a specific crop/market/date combination, these general post-harvest market principles remain reasonable defaults:

- **Early-season and late-season windows typically carry a price premium** over mid-season peak-supply periods, all else being equal — because there is less competing volume in the market at those times.
- **Weekday vs. weekend arrivals can affect same-day price**, since some mandis see reduced trading activity on Sundays (observed directly in this project's AMIS data collection, where Sunday price entries were frequently blank/unreported across multiple commodities).
- **A crop with a short shelf life (like Chaunsa) has less flexibility to "wait for a better price"** than a crop with a long shelf life (like properly-dried rice) — the spoilage curve constrains how long a farmer can realistically hold out, which should be weighed against any price-timing advice. A theoretically better price 10 days out is irrelevant if the crop won't survive 10 more days in available storage conditions.
- **Supply shocks (weather, crop outlook revisions) can override normal seasonal patterns entirely**, as seen in the 2026 data above — advisory logic should treat seasonal assumptions as a starting prior, not a guarantee.

## Practical Takeaways for HarvestGuard's Advisory Logic

- **Always prioritize live/recent AMIS price data over seasonal assumptions** when both are available for a given crop and market.
- **Do not generalize a single season's price trend into a permanent rule** — 2026's rising-price pattern for Chaunsa was likely driven by an unusual supply shortfall, not a structural feature of the market.
- **Cross-reference price-timing advice against the crop's shelf-life data** (see `mango_shelf_life.md`) before recommending a farmer hold out for better prices — the recommendation is only useful if the crop can physically survive the wait.
- **Where possible, give market-specific rather than province-wide price guidance**, since regional variation within Punjab alone can be substantial.

## Sources

- AMIS Punjab (amis.pk), Mango (Chounsa) commodity price data, collected 5-10 July 2026 and 1-5 August 2026 across ~30-60 Punjab mandis per date
- FreshPlaza, "Pakistan's mango export season begins with a tougher road to market" (2026), reporting PHDEC's 20-30% downward crop outlook revision
