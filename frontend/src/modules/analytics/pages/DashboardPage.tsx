import { Button } from "../../../shared/components/ui/Button";
import { Card } from "../../../shared/components/ui/Card";

const kpis = [
  {
    label: "Net revenue",
    value: "EUR 128.4K",
    delta: "+12.6%",
    caption: "vs previous 30 days",
    tone: "primary" as const,
  },
  {
    label: "Inventory accuracy",
    value: "97.8%",
    delta: "+1.9%",
    caption: "tracked locations aligned",
    tone: "secondary" as const,
  },
  {
    label: "Purchase cycle",
    value: "4.2 days",
    delta: "-0.6 day",
    caption: "approval to receipt",
    tone: "highlight" as const,
  },
  {
    label: "Open exceptions",
    value: "18",
    delta: "-7",
    caption: "reconciliations pending",
    tone: "rainbow" as const,
  },
];

const revenuePoints = [
  [40, 218],
  [110, 196],
  [180, 204],
  [250, 168],
  [320, 150],
  [390, 112],
  [460, 124],
  [530, 94],
  [600, 78],
  [670, 56],
];

const forecastPoints = [
  [40, 226],
  [110, 210],
  [180, 188],
  [250, 162],
  [320, 142],
  [390, 118],
  [460, 102],
  [530, 86],
  [600, 72],
  [670, 62],
];

const channels = [
  { label: "Retail", value: "46%", width: "46%" },
  { label: "Wholesale", value: "28%", width: "28%" },
  { label: "Delivery", value: "18%", width: "18%" },
  { label: "Events", value: "8%", width: "8%" },
];

const activityItems = [
  {
    title: "Inventory movement reconciliation",
    time: "08:45",
    description: "Three high-value ingredients need review before end-of-day close.",
  },
  {
    title: "Import pipeline healthy",
    time: "09:10",
    description: "POS sales, invoices and stock movements arrived without parse failures.",
  },
  {
    title: "Purchase approvals",
    time: "09:32",
    description: "Two supplier invoices are waiting for finance confirmation.",
  },
];

const exceptionRows = [
  {
    unit: "Central Kitchen",
    area: "Stock Levels",
    issue: "Theoretical stock diverges by more than 4.5%",
    owner: "Operations",
    status: "Investigating",
  },
  {
    unit: "Riverside Cafe",
    area: "Imports",
    issue: "Manual review required for missing supplier reference",
    owner: "Procurement",
    status: "Queued",
  },
  {
    unit: "Airport Unit",
    area: "Finance",
    issue: "Source mapping pending for one imported revenue batch",
    owner: "Finance",
    status: "Open",
  },
];

function toPath(points: number[][]) {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"} ${point[0]} ${point[1]}`)
    .join(" ");
}

export function DashboardPage() {
  const revenuePath = toPath(revenuePoints);
  const forecastPath = toPath(forecastPoints);

  return (
    <section className="page-section">
      <div className="dashboard-hero">
        <Card
          tone="primary"
          eyebrow="Visual Foundation"
          className="hero-copy"
          hoverable
          title={
            <span className="hero-title">
              Dark premium styling for a practical internal dashboard.
            </span>
          }
          subtitle={
            <span className="hero-text">
              This page is a visual reference for the rest of the application. It keeps
              the product structure intact and demonstrates how KPI cards, filters,
              charts and tables can feel more polished without becoming flashy.
            </span>
          }
          actions={
            <div className="toolbar-group">
              <Button variant="primary" glow>
                Refresh snapshot
              </Button>
              <Button variant="secondary">Export view</Button>
            </div>
          }
        >
          <div className="hero-badges">
            <span className="hero-badge">
              Window <strong>Rolling 30 days</strong>
            </span>
            <span className="hero-badge">
              Theme <strong>Purple glow, dark enterprise</strong>
            </span>
            <span className="hero-badge">
              Charts <strong>Gradient-led emphasis</strong>
            </span>
          </div>
        </Card>

        <Card
          tone="highlight"
          eyebrow="Usage Notes"
          title="How to extend the style"
          subtitle="Keep the same spacing rhythm and reserve the strongest gradients for focus, KPIs and charts."
          className="hero-note"
        >
          <div className="hero-note-list">
            <span>
              <strong>Sidebar:</strong> use glow only on the active route and selected
              filters.
            </span>
            <span>
              <strong>Panels:</strong> keep surfaces dark with subtle border gradients
              and soft hover elevation.
            </span>
            <span>
              <strong>Charts:</strong> use purple-pink-blue accents to carry most of the
              visual energy.
            </span>
          </div>
        </Card>
      </div>

      <div className="kpi-grid">
        {kpis.map((item) => (
          <Card
            key={item.label}
            tone={item.tone}
            className="kpi-card"
            hoverable
            eyebrow={item.label}
          >
            <span className="kpi-value">{item.value}</span>
            <span className={`kpi-delta${item.delta.startsWith("-") ? " down" : ""}`}>
              {item.delta}
            </span>
            <span className="kpi-caption">{item.caption}</span>
          </Card>
        ))}
      </div>

      <div className="dashboard-main">
        <div className="dashboard-stack">
          <Card
            tone="rainbow"
            hoverable
            className="chart-card"
            eyebrow="Chart Styling"
            title="Revenue trajectory"
            subtitle="The chart carries the strongest gradient treatment, while grid lines and labels stay soft."
            actions={
              <div className="chart-legend">
                <span className="chart-legend-item">
                  <span
                    className="chart-legend-swatch"
                    style={{ color: "#d946ef", background: "#d946ef" }}
                  />
                  Actual
                </span>
                <span className="chart-legend-item">
                  <span
                    className="chart-legend-swatch"
                    style={{ color: "#38bdf8", background: "#38bdf8" }}
                  />
                  Forecast
                </span>
              </div>
            }
          >
            <div className="chart-surface">
              <div className="chart-tooltip">
                <strong>Week 4</strong>
                <span>EUR 32.6K actual revenue</span>
              </div>
              <svg
                className="chart-svg"
                viewBox="0 0 720 260"
                role="img"
                aria-label="Sample revenue trend chart"
              >
                <defs>
                  <linearGradient id="actualGradient" x1="0%" x2="100%" y1="0%" y2="0%">
                    <stop offset="0%" stopColor="#8b5cf6" />
                    <stop offset="48%" stopColor="#d946ef" />
                    <stop offset="100%" stopColor="#38bdf8" />
                  </linearGradient>
                  <linearGradient id="areaGradient" x1="0%" x2="0%" y1="0%" y2="100%">
                    <stop offset="0%" stopColor="#d946ef" stopOpacity="0.42" />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.02" />
                  </linearGradient>
                </defs>

                <path
                  d={`${revenuePath} L 670 240 L 40 240 Z`}
                  fill="url(#areaGradient)"
                  opacity="0.95"
                />
                <path
                  d={forecastPath}
                  fill="none"
                  stroke="rgba(56, 189, 248, 0.66)"
                  strokeDasharray="7 8"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                <path
                  d={revenuePath}
                  fill="none"
                  stroke="url(#actualGradient)"
                  strokeWidth="5"
                  strokeLinecap="round"
                  filter="drop-shadow(0 0 12px rgba(139, 92, 246, 0.45))"
                />
                {revenuePoints.map((point) => (
                  <circle
                    key={point.join("-")}
                    cx={point[0]}
                    cy={point[1]}
                    r="4.5"
                    fill="#0b1020"
                    stroke="#c084fc"
                    strokeWidth="2"
                  />
                ))}
              </svg>
            </div>
          </Card>

          <Card
            hoverable
            eyebrow="Exception Queue"
            title="Operational exceptions"
            subtitle="Dark tables should stay calm and readable, using separators instead of heavy borders."
            count={exceptionRows.length}
          >
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Unit</th>
                    <th>Area</th>
                    <th>Issue</th>
                    <th>Owner</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {exceptionRows.map((row) => (
                    <tr key={`${row.unit}-${row.area}`}>
                      <td>{row.unit}</td>
                      <td>{row.area}</td>
                      <td>{row.issue}</td>
                      <td>{row.owner}</td>
                      <td>{row.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <div className="dashboard-stack">
          <Card
            tone="secondary"
            hoverable
            className="chart-card"
            eyebrow="Distribution"
            title="Channel mix"
            subtitle="Bar fills can use the iridescent gradient, but labels and grid stay restrained."
          >
            <div className="chart-list">
              {channels.map((channel) => (
                <div className="chart-list-item" key={channel.label}>
                  <div className="chart-list-top">
                    <strong>{channel.label}</strong>
                    <span className="section-note">{channel.value}</span>
                  </div>
                  <div className="chart-bar" aria-hidden="true">
                    <span style={{ width: channel.width }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card
            tone="highlight"
            hoverable
            eyebrow="Activity"
            title="Operator feed"
            subtitle="Small supporting cards keep glow to a minimum and prioritize readable status text."
          >
            <div className="activity-list">
              {activityItems.map((item) => (
                <article className="activity-item" key={`${item.title}-${item.time}`}>
                  <div className="activity-meta">
                    <strong>{item.title}</strong>
                    <span className="section-note">{item.time}</span>
                  </div>
                  <p>{item.description}</p>
                </article>
              ))}
            </div>
          </Card>

          <Card
            hoverable
            eyebrow="Filter Behaviour"
            title="Selected states"
            subtitle="Selected filters use a soft glow and gradient tint, while unselected chips stay neutral."
          >
            <div className="toolbar-group">
              <span className="filter-chip filter-chip-active">Rolling 7 days</span>
              <span className="filter-chip">Business Units</span>
              <span className="filter-chip">Stock Alerts</span>
              <span className="filter-chip">Finance Mapping</span>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
