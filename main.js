const aboutMeImages = [
  "img/IMG_6827.png",
  "img/IMG_6828.png",
  "img/IMG_6829.png",
  "img/IMG_6830.png",
  "img/IMG_6831.png",
  "img/IMG_6832.png",
  "img/IMG_6833.png"
];

const randomImage = aboutMeImages[Math.floor(Math.random() * aboutMeImages.length)];
const portrait = document.getElementById('portrait');
if (portrait) portrait.src = randomImage;

const revealItems = document.querySelectorAll('[data-reveal]');
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const heroWords = ["developer", "engineer", "artist", "designer", "researcher"];
const heroWordElement = document.getElementById('hero-word');

const shuffle = (list) => {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
};

if (heroWordElement) {
  let queue = shuffle(heroWords);
  const transitionMs = reduceMotion ? 0 : 420;
  const displayMs = reduceMotion ? 1800 : 1600;

  const nextWord = () => {
    if (!queue.length) {
      queue = shuffle(heroWords);
    }
    return queue.shift();
  };

  const enter = (word) => {
    heroWordElement.style.transition = 'none';
    heroWordElement.style.opacity = '0';
    heroWordElement.style.transform = 'translateX(-32px)';
    heroWordElement.textContent = word;
    heroWordElement.getBoundingClientRect();
    heroWordElement.style.transition = `opacity ${transitionMs}ms ease, transform ${transitionMs}ms ease`;
    heroWordElement.style.opacity = '1';
    heroWordElement.style.transform = 'translateX(0)';
  };

  const showWord = (first = false) => {
    const word = nextWord();
    if (reduceMotion) {
      heroWordElement.textContent = word;
      heroWordElement.style.opacity = '1';
    } else if (first) {
      enter(word);
    } else {
      heroWordElement.style.transition = `opacity ${transitionMs}ms ease, transform ${transitionMs}ms ease`;
      heroWordElement.style.opacity = '0';
      heroWordElement.style.transform = 'translateX(32px)';
      window.setTimeout(() => enter(word), transitionMs);
    }
  };

  showWord(true);
  window.setInterval(showWord, displayMs + transitionMs);
}

if (reduceMotion) {
  revealItems.forEach((item) => item.classList.add('is-visible'));
} else {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.18 }
  );

  revealItems.forEach((item) => observer.observe(item));

  // Observe dynamically injected publication items
  const observeNewItems = (items) => items.forEach((el) => observer.observe(el));
  window._observeReveal = observeNewItems;
}

const themeToggle = document.getElementById('theme-toggle');
const applyTheme = (theme) => {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    themeToggle.setAttribute('aria-label', 'Switch to dark mode');
  } else {
    document.documentElement.removeAttribute('data-theme');
    themeToggle.setAttribute('aria-label', 'Switch to light mode');
  }
};
themeToggle?.addEventListener('click', () => {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const next = isLight ? 'dark' : 'light';
  applyTheme(next);
  try { localStorage.setItem('theme', next); } catch (e) {}
});
if (document.documentElement.getAttribute('data-theme') === 'light') {
  themeToggle?.setAttribute('aria-label', 'Switch to dark mode');
}

// Render publications from publications.json
const pubList = document.getElementById('publications-list');
if (pubList) {
  fetch('publications.json')
    .then((r) => r.json())
    .then((pubs) => {
      if (!pubs.length) return;
      pubList.innerHTML = pubs.map((pub) => `
        <article class="timeline__item" data-reveal>
          <div class="timeline__top">
            <h3>${pub.url ? `<a href="${pub.url}" target="_blank" rel="noopener">${pub.title}</a>` : pub.title}</h3>
            ${pub.year ? `<span>${pub.year}</span>` : ''}
          </div>
          ${pub.venue ? `<p><em>${pub.venue}</em></p>` : ''}
          ${pub.abstract ? `<p>${pub.abstract}</p>` : ''}
        </article>
      `).join('');

      const newItems = pubList.querySelectorAll('[data-reveal]');
      if (window._observeReveal) {
        window._observeReveal(newItems);
      } else {
        newItems.forEach((el) => el.classList.add('is-visible'));
      }
    })
    .catch(() => {}); // silently fail — list stays empty
}
