import { Link } from 'react-router-dom';
import { HelpCircle, MessageCircle, BookOpen, Video } from 'lucide-react';

export default function Help() {
  const faqs = [
    { q: 'How does the AI Scanner work?', a: 'Upload a clear close-up of a single leaf. A gatekeeper first checks the image shows a plant, then the trained disease model (38 PlantVillage crop-disease classes) predicts the most likely class. Low-confidence results are marked inconclusive — no diagnosis is invented. If the model has not been trained yet, the scanner says so explicitly.' },
    { q: 'Where does my data live?', a: 'On your own backend database: plants, scan history, watering logs and health logs persist across restarts. Check the backend /api/health endpoint to confirm the service and the ML model status.' },
    { q: 'Can I connect third-party sensors?', a: 'Not yet. Soil-moisture values in the app are the ones you enter yourself, and weather data comes from the Open-Meteo API only when coordinates are configured — otherwise clearly-labelled fallback values are used.' }
  ];

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-text mb-2 flex items-center gap-2">
          <HelpCircle className="text-indigo-500 w-8 h-8" /> Help & Support
        </h1>
        <p className="text-muted">Learn how to use LeafLogic or contact our expert agronomists.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <Link to="/assistant" className="bg-card rounded-2xl p-6 shadow-sm border border-border text-center hover:shadow-md transition-shadow cursor-pointer block">
          <MessageCircle className="w-10 h-10 text-primary mx-auto mb-4" />
          <h3 className="font-bold mb-2">PlantAI Assistant</h3>
          <p className="text-sm text-muted">Ask gardening questions, answered from your real plant data.</p>
        </Link>
        <div title="Care guides are not available yet" className="bg-card rounded-2xl p-6 shadow-sm border border-border text-center opacity-60 cursor-not-allowed">
          <BookOpen className="w-10 h-10 text-orange-500 mx-auto mb-4" />
          <h3 className="font-bold mb-2">Wiki & Guides</h3>
          <p className="text-sm text-muted">Coming soon.</p>
        </div>
        <div title="Video tutorials are not available yet" className="bg-card rounded-2xl p-6 shadow-sm border border-border text-center opacity-60 cursor-not-allowed">
          <Video className="w-10 h-10 text-blue-500 mx-auto mb-4" />
          <h3 className="font-bold mb-2">Video Tutorials</h3>
          <p className="text-sm text-muted">Coming soon.</p>
        </div>
      </div>

      <div className="bg-card rounded-2xl p-8 shadow-sm border border-border">
        <h2 className="text-2xl font-bold mb-6">Frequently Asked Questions</h2>
        <div className="space-y-4">
          {faqs.map((faq, i) => (
            <div key={i} className="border-b border-border pb-4 last:border-0 last:pb-0">
              <h4 className="font-bold text-text mb-2 text-lg flex items-start gap-2">
                <span className="text-primary mt-1">Q.</span> {faq.q}
              </h4>
              <p className="text-muted pl-6">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
