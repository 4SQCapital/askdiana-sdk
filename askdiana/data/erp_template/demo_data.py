"""Seeded sample data in the vendor's own JSON shape.

Demo mode maps these raw records through the pack, the same way as live data. Replace the
generator with records that look exactly like the vendor's API response (field names, nesting, dates).
"""

from __future__ import annotations

import random
from datetime import date, timedelta

SEED = 42
TODAY = date(2026, 7, 8)
RECORD_COUNT = 40
STATUSES = ["Open", "Closed", "Draft"]
NAMES = ["Acme Corp", "Globex", "Initech", "Umbrella", "Stark", "Wayne", "Wonka", "Hooli"]


def generate() -> dict[str, list[dict]]:
    rng = random.Random(SEED)
    records = [{
        "id": str(1000 + i),
        "name": f"{rng.choice(NAMES)} #{i + 1}",
        "status": rng.choice(STATUSES),
        "amount": rng.randint(500, 50_000),
        "date": (TODAY - timedelta(days=rng.randint(0, 365))).isoformat(),
    } for i in range(RECORD_COUNT)]
    return {"records": records}
