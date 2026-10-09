import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import LanguageSwitcher from '../components/LanguageSwitcher';
import FloatingLeaves from '../components/FloatingLeaves';
import OnboardingTour from '../components/OnboardingTour';

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden relative">
      <FloatingLeaves />
      <OnboardingTour />
      
      <Sidebar />
      <main className="flex-1 overflow-y-auto p-4 md:p-8 z-10">
        <div className="max-w-6xl mx-auto flex justify-end">
          <LanguageSwitcher />
        </div>
        <Outlet />
      </main>
    </div>
  );
}
