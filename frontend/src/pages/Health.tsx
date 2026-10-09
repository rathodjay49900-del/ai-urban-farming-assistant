import { motion } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { Activity, Droplets, AlertTriangle, Loader2, ScanLine } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  statsApi, plantApi, scannerApi,
  type DashboardStats, type Plant, type ScanHistoryItem, type HealthLogItem,
} from '../services/api';

const fmtDate = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString() : '—';

export default function Health() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [plants, setPlants] = useState<Plant[]>([]);
  const [scans, setScans] = useState<ScanHistoryItem[]>([]);
  const [logs, setLogs] = useState<HealthLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [s, p, sc] = await Promise.all([
          statsApi.dashboard(),
          plantApi.list(),
          scannerApi.history(),
        ]);
        if (!active) return;
        setStats(s);
        setPlants(p);
        setScans(sc);
        const histories = await Promise.all(
          p.map((pl) => plantApi.healthHistory(pl.id).catch(() => [] as HealthLogItem[])),
        );
        if (!active) return;
        setLogs(histories.flat());
      } catch {
        if (active) setError('Could not load health analytics. Is the backend running?');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  // Daily average health across every recorded health log.
  const trend = (() => {
    const byDay = new Map<string, number[]>();
    for (const log of logs) {
      const day = (log.created_at || '').slice(0, 10);
      if (!day) continue;
      if (!byDay.has(day)) byDay.set(day, []);
      byDay.get(day)!.push(log.health_score);
    }
    return Array.from(byDay.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([day, scores]) => ({
        name: day.slice(5),
        score: Math.round(scores.reduce((sum, v) => sum + v, 0) / scores.length),
      }));
  })();

  const plantBars = plants.map((p) => ({ name: p.name, score: p.health_score }));
  const diseaseAlerts = scans.filter((s) => s.disease);
  const uncertainScans = scans.filter((s) => s.needs_expert && !s.disease);
  const attentionPlants = plants.filter((p) => (p.status || '').toLowerCase() !== 'healthy');
  const hasAnyData = plants.length > 0 || scans.length > 0 || logs.length > 0;

  const cards = [
    {
      label: 'Average Health',
      value: `${stats?.average_health ?? 0}%`,
      sub: stats && stats.total_plants ? `Across ${stats.total_plants} plant(s)` : 'No plants yet',
      icon: Activity,
      color: 'text-primary',
    },
    {
      label: 'Scans Logged',
      value: String(stats?.total_scans ?? 0),
      sub: `${stats?.healthy_scans ?? 0} healthy · ${stats?.diseased_scans ?? 0} diseased`,
      icon: ScanLine,
      color: 'text-sky',
    },
    {
      label: 'Disease Detections',
      value: String(stats?.diseased_scans ?? 0),
      sub: 'From AI scans',
      icon: AlertTriangle,
      color: 'text-danger',
    },
    {
      label: 'Needs Attention',
      value: String(stats?.needs_attention ?? 0),
      sub: 'Plants not marked healthy',
      icon: Droplets,
      color: 'text-warning',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-heading font-bold text-text mb-2">Plant Health Analytics</h1>
        <p className="text-muted">Real health data from your registered plants and scan history.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-muted gap-3">
          <Loader2 className="w-6 h-6 animate-spin" /> Loading analytics...
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl px-6 py-4 text-sm">{error}</div>
      ) : !hasAnyData ? (
        <div className="bg-card border border-dashed border-border rounded-3xl p-16 text-center">
          <div className="text-5xl mb-4">📊</div>
          <h3 className="text-xl font-bold text-text mb-2">No health data yet</h3>
          <p className="text-muted">Add a plant or run a scan to start collecting analytics.</p>
        </div>
      ) : (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {cards.map((card, i) => (
              <motion.div
                key={card.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-card rounded-2xl p-6 shadow-sm border border-border"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className={`p-3 bg-gray-50 rounded-xl ${card.color}`}>
                    <card.icon className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-sm text-muted font-medium">{card.label}</p>
                    <h3 className="text-2xl font-bold text-text">{card.value}</h3>
                  </div>
                </div>
                <p className="text-xs text-muted font-medium">{card.sub}</p>
              </motion.div>
            ))}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} className="bg-card rounded-2xl p-6 shadow-sm border border-border">
              <h3 className="text-lg font-heading font-semibold mb-6">Average Health Trend</h3>
              {trend.length === 0 ? (
                <p className="text-muted text-sm py-16 text-center">No health history recorded yet.</p>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trend}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dx={-10} domain={[0, 100]} />
                      <Tooltip
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        cursor={{ stroke: '#16A34A', strokeWidth: 1, strokeDasharray: '4 4' }}
                      />
                      <Line type="monotone" dataKey="score" stroke="#16A34A" strokeWidth={3} dot={{ fill: '#16A34A', strokeWidth: 2, r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>

            <motion.div initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }} className="bg-card rounded-2xl p-6 shadow-sm border border-border">
              <h3 className="text-lg font-heading font-semibold mb-6">Latest Health by Plant</h3>
              {plantBars.length === 0 ? (
                <p className="text-muted text-sm py-16 text-center">No plants registered yet.</p>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={plantBars}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dx={-10} domain={[0, 100]} />
                      <Tooltip
                        cursor={{ fill: '#F1F5F9' }}
                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                      />
                      <Bar dataKey="score" fill="#0EA5E9" radius={[6, 6, 0, 0]} barSize={40} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>
          </div>

          {/* Alerts */}
          <div className="bg-card rounded-2xl p-6 shadow-sm border border-border">
            <h3 className="text-lg font-heading font-semibold mb-6">Alerts</h3>
            {diseaseAlerts.length === 0 && uncertainScans.length === 0 && attentionPlants.length === 0 ? (
              <p className="text-muted text-sm">No active alerts. All tracked plants look healthy.</p>
            ) : (
              <div className="space-y-3">
                {attentionPlants.map((p) => (
                  <div key={`plant-${p.id}`} className="flex items-start gap-3 p-4 rounded-xl bg-red-50 border border-red-100">
                    <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-semibold text-red-800">{p.name} — {p.status}</p>
                      <p className="text-red-700">Health score {p.health_score}%. Review care and consider a scan.</p>
                    </div>
                  </div>
                ))}
                {diseaseAlerts.map((s) => (
                  <div key={`scan-${s.id}`} className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 border border-amber-100">
                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-semibold text-amber-900">
                        {s.crop || 'Crop'} — {s.disease}
                        {s.confidence != null ? ` (${s.confidence}%)` : ''}
                      </p>
                      <p className="text-amber-800">Detected on {fmtDate(s.created_at)}. Follow the scan treatment plan.</p>
                    </div>
                  </div>
                ))}
                {uncertainScans.map((s) => (
                  <div key={`unc-${s.id}`} className="flex items-start gap-3 p-4 rounded-xl bg-gray-50 border border-border">
                    <AlertTriangle className="w-5 h-5 text-muted flex-shrink-0 mt-0.5" />
                    <div className="text-sm">
                      <p className="font-semibold text-text">Inconclusive scan on {fmtDate(s.created_at)}</p>
                      <p className="text-muted">Confidence too low — expert verification recommended.</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
