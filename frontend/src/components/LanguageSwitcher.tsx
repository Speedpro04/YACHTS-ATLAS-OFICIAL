import { useTranslation } from 'react-i18next';

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const languages = [
    { code: 'pt-BR', label: 'PT', flag: '🇧🇷' },
    { code: 'en-US', label: 'EN', flag: '🇺🇸' },
    { code: 'es-419', label: 'ES', flag: '🌎' },
  ];

  return (
    <div className="flex items-center gap-1">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => i18n.changeLanguage(lang.code)}
          className={`flex items-center gap-1.5 px-2 py-1.5 rounded-sm transition-all ${
            i18n.language === lang.code
              ? 'bg-[#c5a059] text-[#050b18]'
              : 'text-white/40 hover:text-white hover:bg-white/5'
          }`}
          title={lang.label}
        >
          <span className="text-[10px] leading-none">{lang.flag}</span>
          <span className="text-[9px] font-black tracking-widest uppercase leading-none">{lang.label}</span>
        </button>
      ))}
    </div>
  );
}
