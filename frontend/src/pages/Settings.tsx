import { useState } from 'react';
import { Settings as SettingsIcon, Bell, Shield, Moon } from 'lucide-react';

function loadPref(key: string, fallback: boolean): boolean {
  try {
    const stored = localStorage.getItem(key);
    return stored == null ? fallback : stored === '1';
  } catch {
    return fallback;
  }
}

function Toggle({ prefKey, defaultOn, label, hint }: { prefKey: string; defaultOn: boolean; label: string; hint: string }) {
  const [on, setOn] = useState(() => loadPref(prefKey, defaultOn));
  const flip = () => {
    const next = !on;
    setOn(next);
    try {
      localStorage.setItem(prefKey, next ? '1' : '0');
    } catch {
      /* private mode — state still applies for this session */
    }
  };
  return (
    <div className="flex justify-between items-center">
      <div>
        <p className="font-medium text-text">{label}</p>
        <p className="text-sm text-muted">{hint}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={on}
        aria-label={label}
        onClick={flip}
        className={`w-12 h-6 rounded-full relative transition-colors ${on ? 'bg-primary' : 'bg-gray-300'}`}
      >
        <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${on ? 'right-1' : 'left-1'}`}></div>
      </button>
    </div>
  );
}

export default function Settings() {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-heading font-bold text-text mb-2 flex items-center gap-2">
          <SettingsIcon className="text-gray-500 w-8 h-8" /> Settings
        </h1>
        <p className="text-muted">Manage your account and app preferences.</p>
      </div>

      <div className="bg-card rounded-2xl shadow-sm border border-border overflow-hidden">
        <div className="p-6 border-b border-border">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2"><Bell className="w-5 h-5 text-primary" /> Notifications</h2>
          <div className="space-y-4">
            <Toggle prefKey="pref-watering-alerts" defaultOn={true} label="Watering Alerts" hint="Reminder preferences are stored on this device." />
            <Toggle prefKey="pref-disease-warnings" defaultOn={true} label="Disease Warnings" hint="Reminder preferences are stored on this device." />
          </div>
        </div>

        <div className="p-6 border-b border-border">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2"><Shield className="w-5 h-5 text-primary" /> Device Integrations</h2>
          <div className="flex justify-between items-center bg-gray-50 p-4 rounded-xl">
            <div>
              <p className="font-medium text-text">Soil sensors</p>
              <p className="text-xs text-muted font-medium">No sensor connected. Soil-moisture values on the Watering page are the ones you enter yourself.</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2"><Moon className="w-5 h-5 text-primary" /> Appearance</h2>
          <div className="flex gap-4">
            <button className="flex-1 py-3 border-2 border-primary bg-primary/5 rounded-xl font-bold text-primary">Light Mode</button>
            <button disabled title="Dark mode is not available yet" className="flex-1 py-3 border border-border rounded-xl font-medium text-gray-400 cursor-not-allowed">Dark Mode</button>
          </div>
        </div>
      </div>
    </div>
  );
}
