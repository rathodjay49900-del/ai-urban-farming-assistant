import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Loader2, Droplets, ScanLine, AlertTriangle, TrendingUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  statsApi, plantApi, scannerApi, wateringApi,
  type DashboardStats, type Plant, type ScanHistoryItem, type WateringLogItem,
} from '../services/api';

const fmtDate = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString() : '—';

export default function Insights() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [plants, setPlants] = useState<Plant[]>([]);
  const [scans, setScans] = useState<ScanHistoryItem[]>([]);
  const [watering, setWatering] = useState<WateringLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [s, p, sc, w] = await Promise.all([
          statsApi.dashboard(),
          plantApi.list(),
          scannerApi.history(),
          wateringApi.logs(),
        ]);
        if (!active) return;
        setStats(s);
        setPlants(p);
        setScans(sc);
        setWatering(w);
      } catch {
        if (active) setError('Could not load insights. Is the backend running?');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, []);

  const diseaseCounts = new Map<string, number>();
  for (const s of scans) {
    if (s.disease) diseaseCounts.set(s.disease, (diseaseCounts.get(s.disease) ?? 0) + 1);
  }
  const diseaseData = Array.from(diseaseCounts, ([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  const wateringByDay = new Map<string, { ml: number; count: number }>();
  for (const log of watering) {
    const day = (log.watered_at || '').slice(0, 10);
    if (!day) continue;
    const entry = wateringByDay.get(day) ?? { ml: 0, count: 0 };
    entry.ml += log.amount_ml ?? 0;
    entry.count += 1;
    wateringByDay.set(day, entry);
  }
  const waterData = Array.from(wateringByDay.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([day, v]) => ({ name: day.slice(5), ml: Math.round(v.ml), count: v.count }));
  const totalMl = watering.reduce((sum, l) => sum + (l.amount_ml ?? 0), 0);

  const plantBars = plants.map((p) => ({ name: p.name, score: p.health_score }));
  const hasAnyData = plants.length > 0 || scans.length > 0 || watering.length > 0;

  const cards = [
    {
      label: 'Garden Health',
      value: `${stats?.average_health ?? 0}%`,
      sub: 'Average across plants',
      icon: Activity,
      color: 'text-primary',
    },
    {
      label: 'Total Scans',
      value: String(stats?.total_scans ?? 0),
      sub: `${stats?.diseased_scans ?? 0} disease detection(s)`,
      icon: ScanLine,
      color: 'text-sky',
    },
    {
      label: 'Watering Events',
      value: String(watering.length),
      sub: totalMl > 0 ? `${totalMl} ml logged` : 'No volume recorded',
      icon: Droplets,
      color: 'text-ai',
    },
    {
      label: 'Needs Attention',
      value: String(stats?.needs_attention ?? 0),
      sub: 'Plants not marked healthy',
      icon: AlertTriangle,
      color: 'text-danger',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-heading font-bold text-text mb-2 flex items-center gap-2">
          <Activity className="text-purple-500 w-8 h-8" /> Garden Insights
        </h1>
        <p className="text-muted">Analytics computed directly from your plants, scans and watering logs.</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-muted gap-3">
          <Loader2 className="w-6 h-6 animate-spin" /> Loading insights...
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl px-6 py-4 text-sm">{error}</div>
      ) : !hasAnyData ? (
        <div className="bg-card border border-dashed border-border rounded-3xl p-16 text-center">
          <div className="text-5xl mb-4">🔍</div>
          <h3 className="text-xl font-bold text-text mb-2">No data to analyze yet</h3>
          <p className="text-muted">Add a plant, run a scan or log watering to generate insights.</p>
        </div>
      ) : (
        <>
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

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Disease distribution */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-card rounded-2xl p-6 shadow-sm border border-border">
              <div className="flex items-center gap-2 mb-6">
                <TrendingUp className="text-danger w-5 h-5" />
                <h3 className="text-lg font-heading font-semibold">Disease Distribution</h3>
              </div>
              {diseaseData.length === 0 ? (
                <p className="text-muted text-sm py-16 text-center">Data not available — no disease has been detected yet.</p>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={diseaseData} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                      <XAxis type="number" allowDecimals={false} tick={{ fill: '#64748B', fontSize: 12 }} />
                      <YAxis type="category" dataKey="name" width={130} tick={{ fill: '#64748B', fontSize: 11 }} />
                      <Tooltip cursor={{ fill: '#F1F5F9' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                      <Bar dataKey="count" fill="#EF4444" radius={[0, 6, 6, 0]} barSize={22} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>

            {/* Health by plant */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-card rounded-2xl p-6 shadow-sm border border-border">
              <h3 className="text-lg font-heading font-semibold mb-6">Health by Plant</h3>
              {plantBars.length === 0 ? (
                <p className="text-muted text-sm py-16 text-center">Data not available — no plants registered.</p>
              ) : (
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={plantBars}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                      <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dy={10} />
                      <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dx={-10} domain={[0, 100]} />
                      <Tooltip cursor={{ fill: '#F1F5F9' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                      <Bar dataKey="score" fill="#16A34A" radius={[6, 6, 0, 0]} barSize={40} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </motion.div>
          </div>

          {/* Watering activity */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-card rounded-2xl p-6 shadow-sm border border-border">
            <div className="flex items-center gap-2 mb-6">
              <Droplets className="text-ai w-5 h-5" />
              <h3 className="text-lg font-heading font-semibold">Watering Activity (ml per day)</h3>
            </div>
            {waterData.length === 0 ? (
              <p className="text-muted text-sm py-12 text-center">No watering events logged yet.</p>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={waterData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 12 }} dx={-10} />
                    <Tooltip cursor={{ fill: '#F1F5F9' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Bar dataKey="ml" fill="#0EA5E9" radius={[6, 6, 0, 0]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </motion.div>

          {/* Recent scans */}
          <div className="bg-card rounded-2xl p-6 shadow-sm border border-border">
            <h3 className="text-lg font-heading font-semibold mb-6">Recent Scans</h3>
            {scans.length === 0 ? (
              <p className="text-muted text-sm">No scans recorded yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-muted border-b border-border">
                      <th className="py-3 pr-4 font-medium">Date</th>
                      <th className="py-3 pr-4 font-medium">Crop</th>
                      <th className="py-3 pr-4 font-medium">Result</th>
                      <th className="py-3 pr-4 font-medium">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scans.slice(0, 10).map((s) => (
                      <tr key={s.id} className="border-b border-border/60 last:border-0">
                        <td className="py-3 pr-4 whitespace-nowrap">{fmtDate(s.created_at)}</td>
                        <td className="py-3 pr-4">{s.crop || '—'}</td>
                        <td className="py-3 pr-4">
                          {s.disease
                            ? <span className="text-danger font-medium">{s.disease}</span>
                            : s.needs_expert
                              ? <span className="text-muted">Inconclusive</span>
                              : <span className="text-success font-medium">Healthy</span>}
                        </td>
                        <td className="py-3 pr-4">{s.confidence != null ? `${s.confidence}%` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
