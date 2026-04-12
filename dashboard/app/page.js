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
} from 'recharts'

const REFRESH_INTERVAL = 60_000

async function fetchJSON(url) {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

function StatCard({ title, value, sub }) {
  return (
    <div className="rounded-2xl bg-gray-900 p-6">
      <p className="text-sm text-gray-400">{title}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
      {sub && <p className="mt-1 text-xs text-gray-500">{sub}</p>}
    </div>
  )
}

export default function Dashboard() {
  const [yieldData, setYieldData] = useState(null)
  const [activeRuns, setActiveRuns] = useState(null)
  const [breaches, setBreaches] = useState(null)
  const [compliance, setCompliance] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)

  const loadData = useCallback(async () => {
    try {
      const [y, r, t, c] = await Promise.all([
        fetchJSON('/api/yield/daily'),
        fetchJSON('/api/runs/active'),
        fetchJSON('/api/temperature/breaches'),
        fetchJSON('/api/compliance/checks'),
      ])
      setYieldData(y)
      setActiveRuns(r)
      setBreaches(t)
      setCompliance(c)
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
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-gray-400">Loading dashboard...</p>
      </div>
    )
  }

  if (error && !yieldData) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="rounded-2xl bg-gray-900 p-8 text-center">
          <h2 className="text-xl font-semibold text-red-400">API unavailable</h2>
          <p className="mt-2 text-sm text-gray-400">
            Could not reach the FastAPI backend. Start it with{' '}
            <code className="rounded bg-gray-800 px-2 py-0.5">make api</code> and
            refresh.
          </p>
          <p className="mt-4 text-xs text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  const totalYield = Array.isArray(yieldData)
    ? yieldData.reduce((sum, d) => sum + (d.total_kg ?? d.total_yield ?? 0), 0)
    : 0

  const runsCount = Array.isArray(activeRuns) ? activeRuns.length : 0
  const breachCount = Array.isArray(breaches) ? breaches.length : 0
  const complianceCount = Array.isArray(compliance) ? compliance.length : 0

  const chartData = Array.isArray(yieldData)
    ? yieldData.map((d) => ({
        date: d.production_date ?? d.date ?? '',
        yield: d.total_kg ?? d.total_yield ?? 0,
      }))
    : []

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Production Dashboard</h1>
        {lastUpdated && (
          <span className="text-xs text-gray-500">
            Updated {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-lg bg-red-900/30 px-4 py-2 text-sm text-red-300">
          Refresh failed: {error}
        </div>
      )}

      {/* KPI cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Yield"
          value={`${totalYield.toLocaleString()} kg`}
          sub="Last 7 days"
        />
        <StatCard title="Active Runs" value={runsCount} sub="Currently in progress" />
        <StatCard
          title="Temp Breaches"
          value={breachCount}
          sub="Last 24 hours"
        />
        <StatCard
          title="Compliance Issues"
          value={complianceCount}
          sub="Open violations"
        />
      </div>

      {/* Yield chart */}
      <div className="mb-8 rounded-2xl bg-gray-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Daily Yield (kg)</h2>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#111827',
                  border: '1px solid #374151',
                  borderRadius: '0.5rem',
                }}
                labelStyle={{ color: '#d1d5db' }}
                itemStyle={{ color: '#60a5fa' }}
              />
              <Bar dataKey="yield" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-gray-500">No yield data available.</p>
        )}
      </div>

      {/* Active runs table */}
      <div className="rounded-2xl bg-gray-900 p-6">
        <h2 className="mb-4 text-lg font-semibold">Active Runs</h2>
        {runsCount > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-gray-400">
                  <th className="pb-2 pr-4">Run Number</th>
                  <th className="pb-2 pr-4">Line</th>
                  <th className="pb-2 pr-4">Species</th>
                  <th className="pb-2 pr-4">Product</th>
                  <th className="pb-2 pr-4">Target (kg)</th>
                  <th className="pb-2">Actual (kg)</th>
                </tr>
              </thead>
              <tbody>
                {activeRuns.map((run, i) => (
                  <tr key={run.run_number ?? i} className="border-b border-gray-800/50">
                    <td className="py-2 pr-4 font-mono">{run.run_number ?? '-'}</td>
                    <td className="py-2 pr-4">{run.line_name ?? run.line ?? '-'}</td>
                    <td className="py-2 pr-4">{run.species ?? '-'}</td>
                    <td className="py-2 pr-4">{run.product ?? run.product_name ?? '-'}</td>
                    <td className="py-2 pr-4">{run.target_kg ?? '-'}</td>
                    <td className="py-2">{run.actual_kg ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-500">No active runs.</p>
        )}
      </div>
    </main>
  )
}
