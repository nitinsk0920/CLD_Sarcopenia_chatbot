import { animate, cleanInlineStyles, eases, remove, stagger } from "animejs";

const BUTTON_SELECTOR = "button, .btn, a.btn, [data-ui-button]";
const CARD_SELECTOR =
  ".question-card, .form-panel, .admin-stat, .visual-card, .choice-item, [data-hover-card]";
const INPUT_SELECTOR = "input, textarea, select";

function prefersReducedMotion() {
  return (
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches
  );
}

function play(target, parameters) {
  if (!target || prefersReducedMotion()) return null;
  remove(target);
  return animate(target, parameters);
}

function getEnteredElement(event, selector) {
  if (!(event.target instanceof Element)) return null;
  const element = event.target.closest(selector);
  if (!element) return null;
  const relatedTarget = event.relatedTarget;
  if (relatedTarget instanceof Node && element.contains(relatedTarget)) {
    return null;
  }
  return element;
}

function animateButtonHoverIn(target) {
  play(target, {
    scale: 1.015,
    duration: 180,
    ease: eases.outQuad,
  });
}

function animateButtonHoverOut(target) {
  play(target, {
    scale: 1,
    duration: 180,
    ease: eases.outQuad,
    onComplete: () => cleanInlineStyles(target),
  });
}

function animateButtonPress(target) {
  play(target, {
    scale: 0.985,
    duration: 110,
    ease: eases.outQuad,
  });
}

function animateCardHoverIn(target) {
  play(target, {
    translateY: -4,
    duration: 220,
    ease: eases.outQuad,
  });
}

function animateCardHoverOut(target) {
  play(target, {
    translateY: 0,
    duration: 220,
    ease: eases.outQuad,
    onComplete: () => cleanInlineStyles(target),
  });
}

function animateInputFocusIn(target) {
  play(target, {
    borderColor: "rgba(13, 148, 136, 0.65)",
    duration: 200,
    ease: eases.outQuad,
  });
}

function animateInputFocusOut(target) {
  play(target, {
    borderColor: "rgba(169, 198, 221, 1)",
    duration: 180,
    ease: eases.outQuad,
    onComplete: () => cleanInlineStyles(target),
  });
}

export function initializeGlobalMicroInteractions() {
  if (typeof document === "undefined" || prefersReducedMotion()) {
    return () => {};
  }

  function handlePointerOver(event) {
    const button = getEnteredElement(event, BUTTON_SELECTOR);
    if (button) animateButtonHoverIn(button);

    const card = getEnteredElement(event, CARD_SELECTOR);
    if (card) animateCardHoverIn(card);
  }

  function handlePointerOut(event) {
    const button = getEnteredElement(event, BUTTON_SELECTOR);
    if (button) animateButtonHoverOut(button);

    const card = getEnteredElement(event, CARD_SELECTOR);
    if (card) animateCardHoverOut(card);
  }

  function handlePointerDown(event) {
    if (!(event.target instanceof Element)) return;
    const button = event.target.closest(BUTTON_SELECTOR);
    if (button) animateButtonPress(button);
  }

  function handlePointerUp(event) {
    if (!(event.target instanceof Element)) return;
    const button = event.target.closest(BUTTON_SELECTOR);
    if (!button) return;
    if (button.matches(":hover")) {
      animateButtonHoverIn(button);
    } else {
      animateButtonHoverOut(button);
    }
  }

  function handleFocusIn(event) {
    if (!(event.target instanceof Element)) return;
    const input = event.target.closest(INPUT_SELECTOR);
    if (input) animateInputFocusIn(input);
  }

  function handleFocusOut(event) {
    if (!(event.target instanceof Element)) return;
    const input = event.target.closest(INPUT_SELECTOR);
    if (input) animateInputFocusOut(input);
  }

  document.addEventListener("pointerover", handlePointerOver);
  document.addEventListener("pointerout", handlePointerOut);
  document.addEventListener("pointerdown", handlePointerDown);
  document.addEventListener("pointerup", handlePointerUp);
  document.addEventListener("pointercancel", handlePointerUp);
  document.addEventListener("focusin", handleFocusIn);
  document.addEventListener("focusout", handleFocusOut);

  return () => {
    document.removeEventListener("pointerover", handlePointerOver);
    document.removeEventListener("pointerout", handlePointerOut);
    document.removeEventListener("pointerdown", handlePointerDown);
    document.removeEventListener("pointerup", handlePointerUp);
    document.removeEventListener("pointercancel", handlePointerUp);
    document.removeEventListener("focusin", handleFocusIn);
    document.removeEventListener("focusout", handleFocusOut);
  };
}

export function animateChatMessages(container) {
  if (!container || prefersReducedMotion()) return;
  const targets = Array.from(container.querySelectorAll("[data-chat-message]")).filter(
    (element) => !element.dataset.motionReady
  );

  if (!targets.length) return;

  targets.forEach((target) => {
    target.dataset.motionReady = "true";
  });

  animate(targets, {
    opacity: [0, 1],
    translateY: [10, 0],
    duration: 260,
    delay: stagger(45),
    ease: eases.outQuad,
  });
}

export function animateLearningMediaCards(container) {
  if (!container || prefersReducedMotion()) return;
  const targets = Array.from(container.querySelectorAll("[data-media-card]")).filter(
    (element) => !element.dataset.motionReady
  );

  if (!targets.length) return;

  targets.forEach((target) => {
    target.dataset.motionReady = "true";
  });

  animate(targets, {
    opacity: [0, 1],
    scale: [0.985, 1],
    translateY: [12, 0],
    duration: 300,
    delay: stagger(55),
    ease: eases.outQuad,
  });
}

export function observeAnimatedTitles(container) {
  if (!container || prefersReducedMotion() || typeof IntersectionObserver === "undefined") {
    return () => {};
  }

  const titles = Array.from(container.querySelectorAll("[data-animate-title]")).filter(
    (element) => !element.dataset.titleObserved
  );

  if (!titles.length) {
    return () => {};
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const target = entry.target;
        if (target.dataset.titleAnimated) {
          observer.unobserve(target);
          return;
        }

        target.dataset.titleAnimated = "true";
        animate(target, {
          opacity: [0, 1],
          translateY: [16, 0],
          duration: 280,
          ease: eases.outQuad,
          onComplete: () => cleanInlineStyles(target),
        });
        observer.unobserve(target);
      });
    },
    {
      threshold: 0.18,
      rootMargin: "0px 0px -10% 0px",
    }
  );

  titles.forEach((title) => {
    title.dataset.titleObserved = "true";
    title.style.opacity = "0";
    title.style.transform = "translateY(16px)";
    observer.observe(title);
  });

  return () => observer.disconnect();
}

export function animateWelcomeHero(target) {
  if (!target || prefersReducedMotion()) return () => {};

  const heroContent = Array.from(target.querySelectorAll("[data-hero-stagger]"));
  const heroImage = target.querySelector("[data-hero-image]");
  const backgroundLayer = document.querySelector("[data-welcome-bg]");

  if (backgroundLayer) {
    animate(backgroundLayer, {
      opacity: [0.92, 1],
      duration: 420,
      ease: eases.outQuad,
      onComplete: () => cleanInlineStyles(backgroundLayer),
    });
  }

  animate(target, {
    opacity: [0, 1],
    translateY: [20, 0],
    duration: 460,
    ease: eases.outQuad,
    onComplete: () => cleanInlineStyles(target),
  });

  if (heroContent.length) {
    animate(heroContent, {
      opacity: [0, 1],
      translateY: [16, 0],
      duration: 420,
      delay: stagger(95, { start: 90 }),
      ease: eases.outQuad,
      onComplete: () => {
        heroContent.forEach((item) => cleanInlineStyles(item));
      },
    });
  }

  let floatingAnimation = null;
  if (heroImage) {
    animate(heroImage, {
      opacity: [0, 1],
      scale: [0.95, 1],
      duration: 420,
      delay: 180,
      ease: eases.outQuad,
      onComplete: () => cleanInlineStyles(heroImage),
    });

    floatingAnimation = animate(heroImage, {
      translateY: [-4, 4],
      duration: 5200,
      loop: true,
      alternate: true,
      ease: eases.inOutSine,
    });
  }

  return () => {
    floatingAnimation?.pause?.();
  };
}

export function observeWelcomeSections(container) {
  if (!container || prefersReducedMotion() || typeof IntersectionObserver === "undefined") {
    return () => {};
  }

  const sections = Array.from(container.querySelectorAll("[data-welcome-section]")).filter(
    (section) => !section.dataset.welcomeObserved
  );

  if (!sections.length) {
    return () => {};
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;

        const section = entry.target;
        if (section.dataset.welcomeAnimated) {
          observer.unobserve(section);
          return;
        }

        section.dataset.welcomeAnimated = "true";
        animate(section, {
          opacity: [0, 1],
          translateY: [30, 0],
          duration: 400,
          ease: eases.outQuad,
          onComplete: () => cleanInlineStyles(section),
        });

        const cards = Array.from(section.querySelectorAll("[data-welcome-card]")).filter(
          (card) => !card.dataset.welcomeCardAnimated
        );

        if (cards.length) {
          cards.forEach((card) => {
            card.dataset.welcomeCardAnimated = "true";
          });

          animate(cards, {
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 360,
            delay: stagger(85, { start: 100 }),
            ease: eases.outQuad,
            onComplete: () => {
              cards.forEach((card) => cleanInlineStyles(card));
            },
          });
        }

        observer.unobserve(section);
      });
    },
    {
      threshold: 0.18,
      rootMargin: "0px 0px -8% 0px",
    }
  );

  sections.forEach((section) => {
    section.dataset.welcomeObserved = "true";
    section.style.opacity = "0";
    section.style.transform = "translateY(30px)";

    const cards = Array.from(section.querySelectorAll("[data-welcome-card]"));
    cards.forEach((card) => {
      card.style.opacity = "0";
      card.style.transform = "translateY(20px)";
    });

    observer.observe(section);
  });

  return () => observer.disconnect();
}
