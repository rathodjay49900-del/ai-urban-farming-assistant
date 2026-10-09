import { useState, useRef } from 'react';
import { Send, Bot, Mic, MicOff } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { assistantApi } from '../services/api';

export default function Assistant() {
  const [messages, setMessages] = useState([
    { id: 1, role: 'bot', text: 'Hello! I am your AI gardening assistant. How can I help your plants today? 🌱' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  // Use speech recognition if available
  const recognitionRef = useRef<any>(null);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support voice input. Please try Chrome.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    
    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join('');
      setInput(transcript);
    };

    recognition.onerror = (event: any) => {
      console.error(event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
    recognitionRef.current = recognition;
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    }

    const userMessage = { id: Date.now(), role: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    try {
      const data = await assistantApi.chat(userMessage.text);
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'bot', text: data.text }]);
    } catch {
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'bot',
        text: 'I could not reach the assistant service. Please make sure the backend is running.',
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto h-[80vh] flex flex-col bg-card rounded-2xl shadow-sm border border-border overflow-hidden relative">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-4 border-b border-indigo-100 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-ai text-white flex items-center justify-center shadow-sm">
          <Bot className="w-6 h-6" />
        </div>
        <div>
          <h2 className="font-heading font-bold text-text">PlantAI Assistant</h2>
          <p className="text-xs text-ai font-medium">Voice-enabled gardening expert</p>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] rounded-2xl p-4 ${
                msg.role === 'user' 
                  ? 'bg-primary text-white rounded-br-sm' 
                  : 'bg-white border border-border text-text rounded-bl-sm shadow-sm'
              }`}>
                {msg.text}
              </div>
            </motion.div>
          ))}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-white border border-border text-text rounded-2xl rounded-bl-sm p-4 shadow-sm flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} className="p-4 bg-white border-t border-border flex items-center gap-3">
        <button
          type="button"
          onClick={toggleListening}
          className={`p-3 rounded-xl transition-colors flex-shrink-0 ${
            isListening 
              ? 'bg-red-500 text-white animate-pulse' 
              : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
          title={isListening ? "Stop listening" : "Start voice dictation"}
        >
          {isListening ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
        </button>
        
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isListening ? "Listening..." : "Ask me anything about your plants..."}
          className="flex-1 px-4 py-3 rounded-xl border border-border focus:ring-2 focus:ring-primary focus:border-transparent outline-none bg-gray-50"
        />
        
        <button 
          type="submit"
          disabled={!input.trim()}
          className="bg-primary text-white p-3 rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
}
