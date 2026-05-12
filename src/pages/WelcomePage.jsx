import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { animateWelcomeHero } from "../utils/uiAnimations";

const backgroundImage = "/images/images/background.jpg";
const heroImage = "/images/images/doctor.jpg";

const supportPoints = [
  {
    title: "Guided step by step",
    description: "Patients can move through the education flow in a calm, structured order.",
    fallback: "liver",
  },
  {
    title: "Built for simple counselling",
    description: "The design stays clear and low-stress for demos, counselling, and awareness sessions.",
    fallback: "muscle",
  },
  {
    title: "Ready to begin quickly",
    description: "The same existing learning and chatbot flow stays intact behind a cleaner welcome page.",
    fallback: "diet",
  },
];

const overviewTopics = [
  {
    title: "CLD (Chronic Liver Disease)",
    description: "Understand chronic liver disease in simple terms.",
    imageSrc: "/images/icons/lvier.jpg",
    fallback: "liver",
  },
  {
    title: "Sarcopenia",
    description: "Learn about muscle loss and how to manage it.",
    imageSrc: "/images/icons/muscle.jpg",
    fallback: "muscle",
  },
  {
    title: "Diet & Nutrition",
    description: "Discover food choices that support recovery.",
    imageSrc: "/images/icons/lvier.jpg",
    fallback: "diet",
  },
  {
    title: "Exercise & Movement",
    description: "Safe and simple movements for strength.",
    imageSrc: "/images/icons/muscle.jpg",
    fallback: "muscle",
  },
  {
    title: "Safety & Warning Signs",
    description: "Identify warning signs and when to act.",
    imageSrc: "",
    fallback: "diet",
  },
];

const heroHighlights = [
  {
    title: "CLD",
    imageSrc: "/images/icons/lvier.jpg",
    fallback: "liver",
  },
  {
    title: "Sarcopenia",
    imageSrc: "/images/icons/muscle.jpg",
    fallback: "muscle",
  },
];

function IconFallback({ type }) {
  if (type === "liver") {
    return (
      <svg viewBox="0 0 48 48" className="h-8 w-8 text-hospital-700" fill="none">
        <path
          d="M10 28c0-9 7-15 16-15 7 0 12 3 15 8 2 4 2 9-1 13-3 4-8 6-14 6-10 0-16-5-16-12Z"
          fill="currentColor"
          opacity="0.16"
        />
        <path
          d="M10 28c0-9 7-15 16-15 7 0 12 3 15 8M10 28c0 7 6 12 16 12 6 0 11-2 14-6 3-4 3-9 1-13M18 19c1 5 4 8 9 10m-4-14c2 6 7 10 14 11"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (type === "muscle") {
    return (
      <svg viewBox="0 0 48 48" className="h-8 w-8 text-hospital-700" fill="none">
        <path
          d="M14 28c3-3 4-7 4-12h6c0 4 1 7 4 9l4 2c2 1 4 4 4 7 0 5-4 8-10 8H20c-6 0-10-3-10-8 0-2 1-4 4-6Z"
          fill="currentColor"
          opacity="0.16"
        />
        <path
          d="M14 28c3-3 4-7 4-12h6c0 4 1 7 4 9l4 2c2 1 4 4 4 7 0 5-4 8-10 8H20c-6 0-10-3-10-8 0-2 1-4 4-6Zm2-4h8"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  }

  if (type === "diet") {
    return (
      <svg viewBox="0 0 48 48" className="h-8 w-8 text-care-700" fill="none">
        <circle cx="24" cy="24" r="14" fill="currentColor" opacity="0.12" />
        <path
          d="M24 15c4 0 7 3 7 7 0 8-7 12-7 12s-7-4-7-12c0-4 3-7 7-7Z"
          stroke="currentColor"
          strokeWidth="2.4"
        />
        <path d="M24 18v14m-5-9h10" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 48 48" className="h-8 w-8 text-care-700" fill="none">
      <circle cx="24" cy="24" r="14" fill="currentColor" opacity="0.12" />
      <path
        d="M17 28c1-6 5-11 7-11s6 5 7 11M24 17v14m-8 0h16"
        stroke="currentColor"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function FeatureIcon({ imageSrc, fallback, title }) {
  const [failed, setFailed] = useState(false);

  if (imageSrc && !failed) {
    return (
      <img
        src={imageSrc}
        alt={title}
        className="h-14 w-14 rounded-2xl object-cover"
        onError={() => setFailed(true)}
      />
    );
  }

  return (
    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-hospital-100">
      <IconFallback type={fallback} />
    </div>
  );
}

export default function WelcomePage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const heroRef = useRef(null);

  useEffect(() => {
    const stopHeroAnimation = animateWelcomeHero(heroRef.current);

    return () => {
      stopHeroAnimation?.();
    };
  }, []);

  function handleBeginFlow() {
    navigate("/patient-form");
  }

  return (
    <div
      className="relative min-h-screen bg-cover bg-center bg-no-repeat text-slate-700"
      style={{ backgroundImage: `url('${backgroundImage}')` }}
    >
      <div data-welcome-bg className="absolute inset-0" />
      <div className="absolute inset-0 bg-gradient-to-b from-white/8 via-white/5 to-white/10" />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-5 sm:px-6 lg:px-10">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <LanguageSwitcher compact />
          <div className="flex flex-wrap justify-end gap-2">
            <Link
              to="/admin/dashboard"
              className="inline-flex items-center rounded-xl border border-hospital-200 bg-white/90 px-4 py-2 text-sm font-medium text-hospital-700 shadow-sm backdrop-blur-sm"
            >
              Admin Reports
            </Link>
            <button
              type="button"
              onClick={logout}
              className="inline-flex items-center rounded-xl border border-care-200 bg-white/90 px-4 py-2 text-sm font-medium text-care-800 shadow-sm backdrop-blur-sm"
            >
              Logout
            </button>
          </div>
        </div>

        <main className="flex-1 py-4 pb-10 sm:py-6 sm:pb-12">
          <div className="mx-auto w-full max-w-7xl space-y-6">
            <section className="flex min-h-[calc(100vh-8.5rem)] items-start justify-center pt-4 pb-2 sm:min-h-[calc(100vh-9rem)] sm:pt-6 lg:pt-8">
              <div
                ref={heroRef}
                className="w-full max-w-[920px] overflow-hidden rounded-[1.6rem] border border-white/75 bg-white/90 p-6 shadow-soft backdrop-blur-md sm:p-8 lg:p-12"
              >
                <div className="grid gap-8 lg:grid-cols-[1fr_0.95fr] lg:items-center">
                  <div className="max-w-2xl">
                    <div
                      data-hero-stagger
                      className="inline-flex items-center rounded-full border border-[#cfe4f4] bg-[#e6f2ff] px-4 py-1.5 text-sm font-semibold text-hospital-700"
                    >
                      CLD + Sarcopenia Patient Support
                    </div>

                    <h1
                      data-hero-stagger
                      className="mt-6 text-4xl font-bold leading-tight tracking-tight text-slate-800 sm:text-5xl"
                    >
                      Patient Education Assistant
                    </h1>

                    <p
                      data-hero-stagger
                      className="mt-5 max-w-xl text-lg leading-8 text-slate-600 sm:text-xl"
                    >
                      A simple guided learning experience that helps patients understand chronic
                      liver disease, sarcopenia, nutrition, safe movement, and important warning
                      signs in clear everyday language.
                    </p>

                    <div data-hero-stagger className="mt-6 flex flex-wrap gap-3">
                      {heroHighlights.map((item) => (
                        <div
                          key={item.title}
                          className="inline-flex items-center gap-3 rounded-2xl border border-[#dce9f5] bg-[#fbfdff] px-4 py-3"
                        >
                          <FeatureIcon
                            imageSrc={item.imageSrc}
                            fallback={item.fallback}
                            title={item.title}
                          />
                          <div>
                            <p className="text-sm font-semibold uppercase tracking-[0.14em] text-hospital-600">
                              Focus
                            </p>
                            <p className="text-base font-semibold text-slate-800">{item.title}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div data-hero-stagger className="mt-8 flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={handleBeginFlow}
                        className="btn btn-primary min-w-[200px] border-care-600 bg-care-500 px-7 text-lg"
                      >
                        Start Learning
                      </button>
                      <div className="rounded-2xl border border-[#dbeaf6] bg-[#f5fbff] px-4 py-3 text-sm leading-6 text-slate-600 sm:text-base">
                        A calm, hospital-friendly interface for patient education and demo-ready
                        counselling support.
                      </div>
                    </div>
                  </div>

                  <div
                    data-hero-image
                    className="rounded-[1.6rem] border border-[#d9e8f5] bg-gradient-to-br from-[#eef7ff] to-[#f4fbf6] p-4 shadow-soft"
                  >
                    <div className="overflow-hidden rounded-[1.25rem] border border-white/80 bg-white/70 p-3">
                      <img
                        src={heroImage}
                        alt="Doctor guidance illustration"
                        className="h-full min-h-[260px] w-full rounded-[1rem] object-cover sm:min-h-[320px]"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-[1.6rem] border border-white/70 bg-white/88 p-6 shadow-soft backdrop-blur-md sm:p-8">
              <div className="max-w-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-hospital-600">
                  How this helps
                </p>
                <h2 className="mt-2 text-3xl font-bold text-slate-800">
                  Designed for clear, hospital-friendly patient education
                </h2>
                <p className="mt-3 text-base leading-7 text-slate-600 sm:text-lg">
                  As you scroll, the page introduces the learning journey in a simple way before the
                  patient starts the main flow.
                </p>
              </div>

              <div className="mt-6 grid gap-4 lg:grid-cols-3">
                {supportPoints.map((point) => (
                  <article
                    key={point.title}
                    className="rounded-3xl border border-[#dce9f5] bg-[#fbfdff] p-5"
                    data-hover-card
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#eef7ff]">
                        <IconFallback type={point.fallback} />
                      </div>
                      <span className="rounded-full border border-[#dce9f5] bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-care-700">
                        Support
                      </span>
                    </div>
                    <h3 className="mt-4 text-xl font-semibold text-slate-800">{point.title}</h3>
                    <p className="mt-2 text-sm leading-7 text-slate-600 sm:text-base">
                      {point.description}
                    </p>
                  </article>
                ))}
              </div>
            </section>

            <section className="rounded-[1.6rem] border border-white/70 bg-white/88 p-6 shadow-soft backdrop-blur-md sm:p-8">
              <div className="max-w-3xl">
                <p className="text-sm font-semibold uppercase tracking-[0.18em] text-hospital-600">
                  Learning Overview
                </p>
                <h2 className="mt-2 text-3xl font-bold text-slate-800">
                  A simple preview of what patients will learn
                </h2>
                <p className="mt-3 text-base leading-7 text-slate-600 sm:text-lg">
                  This chatbot guides patients through simple, structured health education topics.
                </p>
              </div>

              <div className="mt-7 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                {overviewTopics.map((topic) => (
                  <article
                    key={topic.title}
                    className="rounded-3xl border border-[#dce9f5] bg-[#fbfdff] p-5"
                    data-hover-card
                  >
                    <div className="flex items-center gap-3">
                      <FeatureIcon
                        imageSrc={topic.imageSrc}
                        fallback={topic.fallback}
                        title={topic.title}
                      />
                      <span className="rounded-full border border-[#dce9f5] bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-hospital-600">
                        Topic
                      </span>
                    </div>
                    <h3 className="mt-4 text-lg font-semibold text-slate-800">{topic.title}</h3>
                    <p className="mt-2 text-sm leading-7 text-slate-600 sm:text-base">
                      {topic.description}
                    </p>
                  </article>
                ))}
              </div>

              <div className="mt-7 rounded-3xl border border-[#dbeaf6] bg-[#f5fbff] px-5 py-5">
                <p className="text-base font-semibold text-slate-800">
                  This program includes 4-5 structured sections designed for simple learning.
                </p>
                <div className="mt-3 flex flex-wrap gap-3">
                  {[
                    "Step-by-step learning",
                    "Easy language",
                    "Guided flow",
                    "Quick understanding",
                  ].map((item) => (
                    <span
                      key={item}
                      className="rounded-full border border-[#dce9f5] bg-white px-4 py-2 text-sm font-medium text-slate-600"
                    >
                      {item}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-7 flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-[#d7eadf] bg-[#f4fbf6] px-5 py-5">
                <div className="max-w-2xl">
                  <p className="text-lg font-semibold text-slate-800">
                    Ready to begin your learning journey?
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleBeginFlow}
                  className="btn btn-primary min-w-[220px] border-care-600 bg-care-500 px-7 text-lg"
                >
                  Start Learning
                </button>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
