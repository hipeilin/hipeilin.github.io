document.addEventListener('contextmenu', (e) => e.preventDefault());

const ABOUT_ME_IMAGES = [
    "img/IMG_6827.png",
    "img/IMG_6828.png",
    "img/IMG_6829.png",
    "img/IMG_6830.png",
    "img/IMG_6831.png",
    "img/IMG_6832.png",
    "img/IMG_6833.png"
];
const HERO_WORDS = ["developer", "engineer", "artist", "designer", "researcher"];

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const shuffle = (list) => {
    const copy = [...list];
    for (let i = copy.length - 1; i > 0; i -= 1) {
        const j = Math.floor(Math.random() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
};

// Custom cursor — only on devices with a precise pointer (mouse)
function initCustomCursor() {
    if (!window.matchMedia('(pointer: fine)').matches) return;

    const dot = document.getElementById('cursor-dot');
    const ring = document.getElementById('cursor-ring');
    let mx = window.innerWidth / 2, my = window.innerHeight / 2;
    let rx = mx, ry = my;

    document.addEventListener('mousemove', (e) => {
        mx = e.clientX;
        my = e.clientY;
        dot.style.left = mx + 'px';
        dot.style.top = my + 'px';
    });

    const tick = () => {
        rx += (mx - rx) * 0.7;
        ry += (my - ry) * 0.7;
        ring.style.left = rx + 'px';
        ring.style.top = ry + 'px';
        requestAnimationFrame(tick);
    };
    tick();

    // Shrink ring over publication links, contact links, and nav items
    const isInteractiveLink = (target) =>
        target.closest('.timeline__item a') || target.closest('.nav__links a') || target.closest('.contact-links a');

    document.addEventListener('mouseover', (e) => {
        if (isInteractiveLink(e.target)) {
            ring.style.transition = 'transform .3s ease';
            ring.style.transform = 'translate(-50%, -50%) scale(0.5)';
            dot.style.opacity = '0';

        }
    });
    document.addEventListener('mouseout', (e) => {
        if (isInteractiveLink(e.target)) {
            ring.style.transform = 'translate(-50%, -50%) scale(1)';
            dot.style.opacity = '1';

        }
    });
}

function initRandomPortrait() {
    const portrait = document.getElementById('portrait');
    if (!portrait) return;
    portrait.src = ABOUT_ME_IMAGES[Math.floor(Math.random() * ABOUT_ME_IMAGES.length)];
}

function initHeroWordCycle() {
    const heroWordElement = document.getElementById('hero-word');
    if (!heroWordElement) return;

    let queue = shuffle(HERO_WORDS);
    const transitionMs = reduceMotion ? 0 : 420;
    const displayMs = reduceMotion ? 1800 : 2500;

    const nextWord = () => {
        if (!queue.length) {
            queue = shuffle(HERO_WORDS);
        }
        return queue.shift();
    };

    const enter = (word) => {
        heroWordElement.style.transition = 'none';
        heroWordElement.style.opacity = '0';
        heroWordElement.style.transform = 'translateX(-32px)';
        heroWordElement.textContent = word;
        heroWordElement.setAttribute('data-word', word);
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

// Fades in [data-reveal] elements as they scroll into view; returns a
// function for observing elements injected later (e.g. publications).
function initRevealAnimations() {
    const revealItems = document.querySelectorAll('[data-reveal]');

    if (reduceMotion) {
        revealItems.forEach((item) => item.classList.add('is-visible'));
        return (items) => items.forEach((el) => el.classList.add('is-visible'));
    }

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
    return (items) => items.forEach((el) => observer.observe(el));
}

function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    const applyTheme = (theme) => {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
            themeToggle.setAttribute('aria-label', 'Switch to dark mode');
        } else {
            document.documentElement.removeAttribute('data-theme');
            themeToggle.setAttribute('aria-label', 'Switch to light mode');
        }
    };

    themeToggle.addEventListener('click', () => {
        const isLight = document.documentElement.getAttribute('data-theme') === 'light';
        const next = isLight ? 'dark' : 'light';
        applyTheme(next);
        try { localStorage.setItem('theme', next); } catch (e) { }
    });

    if (document.documentElement.getAttribute('data-theme') === 'light') {
        themeToggle.setAttribute('aria-label', 'Switch to dark mode');
    }
}

function initLocationToggle() {
    const pin = document.getElementById('location-toggle');
    const map = document.getElementById('location-map');
    if (!pin || !map) return;

    pin.addEventListener('click', (e) => {
        e.preventDefault();
        const isOpen = map.classList.toggle('is-open');
        pin.setAttribute('aria-expanded', String(isOpen));
        pin.setAttribute('aria-label', isOpen ? 'Hide map' : 'Show map');
        pin.setAttribute('title', isOpen ? 'Hide map' : 'Show map');
    });
}

function titleCase(str) {
    return str.replace(/\w\S*/g, (w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase());
}

function renderPublication(pub) {
    const title = titleCase(pub.title || '');
    const url = pub.url || pub.link;
    return `
    <article class="timeline__item" data-reveal>
      <div class="timeline__top">
        <h4>${url ? `<a href="${url}" target="_blank" rel="noopener">${title}</a>` : title}</h4>
        ${pub.year ? `<span>${pub.year}</span>` : ''}
      </div>
      ${pub.authors ? `<p class="pub-authors">${pub.authors}</p>` : ''}
      ${pub.venue ? `<p class="pub-venue"><em>${pub.venue}</em></p>` : ''}
    </article>
  `;
}

function initPublications(observeReveal) {
    const pubList = document.getElementById('publications-list');
    if (!pubList) return;

    fetch('publications.json')
        .then((r) => r.json())
        .then((data) => {
            // Supports both the new format ({ publications: [...] }) and the old plain list
            const pubs = Array.isArray(data) ? data : (data.publications || []);
            if (!pubs.length) return;
            pubList.innerHTML = pubs.map(renderPublication).join('');
            observeReveal(pubList.querySelectorAll('[data-reveal]'));
        })
        .catch((err) => console.error('Failed to load publications:', err));
}

initCustomCursor();
initRandomPortrait();
initHeroWordCycle();
initThemeToggle();
initLocationToggle();
const observeReveal = initRevealAnimations();
initPublications(observeReveal);
