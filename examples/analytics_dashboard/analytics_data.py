"""Mock analytics data shared by the chat service.

Mirrors the dataset used by the dashboard's React views
(``views/data/mock.ts``) so chat answers stay consistent with the charts.
"""

KPIS = {
    "revenue": {"label": "Revenue", "value": "$486,200", "delta": "+12.4%", "trend": "up"},
    "active_users": {"label": "Active Users", "value": "8,942", "delta": "+4.1%", "trend": "up"},
    "conversion_rate": {"label": "Conversion Rate", "value": "3.8%", "delta": "-0.3%", "trend": "down"},
    "avg_order_value": {"label": "Avg Order Value", "value": "$152", "delta": "+1.2%", "trend": "up"},
}

REVENUE_SERIES = [
    {"month": "Jan", "revenue": 32000, "orders": 240},
    {"month": "Feb", "revenue": 35500, "orders": 265},
    {"month": "Mar", "revenue": 38200, "orders": 280},
    {"month": "Apr", "revenue": 36800, "orders": 270},
    {"month": "May", "revenue": 41200, "orders": 305},
    {"month": "Jun", "revenue": 44600, "orders": 330},
    {"month": "Jul", "revenue": 43100, "orders": 318},
    {"month": "Aug", "revenue": 47900, "orders": 350},
    {"month": "Sep", "revenue": 49600, "orders": 365},
    {"month": "Oct", "revenue": 52300, "orders": 388},
    {"month": "Nov", "revenue": 55800, "orders": 410},
    {"month": "Dec", "revenue": 61400, "orders": 452},
]

CATEGORY_BREAKDOWN = [
    {"name": "Electronics", "value": 38},
    {"name": "Apparel", "value": 27},
    {"name": "Home & Garden", "value": 18},
    {"name": "Sports", "value": 11},
    {"name": "Other", "value": 6},
]

TOP_PRODUCTS = [
    {"name": "Wireless Earbuds Pro", "units_sold": 1240, "revenue": 86800},
    {"name": "Smart Fitness Watch", "units_sold": 890, "revenue": 71200},
    {"name": "Organic Cotton Hoodie", "units_sold": 2310, "revenue": 57750},
    {"name": "Stainless Steel Water Bottle", "units_sold": 3420, "revenue": 41040},
    {"name": "Ergonomic Desk Lamp", "units_sold": 760, "revenue": 30400},
]

GOALS = [
    {"label": "Monthly revenue", "value": 486200, "target": 600000, "unit": "$"},
    {"label": "New users", "value": 8942, "target": 10000, "unit": ""},
    {"label": "Conversion rate", "value": 3.8, "target": 5, "unit": "%"},
]

RECENT_TRANSACTIONS = [
    {"id": "TXN-1042", "customer": "Acme Corp", "category": "Electronics", "amount": 1240.0, "status": "completed", "date": "2026-06-09"},
    {"id": "TXN-1041", "customer": "Globex Inc", "category": "Apparel", "amount": 89.5, "status": "completed", "date": "2026-06-09"},
    {"id": "TXN-1040", "customer": "Initech", "category": "Home & Garden", "amount": 312.75, "status": "pending", "date": "2026-06-08"},
    {"id": "TXN-1039", "customer": "Umbrella LLC", "category": "Sports", "amount": 58.2, "status": "completed", "date": "2026-06-08"},
    {"id": "TXN-1038", "customer": "Soylent Co", "category": "Electronics", "amount": 2199.0, "status": "refunded", "date": "2026-06-07"},
    {"id": "TXN-1037", "customer": "Hooli", "category": "Apparel", "amount": 145.0, "status": "completed", "date": "2026-06-07"},
    {"id": "TXN-1036", "customer": "Vehement Capital", "category": "Other", "amount": 75.99, "status": "completed", "date": "2026-06-06"},
    {"id": "TXN-1035", "customer": "Massive Dynamic", "category": "Home & Garden", "amount": 410.3, "status": "pending", "date": "2026-06-06"},
]
