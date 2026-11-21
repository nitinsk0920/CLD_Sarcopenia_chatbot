import { Link, useNavigate } from "react-router-dom";
import LanguageSwitcher from "./LanguageSwitcher";
import { useLanguage } from "../i18n/LanguageContext";

export default function AppLayout({
  title,
  subtitle,
  children,
  backTo,
  backLabel,
  nextTo,
  nextLabel,
  onExitFlow,
  onNext,
  nextLoading = false,
}) {
  const { t } = useLanguage();
  const navigate = useNavigate();

  async function handleExitFlow() {
    await onExitFlow?.();
    navigate("/welcome", { replace: true });
  }

  async function handleNext() {
    await onNext?.();
    if (nextTo) navigate(nextTo);
  }

  return (
    <div className="app-shell">
      <div className="flex flex-col gap-3 rounded-xl border border-hospital-200 bg-white/90 px-4 py-3 text-sm font-medium text-hospital-700 shadow-sm sm:flex-row sm:items-end sm:justify-between">
        <div>{t("app.systemName")}</div>
        <LanguageSwitcher compact />
      </div>

      <header className="app-header">
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </header>

      <main className="card">{children}</main>

      <footer className="nav-row">
        {backTo ? (
          <Link className="btn btn-secondary min-w-28" to={backTo}>
            {backLabel || t("app.back")}
          </Link>
        ) : (
          <span className="inline-block min-w-28" />
        )}
        <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
          {onExitFlow ? (
            <button className="btn btn-secondary" type="button" onClick={handleExitFlow}>
              {t("app.home")}
            </button>
          ) : null}
          {nextTo ? (
            onNext ? (
              <button className="btn btn-primary min-w-36" type="button" onClick={handleNext} disabled={nextLoading}>
                {nextLoading ? t("app.loading") : nextLabel || t("app.next")}
              </button>
            ) : (
              <Link className="btn btn-primary min-w-36" to={nextTo}>
                {nextLabel || t("app.next")}
              </Link>
            )
          ) : null}
        </div>
      </footer>
    </div>
  );
}
