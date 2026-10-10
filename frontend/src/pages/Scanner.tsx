import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, Bot, AlertCircle, Camera, XCircle, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { scannerApi } from '../services/api';

export default function Scanner() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const selected = acceptedFiles[0];
    if (selected) {
      setFile(selected);
      setPreview(URL.createObjectURL(selected));
      setValidationError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [] },
    maxFiles: 1
  });

  const handleDemo = (type: 'healthy' | 'disease' | 'invalid') => {
    setValidationError(null);
    if (type === 'healthy') {
      setPreview('https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=800&q=80'); // Healthy plant
    } else if (type === 'disease') {
      setPreview('https://images.unsplash.com/photo-1592150621744-aca64f48394a?w=800&q=80'); // Diseased leaf
    } else {
      setPreview('https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80'); // Sneaker (Invalid)
    }
  };

  const compressImage = (input: Blob): Promise<Blob> => {
    // Shrink large phone photos (4000px, 5-8MB) to max 1024px JPEG ~200-400KB.
    // This is what makes upload + backend inference 3-5x faster.
    return new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(input);
      img.onload = () => {
        const maxEdge = 1024;
        const scale = Math.min(1, maxEdge / Math.max(img.width, img.height));
        const w = Math.round(img.width * scale);
        const h = Math.round(img.height * scale);
        const canvas = document.createElement('canvas');
        canvas.width = w;
        canvas.height = h;
        canvas.getContext('2d')?.drawImage(img, 0, 0, w, h);
        URL.revokeObjectURL(url);
        canvas.toBlob((blob) => resolve(blob || input), 'image/jpeg', 0.82);
      };
      img.onerror = () => { URL.revokeObjectURL(url); resolve(input); };
      img.src = url;
    });
  };

  const quickPlantCheck = (input: Blob): Promise<boolean> => {
    // Instant frontend guard: human/selfie photos have almost no green.
    // Returns true = looks like plant, false = definitely not a plant.
    return new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(input);
      img.onload = () => {
        try {
          const c = document.createElement('canvas');
          c.width = 64; c.height = 64;
          const ctx = c.getContext('2d');
          if (!ctx) { URL.revokeObjectURL(url); resolve(true); return; }
          ctx.drawImage(img, 0, 0, 64, 64);
          const d = ctx.getImageData(0, 0, 64, 64).data;
          let green = 0; const total = 64 * 64;
          for (let i = 0; i < d.length; i += 4) {
            const r = d[i], g = d[i + 1], b = d[i + 2];
            if (g > r && g > b && g > 40 && (g - Math.min(r, b)) > 15) green++;
          }
          URL.revokeObjectURL(url);
          resolve(green / total >= 0.08);
        } catch { URL.revokeObjectURL(url); resolve(true); }
      };
      img.onerror = () => { URL.revokeObjectURL(url); resolve(true); };
      img.src = url;
    });
  };

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setValidationError(null);
    
    try {
      let isHealthyDemo = preview?.includes('1518531933037');
      let isInvalidDemo = preview?.includes('1542291026-7eec264c27ff');

      // If it's a real file upload, we need to send it to the backend
      const formData = new FormData();

      // Instant "Plant unavailable" pop-up for human/selfie photos —
      // no backend call, no plant info shown at all.
      const PLANT_UNAVAILABLE = "Plant unavailable — this photo doesn't look like a plant. Please upload a clear photo of a leaf or plant.";
      if (file) {
        const looksPlant = await quickPlantCheck(file);
        if (!looksPlant) {
          setIsAnalyzing(false);
          setValidationError(PLANT_UNAVAILABLE);
          return;
        }
        const small = await compressImage(file);
        formData.append('file', small, 'leaf.jpg');
      } else {
        // If it's a demo, we need to fetch the image blob and send it
        const response = await fetch(preview!);
        const blob = await response.blob();
        const small = await compressImage(blob);
        formData.append('file', small, 'demo_image.jpg');
        
        if (isInvalidDemo) {
          formData.append('simulate_invalid', 'true');
        }
        if (isHealthyDemo) {
          formData.append('simulate_healthy', 'true');
        }
      }

      // Call the FastAPI backend (gatekeeper + disease predictor combined endpoint)
      const data = await scannerApi.analyze(formData);

      if (!data.success || !data.is_plant_related) {
        setIsAnalyzing(false);
        setValidationError(data.message || "Plant unavailable — this photo doesn't look like a plant. Please upload a clear photo of a leaf or plant.");
        return;
      }

      const previewUrl = preview || (file ? URL.createObjectURL(file) : null);
      if (isHealthyDemo || (data.message === "Your Plant Looks Healthy")) {
        navigate('/scanner/result/demo-healthy', { state: { result: data, preview: previewUrl } });
      } else {
        navigate('/scanner/result/demo-disease', { state: { result: data, preview: previewUrl } });
      }

    } catch (err) {
      console.error(err);
      setIsAnalyzing(false);
      setValidationError("Failed to connect to the AI engine. Make sure the backend is running.");
    }
  };

  const resetScanner = () => {
    setFile(null);
    setPreview(null);
    setValidationError(null);
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-heading font-bold mb-3 text-text">AI Plant Health Scanner</h1>
        <p className="text-muted">Upload a clear photo of a plant or leaf to analyze its health.</p>
      </div>

      <div className="bg-card rounded-3xl p-6 md:p-8 shadow-sm border border-border">
        {!preview ? (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div 
                {...getRootProps()} 
                className={`border-2 border-dashed rounded-3xl p-12 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
                  isDragActive ? 'border-ai bg-indigo-50' : 'border-border hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <input {...getInputProps()} />
                <div className="w-16 h-16 bg-blue-50 text-sky rounded-full flex items-center justify-center mb-6">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-semibold text-text mb-2">Upload Image</h3>
                <p className="text-muted text-sm">Drag & drop your file here</p>
              </div>

              <label className="border-2 border-border rounded-3xl p-12 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-gray-50 hover:border-gray-300 transition-colors w-full h-full">
                <input 
                  type="file" 
                  accept="image/*" 
                  capture="environment"
                  className="hidden" 
                  onChange={(e) => {
                    const selected = e.target.files?.[0];
                    if (selected) {
                      setFile(selected);
                      setPreview(URL.createObjectURL(selected));
                      setValidationError(null);
                    }
                  }}
                />
                <div className="w-16 h-16 bg-green-50 text-primary rounded-full flex items-center justify-center mb-6">
                  <Camera className="w-8 h-8" />
                </div>
                <h3 className="text-lg font-semibold text-text mb-2">Take Photo</h3>
                <p className="text-muted text-sm">Use your device camera</p>
              </label>
            </div>
            
            <div className="pt-6 border-t border-border">
              <p className="text-sm font-medium text-text mb-4 text-center">Try Demo Mode</p>
              <div className="flex flex-wrap justify-center gap-3">
                <button onClick={() => handleDemo('disease')} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm font-medium transition-colors">Disease Demo</button>
                <button onClick={() => handleDemo('healthy')} className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm font-medium transition-colors">Healthy Demo</button>
                <button onClick={() => handleDemo('invalid')} className="px-4 py-2 bg-red-50 hover:bg-red-100 text-danger rounded-xl text-sm font-medium transition-colors">Invalid (Test Guard)</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="relative rounded-3xl overflow-hidden border border-border bg-gray-900 aspect-square md:aspect-[2/1] flex items-center justify-center">
              <img src={preview} alt="Preview" className="w-full h-full object-cover opacity-80" />
              
              <AnimatePresence>
                {validationError && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 bg-gray-900/80 backdrop-blur-md flex flex-col items-center justify-center text-white p-6 text-center"
                  >
                    <XCircle className="w-16 h-16 text-red-400 mb-4" />
                    <h2 className="text-2xl font-bold mb-2">🌱 Plant Unavailable</h2>
                    <p className="text-gray-300 max-w-md mb-6">{validationError}</p>
                    <div className="text-sm text-gray-400 mb-8 space-y-1">
                      <p>✓ A plant leaf</p>
                      <p>✓ A flower or crop</p>
                      <p>✓ A plant showing disease symptoms</p>
                    </div>
                    <button 
                      onClick={resetScanner}
                      className="bg-white text-gray-900 px-6 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-gray-100 transition-colors"
                    >
                      <RefreshCw className="w-5 h-5" />
                      Try Another Image
                    </button>
                  </motion.div>
                )}

                {isAnalyzing && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 bg-indigo-900/60 backdrop-blur-sm flex flex-col items-center justify-center text-white"
                  >
                    {/* Animated scanning line */}
                    <motion.div 
                      className="absolute left-0 right-0 h-1 bg-ai shadow-[0_0_15px_#6366F1]"
                      animate={{ top: ['0%', '100%', '0%'] }}
                      transition={{ duration: 3, ease: 'linear', repeat: Infinity }}
                    />

                    <motion.div
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="mb-6 bg-white/10 p-4 rounded-full backdrop-blur-md"
                    >
                      <Bot className="w-10 h-10 text-ai" />
                    </motion.div>
                    
                    <div className="text-xl font-bold tracking-wide mb-6">AI Vision Processing</div>
                    
                    <div className="space-y-3 text-sm font-medium">
                       <motion.div initial={{opacity:0, x:-20}} animate={{opacity:1, x:0}} transition={{delay:0.2}} className="flex items-center gap-2">
                         <div className="w-2 h-2 rounded-full bg-green-400" /> Image quality OK
                       </motion.div>
                       <motion.div initial={{opacity:0, x:-20}} animate={{opacity:1, x:0}} transition={{delay:1.2}} className="flex items-center gap-2">
                         <div className="w-2 h-2 rounded-full bg-green-400" /> Detecting plant patterns
                       </motion.div>
                       <motion.div initial={{opacity:0, x:-20}} animate={{opacity:1, x:0}} transition={{delay:2.5}} className="flex items-center gap-2">
                         <div className="w-2 h-2 rounded-full bg-blue-400" /> Identifying category
                       </motion.div>
                       <motion.div initial={{opacity:0, x:-20}} animate={{opacity:1, x:0}} transition={{delay:3.5}} className="flex items-center gap-2 text-white/50">
                         <div className="w-2 h-2 rounded-full bg-gray-400" /> Analyzing for disease...
                       </motion.div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {!isAnalyzing && !validationError && (
              <div className="flex flex-col sm:flex-row justify-between items-center bg-gray-50 p-4 rounded-2xl gap-4">
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  <div className="bg-white p-3 rounded-xl shadow-sm border border-border">
                    <UploadCloud className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text truncate max-w-[200px]">
                      {file ? file.name : 'demo_image.jpg'}
                    </p>
                    <button onClick={resetScanner} className="text-xs text-danger font-medium hover:underline">Remove</button>
                  </div>
                </div>
                
                <button 
                  onClick={handleAnalyze}
                  className="w-full sm:w-auto ai-gradient-bg text-white px-8 py-4 rounded-xl font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-3"
                >
                  <Bot className="w-6 h-6" />
                  Scan with AI
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-100 rounded-2xl p-4 flex gap-3 text-blue-800 text-sm">
        <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          AI-generated recommendations are for general plant-care guidance and may not replace advice from a professional agronomist. Our AI is specialized exclusively for plants and farming.
        </p>
      </div>

    </div>
  );
}
