import { motion } from 'framer-motion';
import { MapPin, ArrowRightLeft, MessageCircle, Star } from 'lucide-react';

const swapListings = [
  { id: 1, user: 'Sarah M.', distance: '1.2 km away', offer: '5 Fresh Lemons 🍋', need: 'Mint Leaves 🌿', rating: 4.8 },
  { id: 2, user: 'Rahul K.', distance: '2.5 km away', offer: 'Basil Seeds 🌱', need: 'Any Indoor Plant 🪴', rating: 5.0 },
  { id: 3, user: 'Priya D.', distance: '3.1 km away', offer: 'Aloe Vera Pups 🌵', need: 'Cherry Tomatoes 🍅', rating: 4.5 },
  { id: 4, user: 'Amit S.', distance: '0.8 km away', offer: 'Organic Compost ♻️', need: 'Chilli Seeds 🌶️', rating: 4.9 },
];

export default function Community() {
  return (
    <div className="max-w-6xl mx-auto py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4">
        <div>
          <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-3 py-1 rounded-full text-sm font-bold uppercase tracking-wider mb-2">
            Urban Market
          </div>
          <h1 className="text-3xl font-heading font-bold text-text mb-2">Crop Swap Community</h1>
          <p className="text-muted">Trade your extra harvest and seeds with neighbors nearby.</p>
        </div>
        <button disabled title="Listings are not connected to a backend yet" className="bg-gray-200 text-gray-400 px-6 py-3 rounded-xl font-medium cursor-not-allowed">
          + Create Listing
        </button>
      </div>

      <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-2xl px-6 py-4 text-sm mb-8">
        <span className="font-bold">DEMO preview</span> — these sample listings are placeholders.
        Trading and messaging are not connected to a backend yet.
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {swapListings.map((listing, i) => (
          <motion.div
            key={listing.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-card rounded-2xl p-6 shadow-sm border border-border flex flex-col md:flex-row justify-between gap-6"
          >
            <div className="flex-1 space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center font-bold text-primary text-xl">
                  {listing.user.charAt(0)}
                </div>
                <div>
                  <h3 className="font-bold text-text">{listing.user}</h3>
                  <div className="flex items-center gap-3 text-xs text-muted">
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> {listing.distance}</span>
                    <span className="flex items-center gap-1 text-yellow-500"><Star className="w-3 h-3 fill-current" /> {listing.rating}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-xl flex items-center justify-between border border-gray-100">
                <div className="text-center flex-1">
                  <p className="text-xs text-muted font-medium mb-1">Offering</p>
                  <p className="font-bold text-text">{listing.offer}</p>
                </div>
                <ArrowRightLeft className="w-5 h-5 text-gray-400 mx-2 flex-shrink-0" />
                <div className="text-center flex-1">
                  <p className="text-xs text-muted font-medium mb-1">Looking For</p>
                  <p className="font-bold text-primary">{listing.need}</p>
                </div>
              </div>
            </div>

            <div className="flex md:flex-col gap-3 justify-center">
              <button disabled title="Trading is not connected to a backend yet" className="flex-1 md:flex-none bg-gray-200 text-gray-400 py-3 px-6 rounded-xl font-medium cursor-not-allowed flex items-center justify-center gap-2">
                <ArrowRightLeft className="w-4 h-4" /> Trade
              </button>
              <button disabled title="Messaging is not connected to a backend yet" className="flex-1 md:flex-none bg-white border border-border text-gray-400 py-3 px-6 rounded-xl font-medium cursor-not-allowed flex items-center justify-center gap-2">
                <MessageCircle className="w-4 h-4" /> Message
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
