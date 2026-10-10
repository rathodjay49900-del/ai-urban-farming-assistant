import { motion, AnimatePresence } from 'framer-motion';
import { Droplets, Activity, Plus, QrCode, Printer, X, History, LayoutGrid, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { plantApi, scannerApi, type Plant, type HealthLogItem, type ScanHistoryItem } from '../services/api';

const typeEmoji: Record<string, string> = {
  tomato: '🍅', chilli: '🌶️', chili: '🌶️', mint: '🌿', basil: '🌱',
  rose: '🌹', potato: '🥔', spinach: '🥬', default: '🪴',
};

function emojiFor(type: string): string {
  const key = (type || '').toLowerCase();
  return typeEmoji[key] || typeEmoji.default;
}

export default function Plants() {
  const [plants, setPlants] = useState<Plant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [qrModal, setQrModal] = useState<number | null>(null);
  const [journalModal, setJournalModal] = useState<number | null>(null);
  const [is3DView, setIs3DView] = useState(false);
  const [journalLogs, setJournalLogs] = useState<HealthLogItem[]>([]);
  const [journalScans, setJournalScans] = useState<ScanHistoryItem[]>([]);
  const [journalLoading, setJournalLoading] = useState(false);

  useEffect(() => {
    plantApi.list()
      .then(setPlants)
      .catch(() => setError('Could not load plants. Is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  // Load the real health + scan history when the journal is opened.
  useEffect(() => {
    if (journalModal == null) return;
    setJournalLoading(true);
    Promise.all([
      plantApi.healthHistory(journalModal).catch(() => [] as HealthLogItem[]),
      scannerApi.history(journalModal).catch(() => [] as ScanHistoryItem[]),
    ])
      .then(([logs, scans]) => { setJournalLogs(logs); setJournalScans(scans); })
      .finally(() => setJournalLoading(false));
  }, [journalModal]);

  const activePlant = plants.find(p => p.id === qrModal);
  const journalPlant = plants.find(p => p.id === journalModal);

  return (
    <div className="max-w-6xl mx-auto py-8 relative">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold text-text mb-2">My Plants</h1>
          <p className="text-muted">Manage and monitor all your green friends.</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setIs3DView(!is3DView)}
            className={`px-4 py-3 rounded-xl font-medium shadow-sm flex items-center gap-2 transition-colors ${
              is3DView ? 'bg-primary text-white' : 'bg-white border border-border text-text hover:bg-gray-50'
            }`}
          >
            <LayoutGrid className="w-5 h-5" />
            {is3DView ? 'List View' : '3D View'}
          </button>
          <Link to="/plants/add" className="eco-gradient-bg text-white px-6 py-3 rounded-xl font-medium shadow-sm flex items-center gap-2 hover:shadow-md transition-shadow">
            <Plus className="w-5 h-5" />
            Add Plant
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-muted gap-3">
          <Loader2 className="w-6 h-6 animate-spin" /> Loading your plants...
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-2xl px-6 py-4 text-sm">{error}</div>
      ) : plants.length === 0 ? (
        <div className="bg-card border border-dashed border-border rounded-3xl p-16 text-center">
          <div className="text-5xl mb-4">🪴</div>
          <h3 className="text-xl font-bold text-text mb-2">No plants yet</h3>
          <p className="text-muted mb-6">Register your first plant to start AI monitoring.</p>
          <Link to="/plants/add" className="eco-gradient-bg text-white px-6 py-3 rounded-xl font-medium inline-flex items-center gap-2">
            <Plus className="w-5 h-5" /> Add Plant
          </Link>
        </div>
      ) : (
      <div className={`transition-all duration-700 ${is3DView ? 'py-20 flex justify-center perspective-[2000px]' : ''}`}>
        <div className={
          is3DView 
            ? "grid grid-cols-2 gap-x-12 gap-y-24 w-full max-w-2xl transform rotate-x-[60deg] rotate-z-[-45deg] scale-125 translate-y-12" 
            : "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        }>
        {plants.map((plant, i) => (
          <motion.div
            key={plant.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className={`bg-card rounded-2xl overflow-hidden shadow-sm border border-border group hover:shadow-md transition-all duration-500 ${
              is3DView ? 'shadow-2xl hover:-translate-y-8 hover:scale-105' : ''
            }`}
          >
            <div className="h-32 bg-gradient-to-br from-green-50 to-green-100 flex items-center justify-center text-6xl group-hover:scale-110 transition-transform duration-500 relative">
              {plant.image
                ? <img src={plant.image} alt={plant.name} className="w-20 h-20 object-cover rounded-2xl" />
                : emojiFor(plant.type)}
              <button 
                onClick={() => setQrModal(plant.id)}
                className="absolute top-3 right-3 bg-white p-2 rounded-lg shadow-sm text-gray-500 hover:text-primary hover:scale-105 transition-all"
                title="Generate Smart QR Tag"
              >
                <QrCode className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-text">{plant.name}</h3>
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${
                    plant.status === 'Healthy' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {plant.status}
                  </span>
                </div>
                <div className="w-12 h-12 rounded-full border-4 border-green-100 flex items-center justify-center font-bold text-green-600 text-sm">
                  {plant.health_score}%
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-muted">
                    <Activity className="w-4 h-4" /> Health Score
                  </div>
                  <span className="font-medium">{plant.health_score}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2 text-muted">
                    <Droplets className="w-4 h-4" /> Soil Moisture
                  </div>
                  <span className="font-medium">{plant.soil_moisture != null ? `${plant.soil_moisture}%` : '—'}</span>
                </div>
              </div>

              <button 
                onClick={() => setJournalModal(plant.id)}
                className="w-full py-3 rounded-xl border border-border font-medium text-text hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
              >
                <History className="w-4 h-4" /> Growth Journal
              </button>
            </div>
          </motion.div>
        ))}
      </div>
      </div>
      )}

      {/* QR Code Modal */}
      <AnimatePresence>
        {qrModal && activePlant && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setQrModal(null)}
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-3xl p-8 max-w-sm w-full relative text-center shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              <button 
                onClick={() => setQrModal(null)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-800"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="mb-2">
                <span className="bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase">
                  Smart Plant Tag
                </span>
              </div>
              <h2 className="text-2xl font-bold mt-4 mb-1">{activePlant.name}</h2>
              <p className="text-muted text-sm mb-8">Stick this QR code on your real plant pot!</p>
              
              <div className="bg-gray-50 p-6 rounded-2xl border-2 border-dashed border-gray-200 inline-block mb-8">
                <img 
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://leaflogic.ai/plant/${activePlant.id}`} 
                  alt="QR Code" 
                  className="w-48 h-48 mx-auto"
                />
              </div>
              
              <button 
                onClick={() => window.print()}
                className="w-full bg-primary text-white py-4 rounded-xl font-bold shadow-lg shadow-primary/30 flex items-center justify-center gap-2 hover:bg-primary/90 transition-all active:scale-95"
              >
                <Printer className="w-5 h-5" />
                Print QR Tag
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Journal Modal */}
      <AnimatePresence>
        {journalModal && journalPlant && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setJournalModal(null)}
          >
            <motion.div 
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white rounded-3xl p-6 max-w-2xl w-full relative shadow-2xl overflow-hidden"
              onClick={e => e.stopPropagation()}
            >
              <button 
                onClick={() => setJournalModal(null)}
                className="absolute top-6 right-6 text-gray-400 hover:text-gray-800 z-10"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="mb-6 flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-green-50 to-green-100 rounded-2xl flex items-center justify-center text-3xl shadow-sm">
                  {emojiFor(journalPlant.type)}
                </div>
                <div>
                  <h2 className="text-2xl font-bold">{journalPlant.name}</h2>
                  <p className="text-muted text-sm">Growth Timeline & Journal</p>
                </div>
              </div>

              <div className="relative border-l-2 border-green-100 ml-4 py-2 space-y-8">
                {journalLoading ? (
                  <div className="flex items-center gap-3 pl-8 text-muted text-sm">
                    <Loader2 className="w-5 h-5 animate-spin" /> Loading history...
                  </div>
                ) : journalLogs.length === 0 && journalScans.length === 0 ? (
                  <p className="pl-8 text-sm text-muted">No health or scan history recorded for this plant yet.</p>
                ) : (
                  <>
                    {journalLogs.map((log) => (
                      <div key={`health-${log.id}`} className="relative pl-8">
                        <div className="absolute w-4 h-4 rounded-full bg-primary -left-[9px] top-1 border-4 border-white"></div>
                        <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-bold text-sm text-primary">
                              {log.created_at ? new Date(log.created_at).toLocaleDateString() : '—'}
                            </span>
                            <span className="text-xs font-semibold bg-white px-2 py-1 rounded-md border border-gray-200">
                              {log.health_score}% · {log.status}
                            </span>
                          </div>
                          <p className="text-sm text-text leading-relaxed">{log.note || 'Health recorded.'}</p>
                        </div>
                      </div>
                    ))}
                    {journalScans.map((scan) => (
                      <div key={`scan-${scan.id}`} className="relative pl-8">
                        <div className="absolute w-4 h-4 rounded-full bg-sky-500 -left-[9px] top-1 border-4 border-white"></div>
                        <div className="bg-sky-50/50 rounded-2xl p-4 border border-sky-100">
                          <div className="flex justify-between items-start mb-2">
                            <span className="font-bold text-sm text-sky-700">
                              Scan — {scan.created_at ? new Date(scan.created_at).toLocaleDateString() : '—'}
                            </span>
                            <span className="text-xs font-semibold bg-white px-2 py-1 rounded-md border border-gray-200">
                              {scan.confidence != null ? `${scan.confidence}%` : ''}
                            </span>
                          </div>
                          <p className="text-sm text-text leading-relaxed">
                            {scan.disease
                              ? `Detected: ${scan.disease}`
                              : scan.needs_expert
                                ? 'Inconclusive scan — expert verification recommended.'
                                : 'No disease detected.'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
