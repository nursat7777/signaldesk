import { aggregate, type Metric } from "../service";
export function Trend({
  metrics,
  from,
  to,
  labels,
  format,
}: {
  metrics: Metric[];
  from: string;
  to: string;
  labels: { empty: string; revenue: string; spend: string };
  format: (n: number) => string;
}) {
  if (!metrics.length || from > to)
    return <div className="chart-empty">{labels.empty}</div>;
  const dates = [...new Set(metrics.map((m) => m.date))].sort();
  const points = dates.map((d) =>
    aggregate(metrics.filter((m) => m.date === d)),
  );
  const max =
    Math.max(...points.map((p) => Math.max(p.revenue, p.spend)), 1) * 1.15;
  const x = (i: number) => 64 + i * (900 / Math.max(points.length - 1, 1)),
    y = (v: number) => 230 - (v / max) * 195;
  const path = (k: "revenue" | "spend") =>
    points.map((p, i) => `${i ? "L" : "M"}${x(i)},${y(p[k])}`).join(" ");
  return (
    <div className="chart">
      <svg
        viewBox="0 0 1000 280"
        role="img"
        aria-label={`${labels.revenue} / ${labels.spend}: ${from} — ${to}`}
      >
        <defs>
          <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#c6f27a" stopOpacity=".19" />
            <stop offset="100%" stopColor="#c6f27a" stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 1, 2, 3, 4].map((i) => (
          <g key={i}>
            <line
              x1="64"
              x2="965"
              y1={35 + i * 49}
              y2={35 + i * 49}
              stroke="#2a2e2b"
              strokeDasharray="3 5"
            />
            <text
              x="52"
              y={39 + i * 49}
              textAnchor="end"
              fill="#828b85"
              fontSize="11"
            >
              {format(max * (1 - i / 4))}
            </text>
          </g>
        ))}
        <path
          d={`${path("revenue")} L${x(points.length - 1)},230 L64,230 Z`}
          fill="url(#area)"
        />
        <path
          d={path("revenue")}
          fill="none"
          stroke="#c6f27a"
          strokeWidth="2.6"
          strokeLinejoin="round"
        />
        <path
          d={path("spend")}
          fill="none"
          stroke="#76c8d8"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        {dates.map((d, i) =>
          i % Math.max(1, Math.floor(dates.length / 6)) === 0 ? (
            <text
              key={d}
              x={x(i)}
              y="263"
              textAnchor="middle"
              fill="#828b85"
              fontSize="11"
            >
              {d.slice(5).replace("-", " / ")}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  );
}
