import { HelpCircle, MessageCircle, BookOpen, Video } from 'lucide-react';

export default function Help() {
  const faqs = [
    { q: 'How accurate is the AI Scanner?', a: 'Our zero-shot CLIP model provides ~92% accuracy across 50+ common plant diseases. Ensure your photos are well-lit for best results.' },
    { q: 'How do I earn Leaf Coins?', a: 'You earn coins by consistently watering plants, reporting healthy growth, or swapping seeds in the Community Tab.' },
    { q: 'Can I connect third-party sensors?', a: 'Yes! Go to Settings > Device Integrations to pair supported BLE sensors.' }
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
        <div className="bg-card rounded-2xl p-6 shadow-sm border border-border text-center hover:shadow-md transition-shadow cursor-pointer">
          <MessageCircle className="w-10 h-10 text-primary mx-auto mb-4" />
          <h3 className="font-bold mb-2">Live Chat</h3>
          <p className="text-sm text-muted">Talk to an AI agronomist immediately.</p>
        </div>
        <div className="bg-card rounded-2xl p-6 shadow-sm border border-border text-center hover:shadow-md transition-shadow cursor-pointer">
          <BookOpen className="w-10 h-10 text-orange-500 mx-auto mb-4" />
          <h3 className="font-bold mb-2">Wiki & Guides</h3>
          <p className="text-sm text-muted">Read our comprehensive plant care guides.</p>
        </div>
        <div className="bg-card rounded-2xl p-6 shadow-sm border border-border text-center hover:shadow-md transition-shadow cursor-pointer">
          <Video className="w-10 h-10 text-blue-500 mx-auto mb-4" />
          <h3 className="font-bold mb-2">Video Tutorials</h3>
          <p className="text-sm text-muted">Watch how to prune, repot, and scan.</p>
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
