import { motion } from 'framer-motion';
import { Droplets, CloudRain, Sun, Calendar, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { wateringApi, statsApi, type WateringRecommendation } from '../services/api';

export default function Watering() {
  const [items, setItems] = useState<WateringRecommendation[]>([]);
  const [weather, setWeather] = useState<{ summary?: string; temperature_c?: number; rain_expected?: boolean } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    Promise.all([wateringApi.recommendations(), statsApi.weather()])
      .then(([recs, wx]) => { setItems(recs); setWeather(wx); })
      .catch(() => setError('Could not load watering data. Is the backend running?'))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const waterAll = async () => {
    const due = items.filter((r) => r.water_now && r.plant_id != null);
    await Promise.all(due.map((r) => wateringApi.log({
      plant_id: r.plant_id as number,
      amount_ml: r.amount_ml ?? undefined,
    })));
    load();
  };

  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-heading font-bold text-text mb-2 flex items-center gap-2">
            <Droplets className="text-sky-500 w-8 h-8" /> Smart Irrigation
          </h1>
          <p className="text-muted">Weather-aware watering based on plant type, growth stage and soil moisture.</p>
        </div>
        <button
          onClick={waterAll}
          className="bg-sky-500 hover:bg-sky-600 text-white px-6 py-3 rounded-xl font-medium transition-colors shadow-sm"
        >
          Water All Due Plants
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-card rounded-2xl p-6 shadow-sm border border-border flex items-center gap-4">
          <div className="p-4 bg-sky-50 rounded-xl text-sky-500"><CloudRain className="w-8 h-8" /></div>
          <div>
            <p className="text-sm text-muted">Weather Now</p>
            <p className="text-xl font-bold">{weather?.summary || '—'}</p>
          </div>
        </div>
        <div className="bg-card rounded-2xl p-6 shadow-sm border border-border flex items-center gap-4">
          <div className="p-4 bg-orange-50 rounded-xl text-orange-500"><Sun className="w-8 h-8" /></div>
          <div>
            <p className="text-sm text-muted">Temperature</p>
            <p className="text-xl font-bold">{weather?.temperature_c != null ? `${weather.temperature_c}°C` : '—'}</p>
          </div>
        </div>
        <div className="bg-card rounded-2xl p-6 shadow-sm border border-border flex items-center gap-4">
          <div className="p-4 bg-green-50 rounded-xl text-primary"><Droplets className="w-8 h-8" /></div>
          <div>
            <p className="text-sm text-muted">Rain Expected</p>
            <p className="text-xl font-bold">{weather?.rain_expected ? 'Yes' : 'No'}</p>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-2xl p-6 shadow-sm border border-border">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-muted" /> Upcoming Schedule
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-16 text-muted gap-3">
            <Loader2 className="w-6 h-6 animate-spin" /> Loading schedule...
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">{error}</div>
        ) : items.length === 0 ? (
          <p className="text-muted text-center py-12">No plants to water yet. Add a plant first.</p>
        ) : (
          <div className="space-y-4">
            {items.map((item, i) => (
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                key={item.plant_id ?? i}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <h3 className="font-bold text-lg">{item.plant_name}</h3>
                  <p className="text-sm text-muted">{item.reason}</p>
                </div>
                <div className="flex-1 px-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium">Soil Moisture</span>
                    <span className={item.soil_moisture != null && item.soil_moisture < 30 ? 'text-red-500 font-bold' : 'text-sky-500 font-bold'}>
                      {item.soil_moisture != null ? `${item.soil_moisture}%` : '—'}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${item.soil_moisture != null && item.soil_moisture < 30 ? 'bg-red-500' : 'bg-sky-500'}`}
                      style={{ width: `${item.soil_moisture ?? 0}%` }}
                    ></div>
                  </div>
                </div>
                <div className="flex-1 text-right">
                  <p className={`font-bold ${item.water_now ? 'text-red-500' : 'text-text'}`}>
                    {item.water_now ? 'Water Now' : `Next: ${item.next_watering || '—'}`}
                  </p>
                  <p className="text-xs text-muted">{item.water_now ? `${item.amount_ml ?? 0} ml recommended` : 'On schedule'}</p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
