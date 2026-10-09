import { Settings as SettingsIcon, Bell, Shield, Smartphone, Globe, Moon } from 'lucide-react';

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
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-text">Watering Alerts</p>
                <p className="text-sm text-muted">Get notified when a plant needs water.</p>
              </div>
              <div className="w-12 h-6 bg-primary rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></div>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-text">Disease Warnings</p>
                <p className="text-sm text-muted">AI alerts based on weather changes.</p>
              </div>
              <div className="w-12 h-6 bg-primary rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-b border-border">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2"><Smartphone className="w-5 h-5 text-primary" /> Device Integrations</h2>
          <div className="flex justify-between items-center bg-gray-50 p-4 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center"><Globe className="w-5 h-5 text-blue-600" /></div>
              <div>
                <p className="font-medium text-text">Smart IoT Soil Sensor V2</p>
                <p className="text-xs text-success font-bold">Connected • Battery 89%</p>
              </div>
            </div>
            <button className="text-red-500 text-sm font-bold">Disconnect</button>
          </div>
        </div>

        <div className="p-6">
          <h2 className="font-bold text-lg mb-4 flex items-center gap-2"><Moon className="w-5 h-5 text-primary" /> Appearance</h2>
          <div className="flex gap-4">
            <button className="flex-1 py-3 border-2 border-primary bg-primary/5 rounded-xl font-bold text-primary">Light Mode</button>
            <button className="flex-1 py-3 border border-border rounded-xl font-medium text-muted hover:bg-gray-50">Dark Mode</button>
          </div>
        </div>
      </div>
    </div>
  );
}
