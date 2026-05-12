import { useState } from "react";
import LanguageSwitcher from "./LanguageSwitcher";

export default function LockScreen({ onSubmit, loading = false, error = "" }) {
  const [form, setForm] = useState({
    username: "",
    password: "",
  });

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-gradient-to-b from-hospital-50 via-slate-50 to-hospital-100 px-4 py-6 sm:px-6 lg:px-10">
      <div className="absolute left-4 right-4 top-4 flex justify-end sm:left-6 sm:right-6 sm:top-6 lg:left-10 lg:right-10 lg:top-8">
        <LanguageSwitcher compact />
      </div>

      <section className="w-full max-w-xl rounded-3xl border border-hospital-200 bg-white/95 px-6 py-8 shadow-soft backdrop-blur sm:px-8 sm:py-10">
        <p className="inline-flex rounded-full border border-care-200 bg-care-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-care-800">
          Hospital Access Locked
        </p>
        <h1 className="mt-4 text-3xl font-bold text-hospital-900 sm:text-4xl">
          CLD + Sarcopenia Education Portal
        </h1>
        <p className="mt-3 text-base leading-relaxed text-hospital-700">
          Sign in with the hospital admin account to unlock the chatbot and the
          admin reports dashboard.
        </p>

        <div className="mt-5 rounded-2xl border border-hospital-200 bg-hospital-50 px-4 py-3 text-sm text-hospital-700">
          Access is available only when the subscription is active.
        </div>

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4">
          <label className="field">
            <span>Username</span>
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              autoComplete="username"
              placeholder="Enter hospital username"
              required
              disabled={loading}
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              autoComplete="current-password"
              placeholder="Enter password"
              required
              disabled={loading}
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Signing In..." : "Unlock Access"}
          </button>
        </form>
      </section>
    </div>
  );
}
