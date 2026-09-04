# Cold Chain Infrastructure in Pakistan: Current State

This document summarizes the current availability and gaps in cold storage and cold-chain infrastructure across Pakistan, to help HarvestGuard's advisory logic set realistic expectations about what storage/transport options are actually accessible to farmers in different regions.

## The Capacity Gap

Pakistan's total cold storage capacity is estimated at under 1 million tons, against annual fruit and vegetable production of 13-14 million tons. That works out to **coverage of less than 8% of total production** — meaning the overwhelming majority of Pakistan's perishable harvest has no access to cold storage at any point in its journey from farm to consumer. This gap is a major reason why post-harvest loss percentages for mango and other fruit remain so high (see `pakistan_post_harvest_losses.md`).

## Uneven and Commodity-Specific Infrastructure

The limited cold storage that does exist is not evenly distributed or general-purpose. Much of the existing infrastructure is commodity-specific — built and optimized for potatoes in particular — rather than designed for the temperature and humidity requirements of fruits like mango, which need different (typically higher) storage temperatures and humidity levels than root vegetables. This means a region might show cold storage capacity on paper while having effectively none that's actually usable for a mango or citrus harvest.

There is also very little cold storage infrastructure at ports and airports, the exit points for Pakistan's fruit exports. This has historically forced exporters to rely almost entirely on refrigerated trucks (reefers) for the final leg to Karachi Port or the airport, with limited buffer capacity if a shipment is delayed.

## What's Changing (as of 2025-2026)

PHDEC (Pakistan Horticulture Development and Export Company), the government body responsible for horticulture export growth, has flagged post-harvest losses as the single biggest blocker to export growth and has made cold chain development a stated priority. As of its most recent 3-year plan (approved August 2025), PHDEC has committed to:

- Establishing cold chain storage facilities directly in production hubs (i.e., closer to where crops are actually grown, not just at ports).
- Building cargo-handling cold storage at key airports and seaports.
- Distributing over one million fruit-bagging kits to farmers as a low-cost, non-refrigerated way to protect fruit quality during handling.
- Targeting $2 billion in horticulture exports by 2028, which implicitly requires closing much of the current cold-chain gap.

These are stated commitments and projects in progress rather than completed infrastructure — as of now, the underlying 8% coverage gap described above is still the operating reality for most farmers.

## Regional Notes

Cold storage development in Pakistan tends to cluster around specific production zones for specific crops: Sindh's Mirpurkhas and Tando Allahyar areas for mango, Sargodha and Bhalwal for citrus, Swat and Mansehra for apples. A grower or cooperative outside these specific clusters is statistically far less likely to have practical access to cold storage, even if national-level statistics suggest some capacity exists.

## Practical Takeaways for Storage/Transport Decisions

- **Assume cold storage is not available by default.** Given <8% national coverage, the safer planning assumption for any given farmer or batch is that cold storage is not accessible unless it is specifically confirmed for that location (which is why HarvestGuard's market/location data tracks `cold_storage_available` per mandi rather than assuming it everywhere).
- **Even where cold storage exists, it may not suit the crop.** Potato-optimized facilities are not necessarily appropriate for mango or citrus without verification of temperature/humidity settings.
- **Non-refrigerated interventions matter more in Pakistan's current reality than they might in markets with better cold-chain coverage.** Fruit bagging, MAP-style packaging, minimizing time in open trucks during peak heat, and fast transport to the nearest usable market are often the only realistic levers available to most farmers today.
- **The situation is improving but slowly.** Advisory outputs shouldn't assume near-term infrastructure improvements will change a specific farmer's options within a single season.

## Sources

- Pakistan Business Council, "The Missing Link: Building Pakistan's Cold Chain" (pbc.org.pk/research/the-missing-link-building-pakistans-cold-chain)
- Business Recorder / The Nation, coverage of PHDEC board's 3-year horticulture export plan (approved August 18, 2025)
- Izhar Foster, "Cold Storage Demand in Pakistan: 2026 Market Outlook"
- PHDEC official website and September 2025 newsletter (phdec.gov.pk)
