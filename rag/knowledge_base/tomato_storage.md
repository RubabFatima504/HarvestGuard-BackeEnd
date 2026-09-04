# Tomato Storage: Packing, Handling, and Shelf Life

This document summarizes Pakistani research on tomato post-harvest handling and storage, to guide HarvestGuard's advisory logic for this highly perishable vegetable crop.

## Tomato's Risk Profile: Between Mango and Potato

Tomato decays faster than potato (a dormant tuber) but generally slower than mango at equivalent ambient heat, consistent with it being a climacteric fruit with a moderate respiration rate. Where mango can drop to unsellable within a day or two of extreme heat exposure, and potato can hold for months even at ambient temperature, tomato's realistic ambient shelf life sits in the range of **one to two weeks** — meaning it needs faster action than potato, but has somewhat more buffer than mango.

## What Determines Shelf Life: Packing Matters as Much as Temperature

A University of the Punjab (Lahore) study tested three common Pakistani packing materials — wooden crates, corrugated cardboard boxes, and nylon mesh bags — at room temperature (20°C) over a 12-day period, and found meaningful differences in outcome:

- **Corrugated cardboard boxes performed best**, giving roughly **10 days** of usable shelf life before mechanical/fungal damage became significant. The soft cushioning and vibration resistance of cardboard reduced physical bruising during handling and transport.
- **Open containers and nylon mesh bags performed worst**, showing accelerated fruit decay due to faster fungal sporulation and mycelial spread — the open structure that seems like it should help with airflow actually increases exposure to contamination and physical damage.
- **Wooden crates performed reasonably** but were prone to physical damage from improperly fixed wooden pieces and nails, an entirely preventable handling issue rather than an inherent limitation of the material.

Without proper packaging — for example, tomatoes carried loose in a gunny bag, which remains common informal practice in Pakistani markets — shelf life drops to roughly **7 days** before unacceptable decay and weight loss.

## The Scale of Loss in Pakistan

Pakistani tomato supply chains report **up to 30% shipment losses** attributable specifically to improper packing material and physical damage — a loss point that is highly preventable through packing choice alone, independent of any cold chain investment. Losses also scale sharply with transport distance: **7-9% loss for farm-to-market distances under 50km**, rising to **19-27% loss for distances over 800km**. This distance effect compounds whatever packing-related losses already exist, meaning a poorly-packed long-distance shipment faces the worst of both risk factors simultaneously.

More broadly, Pakistani produce (tomatoes specifically highlighted) suffers **30-50% postharvest losses**, compared to under 15% in developed countries — a gap attributed heavily to Pakistan's energy/infrastructure constraints limiting cold-chain availability, consistent with the broader cold-chain coverage gap described in `cold_chain_pakistan.md`.

## Why Domestic Production Still Falls Short of Demand

Despite meaningful domestic tomato production growth, Pakistan still imports tomatoes from neighboring countries (particularly India) during several months of the year to meet demand. This context matters for market-timing logic: import availability can suppress domestic tomato prices during off-peak local production windows, an additional variable beyond simple local supply/demand that mango and rice don't face in the same way.

## Practical Takeaways for HarvestGuard's Advisory Logic

- **Packing material recommendation is a distinct, low-cost lever for tomato** that doesn't exist in the same way for mango or rice — advisory output for tomato batches should specifically flag packing quality (cardboard > wooden crate > mesh bag/loose) as an actionable, cheap intervention.
- **Distance-based loss scaling (7-9% under 50km vs 19-27% over 800km) means tomato is a poor candidate for long-distance "wait for a better market" recommendations** compared to more robust crops — the transport loss itself can erode most of any price advantage from a distant market.
- **Tomato's shelf life (7-17 days depending on handling) sits in a useful middle ground for HarvestGuard's scenario modeling** — long enough that a 1-2 day storage/transport decision window is meaningful (unlike mango's near-immediate urgency), but short enough that "wait it out" is rarely the right call (unlike potato).
- **Import competition should be treated as a market-context factor**, not just a spoilage/storage one, when the advisory agent reasons about expected sale price for tomato specifically.

## Sources

- Saeed, A.F.U.H., Khan, S.N., Sarwar, A., Tahira, J.J. (2010). "Effect of packing materials on storage of tomato." *Mycopath*, 8(2): 85-89. Institute of Plant Pathology, University of the Punjab, Lahore.
- Firdous, N. (2021). "Post-harvest losses in different fresh produces and vegetables in Pakistan with particular focus on tomatoes." *Journal of Horticulture and Postharvest Research*, 4(1): 71-86.
