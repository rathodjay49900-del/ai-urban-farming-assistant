import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, ChevronRight, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const steps = [
  {
    title: "Welcome to LeafLogic! 🌱",
    content: "Your AI Urban Farming Assistant. Register plants, scan leaves, and track watering — all stored in your own database.",
    path: "/dashboard"
  },
  {
    title: "AI Disease Scanner 🔍",
    content: "Upload a clear close-up of a single leaf. The scanner checks it shows a plant, then the trained model predicts the disease class — or honestly says when it cannot tell.",
    path: "/scanner"
  },
  {
    title: "Watering & Insights 💧",
    content: "Log real watering events and watch health analytics computed from your own records — never invented numbers.",
    path: "/watering"
  },
  {
    title: "You're all set! 🚀",
    content: "Explore the app and grow a healthy garden. Happy farming!",
    path: "/dashboard"
  }
];

const SEEN_KEY = 'leaflogic-tour-seen';

export default function OnboardingTour() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Show the tour only on the first visit; never nag returning users.
    let seen = false;
    try {
      seen = localStorage.getItem(SEEN_KEY) === '1';
    } catch {
      seen = false;
    }
    if (!seen) setTimeout(() => setIsVisible(true), 1500);
  }, []);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);
      navigate(steps[nextStep].path);
    } else {
      closeTour();
    }
  };

  const closeTour = () => {
    setIsVisible(false);
    try {
      localStorage.setItem(SEEN_KEY, '1');
    } catch {
      /* private mode — tour may reappear next visit */
    }
    navigate('/dashboard');
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div 
          initial={{ opacity: 0, y: 50, x: 50 }}
          animate={{ opacity: 1, y: 0, x: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="fixed bottom-8 right-8 z-[100] max-w-sm w-full"
        >
          {/* Pulsing indicator */}
          <div className="absolute -top-3 -left-3 w-6 h-6">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-6 w-6 bg-primary border-2 border-white"></span>
          </div>

          <div className="bg-white rounded-3xl p-6 shadow-2xl border border-border relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gray-100">
              <div 
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              />
            </div>

            <button 
              onClick={closeTour}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-800"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex gap-4 mt-2">
              <div className="w-12 h-12 bg-indigo-50 rounded-full flex items-center justify-center text-ai flex-shrink-0">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-text mb-1">{steps[currentStep].title}</h3>
                <p className="text-sm text-muted leading-relaxed mb-6">
                  {steps[currentStep].content}
                </p>
                
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    {steps.map((_, i) => (
                      <div 
                        key={i} 
                        className={`w-2 h-2 rounded-full transition-colors ${i === currentStep ? 'bg-primary' : 'bg-gray-200'}`}
                      />
                    ))}
                  </div>
                  
                  <button 
                    onClick={handleNext}
                    className="bg-text text-white px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-1 hover:bg-primary transition-colors"
                  >
                    {currentStep === steps.length - 1 ? 'Finish' : 'Next'} 
                    {currentStep !== steps.length - 1 && <ChevronRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
