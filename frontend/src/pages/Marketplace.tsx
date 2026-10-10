import { motion } from 'framer-motion';
import { ShoppingCart, Star, Package, Users } from 'lucide-react';

const products = [
  { id: 1, name: 'Premium Heirloom Tomato Seeds', price: '₹149', rating: 4.8, type: 'Seeds', img: '🍅' },
  { id: 2, name: 'Smart IoT Soil Moisture Sensor', price: '₹899', rating: 4.9, type: 'Tech', img: '🔌' },
  { id: 3, name: 'Organic Compost Mix (5kg)', price: '₹299', rating: 4.7, type: 'Fertilizer', img: '🍂' },
  { id: 4, name: 'Hire an Expert Urban Gardener', price: '₹499/hr', rating: 5.0, type: 'Service', img: '👨‍🌾' }
];

export default function Marketplace() {
  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-heading font-bold text-text mb-2">LeafLogic Store</h1>
          <p className="text-muted">Buy premium seeds, smart tools, or hire experts.</p>
        </div>
        <div className="bg-primary/10 text-primary px-4 py-2 rounded-xl font-bold flex items-center gap-2">
          <ShoppingCart className="w-5 h-5" />
          <span>Cart (0)</span>
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-2xl px-6 py-4 text-sm mb-8">
        <span className="font-bold">DEMO preview</span> — sample catalog only.
        Checkout and cart are not connected to a backend yet.
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {products.map((product, idx) => (
          <motion.div 
            key={product.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="bg-card rounded-2xl p-6 shadow-sm border border-border group hover:shadow-xl transition-all"
          >
            <div className="w-full h-40 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl mb-4 flex items-center justify-center text-7xl group-hover:scale-105 transition-transform">
              {product.img}
            </div>
            
            <div className="mb-4">
              <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded-md mb-2 inline-block">
                {product.type}
              </span>
              <h3 className="font-bold text-text line-clamp-2 min-h-[40px]">{product.name}</h3>
              <div className="flex items-center gap-1 text-yellow-500 mt-1 text-sm font-medium">
                <Star className="w-4 h-4 fill-current" /> {product.rating}
              </div>
            </div>
            
            <div className="flex justify-between items-center mt-auto">
              <span className="text-xl font-black text-text">{product.price}</span>
              <button disabled title="Checkout is not connected to a backend yet" className="bg-gray-200 text-gray-400 p-2 rounded-lg cursor-not-allowed">
                <ShoppingCart className="w-5 h-5" />
              </button>
            </div>
          </motion.div>
        ))}
      </div>
      
      {/* B2B / Business Model Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-12 bg-gradient-to-r from-gray-900 to-gray-800 rounded-3xl p-8 md:p-12 text-white flex flex-col md:flex-row items-center justify-between gap-8"
      >
        <div className="max-w-xl">
          <span className="text-primary font-bold tracking-widest uppercase text-sm mb-2 block">Enterprise Plan</span>
          <h2 className="text-3xl font-bold mb-4">Are you a commercial nursery?</h2>
          <p className="text-gray-300 mb-6">
            Get bulk access to our AI disease API, bulk seeds, and automated drone integrations.
          </p>
          <button disabled title="Contact form is not connected yet" className="bg-gray-600 text-gray-300 px-6 py-3 rounded-xl font-bold cursor-not-allowed">
            Contact Sales
          </button>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/10 backdrop-blur-sm p-4 rounded-2xl text-center">
            <Package className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <div className="font-bold text-2xl">API</div>
            <div className="text-xs text-gray-400">Disease detection endpoint</div>
          </div>
          <div className="bg-white/10 backdrop-blur-sm p-4 rounded-2xl text-center">
            <Users className="w-8 h-8 text-blue-400 mx-auto mb-2" />
            <div className="font-bold text-2xl">38</div>
            <div className="text-xs text-gray-400">Supported crop-disease classes</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
