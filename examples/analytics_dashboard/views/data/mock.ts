export interface RevenuePoint {
  month: string;
  revenue: number;
  orders: number;
}

export const revenueSeries: RevenuePoint[] = [
  { month: "Jan", revenue: 32000, orders: 240 },
  { month: "Feb", revenue: 35500, orders: 265 },
  { month: "Mar", revenue: 38200, orders: 280 },
  { month: "Apr", revenue: 36800, orders: 270 },
  { month: "May", revenue: 41200, orders: 305 },
  { month: "Jun", revenue: 44600, orders: 330 },
  { month: "Jul", revenue: 43100, orders: 318 },
  { month: "Aug", revenue: 47900, orders: 350 },
  { month: "Sep", revenue: 49600, orders: 365 },
  { month: "Oct", revenue: 52300, orders: 388 },
  { month: "Nov", revenue: 55800, orders: 410 },
  { month: "Dec", revenue: 61400, orders: 452 },
];

export interface CategorySlice {
  name: string;
  value: number;
}

export const categoryBreakdown: CategorySlice[] = [
  { name: "Electronics", value: 38 },
  { name: "Apparel", value: 27 },
  { name: "Home & Garden", value: 18 },
  { name: "Sports", value: 11 },
  { name: "Other", value: 6 },
];

export interface Transaction {
  id: string;
  customer: string;
  category: string;
  amount: number;
  status: "completed" | "pending" | "refunded";
  date: string;
}

export const recentTransactions: Transaction[] = [
  { id: "TXN-1042", customer: "Acme Corp", category: "Electronics", amount: 1240.0, status: "completed", date: "2026-06-09" },
  { id: "TXN-1041", customer: "Globex Inc", category: "Apparel", amount: 89.5, status: "completed", date: "2026-06-09" },
  { id: "TXN-1040", customer: "Initech", category: "Home & Garden", amount: 312.75, status: "pending", date: "2026-06-08" },
  { id: "TXN-1039", customer: "Umbrella LLC", category: "Sports", amount: 58.2, status: "completed", date: "2026-06-08" },
  { id: "TXN-1038", customer: "Soylent Co", category: "Electronics", amount: 2199.0, status: "refunded", date: "2026-06-07" },
  { id: "TXN-1037", customer: "Hooli", category: "Apparel", amount: 145.0, status: "completed", date: "2026-06-07" },
  { id: "TXN-1036", customer: "Vehement Capital", category: "Other", amount: 75.99, status: "completed", date: "2026-06-06" },
  { id: "TXN-1035", customer: "Massive Dynamic", category: "Home & Garden", amount: 410.3, status: "pending", date: "2026-06-06" },
];

export interface TopProduct {
  name: string;
  unitsSold: number;
  revenue: number;
}

export const topProducts: TopProduct[] = [
  { name: "Wireless Earbuds Pro", unitsSold: 1240, revenue: 86800 },
  { name: "Smart Fitness Watch", unitsSold: 890, revenue: 71200 },
  { name: "Organic Cotton Hoodie", unitsSold: 2310, revenue: 57750 },
  { name: "Stainless Steel Water Bottle", unitsSold: 3420, revenue: 41040 },
  { name: "Ergonomic Desk Lamp", unitsSold: 760, revenue: 30400 },
];

export interface Goal {
  label: string;
  value: number;
  target: number;
  variant?: "default" | "success" | "warning" | "error";
}

export const goals: Goal[] = [
  { label: "Monthly revenue ($486.2K / $600K)", value: 486200, target: 600000 },
  { label: "New users (8,942 / 10,000)", value: 8942, target: 10000, variant: "success" },
  { label: "Conversion rate (3.8% / 5%)", value: 3.8, target: 5, variant: "warning" },
];

export const engagementMetrics: Goal[] = [
  { label: "DAU / MAU ratio (62 / 100)", value: 62, target: 100, variant: "success" },
  { label: "30-day retention (48 / 100)", value: 48, target: 100 },
  { label: "NPS score (41 / 100)", value: 41, target: 100, variant: "warning" },
];

export interface ActivityItem {
  title: string;
  description?: string;
  timestamp?: string;
  status?: "complete" | "current" | "upcoming";
}

export const activityFeed: ActivityItem[] = [
  {
    title: "Weekly report generated",
    description: "Sales and usage summary sent to the team",
    timestamp: "2026-06-10",
    status: "complete",
  },
  {
    title: "New cohort onboarded",
    description: "214 new users signed up via the partner campaign",
    timestamp: "2026-06-08",
    status: "complete",
  },
  {
    title: "Category breakdown refreshed",
    description: "Recalculated from the latest order data",
    timestamp: "2026-06-07",
    status: "complete",
  },
  {
    title: "Quarterly review",
    description: "Scheduled with the leadership team",
    timestamp: "2026-06-15",
    status: "current",
  },
  {
    title: "Q3 planning",
    description: "Roadmap discussion for next quarter",
    timestamp: "2026-07-01",
    status: "upcoming",
  },
];

export interface Kpi {
  label: string;
  value: string;
  delta: string;
  trend: "up" | "down" | "flat";
  sparkline: number[];
}

export const kpis: Record<"revenue" | "activeUsers" | "conversionRate" | "avgOrderValue", Kpi> = {
  revenue: {
    label: "Revenue",
    value: "$486,200",
    delta: "+12.4%",
    trend: "up",
    sparkline: [32, 35.5, 38.2, 36.8, 41.2, 44.6, 43.1, 47.9, 49.6, 52.3, 55.8, 61.4],
  },
  activeUsers: {
    label: "Active Users",
    value: "8,942",
    delta: "+4.1%",
    trend: "up",
    sparkline: [6.8, 7.0, 7.1, 7.3, 7.6, 7.8, 7.9, 8.1, 8.3, 8.5, 8.7, 8.9],
  },
  conversionRate: {
    label: "Conversion Rate",
    value: "3.8%",
    delta: "-0.3%",
    trend: "down",
    sparkline: [4.3, 4.2, 4.2, 4.1, 4.0, 4.0, 3.9, 3.9, 3.9, 3.8, 3.8, 3.8],
  },
  avgOrderValue: {
    label: "Avg Order Value",
    value: "$152",
    delta: "+1.2%",
    trend: "up",
    sparkline: [148, 149, 150, 149, 150, 151, 150, 151, 152, 151, 152, 152],
  },
};
