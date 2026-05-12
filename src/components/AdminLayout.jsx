import { Link, NavLink } from "react-router-dom";
import LanguageSwitcher from "./LanguageSwitcher";
import { useLanguage } from "../i18n/LanguageContext";

function navClass({ isActive }) {
  return `btn ${isActive ? "btn-primary" : "btn-secondary"} min-w-36`;
}

export default function AdminLayout({ title, subtitle, onLogout, children }) {
  const { t } = useLanguage();

  return (
    <div className="mx-auto min-h-screen w-full max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
      <header className="rounded-2xl border border-hospital-200 bg-white p-5 shadow-soft sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="inline-flex rounded-full border border-care-200 bg-care-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-care-800">
              {t("admin.layout.badge")}
            </p>
            <h1 className="mt-3 text-2xl font-bold text-hospital-900 sm:text-3xl">{title}</h1>
            {subtitle ? <p className="mt-2 text-base text-hospital-700">{subtitle}</p> : null}
          </div>

          <div className="flex flex-col gap-3 sm:items-end">
            <LanguageSwitcher compact />
            <div className="flex flex-wrap gap-2">
            <Link to="/welcome" className="btn btn-secondary min-w-32">
              {t("admin.layout.patientApp")}
            </Link>
            <button type="button" className="btn btn-primary min-w-32" onClick={onLogout}>
              {t("admin.layout.logout")}
            </button>
            </div>
          </div>
        </div>

        <nav className="mt-5 flex flex-wrap gap-2">
          <NavLink to="/admin/dashboard" className={navClass}>
            {t("admin.layout.dashboard")}
          </NavLink>
          <NavLink to="/admin/patients" className={navClass}>
            {t("admin.layout.patients")}
          </NavLink>
        </nav>
      </header>

      <main className="mt-4 rounded-2xl border border-hospital-200 bg-white p-5 shadow-soft sm:p-6">
        {children}
      </main>
    </div>
  );
}
