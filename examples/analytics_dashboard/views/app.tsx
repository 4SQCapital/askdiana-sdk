import React from "react";
import {
  App,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Stat,
  Grid,
  DataTable,
  Badge,
  Progress,
  Timeline,
  Alert,
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
  type DataTableColumn,
  type InitData,
} from "askdiana-ui";
import { RevenueChart } from "./components/RevenueChart";
import { CategoryChart } from "./components/CategoryChart";
import { MiniChart } from "./components/MiniChart";
import {
  kpis,
  recentTransactions,
  topProducts,
  goals,
  engagementMetrics,
  activityFeed,
  type Transaction,
  type TopProduct,
} from "./data/mock";

const STATUS_VARIANT: Record<Transaction["status"], "success" | "warning" | "error"> = {
  completed: "success",
  pending: "warning",
  refunded: "error",
};

const transactionColumns: DataTableColumn<Transaction>[] = [
  { key: "id", header: "Transaction", sortable: true },
  { key: "customer", header: "Customer", sortable: true },
  { key: "category", header: "Category", sortable: true },
  {
    key: "amount",
    header: "Amount",
    align: "right",
    sortable: true,
    render: (row) => `$${row.amount.toFixed(2)}`,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => <Badge variant={STATUS_VARIANT[row.status]} content={row.status} />,
  },
  { key: "date", header: "Date", sortable: true },
];

const productColumns: DataTableColumn<TopProduct>[] = [
  { key: "name", header: "Product", sortable: true },
  {
    key: "unitsSold",
    header: "Units sold",
    align: "right",
    sortable: true,
    render: (row) => row.unitsSold.toLocaleString(),
  },
  {
    key: "revenue",
    header: "Revenue",
    align: "right",
    sortable: true,
    render: (row) => `$${row.revenue.toLocaleString()}`,
  },
];

const FAQS = [
  {
    question: "How is revenue calculated?",
    answer: "Revenue is the sum of completed order totals, before refunds and taxes.",
  },
  {
    question: "How often is data refreshed?",
    answer: "The dashboard pulls a fresh snapshot once a day at 06:00 UTC.",
  },
  {
    question: "Can I export this data?",
    answer: "Yes — the recent transactions and top products tables can be sorted by any column, then copied or exported from your browser.",
  },
];

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      {children}
    </div>
  );
}

export default function AnalyticsApp({}: { init: InitData; installId: string }) {
  return (
    <App bare>
      <div className="space-y-6 p-4">
        <div>
          <h1 className="text-lg font-semibold">Analytics Dashboard</h1>
          <p className="text-sm text-muted-foreground">Sales and usage overview</p>
        </div>

        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="sales">Sales</TabsTrigger>
            <TabsTrigger value="users">Users</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4 space-y-6">
            <Grid columns={2} gap={3}>
              {Object.values(kpis).map((kpi) => (
                <Stat key={kpi.label} label={kpi.label} value={kpi.value} delta={kpi.delta} trend={kpi.trend}>
                  <div className="ml-auto">
                    <MiniChart data={kpi.sparkline} />
                  </div>
                </Stat>
              ))}
            </Grid>

            <Section title="Goals this month">
              <div className="space-y-3 rounded-md border border-border bg-card p-3">
                {goals.map((goal) => (
                  <Progress
                    key={goal.label}
                    label={goal.label}
                    value={goal.value}
                    max={goal.target}
                    variant={goal.variant}
                  />
                ))}
              </div>
            </Section>

            <Section title="Revenue trend">
              <RevenueChart />
            </Section>

            <Section title="Category breakdown">
              <CategoryChart />
            </Section>
          </TabsContent>

          <TabsContent value="sales" className="mt-4 space-y-6">
            <Alert variant="info">Showing data for the last 30 days, refreshed daily at 06:00 UTC.</Alert>

            <Section title="Revenue trend">
              <RevenueChart />
            </Section>

            <Section title="Top products">
              <DataTable columns={productColumns} data={topProducts} />
            </Section>

            <Section title="Recent transactions">
              <DataTable columns={transactionColumns} data={recentTransactions} />
            </Section>
          </TabsContent>

          <TabsContent value="users" className="mt-4 space-y-6">
            <Stat
              label={kpis.activeUsers.label}
              value={kpis.activeUsers.value}
              delta={kpis.activeUsers.delta}
              trend={kpis.activeUsers.trend}
            />

            <Section title="Engagement">
              <div className="space-y-3 rounded-md border border-border bg-card p-3">
                {engagementMetrics.map((metric) => (
                  <Progress
                    key={metric.label}
                    label={metric.label}
                    value={metric.value}
                    max={metric.target}
                    variant={metric.variant}
                  />
                ))}
              </div>
            </Section>

            <Section title="Usage by category">
              <CategoryChart />
            </Section>
          </TabsContent>

          <TabsContent value="activity" className="mt-4 space-y-6">
            <Section title="Recent activity">
              <Timeline items={activityFeed} />
            </Section>

            <Section title="Frequently asked questions">
              <Accordion type="single" collapsible className="rounded-md border border-border px-3">
                {FAQS.map((faq) => (
                  <AccordionItem key={faq.question} value={faq.question}>
                    <AccordionTrigger>{faq.question}</AccordionTrigger>
                    <AccordionContent>{faq.answer}</AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </Section>
          </TabsContent>
        </Tabs>
      </div>
    </App>
  );
}
