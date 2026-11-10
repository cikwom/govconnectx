import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

export type Language = "en" | "ha" | "yo" | "ig";
const dictionaries: Record<Language, Record<string, string>> = {
  en: {},
  ha: {
    "Community services": "Ayyukan al'umma",
    "Command Centre": "Cibiyar umarni",
    "Sign out": "Fita",
    "Citizen Dashboard": "Shafin dan kasa",
    "Your reports": "Rahotanninku",
    "Submit a report": "Gabatar da rahoto",
    "Community help centre": "Cibiyar taimakon al'umma",
    "Lost and Found": "Abubuwan da suka bata da aka samo",
    "Government service directory": "Jerin ayyukan gwamnati",
  },
  yo: {
    "Community services": "Awọn iṣẹ́ àwùjọ",
    "Command Centre": "Ibùdó ìṣàkóso",
    "Sign out": "Jáde",
    "Citizen Dashboard": "Pẹpẹ ọmọ ìlú",
    "Your reports": "Àwọn ìròyìn rẹ",
    "Submit a report": "Fi ìròyìn ránṣẹ́",
    "Community help centre": "Ile-iṣẹ́ ìrànlọ́wọ́ àwùjọ",
    "Lost and Found": "Ohun tó sọnù àti ohun tí a rí",
    "Government service directory": "Àkójọ iṣẹ́ ìjọba",
  },
  ig: {
    "Community services": "Ọrụ obodo",
    "Command Centre": "Ebe njikwa",
    "Sign out": "Pụọ",
    "Citizen Dashboard": "Dashboard nwa amaala",
    "Your reports": "Akụkọ gị",
    "Submit a report": "Nyefee akụkọ",
    "Community help centre": "Ebe enyemaka obodo",
    "Lost and Found": "Ihe furu efu na ihe achọtara",
    "Government service directory": "Ndepụta ọrụ gọọmentị",
  },
};

type LanguageContextValue = { language: Language; setLanguage: (language: Language) => void; t: (key: string) => string };
const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem("govconnectx_language");
    return saved === "ha" || saved === "yo" || saved === "ig" ? saved : "en";
  });
  const setLanguage = (next: Language) => {
    localStorage.setItem("govconnectx_language", next);
    setLanguageState(next);
  };
  const value = useMemo(() => ({ language, setLanguage, t: (key: string) => dictionaries[language][key] ?? key }), [language]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useLanguage must be used inside LanguageProvider");
  return context;
}
