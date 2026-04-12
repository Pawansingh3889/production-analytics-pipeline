'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts'

const REFRESH_INTERVAL = 60_000
const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']

async function fetchJSON(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

function StatCard({ title, value, sub, color }) {
  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
      <p className="text-sm text-gray-400">{title}</p>
      <p className={`mt-2 text-3xl font-bold ${color || 'text-blue-400'}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-500">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [yieldData, setYieldData] = useState([])
  const [activeRuns, setActiveRuns] = useState([])
  const [breaches, setBreaches] = useState([])
  const [compliance, setCompliance] = useState([])
  const [products, setProducts] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const loadData = useCallback(async () => {
    try {
      const [y, r, t, c, p] = await Promise.all([
        fetchJSON('/api/yield/daily?days=14'),
        fetchJSON('/api/runs/active'),
        fetchJSON('/api/temperature/breaches'),
        fetchJSON('/api/compliance/checks'),
        fetchJSON('/api/products'),
      ])
      setYieldData(y.data || [])
      setActiveRuns(r.data || [])
      setBreaches(t.data || [])
      setCompliance(c.data || [])
      setProducts(p.data || p || [])
      setError(null)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const id = setInterval(loadData, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [loadData])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-400">Loading production data...</p>
        </div>
      </div>
    )
  }

  if (error && yieldData.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-950">
        <div className="rounded-2xl bg-gray-900 p-8 text-center max-w-md">
          <div className="text-4xl mb-4">&#9888;</div>
          <h2 className="text-xl font-semibold text-red-400">API Unavailable</h2>
          <p className="mt-2 text-sm text-gray-400">
            Start the FastAPI backend:
          </p>
          <code className="mt-2 block rounded bg-gray-800 px-4 py-2 text-sm text-green-400">
            make api
          </code>
          <p className="mt-4 text-xs text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  // Aggregate yield by date for the chart
  const yieldByDate = {}
  yieldData.forEach((d) => {
    const date = (d.production_date || '').split(' ')[0]
    if (!yieldByDate[date]) yieldByDate[date] = { date, runs: 0, lines: new Set() }
    yieldByDate[date].runs += d.runs || 0
    if (d.prod_line) yieldByDate[date].lines.add(d.prod_line)
  })
  const chartData = Object.values(yieldByDate)
    .map((d) => ({ date: d.date, runs: d.runs, lines: d.lines.size }))
    .sort((a, b) => a.date.localeCompare(b.date))

  // Species breakdown for pie chart
  const speciesCount = {}
  yieldData.forEach((d) => {
    const sp = d.species || 'unknown'
    speciesCount[sp] = (speciesCount[sp] || 0) + (d.runs || 1)
  })
  const pieData = Object.entries(speciesCount)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  // Line breakdown
  const lineCount = {}
  yieldData.forEach((d) => {
    const ln = d.prod_line || 'unknown'
    lineCount[ln] = (lineCount[ln] || 0) + (d.runs || 1)
  })
  const lineData = Object.entries(lineCount)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)

  const totalRuns = yieldData.reduce((s, d) => s + (d.runs || 0), 0)
  const activeCount = activeRuns.length
  const breachCount = breaches.length
  const complianceCount = compliance.length

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Production Dashboard</h1>
            <p className="text-sm text-gray-500">Fish production analytics — real-time data from SI Integreater</p>
          </div>
          <div className="text-right">
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <br />
            <button
              onClick={loadData}
              className="mt-1 rounded bg-blue-600 px-3 py-1 text-xs font-medium hover:bg-blue-500 transition"
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 rounded-lg bg-red-900/30 border border-red-800 px-4 py-2 text-sm text-red-300">
            Last refresh failed: {error}
          </div>
        )}

        {/* KPI Cards */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Total Runs" value={totalRuns} sub="Last 14 days" color="text-blue-400" />
          <StatCard title="Active Runs" value={activeCount} sub="Currently in progress" color="text-green-400" />
          <StatCard title="Temp Breaches" value={breachCount} sub="Last 24 hours" color={breachCount > 0 ? "text-red-400" : "text-green-400"} />
          <StatCard title="Compliance Flags" value={complianceCount} sub="Giveaway + violations" color={complianceCount > 0 ? "text-amber-400" : "text-green-400"} />
        </div>

        {/* Charts Row */}
        <div className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-2">

          {/* Daily Runs Bar Chart */}
          <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
            <h2 className="mb-4 text-lg font-semibold">Daily Production Runs</h2>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} angle={-45} textAnchor="end" height={60} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '0.5rem' }}
                    labelStyle={{ color: '#d1d5db' }}
                  />
                  <Bar dataKey="runs" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Runs" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-500 py-20 text-center">No production data available</p>
            )}
          </div>

          {/* Species Pie Chart */}
          <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
            <h2 className="mb-4 text-lg font-semibold">Production by Species</h2>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={100} innerRadius={50} dataKey="value" label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}>
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '0.5rem' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-gray-500 py-20 text-center">No species data available</p>
            )}
          </div>
        </div>

        {/* Line Performance */}
        <div className="mb-8 rounded-2xl bg-gray-900 border border-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold">Runs by Production Line</h2>
          {lineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={lineData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#6b7280', fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '0.5rem' }} />
                <Bar dataKey="value" fill="#22c55e" radius={[0, 4, 4, 0]} name="Runs" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-500 py-10 text-center">No line data</p>
          )}
        </div>

        {/* Active Runs Table */}
        <div className="mb-8 rounded-2xl bg-gray-900 border border-gray-800 p-6">
          <h2 className="mb-4 text-lg font-semibold">Active Runs ({activeCount})</h2>
          {activeCount > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400">
                    <th className="pb-3 pr-4">Run</th>
                    <th className="pb-3 pr-4">Product</th>
                    <th className="pb-3 pr-4">Line</th>
                    <th className="pb-3 pr-4">Species</th>
                    <th className="pb-3 pr-4">Shift</th>
                    <th className="pb-3">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {activeRuns.slice(0, 20).map((run, i) => (
                    <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                      <td className="py-3 pr-4 font-mono text-blue-400">{run.run_number}</td>
                      <td className="py-3 pr-4">{run.description || run.product_code}</td>
                      <td className="py-3 pr-4">{run.prod_line}</td>
                      <td className="py-3 pr-4 capitalize">{run.species}</td>
                      <td className="py-3 pr-4">
                        <span className={`rounded px-2 py-0.5 text-xs font-medium ${run.shift_code === 'DAY' ? 'bg-amber-900/50 text-amber-300' : run.shift_code === 'NIGHT' ? 'bg-indigo-900/50 text-indigo-300' : 'bg-gray-800 text-gray-400'}`}>
                          {run.shift_code}
                        </span>
                      </td>
                      <td className="py-3 text-gray-400">{(run.production_date || '').split(' ')[0]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500 py-4">All runs complete. No active production.</p>
          )}
        </div>

        {/* Compliance Alerts */}
        {complianceCount > 0 && (
          <div className="mb-8 rounded-2xl bg-gray-900 border border-amber-800/50 p-6">
            <h2 className="mb-4 text-lg font-semibold text-amber-400">Compliance Flags ({complianceCount})</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400">
                    <th className="pb-3 pr-4">Run</th>
                    <th className="pb-3 pr-4">Product</th>
                    <th className="pb-3 pr-4">Issue</th>
                    <th className="pb-3">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {compliance.slice(0, 10).map((c, i) => (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-2 pr-4 font-mono">{c.run_number}</td>
                      <td className="py-2 pr-4">{c.description || c.product_code}</td>
                      <td className="py-2 pr-4 text-amber-400">{c.giveaway_flag || c.product_code_flag || 'Flag'}</td>
                      <td className="py-2">{c.giveaway_pct ? `${c.giveaway_pct}%` : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {complianceCount > 10 && (
                <p className="mt-2 text-xs text-gray-500">Showing 10 of {complianceCount} flags</p>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-gray-600 mt-8">
          Production Analytics Pipeline — FastAPI + Next.js + dbt — Auto-refreshes every 60s
        </div>
      </div>
    </main>
  )
}
