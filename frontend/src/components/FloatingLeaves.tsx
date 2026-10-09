import { motion } from 'framer-motion';

export default function AnimatedBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-[-1] bg-[#F8FAFC]">
      {/* Light Elegant Nature Orbs for Premium Light Mode */}
      <motion.div 
        className="absolute w-[40vw] h-[40vw] rounded-full bg-green-200/40 blur-[100px]"
        animate={{ 
          x: ['-10vw', '50vw', '-10vw'],
          y: ['-10vh', '30vh', '-10vh'],
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
      />
      <motion.div 
        className="absolute w-[50vw] h-[50vw] rounded-full bg-emerald-200/30 blur-[120px]"
        animate={{ 
          x: ['60vw', '10vw', '60vw'],
          y: ['40vh', '-20vh', '40vh'],
        }}
        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
      />
      <motion.div 
        className="absolute w-[30vw] h-[30vw] rounded-full bg-yellow-100/40 blur-[80px]"
        animate={{ 
          x: ['20vw', '80vw', '20vw'],
          y: ['80vh', '10vh', '80vh'],
        }}
        transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}
