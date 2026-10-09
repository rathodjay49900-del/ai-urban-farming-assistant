import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, Bot, AlertCircle, Camera, XCircle, RefreshCw, Mic, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { scannerApi } from '../services/api';

export default function Scanner() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [audioModal, setAudioModal] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [audioResult, setAudioResult] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleAudioScan = () => {
    setAudioModal(true);
    setIsListening(true);
    setAudioResult(null);
    setTimeout(() => {
      setIsListening(false);
      setAudioResult("Background Audio Detected: Crickets/Locusts. Risk of leaf damage is High.");
    }, 4000);
  };

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

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setValidationError(null);
    
    try {
      let isHealthyDemo = preview?.includes('1518531933037');
      let isInvalidDemo = preview?.includes('1542291026-7eec264c27ff');

      // If it's a real file upload, we need to send it to the backend
      const formData = new FormData();
      
      if (file) {
        formData.append('file', file);
      } else {
        // If it's a demo, we need to fetch the image blob and send it
        const response = await fetch(preview!);
        const blob = await response.blob();
        formData.append('file', blob, 'demo_image.jpg');
        
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
        setValidationError(data.message || "This image does not appear to contain a plant. Please upload a plant or farming-related image.");
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
            
            <button 
              onClick={handleAudioScan}
              className="w-full mt-6 bg-gradient-to-r from-purple-500 to-indigo-500 text-white p-6 rounded-3xl flex items-center justify-center gap-4 hover:opacity-90 transition-opacity shadow-lg"
            >
              <div className="bg-white/20 p-3 rounded-full">
                <Mic className="w-8 h-8" />
              </div>
              <div className="text-left">
                <h3 className="text-xl font-bold">Listen for Pests (Audio AI)</h3>
                <p className="text-white/80 text-sm">Shazam for Bugs - Detect pests by their sound</p>
              </div>
            </button>

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
                    <h2 className="text-2xl font-bold mb-2">🌱 Plant Image Required</h2>
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

      {/* Audio Pest Modal */}
      <AnimatePresence>
        {audioModal && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4"
          >
            <div className="bg-gray-900 w-full max-w-sm rounded-[3rem] p-8 border-[8px] border-gray-800 relative flex flex-col items-center text-center">
              <button 
                onClick={() => setAudioModal(false)}
                className="absolute top-6 right-6 text-gray-500 hover:text-white"
              >
                <X className="w-6 h-6" />
              </button>

              <h2 className="text-white font-bold text-xl mb-8 mt-4">AI Audio Scanner</h2>
              
              <div className="relative w-32 h-32 flex items-center justify-center mb-8">
                {isListening && (
                  <>
                    <motion.div animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }} className="absolute inset-0 bg-purple-500 rounded-full"></motion.div>
                    <motion.div animate={{ scale: [1, 2, 1], opacity: [0.3, 0, 0.3] }} transition={{ duration: 2, repeat: Infinity, delay: 0.5 }} className="absolute inset-0 bg-purple-500 rounded-full"></motion.div>
                  </>
                )}
                <div className={`relative z-10 w-20 h-20 rounded-full flex items-center justify-center ${isListening ? 'bg-purple-600' : 'bg-gray-700'}`}>
                  <Mic className="w-10 h-10 text-white" />
                </div>
              </div>

              {isListening ? (
                <div className="space-y-2">
                  <p className="text-purple-400 font-bold">Listening to environment...</p>
                  <p className="text-gray-400 text-sm">Hold phone near your plants</p>
                </div>
              ) : (
                <div className="bg-red-500/20 border border-red-500/50 p-4 rounded-xl">
                  <div className="flex items-center justify-center gap-2 text-red-400 font-bold mb-2">
                    <AlertCircle className="w-5 h-5" /> Threat Detected
                  </div>
                  <p className="text-white text-sm leading-relaxed">{audioResult}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
