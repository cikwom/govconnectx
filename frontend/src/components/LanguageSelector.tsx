import { useLanguage, type Language } from "../state/LanguageContext";

export default function LanguageSelector() {
  const { language, setLanguage, t } = useLanguage();
  return (
    <label className="language-control">
      <select aria-label={t("Interface language")} value={language} onChange={event => setLanguage(event.target.value as Language)}>
        <option value="en">English</option>
        <option value="ha">Hausa</option>
        <option value="yo">Yorùbá</option>
        <option value="ig">Igbo</option>
      </select>
    </label>
  );
}
