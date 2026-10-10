import { NavLink } from 'react-router-dom';
import { Home, Leaf, ScanSearch, Droplets, Activity, Bot, Settings, HelpCircle, User, Users, ShoppingCart } from 'lucide-react';

const navItems = [
  { icon: Home, label: 'Dashboard', path: '/dashboard' },
  { icon: Leaf, label: 'My Plants', path: '/plants' },
  { icon: ScanSearch, label: 'Disease Scanner', path: '/scanner' },
  { icon: Users, label: 'Crop Swap', path: '/community' },
  { icon: Droplets, label: 'Watering', path: '/watering' },
  { icon: Activity, label: 'Plant Health', path: '/health' },
  { icon: Bot, label: 'AI Assistant', path: '/assistant' },
  { icon: ShoppingCart, label: 'Marketplace', path: '/marketplace' },
];

const secondaryItems = [
  { icon: Activity, label: 'Insights', path: '/insights' },
  { icon: Settings, label: 'Settings', path: '/settings' },
  { icon: HelpCircle, label: 'Help', path: '/help' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-card border-r border-border h-full flex flex-col transition-all duration-300 hidden md:flex">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg eco-gradient-bg flex items-center justify-center text-white font-bold shadow-sm">
          🌱
        </div>
        <span className="font-heading font-bold text-lg text-text">AI Urban Farming</span>
      </div>

      <nav className="flex-1 px-4 space-y-1 mt-4">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                isActive
                  ? 'bg-green-50 text-primary font-medium'
                  : 'text-muted hover:bg-gray-50 hover:text-text'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}

        <div className="my-6 border-t border-border"></div>

        {secondaryItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
                isActive
                  ? 'bg-green-50 text-primary font-medium'
                  : 'text-muted hover:bg-gray-50 hover:text-text'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 px-4 py-2 hover:bg-gray-50 rounded-xl cursor-pointer">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
            <User className="w-5 h-5" />
          </div>
          <div>
            <p className="text-sm font-medium text-text">Gardener</p>
            <p className="text-xs text-muted">Local garden</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
