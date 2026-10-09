import { useState } from 'react';
import { Globe } from 'lucide-react';

const languages = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'hi', label: 'हिंदी', flag: '🇮🇳' },
  { code: 'gu', label: 'ગુજરાતી', flag: '🦁' },
];

export default function LanguageSwitcher() {
  const [currentLang, setCurrentLang] = useState('en');

  // Trigger Google Translate when the language is changed
  const handleLanguageChange = (langCode: string) => {
    setCurrentLang(langCode);
    
    // Google Translate uses a hidden select element. 
    // We need to find it and simulate a change event.
    const select = document.querySelector('.goog-te-combo') as HTMLSelectElement;
    if (select) {
      select.value = langCode;
      select.dispatchEvent(new Event('change'));
    } else {
      // If the combo box isn't ready yet, it means Google Translate script hasn't fully loaded
      console.warn("Google Translate is not ready yet.");
      
      // Fallback: reload the page with Google Translate URL param if needed
      if (langCode !== 'en') {
        const url = new URL(window.location.href);
        url.searchParams.set('lang', langCode);
        document.cookie = `googtrans=/en/${langCode}; path=/`;
        window.location.reload();
      }
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-border p-2 flex items-center gap-2 mb-6 w-fit">
      <div className="bg-green-50 p-2 rounded-lg text-primary mr-2">
        <Globe className="w-5 h-5" />
      </div>
      
      <div className="flex gap-2">
        {languages.map((lang) => (
          <label 
            key={lang.code}
            className={`cursor-pointer px-4 py-2 rounded-lg font-medium text-sm transition-all flex items-center gap-2 border-2 ${
              currentLang === lang.code 
                ? 'border-primary bg-primary/5 text-primary' 
                : 'border-transparent text-muted hover:bg-gray-50'
            }`}
          >
            <input 
              type="radio" 
              name="language" 
              value={lang.code}
              checked={currentLang === lang.code}
              onChange={() => handleLanguageChange(lang.code)}
              className="hidden" 
            />
            <span>{lang.flag}</span>
            {lang.label}
          </label>
        ))}
      </div>
    </div>
  );
}
