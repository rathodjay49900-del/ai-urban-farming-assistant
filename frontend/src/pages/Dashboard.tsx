import { motion } from 'framer-motion';
import { Leaf, Droplets, AlertTriangle, Bell, X, Printer, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  statsApi, plantApi, wateringApi,
  type DashboardStats, type Plant, type WateringRecommendation,
} from '../services/api';

export default function Dashboard() {
  const [sosModal, setSosModal] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [plants, setPlants] = useState<Plant[]>([]);
  const [recs, setRecs] = useState<WateringRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [backendDown, setBackendDown] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([statsApi.dashboard(), plantApi.list(), wateringApi.recommendations()])
      .then(([s, p, r]) => {
        if (!active) return;
        setStats(s);
        setPlants(p);
        setRecs(r);
      })
      .catch(() => { if (active) setBackendDown(true); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const dueNow = recs.filter((r) => r.water_now);
  const withMoisture = plants.filter((p) => p.soil_moisture != null);
  const attention = plants.filter((p) => (p.status || '').toLowerCase() !== 'healthy');

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl p-8 eco-gradient-bg text-white relative overflow-hidden"
      >
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h1 className="text-4xl font-heading font-bold mb-4">
              Your Garden,<br />Powered by AI. 🌱
            </h1>
            <p className="text-green-50 mb-6 max-w-md">
              Monitor plant health. Detect diseases. Water on schedule.
            </p>
            <div className="flex flex-wrap gap-4 mt-6">
              <Link to="/scanner" className="bg-white text-primary px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-shadow">
                Scan a Plant
              </Link>
              <button
                onClick={() => setSosModal(true)}
                className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-all flex items-center gap-2"
              >
                <Bell className="w-5 h-5" />
                Plant Emergency
              </button>
              <button
                onClick={() => window.print()}
                className="bg-white/20 hover:bg-white/30 backdrop-blur-md text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 border border-white/30"
              >
                <Printer className="w-5 h-5" /> Print
              </button>
            </div>
          </div>

          <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 border border-white/30 text-center min-w-[200px]">
            <p className="text-sm font-medium text-green-50 mb-2">Garden Health Score</p>
            <div className="text-5xl font-bold flex items-center justify-center gap-1">
              {stats?.average_health ?? 0}<span className="text-2xl opacity-80">%</span>
            </div>
            <p className="text-xs text-green-100 mt-2">
              {stats && stats.total_plants > 0
                ? `Average across ${stats.total_plants} plant(s)`
                : 'Add a plant to start tracking'}
            </p>
          </div>
        </div>
      </motion.div>

      {backendDown && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl px-6 py-4 text-sm">
          Could not reach the backend. Start it with <code>uvicorn main:app --reload</code> from the
          <code> backend</code> folder, then refresh this page.
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted gap-3">
          <Loader2 className="w-6 h-6 animate-spin" /> Loading your garden...
        </div>
      ) : (
        <>
          {/* Stats Grid — all values from /api/stats/dashboard */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Plants', value: String(stats?.total_plants ?? 0), sub: `${stats?.total_scans ?? 0} scans logged`, icon: Leaf, color: 'text-primary' },
              { label: 'Healthy Plants', value: String(stats?.healthy_plants ?? 0), sub: stats && stats.total_plants ? `${Math.round((stats.healthy_plants / stats.total_plants) * 100)}% healthy` : 'no plants yet', icon: Leaf, color: 'text-success' },
              { label: 'Need Attention', value: String(stats?.needs_attention ?? 0), sub: 'Requires action', icon: AlertTriangle, color: 'text-danger' },
              { label: 'Water Today', value: String(stats?.water_today ?? 0), sub: 'plants need water', icon: Droplets, color: 'text-sky' },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-card rounded-2xl p-6 shadow-sm border border-border"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className={`p-3 rounded-xl bg-gray-50 ${stat.color}`}>
                    <stat.icon className="w-6 h-6" />
                  </div>
                </div>
                <h3 className="text-3xl font-bold text-text mb-1">{stat.value}</h3>
                <p className="text-sm font-medium text-text">{stat.label}</p>
                <p className="text-xs text-muted mt-1">{stat.sub}</p>
              </motion.div>
            ))}
          </div>

          {/* Watering due + recorded moisture — real backend data */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-card rounded-2xl p-6 shadow-sm border border-border"
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-heading font-semibold flex items-center gap-2">
                  <Droplets className="w-5 h-5 text-sky-500" /> Needs Water Today
                </h2>
                <Link to="/watering" className="text-sm font-medium text-primary hover:underline">
                  Open Watering →
                </Link>
              </div>
              {dueNow.length === 0 ? (
                <p className="text-muted text-sm py-8 text-center">
                  {plants.length === 0
                    ? 'No plants registered yet.'
                    : 'Nothing due right now. All plants are on schedule.'}
                </p>
              ) : (
                <div className="space-y-3">
                  {dueNow.slice(0, 5).map((r) => (
                    <div key={r.plant_id ?? r.plant_name} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                      <div>
                        <p className="font-semibold text-sm text-text">{r.plant_name}</p>
                        <p className="text-xs text-muted">{r.reason}</p>
                      </div>
                      <span className="text-sm font-bold text-sky-600">
                        {r.amount_ml != null ? `${r.amount_ml} ml` : 'Due'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-card rounded-2xl p-6 shadow-sm border border-border"
            >
              <h2 className="text-lg font-heading font-semibold mb-1">Recorded Soil Moisture</h2>
              <p className="text-xs text-muted mb-4">
                Values you entered for your plants — not live sensor readings.
              </p>
              {withMoisture.length === 0 ? (
                <p className="text-muted text-sm py-8 text-center">
                  No moisture values recorded yet.
                </p>
              ) : (
                <div className="space-y-4">
                  {withMoisture.slice(0, 5).map((p) => (
                    <div key={p.id}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-text">{p.name}</span>
                        <span className={`font-bold ${p.soil_moisture != null && p.soil_moisture < 30 ? 'text-red-500' : 'text-sky-500'}`}>
                          {p.soil_moisture}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${p.soil_moisture != null && p.soil_moisture < 30 ? 'bg-red-500' : 'bg-sky-500'}`}
                          style={{ width: `${p.soil_moisture ?? 0}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </div>

          {/* Plants needing attention — real statuses */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-card rounded-2xl p-6 shadow-sm border border-border"
          >
            <h2 className="text-lg font-heading font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-warning" /> Needs Attention
            </h2>
            {plants.length === 0 ? (
              <p className="text-muted text-sm">
                No plants yet. <Link to="/plants/add" className="text-primary font-medium hover:underline">Add your first plant</Link> to start monitoring.
              </p>
            ) : attention.length === 0 ? (
              <p className="text-muted text-sm">All tracked plants are marked healthy. 🎉</p>
            ) : (
              <div className="space-y-3">
                {attention.map((p) => (
                  <div key={p.id} className="flex items-start gap-4 p-4 rounded-xl bg-red-50 border border-red-100">
                    <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-sm text-red-800">{p.name} — {p.status}</p>
                      <p className="text-sm text-red-700">Health score {p.health_score}%. Consider running a scan.</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </>
      )}

      {/* Emergency Modal — honest guidance, no fake expert alerts */}
      {sosModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            className="bg-white rounded-3xl p-8 max-w-md w-full relative"
          >
            <button onClick={() => setSosModal(false)} className="absolute top-4 right-4 text-gray-400 hover:text-gray-800">
              <X className="w-6 h-6" />
            </button>
            <div className="w-16 h-16 bg-red-100 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bell className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-bold text-center mb-2">Plant Emergency</h2>
            <p className="text-center text-muted mb-6">
              If a plant looks sick, run an AI scan for a diagnosis and treatment plan.
            </p>
            <div className="space-y-3">
              <Link to="/scanner" className="w-full block text-center bg-red-500 text-white py-3 rounded-xl font-medium hover:bg-red-600">
                Start Emergency Scan
              </Link>
              <button onClick={() => setSosModal(false)} className="w-full py-3 rounded-xl border border-border font-medium hover:bg-gray-50">
                Close
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
