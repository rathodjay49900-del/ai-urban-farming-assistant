import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, CheckCircle2, Compass, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { plantApi } from '../services/api';

export default function AddPlant() {
  const [success, setSuccess] = useState(false);
  const [arModal, setArModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: '',
    type: '',
    location: 'Balcony (East Facing)',
    image: '' as string | null,
  });
  const navigate = useNavigate();

  const { getRootProps, getInputProps } = useDropzone({
    accept: { 'image/*': [] },
    maxFiles: 1,
    onDrop: (files) => {
      const selected = files[0];
      if (!selected) return;
      const reader = new FileReader();
      reader.onload = () => setForm((f) => ({ ...f, image: String(reader.result) }));
      reader.readAsDataURL(selected);
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await plantApi.create({
        name: form.name,
        type: form.type,
        location: form.location,
        image: form.image || undefined,
      });
      setSuccess(true);
      setTimeout(() => navigate('/plants'), 2000);
    } catch (err) {
      console.error(err);
      setError('Could not save the plant. Make sure the backend is running.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-text mb-2">Add New Plant</h1>
        <p className="text-muted">Register a new plant to start AI monitoring.</p>
      </div>

      <AnimatePresence>
        {success ? (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-green-50 border border-green-200 rounded-3xl p-12 text-center"
          >
            <motion.div 
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", delay: 0.2 }}
              className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 text-success"
            >
              <CheckCircle2 className="w-10 h-10" />
            </motion.div>
            <h2 className="text-2xl font-bold text-green-800 mb-2">🌱 Plant Added Successfully!</h2>
            <p className="text-green-600">Your plant is now being monitored by AI.</p>
          </motion.div>
        ) : (
          <motion.form 
            onSubmit={handleSubmit}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-card rounded-2xl p-8 shadow-sm border border-border">
              <div 
                {...getRootProps()} 
                className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:bg-gray-50 transition-colors cursor-pointer mb-8"
              >
                <input {...getInputProps()} />
                <UploadCloud className="w-8 h-8 text-gray-400 mx-auto mb-3" />
                <p className="text-sm font-medium">Upload Plant Image</p>
                <p className="text-xs text-muted mt-1">Drag & drop or browse</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Plant Name</label>
                  <input
                    required
                    type="text"
                    placeholder="e.g. Balcony Tomato"
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text mb-2">Plant Type</label>
                  <select
                    required
                    value={form.type}
                    onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:ring-2 focus:ring-primary focus:border-transparent outline-none bg-white"
                  >
                    <option value="">Select type</option>
                    <option>Tomato</option>
                    <option>Chilli</option>
                    <option>Mint</option>
                    <option>Basil</option>
                    <option>Rose</option>
                  </select>
                </div>
                <div className="md:col-span-2">
                  <div className="flex justify-between items-center mb-2">
                    <label className="block text-sm font-medium text-text">Location & Placement</label>
                    <button 
                      type="button" 
                      onClick={() => setArModal(true)}
                      className="text-xs font-bold text-primary flex items-center gap-1 bg-primary/10 px-3 py-1 rounded-full hover:bg-primary/20 transition-colors"
                    >
                      <Compass className="w-3 h-3" />
                      AR Sun Tracker
                    </button>
                  </div>
                  <select
                    value={form.location}
                    onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                    className="w-full px-4 py-3 rounded-xl border border-border focus:ring-2 focus:ring-primary focus:border-transparent outline-none bg-white"
                  >
                    <option>Balcony (East Facing) - 🌞 Recommended</option>
                    <option>Living Room Window</option>
                    <option>Kitchen Counter</option>
                    <option>Garden</option>
                  </select>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
                {error}
              </div>
            )}

            <div className="flex justify-end gap-4">
              <button type="button" onClick={() => navigate('/plants')} className="px-6 py-3 rounded-xl font-medium text-muted hover:text-text hover:bg-gray-100 transition-colors">
                Cancel
              </button>
              <button type="submit" disabled={saving} className="eco-gradient-bg text-white px-8 py-3 rounded-xl font-medium shadow-sm hover:shadow-md transition-shadow disabled:opacity-60">
                {saving ? 'Saving...' : '+ Add Plant'}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* AR Modal Mockup */}
      <AnimatePresence>
        {arModal && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4"
          >
            <div className="bg-gray-900 w-full max-w-sm rounded-[3rem] aspect-[9/19] border-[8px] border-gray-800 relative overflow-hidden flex flex-col justify-between">
              <div className="absolute top-6 right-6 z-10">
                <button onClick={() => setArModal(false)} className="bg-black/50 text-white p-2 rounded-full">
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="flex-1 flex flex-col items-center justify-center p-6 relative">
                {/* Simulated Camera View Background */}
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1599598425947-3300262955bf?q=80&w=400')] bg-cover bg-center opacity-40 mix-blend-luminosity"></div>
                
                <div className="relative z-10 text-center">
                  <Compass className="w-16 h-16 text-yellow-400 mx-auto mb-4 animate-spin-slow" />
                  <h3 className="text-white text-xl font-bold mb-2">Analyzing Sunlight...</h3>
                  <p className="text-gray-300 text-sm mb-8">Move your phone around the room</p>
                  
                  <div className="bg-white/10 backdrop-blur-md border border-white/20 p-4 rounded-2xl text-left">
                    <p className="text-green-400 font-bold text-sm mb-1 flex items-center gap-2">✓ Perfect Spot Found</p>
                    <p className="text-white text-sm">Place your plant 2 meters to the left for optimal morning sun (East).</p>
                  </div>
                </div>
              </div>
              
              <div className="p-6 pb-10 bg-gradient-to-t from-black to-transparent relative z-10">
                <button 
                  onClick={() => setArModal(false)}
                  className="w-full bg-primary text-white py-4 rounded-full font-bold shadow-lg shadow-primary/30"
                >
                  Save Location
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
