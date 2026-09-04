# Potato Storage: Temperature and Shelf Life

This document summarizes research on potato storage behavior, with a focus on how temperature determines shelf life, to guide HarvestGuard's advisory logic for this crop.

## Why Potato Behaves Differently From Fruit Crops

Potato is fundamentally different from mango, tomato, or other fresh produce in HarvestGuard's crop list: it is a **dormant tuber**, not a ripening fruit. A harvested potato is in a resting physiological state and only begins actively deteriorating once dormancy breaks — sprouting, softening, and starch-to-sugar conversion accelerate rapidly after that point. This means potato's shelf life is far longer than mango's even under similarly warm conditions, and the key control variable is delaying dormancy break rather than slowing ripening.

## How Temperature Changes Storage Life

A controlled study on the Lady Rosetta potato variety, tested at three storage temperatures (5°C, 15°C, and 25°C), found a clear pattern:

- **At 5°C**, tuber dormancy was maintained for up to **126 days** — the longest storage life of the three temperatures tested. The trade-off is increased sugar accumulation and reduced starch content, which negatively affects processing quality (e.g., chip/fry color) — though this matters much less for potatoes headed to fresh consumption rather than processing.
- **At 15°C**, potatoes retained lower sugar content and better processing color than the 5°C batch, but showed increased enzymatic browning-related activity (polyphenol oxidase and peroxidase) as storage progressed. This is a reasonable middle-ground temperature for fresh-market (non-processing) potatoes.
- **At 25°C**, storage life was significantly reduced: dormancy broke by around **day 84**, after which starch degradation and sugar accumulation accelerated sharply, alongside earlier sprouting.

The practical takeaway: potato's storage life at typical Pakistani ambient summer temperatures (often 25°C+) is still measured in **months (around 2-3), not days or weeks** — a dramatically different risk profile than mango, which can spoil within days at similar heat.

## Pakistan-Specific Loss Data

A postharvest loss survey in Swat district, Khyber Pakhtunkhwa, found **10.08% of potato loss occurring during storage**, and a further **3.98% lost during transport**. Compared to mango's post-harvest losses (frequently cited at 30-40% in Pakistan), potato's overall loss rate is meaningfully lower — consistent with it being a more storage-forgiving crop. The reported causes were consistent with general Pakistani post-harvest infrastructure gaps: inadequate storage facilities and poor packaging materials, rather than any inherent fragility of the crop itself.

## Punjab Production Context

Potato is grown across Punjab, with the largest producing districts being Okara, Sahiwal, Kasur, Sialkot, Sheikhupura, Narowal, Lahore, Pakpattan, Jhang, Toba Tek Singh, and Gujranwala. Common varieties fall into two broad groups: red-skinned (Desiree, Cardinal, Raja, Synphonia, Barna) and white-skinned (Santana, Santé, Diamond). Storage temperature research is not always variety-specific in the available literature, so the temperature/duration figures above should be treated as representative rather than exact for every Pakistani variety.

## Practical Takeaways for HarvestGuard's Advisory Logic

- **Potato's decay curve should be modeled as far slower than mango or tomato.** A batch of potatoes at ambient heat still has weeks to months of usable window, not days — advisory urgency language appropriate for mango would be badly miscalibrated if applied to potato.
- **Cold storage still meaningfully extends life (84 days → 126 days, roughly 1.5x)**, but the absolute stakes of a delay are much lower than for mango, where the equivalent temperature gap can mean the difference between a sellable batch and a total loss within a single day.
- **Storage duration matters more than transport speed for potato**, the reverse of mango's priority ordering (see `mango_handling_best_practices.md`, where transport heat exposure was the dominant risk factor). This should shape which risk factors HarvestGuard's spoilage agent weights most heavily per crop.
- **Pakistan's lower relative loss rate for potato (compared to mango) reflects the crop's forgiving storage physiology, not necessarily better infrastructure** — the same weak cold-chain and storage conditions exist for both crops, but potato tolerates them better.

## Sources

- Abbasi, K.S., Masud, T., Qayyum, A., Khan, S.U., Abbas, S., Jenks, M.A. "Storage stability of potato variety Lady Rosetta under comparative temperature regimes." (Pakistani-authored research collaboration, PMAS-Arid Agriculture University Rawalpindi)
- "Quality Deterioration of Postharvest Fruits and Vegetables in Developing Country Pakistan: A Mini Overview" (2021), citing Swat district, KPK postharvest loss survey data
