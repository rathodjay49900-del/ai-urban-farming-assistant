import { motion } from 'framer-motion';
import { Bot, CheckCircle, AlertTriangle, Droplets, Leaf, Thermometer, Sun } from 'lucide-react';
import { Link, useParams, useLocation } from 'react-router-dom';

export default function ScannerResult() {
  const { id } = useParams();
  const location = useLocation();
  const state = location.state as { result?: any, preview?: string } | null;
  const apiResult = state?.result;
  
  const isHealthy = apiResult 
    ? (apiResult.message === "Your Plant Looks Healthy") 
    : (id === 'demo-healthy');

  const hasApi = !!apiResult;
  const uncertain = !!apiResult && (apiResult.low_confidence || apiResult.needs_expert);
  // The disease panel may ONLY render when the backend returned a real disease.
  const undetermined = !isHealthy && (!hasApi || uncertain || !apiResult?.disease);

  // Use dynamic info from backend if available, fallback to mock
  const plantInfo = apiResult?.plant_info || {
    name: "Tomato",
    scientific_name: "Solanum lycopersicum",
    category: "Vegetable",
    sunlight: "6-8 hours/day",
    water: "Regular watering with consistent soil moisture",
    temperature: "Warm growing conditions",
    soil: "Well-draining soil"
  };

  // All values below come from the backend; nothing disease-specific is invented.
  const diseaseResult = {
    disease: apiResult?.disease ?? '',
    confidence: apiResult?.confidence ?? null,
    severity: apiResult?.severity ?? 'Unknown',
    symptoms: apiResult?.symptoms?.length ? apiResult.symptoms : [],
    treatment: apiResult?.treatment?.length ? apiResult.treatment : [],
    prevention: apiResult?.prevention?.length ? apiResult.prevention : [],
    explanation: apiResult?.explanation ?? '',
  };

  const imageSrc = state?.preview || (isHealthy 
    ? 'https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=400&q=80' 
    : 'https://images.unsplash.com/photo-1592150621744-aca64f48394a?w=400&q=80');

  return (
    <div className="max-w-5xl mx-auto py-8 space-y-8">
      <div className="flex items-center gap-4 mb-8">
        <Link to="/scanner" className="text-muted hover:text-text">&larr; Back to Scanner</Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Image & Plant Info */}
        <div className="space-y-6">
          <div className="bg-card rounded-3xl p-6 shadow-sm border border-border">
            <div className="aspect-square rounded-2xl overflow-hidden border border-border mb-6">
              <img src={imageSrc} alt="Analyzed plant" className="w-full h-full object-cover" />
            </div>
            
            <h3 className="text-xl font-heading font-bold text-text mb-4">Plant Information</h3>
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted font-medium mb-1 uppercase tracking-wider">Name</p>
                <p className="font-semibold">{plantInfo.name} <span className="text-muted font-normal italic">({plantInfo.scientific_name})</span></p>
              </div>
              <div className="flex items-center gap-3">
                <Leaf className="w-5 h-5 text-primary" />
                <div>
                  <p className="text-xs text-muted font-medium">Category</p>
                  <p className="text-sm font-medium">{plantInfo.category}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Sun className="w-5 h-5 text-warning" />
                <div>
                  <p className="text-xs text-muted font-medium">Sunlight</p>
                  <p className="text-sm font-medium">{plantInfo.sunlight}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Droplets className="w-5 h-5 text-sky" />
                <div>
                  <p className="text-xs text-muted font-medium">Watering</p>
                  <p className="text-sm font-medium text-text line-clamp-1" title={plantInfo.water}>{plantInfo.water}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Thermometer className="w-5 h-5 text-red-400" />
                <div>
                  <p className="text-xs text-muted font-medium">Temperature</p>
                  <p className="text-sm font-medium">{plantInfo.temperature}</p>
                </div>
              </div>
            </div>
            
            <button className="w-full mt-6 py-2 border border-border rounded-xl text-sm font-medium text-text hover:bg-gray-50 transition-colors">
              View Complete Guide
            </button>
          </div>
        </div>

        {/* Right Column: AI Analysis */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-card rounded-3xl p-8 shadow-sm border border-border">
            {(apiResult?.low_confidence || apiResult?.needs_expert) && (
              <div className="mb-6 bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-900 text-sm">Uncertain result — expert verification recommended</p>
                  <p className="text-amber-800 text-sm">{apiResult?.message || 'The AI confidence is low. Please retake a clearer close-up of a single leaf or consult an expert before treating this plant.'}</p>
                </div>
              </div>
            )}
            {isHealthy ? (
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium mb-4">
                  <CheckCircle className="w-4 h-4" />
                  Healthy Plant Detected
                </div>
                <h1 className="text-4xl font-heading font-bold text-text mb-4">Your Plant Looks Healthy</h1>
                <p className="text-muted mb-6">No major disease indicators were detected.</p>
                
                <div className="flex items-center gap-4 mb-8">
                  <div className="bg-gray-50 rounded-xl px-4 py-3 border border-border">
                    <p className="text-xs text-muted mb-1">AI Confidence</p>
                    <p className="text-xl font-bold text-primary">{apiResult?.confidence ?? 0}%</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl px-4 py-3 border border-border">
                    <p className="text-xs text-muted mb-1">Health Status</p>
                    <p className="text-xl font-bold text-text">Excellent</p>
                  </div>
                </div>

                <h3 className="text-lg font-heading font-semibold mb-4">Recommended Care</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-xl border border-blue-100">
                    <Droplets className="w-5 h-5 text-sky" />
                    <span className="text-sm font-medium text-blue-900">Maintain consistent watering</span>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-orange-50 rounded-xl border border-orange-100">
                    <Sun className="w-5 h-5 text-warning" />
                    <span className="text-sm font-medium text-orange-900">Provide adequate sunlight</span>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-green-50 rounded-xl border border-green-100">
                    <Leaf className="w-5 h-5 text-primary" />
                    <span className="text-sm font-medium text-green-900">Monitor new growth</span>
                  </div>
                  <div className="flex items-center gap-3 p-4 bg-purple-50 rounded-xl border border-purple-100">
                    <CheckCircle className="w-5 h-5 text-purple-600" />
                    <span className="text-sm font-medium text-purple-900">Check leaves regularly</span>
                  </div>
                </div>
              </div>
            ) : undetermined ? (
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 text-amber-700 text-sm font-medium mb-4">
                  <AlertTriangle className="w-4 h-4" />
                  Result Inconclusive
                </div>
                <h1 className="text-3xl font-heading font-bold text-text mb-4">Diagnosis Unavailable</h1>
                <p className="text-muted mb-6">
                  The AI could not confidently confirm a disease for this image. No treatment is
                  recommended based on this result.
                </p>

                <div className="bg-gray-50 rounded-xl px-4 py-3 border border-border inline-block mb-8">
                  <p className="text-xs text-muted mb-1">AI Confidence</p>
                  <p className="text-xl font-bold text-text">{apiResult?.confidence ?? 0}%</p>
                </div>

                <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-3 text-indigo-900 font-semibold">
                    <Bot className="w-5 h-5 text-ai" />
                    What should I do?
                  </div>
                  <ul className="space-y-3 text-sm text-indigo-800">
                    <li className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-ai mt-1.5 flex-shrink-0" />
                      Retake a clear, well-lit close-up of a single leaf against a plain background.
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-ai mt-1.5 flex-shrink-0" />
                      Avoid treating the plant based on an uncertain result.
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-ai mt-1.5 flex-shrink-0" />
                      Consult a local agronomist or nursery for verification.
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              <div>
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-100 text-red-700 text-sm font-medium mb-4">
                  <AlertTriangle className="w-4 h-4" />
                  Plant Health Issue Detected
                </div>
                <h1 className="text-4xl font-heading font-bold text-text mb-4">{diseaseResult.disease}</h1>
                
                <div className="flex items-center gap-4 mb-8">
                  <div className="bg-gray-50 rounded-xl px-4 py-3 border border-border">
                    <p className="text-xs text-muted mb-1">AI Confidence</p>
                    <p className="text-xl font-bold ai-gradient">{diseaseResult.confidence != null ? `${diseaseResult.confidence}%` : '—'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-xl px-4 py-3 border border-border">
                    <p className="text-xs text-muted mb-1">Severity</p>
                    <p className="text-xl font-bold text-warning">{diseaseResult.severity}</p>
                  </div>
                </div>

                <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6 mb-8">
                  <div className="flex items-center gap-2 mb-3 text-indigo-900 font-semibold">
                    <Bot className="w-5 h-5 text-ai" />
                    Why did AI detect this?
                  </div>
                  <p className="text-indigo-800 text-sm leading-relaxed">
                    {diseaseResult.explanation}
                  </p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-heading font-semibold mb-4 flex items-center gap-2 text-warning">
                      <AlertTriangle className="w-5 h-5" />
                      Symptoms
                    </h3>
                    <ul className="space-y-3">
                      {diseaseResult.symptoms.length === 0 && (
                        <li className="text-sm text-muted">Not provided by the model.</li>
                      )}
                      {diseaseResult.symptoms.map((symptom, i) => (
                        <li key={i} className="flex items-start gap-3 text-sm text-text">
                          <div className="w-1.5 h-1.5 rounded-full bg-warning mt-1.5 flex-shrink-0" />
                          {symptom}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h3 className="text-lg font-heading font-semibold mb-4 flex items-center gap-2 text-primary">
                      <CheckCircle className="w-5 h-5" />
                      Treatment
                    </h3>
                    <ul className="space-y-3">
                      {diseaseResult.treatment.length === 0 && (
                        <li className="text-sm text-muted">Not provided by the model — consult an expert.</li>
                      )}
                      {diseaseResult.treatment.map((treatment, i) => (
                        <li key={i} className="flex items-start gap-3 text-sm text-text">
                          <div className="w-5 h-5 rounded-full bg-green-100 text-primary flex items-center justify-center text-xs font-bold flex-shrink-0">
                            {i + 1}
                          </div>
                          <span className="mt-0.5 leading-relaxed">{treatment}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div className="bg-gradient-to-r from-blue-50 to-green-50 rounded-3xl p-6 md:p-8 border border-blue-100 flex flex-col md:flex-row items-center justify-between gap-6">
            <div>
              <h3 className="text-lg font-heading font-semibold text-text mb-1">Update Plant Care</h3>
              <p className="text-sm text-muted">Adjust watering schedule based on AI recommendations to help recovery.</p>
            </div>
            <button className="bg-white px-8 py-4 rounded-xl font-bold shadow-sm hover:shadow-md transition-shadow text-primary flex items-center gap-2 whitespace-nowrap">
              <Droplets className="w-5 h-5" />
              Update Watering
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
