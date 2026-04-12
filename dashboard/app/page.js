'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, Legend,
} from 'recharts'

const REFRESH = 60_000
const BLUE = '#3b82f6'
const GREEN = '#22c55e'
const AMBER = '#f59e0b'
const RED = '#ef4444'
const PURPLE = '#8b5cf6'
const CYAN = '#06b6d4'
const PINK = '#ec4899'
const ORANGE = '#f97316'
const COLORS = [BLUE, GREEN, AMBER, RED, PURPLE, CYAN, PINK, ORANGE, '#14b8a6', '#a855f7', '#6366f1', '#64748b']

async function api(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status}`)
  return r.json()
}

function Card({ title, value, sub, color, icon }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700/50 p-6 transition-all hover:border-gray-600 hover:shadow-lg hover:shadow-blue-500/5">
      <div className="absolute top-0 right-0 w-24 h-24 opacity-5 text-7xl">{icon}</div>
      <p className="text-sm font-medium text-gray-400 tracking-wide uppercase">{title}</p>
      <p className={`mt-3 text-4xl font-extrabold tracking-tight ${color || 'text-blue-400'}`}>{value}</p>
      {sub && <p className="mt-2 text-xs text-gray-500">{sub}</p>}
    </div>
  )
}

function Section({ title, children, badge, badgeColor }) {
  return (
    <div className="rounded-2xl bg-gradient-to-br from-gray-900 to-gray-800/80 border border-gray-700/50 p-6">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-bold tracking-tight">{title}</h2>
        {badge !== undefined && (
          <span className={`rounded-full px-3 py-1 text-xs font-bold ${badgeColor || 'bg-blue-500/20 text-blue-400'}`}>
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

export default function Dashboard() {
  const [y, setY] = useState([])
  const [runs, setRuns] = useState([])
  const [breaches, setBreaches] = useState([])
  const [comp, setComp] = useState([])
  const [err, setErr] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updated, setUpdated] = useState(null)

  const load = useCallback(async () => {
    try {
      const [a, b, c, d] = await Promise.all([
        api('/api/yield/daily?days=14'),
        api('/api/runs/active'),
        api('/api/temperature/breaches'),
        api('/api/compliance/checks'),
      ])
      setY(a.data || [])
      setRuns(b.data || [])
      setBreaches(c.data || [])
      setComp(d.data || [])
      setErr(null)
      setUpdated(new Date())
    } catch (e) { setErr(e.message) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load(); const id = setInterval(load, REFRESH); return () => clearInterval(id) }, [load])

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950">
      <div className="text-center">
        <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        <p className="mt-4 text-gray-400 animate-pulse">Loading production data...</p>
      </div>
    </div>
  )

  if (err && y.length === 0) return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950">
      <div className="rounded-2xl bg-gray-900 border border-red-800/50 p-10 text-center max-w-md">
        <div className="text-5xl mb-4">&#9888;&#65039;</div>
        <h2 className="text-xl font-bold text-red-400">API Unavailable</h2>
        <p className="mt-3 text-sm text-gray-400">Start the backend:</p>
        <code className="mt-3 block rounded-lg bg-gray-800 px-4 py-3 text-sm text-green-400 font-mono">make api</code>
      </div>
    </div>
  )

  // Aggregate by date
  const byDate = {}
  y.forEach(d => {
    const dt = (d.production_date || '').split(' ')[0]
    if (!byDate[dt]) byDate[dt] = { date: dt, runs: 0 }
    byDate[dt].runs += d.runs || 0
  })
  const chartData = Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date))

  // Species
  const sp = {}
  y.forEach(d => { const s = d.species || '?'; sp[s] = (sp[s] || 0) + (d.runs || 1) })
  const pieData = Object.entries(sp).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)

  // Lines
  const ln = {}
  y.forEach(d => { const l = d.prod_line || '?'; ln[l] = (ln[l] || 0) + (d.runs || 1) })
  const lineData = Object.entries(ln).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)

  // Shifts
  const sh = {}
  y.forEach(d => { const s = d.shift_code || '?'; sh[s] = (sh[s] || 0) + (d.runs || 1) })
  const shiftData = Object.entries(sh).map(([name, value]) => ({ name, value }))

  const totalRuns = y.reduce((s, d) => s + (d.runs || 0), 0)

  return (
    <main className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-sm font-bold">P</div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">Production Dashboard</h1>
              <p className="text-xs text-gray-500">Fish production analytics</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {updated && <span className="text-xs text-gray-500">Updated {updated.toLocaleTimeString()}</span>}
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" title="Live" />
            <button onClick={load} className="rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-semibold hover:bg-blue-500 transition-all active:scale-95">
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

        {err && <div className="mb-6 rounded-lg bg-red-900/20 border border-red-800/50 px-4 py-2 text-sm text-red-300">{err}</div>}

        {/* KPI Cards */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card title="Production Runs" value={totalRuns} sub="Last 14 days" color="text-blue-400" icon="&#128200;" />
          <Card title="Active Runs" value={runs.length} sub="Currently in progress" color="text-green-400" icon="&#9881;" />
          <Card title="Temp Breaches" value={breaches.length} sub="Last 24 hours" color={breaches.length > 0 ? "text-red-400" : "text-green-400"} icon="&#127777;" />
          <Card title="Compliance Flags" value={comp.length} sub="Giveaway > 3%" color={comp.length > 0 ? "text-amber-400" : "text-green-400"} icon="&#9888;" />
        </div>

        {/* Charts Row 1 */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Daily runs - area chart */}
          <div className="lg:col-span-2">
            <Section title="Daily Production Runs" badge={`${chartData.length} days`}>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={BLUE} stopOpacity={0.3} />
                        <stop offset="95%" stopColor={BLUE} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f', borderRadius: '0.75rem', boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }} />
                    <Area type="monotone" dataKey="runs" stroke={BLUE} strokeWidth={2} fill="url(#blueGrad)" name="Runs" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : <p className="text-gray-500 py-20 text-center">No data</p>}
            </Section>
          </div>

          {/* Species donut */}
          <Section title="By Species" badge={`${pieData.length} types`}>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} innerRadius={55} dataKey="value" paddingAngle={2}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={{ stroke: '#4b5563' }}>
                    {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f', borderRadius: '0.75rem' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-500 py-20 text-center">No data</p>}
          </Section>
        </div>

        {/* Charts Row 2 */}
        <div className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Line performance */}
          <Section title="Runs by Production Line" badge={`${lineData.length} lines`} badgeColor="bg-green-500/20 text-green-400">
            {lineData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={lineData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis type="number" tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <YAxis dataKey="name" type="category" width={90} tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f', borderRadius: '0.75rem' }} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} name="Runs">
                    {lineData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-500 py-10 text-center">No data</p>}
          </Section>

          {/* Shift breakdown */}
          <Section title="Runs by Shift" badge={`${shiftData.length} shifts`} badgeColor="bg-purple-500/20 text-purple-400">
            {shiftData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={shiftData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e3a5f', borderRadius: '0.75rem' }} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]} name="Runs">
                    {shiftData.map((e, i) => (
                      <Cell key={i} fill={e.name === 'DAY' ? AMBER : e.name === 'NIGHT' ? PURPLE : CYAN} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-gray-500 py-10 text-center">No data</p>}
          </Section>
        </div>

        {/* Active Runs */}
        <div className="mb-6">
          <Section title="Active Runs" badge={runs.length} badgeColor={runs.length > 0 ? "bg-green-500/20 text-green-400" : "bg-gray-700 text-gray-400"}>
            {runs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-xs text-gray-400 uppercase tracking-wider">
                      <th className="pb-3 pr-4">Run</th>
                      <th className="pb-3 pr-4">Product</th>
                      <th className="pb-3 pr-4">Line</th>
                      <th className="pb-3 pr-4">Species</th>
                      <th className="pb-3 pr-4">Shift</th>
                      <th className="pb-3">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runs.slice(0, 20).map((r, i) => (
                      <tr key={i} className="border-b border-gray-800/30 hover:bg-white/[0.02] transition">
                        <td className="py-3 pr-4 font-mono text-blue-400 font-semibold">{r.run_number}</td>
                        <td className="py-3 pr-4 font-medium">{r.description || r.product_code}</td>
                        <td className="py-3 pr-4 text-gray-400">{r.prod_line}</td>
                        <td className="py-3 pr-4 capitalize text-gray-400">{r.species}</td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold
                            ${r.shift_code === 'DAY' ? 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30' :
                              r.shift_code === 'NIGHT' ? 'bg-indigo-500/15 text-indigo-400 ring-1 ring-indigo-500/30' :
                              'bg-cyan-500/15 text-cyan-400 ring-1 ring-cyan-500/30'}`}>
                            {r.shift_code}
                          </span>
                        </td>
                        <td className="py-3 text-gray-500">{(r.production_date || '').split(' ')[0]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center">
                <div className="text-3xl mb-2">&#9989;</div>
                <p className="text-sm text-gray-500">All runs complete</p>
              </div>
            )}
          </Section>
        </div>

        {/* Compliance */}
        {comp.length > 0 && (
          <div className="mb-6">
            <Section title="Compliance Flags" badge={comp.length} badgeColor="bg-amber-500/20 text-amber-400">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-gray-700 text-xs text-gray-400 uppercase tracking-wider">
                      <th className="pb-3 pr-4">Run</th>
                      <th className="pb-3 pr-4">Product</th>
                      <th className="pb-3 pr-4">Issue</th>
                      <th className="pb-3">Giveaway</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comp.slice(0, 10).map((c, i) => (
                      <tr key={i} className="border-b border-gray-800/30 hover:bg-white/[0.02] transition">
                        <td className="py-3 pr-4 font-mono text-amber-400">{c.run_number}</td>
                        <td className="py-3 pr-4">{c.description || c.product_code}</td>
                        <td className="py-3 pr-4">
                          <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-400 ring-1 ring-amber-500/20">
                            {c.giveaway_flag || 'Flag'}
                          </span>
                        </td>
                        <td className="py-3">
                          <span className={`font-bold ${parseFloat(c.giveaway_pct) > 3.5 ? 'text-red-400' : 'text-amber-400'}`}>
                            {c.giveaway_pct}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {comp.length > 10 && (
                  <p className="mt-3 text-xs text-gray-500 text-center">Showing 10 of {comp.length} flags</p>
                )}
              </div>
            </Section>
          </div>
        )}

        {/* Footer */}
        <div className="text-center py-6 border-t border-gray-800/50 mt-8">
          <p className="text-xs text-gray-600">
            Production Analytics Pipeline &mdash; FastAPI + Next.js + dbt &mdash; Auto-refreshes every 60s
          </p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="h-1.5 w-1.5 rounded-full bg-green-500" />
            <span className="text-xs text-gray-600">Live</span>
          </div>
        </div>
      </div>
    </main>
  )
}
