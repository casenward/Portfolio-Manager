import React, { useState, useMemo, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  ArrowUpRight,
  ArrowDownRight,
  ChevronUp,
  ChevronDown,
  Info,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Placeholders — performance / metrics / YTD not wired yet.
// ---------------------------------------------------------------------------

const SECTOR_COLORS = ["#4FB8C4", "#7C93C9", "#9B7EC4", "#D9A441", "#8FA85B", "#4F8FA6", "#C77DAE", "#7C9186"];

const RANGES = ["1M", "3M", "YTD", "1Y", "ALL"];

const PERFORMANCE_SERIES = {
  "1M": [
    ["Wk 1", "none", "none"], ["Wk 2", "none", "none"], ["Wk 3", "none", "none"], ["Wk 4", "none", "none"],
  ],
  "3M": [
    ["Apr", "none", "none"], ["May", "none", "none"], ["Jun", "none", "none"], ["Jul", "none", "none"],
  ],
  YTD: [
    ["Jan", "none", "none"], ["Feb", "none", "none"], ["Mar", "none", "none"], ["Apr", "none", "none"],
    ["May", "none", "none"], ["Jun", "none", "none"], ["Jul", "none", "none"],
  ],
  "1Y": [
    ["Aug", "none", "none"], ["Sep", "none", "none"], ["Oct", "none", "none"], ["Nov", "none", "none"],
    ["Dec", "none", "none"], ["Jan", "none", "none"], ["Feb", "none", "none"], ["Mar", "none", "none"],
    ["Apr", "none", "none"], ["May", "none", "none"], ["Jun", "none", "none"], ["Jul", "none", "none"],
  ],
  ALL: [
    ["2023", "none", "none"], ["2024", "none", "none"], ["2025", "none", "none"], ["2026", "none", "none"],
  ],
};

const METRICS = [
  { key: "sharpe", label: "Sharpe Ratio", value: "none", desc: "Return per unit of total risk" },
  { key: "sortino", label: "Sortino Ratio", value: "none", desc: "Return per unit of downside risk" },
  { key: "calmar", label: "Calmar Ratio", value: "none", desc: "Annualized return vs. max drawdown" },
  { key: "sterling", label: "Sterling Ratio", value: "none", desc: "Return vs. average annual drawdown" },
  { key: "omega", label: "Omega Ratio", value: "none", desc: "Probability-weighted gains vs. losses" },
  { key: "treynor", label: "Treynor Ratio", value: "none", desc: "Return per unit of market risk" },
  { key: "info", label: "Information Ratio", value: "none", desc: "Excess return vs. tracking error" },
  { key: "beta", label: "Beta", value: "none", desc: "Sensitivity to market moves" },
  { key: "maxdd", label: "Max Drawdown", value: "none", desc: "Largest peak-to-trough decline", negative: true },
  { key: "vol", label: "Volatility (Ann.)", value: "none", desc: "Standard deviation of returns" },
];

const DAY_CHANGE = "none";
const YTD_CHANGE = "none";

// ---------------------------------------------------------------------------

function isNumber(n) {
  return typeof n === "number" && Number.isFinite(n);
}

function fmtCurrency(n) {
  if (!isNumber(n)) return "—";
  return n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

function ChangeBadge({ value, size = "md" }) {
  if (!isNumber(value)) {
    return <span className={`change-badge ${size}`}>—</span>;
  }
  const up = value >= 0;
  return (
    <span className={`change-badge ${up ? "up" : "down"} ${size}`}>
      {up ? <ArrowUpRight size={size === "sm" ? 12 : 14} /> : <ArrowDownRight size={size === "sm" ? 12 : 14} />}
      {up ? "+" : ""}
      {value.toFixed(2)}%
    </span>
  );
}

function TickerTape({ holdings }) {
  if (!holdings.length) return null;
  const items = [...holdings, ...holdings];
  return (
    <div className="tape-wrap" role="marquee" aria-label="Holdings ticker">
      <div className="tape-track">
        {items.map((h, i) => (
          <span className="tape-item" key={i}>
            <span className="tape-symbol">{h.symbol}</span>
            <span className={isNumber(h.dayChg) && h.dayChg >= 0 ? "tape-up" : "tape-down"}>
              {isNumber(h.dayChg) ? (
                <>
                  {h.dayChg >= 0 ? "▲" : "▼"} {Math.abs(h.dayChg).toFixed(2)}%
                </>
              ) : (
                "—"
              )}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

function PerformanceChart() {
  const [range, setRange] = useState("YTD");
  const data = PERFORMANCE_SERIES[range].map(([label, portfolio, benchmark]) => ({ label, portfolio, benchmark }));

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Performance</h2>
          <p className="panel-sub">Cumulative return vs. S&amp;P 500</p>
        </div>
        <div className="range-toggle" role="tablist" aria-label="Time range">
          {RANGES.map((r) => (
            <button
              key={r}
              role="tab"
              aria-selected={range === r}
              className={`range-btn ${range === r ? "active" : ""}`}
              onClick={() => setRange(r)}
            >
              {r}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 10, right: 12, left: -12, bottom: 0 }}>
          <defs>
            <linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#C9A035" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#C9A035" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#232936" vertical={false} />
          <XAxis dataKey="label" stroke="#6B7284" fontSize={12} fontFamily="'IBM Plex Mono', monospace" tickLine={false} axisLine={{ stroke: "#232936" }} />
          <YAxis stroke="#6B7284" fontSize={12} fontFamily="'IBM Plex Mono', monospace" tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            contentStyle={{ background: "#151A24", border: "1px solid #2A3140", borderRadius: 6, fontFamily: "'IBM Plex Mono', monospace", fontSize: 12 }}
            labelStyle={{ color: "#E9E6DD" }}
            formatter={(value, name) => [
              isNumber(value) ? `${value.toFixed(2)}%` : "—",
              name === "portfolio" ? "Portfolio" : "S&P 500",
            ]}
          />
          <Area type="monotone" dataKey="benchmark" stroke="#6B7284" strokeWidth={1.5} strokeDasharray="4 3" fill="none" dot={false} />
          <Area type="monotone" dataKey="portfolio" stroke="#C9A035" strokeWidth={2} fill="url(#portfolioFill)" dot={false} />
        </AreaChart>
      </ResponsiveContainer>

      <div className="legend-row">
        <span className="legend-item"><i className="dot gold" /> Portfolio</span>
        <span className="legend-item"><i className="dot dash" /> S&amp;P 500</span>
      </div>
    </div>
  );
}

function AllocationPanel({ sectors }) {
  const [hover, setHover] = useState(null);
  const sorted = useMemo(
    () => [...sectors].sort((a, b) => b.value - a.value),
    [sectors]
  );

  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Allocation</h2>
          <p className="panel-sub">By sector</p>
        </div>
      </div>
      {sorted.length === 0 ? (
        <p className="panel-sub">No sector data</p>
      ) : (
        <>
          <div className="donut-wrap">
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={sorted}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={58}
                  outerRadius={82}
                  paddingAngle={2}
                  onMouseEnter={(_, i) => setHover(i)}
                  onMouseLeave={() => setHover(null)}
                >
                  {sorted.map((_, i) => (
                    <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} opacity={hover === null || hover === i ? 1 : 0.35} stroke="#0B0E13" strokeWidth={2} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="donut-center">
              <span className="donut-value">{hover !== null ? `${sorted[hover].value}%` : `${sorted.length}`}</span>
              <span className="donut-label">{hover !== null ? sorted[hover].name : "sectors"}</span>
            </div>
          </div>
          <ul className="sector-list">
            {sorted.map((s, i) => (
              <li key={s.name} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
                <span className="sector-name"><i className="dot" style={{ background: SECTOR_COLORS[i % SECTOR_COLORS.length] }} />{s.name}</span>
                <span className="sector-value">{s.value}%</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

function MetricsGrid() {
  const [active, setActive] = useState(null);
  return (
    <div className="panel">
      <div className="panel-head">
        <div>
          <h2>Risk &amp; Return Metrics</h2>
          <p className="panel-sub">Trailing 12 months</p>
        </div>
      </div>
      <div className="metrics-grid">
        {METRICS.map((m) => (
          <div
            key={m.key}
            className="metric-card"
            onMouseEnter={() => setActive(m.key)}
            onMouseLeave={() => setActive(null)}
            tabIndex={0}
            onFocus={() => setActive(m.key)}
            onBlur={() => setActive(null)}
          >
            <div className="metric-top">
              <span className="metric-label">{m.label}</span>
              <Info size={12} className="metric-info-icon" />
            </div>
            <span className={`metric-value ${m.negative ? "down-text" : ""}`}>{m.value}</span>
            <span className={`metric-desc ${active === m.key ? "show" : ""}`}>{m.desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const HOLDINGS_TABS = [
  { id: "traditional", label: "Traditional" },
  { id: "sustainable", label: "Sustainable" },
  { id: "combined", label: "Combined" },
];

function accountLabel(account) {
  if (account === "both") return "Both";
  if (account === "sustainable") return "Sustainable";
  if (account === "traditional") return "Traditional";
  return account || "—";
}

/** Merge same-symbol rows across accounts for the Combined tab. */
function mergeCombinedHoldings(holdings) {
  const bySymbol = new Map();

  for (const h of holdings) {
    const key = h.symbol;
    const existing = bySymbol.get(key);
    if (!existing) {
      bySymbol.set(key, {
        ...h,
        accounts: new Set(h.account ? [h.account] : []),
      });
      continue;
    }

    const nextValue =
      (isNumber(existing.value) ? existing.value : 0) +
      (isNumber(h.value) ? h.value : 0);

    // Value-weighted day change when both legs have a %.
    let nextDay = existing.dayChg;
    if (isNumber(existing.dayChg) && isNumber(h.dayChg) && nextValue > 0) {
      const w0 = isNumber(existing.value) ? existing.value : 0;
      const w1 = isNumber(h.value) ? h.value : 0;
      nextDay = (existing.dayChg * w0 + h.dayChg * w1) / nextValue;
    } else if (!isNumber(existing.dayChg) && isNumber(h.dayChg)) {
      nextDay = h.dayChg;
    }

    if (h.account) existing.accounts.add(h.account);

    bySymbol.set(key, {
      ...existing,
      value: nextValue,
      price: isNumber(h.price) ? h.price : existing.price,
      dayChg: isNumber(nextDay) ? Math.round(nextDay * 100) / 100 : nextDay,
      name: existing.name || h.name,
      sector: existing.sector || h.sector,
    });
  }

  return [...bySymbol.values()].map((h) => {
    const accounts = h.accounts || new Set();
    let account = h.account;
    if (accounts.size > 1) account = "both";
    else if (accounts.size === 1) account = [...accounts][0];

    const { accounts: _drop, ...rest } = h;
    return { ...rest, account };
  });
}

function HoldingsTable({ holdings }) {
  const [open, setOpen] = useState(true);
  const [tab, setTab] = useState("combined");
  const [sortKey, setSortKey] = useState("weight");
  const [sortDir, setSortDir] = useState("desc");

  const hasAccount = holdings.some((h) => typeof h.account === "string" && h.account.length > 0);

  const visible = useMemo(() => {
    let filtered;
    if (tab === "combined") {
      filtered = mergeCombinedHoldings(holdings);
    } else if (!hasAccount) {
      filtered = holdings;
    } else {
      filtered = holdings.filter((h) => h.account === tab);
    }

    const equity = filtered.reduce(
      (sum, h) => sum + (isNumber(h.value) ? h.value : 0),
      0
    );
    return filtered.map((h) => ({
      ...h,
      weight:
        equity > 0 && isNumber(h.value)
          ? Math.round((h.value / equity) * 1000) / 10
          : 0,
    }));
  }, [holdings, tab, hasAccount]);

  const sorted = useMemo(() => {
    const copy = [...visible];
    const key = sortKey === "account" && tab !== "combined" ? "weight" : sortKey;
    copy.sort((a, b) => {
      const av = a[key];
      const bv = b[key];
      if (typeof av === "string" || typeof bv === "string") {
        const as = av == null ? "" : String(av);
        const bs = bv == null ? "" : String(bv);
        return sortDir === "asc" ? as.localeCompare(bs) : bs.localeCompare(as);
      }
      const an = isNumber(av) ? av : -Infinity;
      const bn = isNumber(bv) ? bv : -Infinity;
      return sortDir === "asc" ? an - bn : bn - an;
    });
    return copy;
  }, [visible, sortKey, sortDir, tab]);

  function selectTab(next) {
    setTab(next);
    if (sortKey === "account" && next !== "combined") {
      setSortKey("weight");
    }
  }

  function toggleSort(key) {
    if (key === sortKey) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const cols = [
    { key: "symbol", label: "Symbol" },
    { key: "name", label: "Name" },
    ...(tab === "combined" && hasAccount ? [{ key: "account", label: "Account" }] : []),
    { key: "sector", label: "Sector" },
    { key: "price", label: "Price" },
    { key: "weight", label: "Weight" },
    { key: "dayChg", label: "Day" },
  ];

  return (
    <div className={`panel holdings-folder ${open ? "open" : "closed"}`}>
      <button
        type="button"
        className="holdings-folder-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="holdings-folder-title">
          {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          <h2>Holdings</h2>
        </span>
        <p className="panel-sub">{holdings.length} positions</p>
      </button>

      {open && (
        <div className="holdings-folder-body">
          <div className="holdings-tabs" role="tablist" aria-label="Holdings account">
            {HOLDINGS_TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                className={`holdings-tab ${tab === t.id ? "active" : ""}`}
                onClick={() => selectTab(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
          {!hasAccount && (
            <p className="panel-sub holdings-tab-count">
              Account tabs need a restarted API (missing account field on holdings).
            </p>
          )}
          <p className="panel-sub holdings-tab-count">{sorted.length} positions</p>
          <div className="table-scroll">
            <table className="holdings-table">
              <thead>
                <tr>
                  {cols.map((c) => (
                    <th key={c.key}>
                      <button className="th-btn" onClick={() => toggleSort(c.key)}>
                        {c.label}
                        {sortKey === c.key && (sortDir === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                      </button>
                    </th>
                  ))}
                  <th className="num-col">Value</th>
                </tr>
              </thead>
              <tbody>
                {sorted.length === 0 ? (
                  <tr>
                    <td colSpan={cols.length + 1} className="dim">
                      No positions in this account
                    </td>
                  </tr>
                ) : (
                  sorted.map((h, i) => (
                    <tr key={`${h.account || "na"}-${h.symbol}-${i}`}>
                      <td className="mono symbol-cell">{h.symbol}</td>
                      <td className="dim">{h.name}</td>
                      {tab === "combined" && hasAccount && (
                        <td>
                          <span className="sector-pill">
                            {accountLabel(h.account)}
                          </span>
                        </td>
                      )}
                      <td><span className="sector-pill">{h.sector}</span></td>
                      <td className="mono">{isNumber(h.price) ? `$${h.price.toFixed(2)}` : "—"}</td>
                      <td className="mono">
                        <div className="weight-bar-wrap">
                          <div className="weight-bar" style={{ width: `${isNumber(h.weight) ? Math.min(h.weight * 4, 100) : 0}%` }} />
                          <span>{isNumber(h.weight) ? `${h.weight}%` : "—"}</span>
                        </div>
                      </td>
                      <td className="mono"><ChangeBadge value={h.dayChg} size="sm" /></td>
                      <td className="mono num-col">
                        {isNumber(h.value) ? fmtCurrency(h.value) : "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default function PortfolioDashboard() {
  const [totalWorth, setTotalWorth] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setStatus("loading");
      setError(null);
      try {
        const response = await fetch("/api/dashboard");
        if (!response.ok) {
          throw new Error(`API ${response.status}`);
        }
        const data = await response.json();
        if (cancelled) return;
        setTotalWorth(data.total_worth);
        setCompanies(data.companies || []);
        setSectors(data.sectors || []);
        setStatus("ready");
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load dashboard");
        setStatus("error");
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="dash-root">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

        html, body, #root {
          margin: 0;
          min-height: 100%;
          background: #0A1310;
          scrollbar-gutter: stable;
        }

        .dash-root {
          --bg: #0A1310;
          --surface: #101B15;
          --surface-2: #17251C;
          --border: #223226;
          --text: #E6EDE6;
          --text-dim: #7C9186;
          --gain: #4FBF6E;
          --loss: #D14F45;
          --gold: #4FB8C4;

          background: var(--bg);
          color: var(--text);
          font-family: 'Inter', sans-serif;
          padding: 28px 32px 48px;
          min-height: 100%;
          box-sizing: border-box;
        }
        .dash-root * { box-sizing: border-box; }
        .dash-root button {
          font-family: inherit;
          background: none;
          border: none;
          color: inherit;
          cursor: pointer;
        }
        .dash-root button:focus-visible,
        .dash-root [tabindex]:focus-visible {
          outline: 2px solid var(--gold);
          outline-offset: 2px;
          border-radius: 4px;
        }

        .status-banner {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 13px;
          color: var(--text-dim);
          margin-bottom: 16px;
        }
        .status-banner.error { color: var(--loss); }

        /* Header */
        .top-bar {
          display: flex;
          justify-content: space-between;
          align-items: flex-end;
          flex-wrap: wrap;
          gap: 16px;
          margin-bottom: 18px;
        }
        .eyebrow {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--gold);
          margin: 0 0 6px;
        }
        .total-value {
          font-family: 'Source Serif 4', serif;
          font-size: 44px;
          font-weight: 600;
          line-height: 1;
          margin: 0;
          letter-spacing: -0.01em;
        }
        .top-bar-right {
          display: flex;
          gap: 24px;
          align-items: center;
        }
        .stat-block { text-align: right; }
        .stat-label {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 10px;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--text-dim);
          margin: 0 0 4px;
        }

        .change-badge {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          font-family: 'IBM Plex Mono', monospace;
          font-weight: 500;
          border-radius: 4px;
          padding: 2px 6px;
        }
        .change-badge.md { font-size: 15px; padding: 3px 8px; }
        .change-badge.sm { font-size: 12px; padding: 1px 5px; }
        .change-badge.up { color: var(--gain); background: rgba(95,168,140,0.12); }
        .change-badge.down { color: var(--loss); background: rgba(193,88,78,0.12); }

        /* Ticker tape */
        .tape-wrap {
          overflow: hidden;
          border-top: 1px solid var(--border);
          border-bottom: 1px solid var(--border);
          background: #0D1712;
          margin-bottom: 24px;
          padding: 9px 0;
        }
        .tape-track {
          display: flex;
          gap: 32px;
          width: max-content;
          animation: scroll-tape 38s linear infinite;
        }
        @media (prefers-reduced-motion: reduce) {
          .tape-track { animation: none; overflow-x: auto; }
        }
        @keyframes scroll-tape {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        .tape-item {
          display: inline-flex;
          gap: 8px;
          align-items: baseline;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 12px;
          white-space: nowrap;
        }
        .tape-symbol { color: var(--text); letter-spacing: 0.04em; }
        .tape-up { color: var(--gain); }
        .tape-down { color: var(--loss); }

        /* Layout grid */
        .grid-2col {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 20px;
          margin-bottom: 20px;
        }
        @media (max-width: 860px) {
          .grid-2col { grid-template-columns: 1fr; }
        }

        .panel {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: 10px;
          padding: 20px 22px;
          margin-bottom: 20px;
        }
        .panel:last-child { margin-bottom: 0; }
        .panel-head {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          margin-bottom: 14px;
          flex-wrap: wrap;
        }
        .panel h2 {
          font-family: 'Source Serif 4', serif;
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 2px;
        }
        .panel-sub {
          font-size: 12px;
          color: var(--text-dim);
          margin: 0;
        }

        /* Range toggle */
        .range-toggle {
          display: flex;
          background: var(--surface-2);
          border: 1px solid var(--border);
          border-radius: 7px;
          padding: 2px;
        }
        .range-btn {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          padding: 5px 10px;
          border-radius: 5px;
          color: var(--text-dim);
        }
        .range-btn.active {
          background: var(--gold);
          color: #06171A;
          font-weight: 600;
        }

        .legend-row {
          display: flex;
          gap: 18px;
          margin-top: 4px;
          padding-left: 4px;
        }
        .legend-item {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: var(--text-dim);
        }
        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          display: inline-block;
        }
        .dot.gold { background: var(--gold); }
        .dot.dash { background: var(--text-dim); }

        /* Allocation donut */
        .donut-wrap { position: relative; }
        .donut-center {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          text-align: center;
          pointer-events: none;
        }
        .donut-value {
          display: block;
          font-family: 'Source Serif 4', serif;
          font-size: 24px;
          font-weight: 600;
        }
        .donut-label {
          display: block;
          font-size: 10px;
          color: var(--text-dim);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        .sector-list {
          list-style: none;
          margin: 10px 0 0;
          padding: 0;
        }
        .sector-list li {
          display: flex;
          justify-content: space-between;
          padding: 6px 2px;
          font-size: 13px;
          border-top: 1px solid var(--border);
        }
        .sector-name { display: flex; align-items: center; gap: 8px; }
        .sector-value { font-family: 'IBM Plex Mono', monospace; color: var(--text-dim); }

        /* Metrics grid */
        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 12px;
        }
        @media (max-width: 980px) { .metrics-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 600px) { .metrics-grid { grid-template-columns: repeat(2, 1fr); } }

        .metric-card {
          background: var(--surface-2);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 12px 13px;
          position: relative;
          min-height: 92px;
        }
        .metric-top {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }
        .metric-label {
          font-size: 11px;
          color: var(--text-dim);
          letter-spacing: 0.02em;
        }
        .metric-info-icon { color: #4B5262; flex-shrink: 0; margin-top: 1px; }
        .metric-value {
          display: block;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 20px;
          font-weight: 600;
          color: var(--gold);
        }
        .metric-value.down-text { color: var(--loss); }
        .metric-desc {
          display: block;
          font-size: 10.5px;
          color: var(--text-dim);
          margin-top: 6px;
          max-height: 0;
          overflow: hidden;
          opacity: 0;
          transition: max-height 0.15s ease, opacity 0.15s ease;
        }
        .metric-desc.show { max-height: 40px; opacity: 1; }

        /* Holdings folder */
        .holdings-folder { padding-top: 14px; padding-bottom: 14px; }
        .holdings-folder-toggle {
          display: flex;
          width: 100%;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          text-align: left;
          padding: 0;
        }
        .holdings-folder-title {
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }
        .holdings-folder-title h2 { margin: 0; }
        .holdings-folder-body { margin-top: 14px; }
        .holdings-tabs {
          display: flex;
          background: var(--surface-2);
          border: 1px solid var(--border);
          border-radius: 7px;
          padding: 2px;
          width: fit-content;
          margin-bottom: 10px;
        }
        .holdings-tab {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 11px;
          padding: 5px 12px;
          border-radius: 5px;
          color: var(--text-dim);
        }
        .holdings-tab.active {
          background: var(--gold);
          color: #06171A;
          font-weight: 600;
        }
        .holdings-tab-count { margin: 0 0 10px; }

        /* Holdings table */
        .table-scroll {
          overflow: auto;
          max-height: min(520px, 60vh);
        }
        .holdings-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }
        .holdings-table th {
          text-align: left;
          padding: 8px 10px;
          border-bottom: 1px solid var(--border);
        }
        .th-btn {
          display: inline-flex;
          align-items: center;
          gap: 3px;
          font-size: 11px;
          color: var(--text-dim);
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        .holdings-table td {
          padding: 9px 10px;
          border-bottom: 1px solid var(--border);
          white-space: nowrap;
        }
        .holdings-table tr:last-child td { border-bottom: none; }
        .symbol-cell { color: var(--gold); font-weight: 600; }
        .dim { color: var(--text-dim); }
        .mono { font-family: 'IBM Plex Mono', monospace; }
        .num-col { text-align: right; }
        .sector-pill {
          font-size: 11px;
          background: var(--surface-2);
          border: 1px solid var(--border);
          padding: 2px 8px;
          border-radius: 100px;
          color: var(--text-dim);
        }
        .weight-bar-wrap {
          position: relative;
          width: 90px;
          height: 16px;
          display: flex;
          align-items: center;
        }
        .weight-bar {
          position: absolute;
          left: 0; top: 6px;
          height: 4px;
          background: var(--gold);
          border-radius: 2px;
          opacity: 0.5;
        }
        .weight-bar-wrap span { position: relative; z-index: 1; font-size: 12px; }
      `}</style>

      {status === "loading" && (
        <p className="status-banner">Loading portfolio…</p>
      )}
      {status === "error" && (
        <p className="status-banner error">Could not load dashboard: {error}</p>
      )}

      <div className="top-bar">
        <div>
          <p className="eyebrow">Portfolio Overview</p>
          <p className="total-value">{fmtCurrency(totalWorth)}</p>
        </div>
        <div className="top-bar-right">
          <div className="stat-block">
            <p className="stat-label">Today</p>
            <ChangeBadge value={DAY_CHANGE} />
          </div>
          <div className="stat-block">
            <p className="stat-label">YTD</p>
            <ChangeBadge value={YTD_CHANGE} />
          </div>
        </div>
      </div>

      <TickerTape holdings={companies} />

      <div className="grid-2col">
        <PerformanceChart />
        <AllocationPanel sectors={sectors} />
      </div>

      <MetricsGrid />
      <HoldingsTable holdings={companies} />
    </div>
  );
}
