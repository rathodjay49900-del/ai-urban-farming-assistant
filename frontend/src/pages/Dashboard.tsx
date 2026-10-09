import { motion } from 'framer-motion';
import { Leaf, Droplets, AlertTriangle, CloudSun, Flame, Award, Cpu, Wifi, Bell, X, DollarSign, Cloud, Download, FileText, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { statsApi, type DashboardStats } from '../services/api';

export default function Dashboard() {
  const [moisture, setMoisture] = useState(34);
  const [sosModal, setSosModal] = useState(false);
  const [pdfStatus, setPdfStatus] = useState<'idle' | 'generating' | 'done'>('idle');
  const [stats, setStats] = useState<DashboardStats | null>(null);

  // Simulate live sensor data
  useEffect(() => {
    const interval = setInterval(() => {
      setMoisture(prev => prev > 20 ? prev - 1 : 45); // Fluctuate between 20 and 45
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    statsApi.dashboard().then(setStats).catch(() => setStats(null));
  }, []);

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
            <div className="flex items-center gap-3 mb-2">
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1 backdrop-blur-md">
                <Flame className="w-4 h-4 text-orange-300" /> 12 Day Streak!
              </span>
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1 backdrop-blur-md">
                <Award className="w-4 h-4 text-yellow-300" /> 450 Leaf Coins
              </span>
            </div>
            <h1 className="text-4xl font-heading font-bold mb-4">
              Your Garden,<br />Powered by AI. 🌱
            </h1>
            <p className="text-green-50 mb-6 max-w-md">
              Monitor plant health. Detect diseases. Earn rewards for keeping your urban jungle alive.
            </p>
            <div className="flex flex-wrap gap-4 mt-6">
              <Link to="/scanner" className="bg-white text-primary px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-shadow">
                Scan a Plant
              </Link>
              <button 
                onClick={() => setSosModal(true)}
                className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-all flex items-center gap-2 animate-pulse"
              >
                <Bell className="w-5 h-5" />
                SOS Emergency
              </button>
              <button 
                onClick={() => {
                  setPdfStatus('generating');
                  setTimeout(() => setPdfStatus('done'), 2500);
                  setTimeout(() => setPdfStatus('idle'), 5000);
                }}
                className="bg-white/20 hover:bg-white/30 backdrop-blur-md text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2 border border-white/30"
              >
                {pdfStatus === 'idle' && <><Download className="w-5 h-5" /> Export PDF</>}
                {pdfStatus === 'generating' && <><FileText className="w-5 h-5 animate-pulse" /> Generating...</>}
                {pdfStatus === 'done' && <><CheckCircle className="w-5 h-5 text-green-300" /> Downloaded!</>}
              </button>
            </div>
          </div>
          
          <div className="bg-white/20 backdrop-blur-md rounded-2xl p-6 border border-white/30 text-center min-w-[200px]">
            <p className="text-sm font-medium text-green-50 mb-2">Garden Health Score</p>
            <div className="text-5xl font-bold flex items-center justify-center gap-1">
              {stats?.average_health ?? 0}<span className="text-2xl opacity-80">%</span>
            </div>
            <p className="text-xs text-green-100 mt-2">Top 5% of Urban Farmers 🏆</p>
          </div>
        </div>
      </motion.div>

      {/* Stats Grid */}
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

      {/* Sustainability & Eco-Impact */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl p-6 shadow-sm text-white md:col-span-2 relative overflow-hidden"
        >
          <div className="relative z-10 flex flex-col md:flex-row items-center gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Leaf className="w-5 h-5 text-green-200" />
                <h2 className="text-xl font-bold">Eco-Hero Impact</h2>
              </div>
              <p className="text-green-50 text-sm mb-6 max-w-sm">By growing your own food, you are directly reducing carbon emissions and plastic waste.</p>
              
              <div className="flex gap-8">
                <div>
                  <p className="text-green-100 text-xs font-medium mb-1">CO₂ Absorbed</p>
                  <p className="text-3xl font-bold flex items-baseline gap-1">12.5 <span className="text-lg font-medium text-green-200">kg</span></p>
                </div>
                <div>
                  <p className="text-green-100 text-xs font-medium mb-1">Plastic Saved</p>
                  <p className="text-3xl font-bold flex items-baseline gap-1">28 <span className="text-lg font-medium text-green-200">wrappers</span></p>
                </div>
              </div>
            </div>
            
            <div className="w-32 h-32 bg-white/10 rounded-full border-[8px] border-white/20 flex flex-col items-center justify-center flex-shrink-0">
              <Cloud className="w-8 h-8 mb-1" />
              <span className="font-bold text-center leading-tight">Top 10%<br/><span className="text-xs font-normal">in City</span></span>
            </div>
          </div>
          <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-white opacity-5 rounded-full blur-2xl"></div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="bg-card rounded-2xl p-6 shadow-sm border border-border flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center gap-2 mb-4">
              <DollarSign className="w-5 h-5 text-green-600" />
              <h2 className="text-lg font-bold text-text">Grocery Savings</h2>
            </div>
            <p className="text-sm text-muted mb-2">Value of your harvested Tomatoes, Basil, and Mint this month.</p>
          </div>
          
          <div>
            <div className="text-4xl font-bold text-green-600 mb-2">₹1,240</div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div className="bg-green-500 h-2 rounded-full" style={{ width: '75%' }}></div>
            </div>
            <p className="text-xs text-muted mt-2 text-right">75% of monthly goal (₹1,500)</p>
          </div>
        </motion.div>
      </div>

      {/* IoT Sensors & Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Simulated IoT Sensor Widget */}
        <motion.div 
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-card rounded-2xl p-6 shadow-sm border border-border lg:col-span-1 relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-4">
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
          </div>
          
          <div className="flex items-center gap-3 mb-6">
            <Cpu className="w-6 h-6 text-indigo-500" />
            <h2 className="text-lg font-heading font-semibold">Live Smart Sensors</h2>
          </div>
          
          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted flex items-center gap-2"><Droplets className="w-4 h-4"/> Soil Moisture</span>
                <span className={`font-bold ${moisture < 30 ? 'text-red-500' : 'text-sky-500'}`}>{moisture}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div className={`h-2 rounded-full transition-all duration-1000 ${moisture < 30 ? 'bg-red-500' : 'bg-sky-500'}`} style={{ width: `${moisture}%` }}></div>
              </div>
              {moisture < 30 && <p className="text-xs text-red-500 mt-2 font-medium">Critical: Balcony planters need water!</p>}
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted flex items-center gap-2"><CloudSun className="w-4 h-4"/> Ambient Light</span>
                <span className="font-bold text-amber-500">Lux 4,200</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div className="bg-amber-400 h-2 rounded-full" style={{ width: '65%' }}></div>
              </div>
            </div>
            
            <div className="bg-indigo-50 rounded-xl p-3 flex items-center gap-3 border border-indigo-100">
              <Wifi className="w-5 h-5 text-indigo-400" />
              <p className="text-xs text-indigo-800 font-medium">IoT Hub connected. Last sync: just now.</p>
            </div>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-card rounded-2xl p-6 shadow-sm border border-border lg:col-span-2"
        >
           <h2 className="text-lg font-heading font-semibold mb-6">Smart Recommendations</h2>
           <div className="space-y-4">
             {[
               { title: 'Plant Care', msg: 'Your basil needs more sunlight.', icon: '🌱' },
               { title: 'Watering', msg: 'Tomato should be watered today.', icon: '💧' },
               { title: 'Health Alert', msg: 'Chilli health score dropped by 8%.', icon: '⚠️' }
             ].map((rec, i) => (
               <div key={i} className="flex items-start gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors border border-transparent hover:border-border cursor-pointer">
                 <div className="text-2xl">{rec.icon}</div>
                 <div className="flex-1">
                   <h4 className="font-semibold text-sm text-text">{rec.title}</h4>
                   <p className="text-sm text-muted">{rec.msg}</p>
                 </div>
                 <button className="text-primary text-sm font-medium self-center bg-primary/10 px-3 py-1 rounded-lg">Fix</button>
               </div>
             ))}
           </div>
        </motion.div>
      </div>
      {/* SOS Modal */}
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
            <h2 className="text-2xl font-bold text-center mb-2">Plant Emergency!</h2>
            <p className="text-center text-muted mb-6">
              AI is initiating a fast-track diagnostic and alerting 3 expert gardeners in your area.
            </p>
            <div className="space-y-3">
              <Link to="/scanner" className="w-full block text-center bg-red-500 text-white py-3 rounded-xl font-medium hover:bg-red-600">
                Start Emergency Scan
              </Link>
              <button className="w-full py-3 rounded-xl border border-border font-medium hover:bg-gray-50">
                Call Local Nursery (Simulated)
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
