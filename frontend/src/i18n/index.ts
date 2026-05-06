import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import pt from './locales/pt.json';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      'pt-BR': { translation: pt },
    },
    lng: 'pt-BR',
    fallbackLng: 'pt-BR',
    supportedLngs: ['pt-BR'],
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
