document.querySelectorAll('.alert:not(.form-error-summary):not([data-persistent="true"])').forEach((alert) => setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert).close(), 5000));

const disclaimerGate = document.querySelector('[data-disclaimer-gate]');
if (disclaimerGate) {
  const homePaths = ['/', '/home/'];
  if (!homePaths.includes(window.location.pathname)) {
    disclaimerGate.setAttribute('hidden', '');
  } else {
  const acceptButton = disclaimerGate.querySelector('[data-disclaimer-accept]');
  const declineButton = disclaimerGate.querySelector('[data-disclaimer-decline]');
  const consentStorageKey = 'sciDisclaimerConsentSessionV1';

  const closeDisclaimerGate = () => {
    disclaimerGate.setAttribute('hidden', '');
    document.body.classList.remove('disclaimer-lock');
  };

  const openDisclaimerGate = () => {
    disclaimerGate.removeAttribute('hidden');
    document.body.classList.add('disclaimer-lock');
    acceptButton?.focus();
  };

  let hasAccepted = false;
  try {
    hasAccepted = window.sessionStorage.getItem(consentStorageKey) === 'accepted';
  } catch (error) {
    hasAccepted = false;
  }

  if (hasAccepted) {
    closeDisclaimerGate();
  } else {
    openDisclaimerGate();
  }

  acceptButton?.addEventListener('click', () => {
    try {
      window.sessionStorage.setItem(consentStorageKey, 'accepted');
    } catch (error) {
      // Ignore storage failures and allow access for the current page view.
    }
    closeDisclaimerGate();
  });

  declineButton?.addEventListener('click', () => {
    try {
      window.sessionStorage.removeItem(consentStorageKey);
    } catch (error) {
      // Ignore storage failures while exiting.
    }
    window.location.href = 'about:blank';
  });
  }
}

const firstInvalidField = document.querySelector('.form-panel .errorlist + input, .form-panel .errorlist + select, .form-panel .errorlist + textarea');
if (firstInvalidField) firstInvalidField.focus();
document.querySelectorAll('[data-photo-src]').forEach((button) => {
  button.addEventListener('click', () => {
    const mainPhoto = document.querySelector('#mainListingPhoto');
    if (!mainPhoto) return;
    mainPhoto.src = button.dataset.photoSrc;
    document.querySelectorAll('[data-photo-src]').forEach((item) => item.classList.remove('active'));
    button.classList.add('active');
  });
});

const photoInput = document.querySelector('#id_photos');
const photoPreview = document.querySelector('#photoPreview');
const photoCount = document.querySelector('#photoCount');
if (photoInput && photoPreview && photoCount && typeof DataTransfer !== 'undefined') {
  const selectedPhotos = new DataTransfer();
  const existingCount = Number(photoInput.dataset.existingCount || 0);

  const updatePhotoCount = () => {
    photoCount.textContent = `${existingCount + selectedPhotos.files.length} of 4 photos`;
  };

  photoInput.addEventListener('change', () => {
    const incoming = Array.from(photoInput.files);
    const available = 4 - existingCount - selectedPhotos.files.length;
    incoming.slice(0, Math.max(available, 0)).forEach((file) => {
      const duplicate = Array.from(selectedPhotos.files).some((item) => item.name === file.name && item.size === file.size);
      if (!duplicate) selectedPhotos.items.add(file);
    });
    photoInput.files = selectedPhotos.files;
    photoPreview.querySelectorAll('.preview-tile.selected').forEach((tile) => tile.remove());
    Array.from(selectedPhotos.files).forEach((file, index) => {
      const tile = document.createElement('div');
      tile.className = 'preview-tile selected';
      const image = document.createElement('img');
      image.src = URL.createObjectURL(file);
      image.alt = `Selected photo ${index + 1}`;
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'remove-preview';
      remove.setAttribute('aria-label', `Remove ${file.name}`);
      remove.innerHTML = '&times;';
      remove.addEventListener('click', () => {
        const kept = Array.from(selectedPhotos.files).filter((_, itemIndex) => itemIndex !== index);
        selectedPhotos.items.clear();
        kept.forEach((item) => selectedPhotos.items.add(item));
        photoInput.files = selectedPhotos.files;
        photoInput.dispatchEvent(new Event('change'));
      });
      tile.append(image, remove);
      photoPreview.append(tile);
    });
    updatePhotoCount();
  });
  updatePhotoCount();
}

document.querySelectorAll('[data-phone-input]').forEach((input) => {
  const formatPhone = () => {
    let digits = input.value.replace(/\D/g, '');
    if (digits.length === 11 && digits.startsWith('1')) digits = digits.slice(1);
    digits = digits.slice(0, 10);
    if (digits.length > 6) input.value = `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6)}`;
    else if (digits.length > 3) input.value = `${digits.slice(0, 3)}-${digits.slice(3)}`;
    else input.value = digits;
  };
  input.addEventListener('input', formatPhone);
  formatPhone();
});

const listingCategory = document.querySelector('#id_category[data-listing-category]');
const listingPrice = document.querySelector('#id_price[data-listing-price]');
const listingEmail = document.querySelector('#id_contact_email[data-listing-email]');
if (listingCategory && listingPrice && listingEmail) {
  const priceRow = listingPrice.closest('p');
  const emailRow = listingEmail.closest('p');
  const noPriceCategories = ['Community Post', 'Volunteer Service'];

  const toggleCommunityPostFields = () => {
    const isCommunityPost = listingCategory.value === 'Community Post';
    const isNoPriceCategory = noPriceCategories.includes(listingCategory.value);
    if (priceRow) priceRow.style.display = isNoPriceCategory ? 'none' : '';
    if (isNoPriceCategory) {
      listingPrice.value = '0.00';
      listingPrice.disabled = true;
      listingEmail.required = !isCommunityPost;
      if (isCommunityPost && emailRow) {
        let note = emailRow.querySelector('.community-email-note');
        if (!note) {
          note = document.createElement('small');
          note.className = 'community-email-note text-muted d-block';
          note.textContent = 'Optional for Community Post.';
          emailRow.appendChild(note);
        }
      } else if (emailRow) {
        const note = emailRow.querySelector('.community-email-note');
        if (note) note.remove();
      }
    } else {
      listingPrice.disabled = false;
      listingEmail.required = true;
      if (emailRow) {
        const note = emailRow.querySelector('.community-email-note');
        if (note) note.remove();
      }
    }
  };

  listingCategory.addEventListener('change', toggleCommunityPostFields);
  toggleCommunityPostFields();
}

document.querySelectorAll('[data-hero-slideshow]').forEach((slideshow) => {
  const slides = Array.from(slideshow.querySelectorAll('.hero-slide'));
  const dots = Array.from(slideshow.querySelectorAll('.hero-slide-dots span'));
  const previousButton = slideshow.querySelector('[data-slide-previous]');
  const nextButton = slideshow.querySelector('[data-slide-next]');
  if (slides.length < 2) return;
  let current = 0;

  const showSlide = (index) => {
    slides[current].classList.remove('active');
    dots[current]?.classList.remove('active');
    current = (index + slides.length) % slides.length;
    slides[current].classList.add('active');
    dots[current]?.classList.add('active');
    slideshow.dispatchEvent(new CustomEvent('slidechange', { detail: slides[current] }));
  };

  let timer;
  const startTimer = () => {
    window.clearTimeout(timer);
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const holidayShowing = slides[current].classList.contains('holiday-slide');
      timer = window.setTimeout(() => {
        showSlide(current + 1);
        startTimer();
      }, holidayShowing ? 7000 : 4000);
    }
  };

  previousButton?.addEventListener('click', () => {
    showSlide(current - 1);
    startTimer();
  });
  nextButton?.addEventListener('click', () => {
    showSlide(current + 1);
    startTimer();
  });
  startTimer();
  holidayEffects(slideshow, slides[current]);
});

/* Animated effects drawn over the holiday slides (fireworks, hearts, leaves, snow, ...). */
function holidayEffects(slideshow, firstSlide) {
  const canvas = slideshow.querySelector('[data-holiday-effects]');
  if (!canvas || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const ctx = canvas.getContext('2d');
  const RWB = ['#ffffff', '#e0162b', '#3c6eff'];
  const THEMES = {
    'new-years-day': { kind: 'fireworks', colors: ['#ffd23f', '#ff4fd8', '#4fc3ff', '#ff7a2f', '#ffffff'] },
    'independence-day': { kind: 'fireworks', colors: RWB },
    'valentines-day': { kind: 'hearts', colors: ['#ff2d55', '#ff6b8b', '#d10f3f'] },
    'mothers-day': { kind: 'petals', colors: ['#f7a8c8', '#e58ab8', '#fbd3e4', '#c98bd8'] },
    'st-patricks-day': { kind: 'shamrocks', colors: ['#3fbf4f', '#7ed957', '#2e9b3e'] },
    'easter': { kind: 'confetti', colors: ['#ff8fc7', '#8fd3ff', '#ffe066', '#b4f08c', '#c9a3ff'] },
    'juneteenth': { kind: 'confetti', colors: ['#c8102e', '#111111', '#078930', '#fcd116'] },
    'fathers-day': { kind: 'confetti', colors: ['#1f5fbf', '#ffffff', '#ff6b8b', '#6ec1ff'] },
    'labor-day': { kind: 'confetti', colors: RWB },
    'columbus-day': { kind: 'confetti', colors: ['#009246', '#ffffff', '#ce2b37'] },
    'washingtons-birthday': { kind: 'stars', colors: RWB },
    'memorial-day': { kind: 'stars', colors: ['#ffffff', '#dfe8ff'] },
    'veterans-day': { kind: 'stars', colors: ['#e0162b', '#2a4fbf', '#d4a017'] },
    'mlk-day': { kind: 'sparkles', colors: ['#ffe9a8', '#ffffff', '#ffd27a'] },
    'halloween': { kind: 'bats', colors: ['#111111', '#2a1a0a'] },
    'thanksgiving-day': { kind: 'leaves', colors: ['#d2691e', '#b5651d', '#e8a33d', '#a0522d', '#cc4b1f'] },
    'christmas-day': { kind: 'snow', colors: ['#ffffff'] },
    bubbles: { kind: 'bubbles', colors: ['rgba(220, 245, 255, 0.85)'] },
    gulls: { kind: 'gulls', colors: ['#f4f6f8', '#e2e6ea'] },
    sunlight: { kind: 'motes', colors: ['#fff3c4', '#ffe9a0', '#ffffff'] },
  };
  const COUNTS = { hearts: 16, bats: 7, snow: 70, sparkles: 26, stars: 22, bubbles: 22, gulls: 4, motes: 30 };
  const SWAY = { hearts: 1, snow: 1, petals: 1, leaves: 1, bubbles: 1 };
  let theme = null;
  let parts = [];
  let frame = 0;
  let running = false;
  let width = 0;
  let height = 0;
  const rand = (a, b) => a + Math.random() * (b - a);
  const pick = (list) => list[Math.floor(Math.random() * list.length)];
  const scale = () => Math.max(width, 300) / 600;

  const resize = () => {
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  };

  const spawn = (anywhere) => {
    const kind = theme.kind;
    const color = pick(theme.colors);
    const s = scale();
    if (kind === 'bubbles') {
      return { x: rand(0, width), y: anywhere ? rand(0, height) : height + 20, vx: 0, vy: -rand(0.5, 1.4), s: rand(2, 7) * s, a: rand(0, 6), color };
    }
    if (kind === 'gulls') {
      return { x: anywhere ? rand(0, width) : -40, y: rand(height * 0.05, height * 0.4), vx: rand(0.5, 1.1), vy: rand(-0.1, 0.1), s: rand(9, 16) * s, a: rand(0, 6), spin: 0, color };
    }
    if (kind === 'motes') {
      return { x: rand(0, width), y: rand(0, height), vx: rand(-0.25, 0.25), vy: -rand(0.05, 0.3), s: rand(1.5, 3.5) * s, a: rand(0, 6), spin: 0, life: rand(150, 320), age: 0, color };
    }
    if (kind === 'hearts') {
      return { x: rand(0, width), y: anywhere ? rand(0, height) : height + 20, vx: 0, vy: -rand(0.5, 1.2), s: rand(8, 18) * s, a: rand(0, 6), color };
    }
    if (kind === 'bats') {
      return { x: anywhere ? rand(0, width) : -30, y: rand(height * 0.05, height * 0.6), vx: rand(1, 2.2), vy: 0, s: rand(10, 20) * s, a: rand(0, 6), spin: 0, color };
    }
    if (kind === 'sparkles' || kind === 'stars') {
      return { x: rand(0, width), y: anywhere ? rand(0, height) : -10, vx: 0, vy: kind === 'stars' ? rand(0.3, 0.8) : 0, s: rand(3, 8) * s, a: rand(0, 6), life: rand(80, 200), age: 0, color };
    }
    const snow = kind === 'snow';
    return { x: rand(0, width), y: anywhere ? rand(0, height) : -20, vx: rand(-0.4, 0.4), vy: rand(0.6, 1.6) * (snow ? 0.7 : 1), s: rand(snow ? 2 : 5, snow ? 5 : 11) * s, a: rand(0, 6), spin: rand(-0.05, 0.05), color };
  };

  const burst = () => {
    const x = rand(width * 0.15, width * 0.85);
    const y = rand(height * 0.1, height * 0.45);
    const color = pick(theme.colors);
    const count = 46;
    for (let i = 0; i < count; i += 1) {
      const angle = (Math.PI * 2 * i) / count;
      const speed = rand(1.5, 3.4) * scale();
      parts.push({ x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed, life: rand(50, 80), age: 0, color });
    }
  };

  const heart = (p) => {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.scale(p.s / 16, p.s / 16);
    ctx.beginPath();
    ctx.moveTo(0, 5);
    ctx.bezierCurveTo(-14, -6, -6, -16, 0, -8);
    ctx.bezierCurveTo(6, -16, 14, -6, 0, 5);
    ctx.fillStyle = p.color;
    ctx.globalAlpha = 0.85;
    ctx.fill();
    ctx.restore();
  };

  const shamrock = (p) => {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.a);
    ctx.fillStyle = p.color;
    ctx.fillRect(-p.s * 0.08, 0, p.s * 0.16, p.s * 1.1);
    for (let i = 0; i < 3; i += 1) {
      ctx.rotate((Math.PI * 2) / 3);
      ctx.beginPath();
      ctx.arc(0, -p.s * 0.55, p.s * 0.5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  };

  const star = (p, alpha) => {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.a);
    ctx.globalAlpha = alpha;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    for (let i = 0; i < 10; i += 1) {
      const r = i % 2 ? p.s * 0.45 : p.s;
      const t = (Math.PI * i) / 5 - Math.PI / 2;
      ctx.lineTo(Math.cos(t) * r, Math.sin(t) * r);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  };

  const bat = (p) => {
    const flap = Math.sin(frame * (theme.kind === 'gulls' ? 0.12 : 0.35) + p.a) * 0.6;
    ctx.save();
    ctx.translate(p.x, p.y + Math.sin(frame * 0.05 + p.a) * 6);
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.quadraticCurveTo(-p.s * 0.6, -p.s * (0.2 + flap), -p.s * 1.3, -p.s * flap);
    ctx.quadraticCurveTo(-p.s * 0.7, p.s * 0.1, -p.s * 0.5, p.s * 0.25);
    ctx.quadraticCurveTo(-p.s * 0.25, p.s * 0.1, 0, p.s * 0.3);
    ctx.quadraticCurveTo(p.s * 0.25, p.s * 0.1, p.s * 0.5, p.s * 0.25);
    ctx.quadraticCurveTo(p.s * 0.7, p.s * 0.1, p.s * 1.3, -p.s * flap);
    ctx.quadraticCurveTo(p.s * 0.6, -p.s * (0.2 + flap), 0, 0);
    ctx.fill();
    ctx.restore();
  };

  const leaf = (p) => {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.a);
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.ellipse(0, 0, p.s, p.s * 0.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = 'rgba(80, 40, 10, 0.6)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(-p.s, 0);
    ctx.lineTo(p.s * 1.2, 0);
    ctx.stroke();
    ctx.restore();
  };

  const flake = (p) => {
    ctx.save();
    ctx.translate(p.x, p.y);
    ctx.rotate(p.a);
    ctx.fillStyle = p.color;
    ctx.beginPath();
    if (theme.kind === 'snow') {
      ctx.globalAlpha = 0.9;
      ctx.arc(0, 0, p.s, 0, Math.PI * 2);
      ctx.fill();
    } else if (theme.kind === 'petals') {
      ctx.ellipse(0, 0, p.s * 0.9, p.s * 0.45, 0, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2);
    }
    ctx.restore();
  };

  const fireworks = () => {
    if (frame % 55 === 1) burst();
    ctx.globalCompositeOperation = 'lighter';
    parts = parts.filter((p) => {
      p.age += 1;
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.97;
      p.vy = p.vy * 0.97 + 0.04;
      ctx.globalAlpha = Math.max(0, 1 - p.age / p.life);
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2.2, 0, Math.PI * 2);
      ctx.fill();
      return p.age < p.life;
    });
    ctx.globalCompositeOperation = 'source-over';
  };

  const falling = () => {
    const kind = theme.kind;
    const target = COUNTS[kind] || 34;
    while (parts.length < target) parts.push(spawn(false));
    parts = parts.filter((p) => {
      p.a += p.spin === undefined ? 0.02 : p.spin;
      p.x += p.vx + (SWAY[kind] ? Math.sin(frame * 0.02 + p.a) * 0.4 : 0);
      p.y += p.vy;
      if (kind === 'motes') {
        p.age += 1;
        ctx.globalAlpha = Math.sin(Math.PI * Math.min(1, p.age / p.life)) * 0.8;
        ctx.fillStyle = p.color;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = p.s * 4;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.s, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
        return p.age < p.life;
      }
      if (kind === 'bubbles') {
        ctx.globalAlpha = 0.8;
        ctx.strokeStyle = p.color;
        ctx.lineWidth = 1.3;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.s, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.beginPath();
        ctx.arc(p.x - p.s * 0.35, p.y - p.s * 0.35, p.s * 0.25, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
        return p.y > -20;
      }
      if (kind === 'sparkles' || kind === 'stars') {
        p.age += 1;
        star(p, Math.sin(Math.PI * Math.min(1, p.age / p.life)) * 0.9);
        return p.age < p.life && p.y < height + 20;
      }
      if (kind === 'hearts') heart(p);
      else if (kind === 'shamrocks') shamrock(p);
      else if (kind === 'bats' || kind === 'gulls') bat(p);
      else if (kind === 'leaves') leaf(p);
      else flake(p);
      return p.y > -40 && p.y < height + 40 && p.x < width + 40;
    });
  };

  const draw = () => {
    if (!running || !theme) {
      running = false;
      return;
    }
    frame += 1;
    ctx.clearRect(0, 0, width, height);
    if (theme.kind === 'fireworks') fireworks();
    else falling();
    ctx.globalAlpha = 1;
    window.requestAnimationFrame(draw);
  };

  const show = (slide) => {
    theme = THEMES[slide && slide.dataset ? slide.dataset.holiday || slide.dataset.effect : ''] || null;
    parts = [];
    resize();
    ctx.clearRect(0, 0, width, height);
    if (!theme) return;
    if (theme.kind !== 'fireworks') {
      const target = COUNTS[theme.kind] || 34;
      for (let i = 0; i < target; i += 1) parts.push(spawn(true));
    }
    if (!running) {
      running = true;
      window.requestAnimationFrame(draw);
    }
  };

  window.addEventListener('resize', () => {
    if (theme) resize();
  });
  slideshow.addEventListener('slidechange', (event) => show(event.detail));
  show(firstSlide);
}

const lostFoundImages = document.querySelectorAll('.lost-images img');
if (lostFoundImages.length) {
  const previewBackdrop = document.createElement('div');
  previewBackdrop.className = 'lost-hover-preview-backdrop';
  previewBackdrop.setAttribute('aria-hidden', 'true');

  const previewImage = document.createElement('img');
  previewImage.className = 'lost-hover-preview-image';
  previewImage.alt = '';
  previewBackdrop.appendChild(previewImage);
  document.body.appendChild(previewBackdrop);

  const showPreview = (image) => {
    previewImage.src = image.currentSrc || image.src;
    previewImage.alt = image.alt || 'Lost and found preview';
    previewBackdrop.classList.add('active');
  };

  const hidePreview = () => {
    previewBackdrop.classList.remove('active');
  };

  lostFoundImages.forEach((image) => {
    if (image.closest('.moderation-pending-media')) return;
    image.addEventListener('mouseenter', () => showPreview(image));
    image.addEventListener('mouseleave', hidePreview);
  });
}

document.querySelectorAll('input[type="password"]').forEach((input) => {
  const wrapper = document.createElement('div');
  wrapper.className = 'password-field-wrap';
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'password-toggle-btn';
  toggle.setAttribute('aria-label', 'Show password');
  toggle.innerHTML = '<i class="bi bi-eye"></i>';
  toggle.addEventListener('click', () => {
    const isHidden = input.type === 'password';
    input.type = isHidden ? 'text' : 'password';
    toggle.innerHTML = isHidden ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
    toggle.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
  });
  wrapper.appendChild(toggle);
});

const passwordField = document.getElementById('id_password1');
const passwordChecklist = document.querySelector('#id_password1_helptext ul');
if (passwordField && passwordChecklist && typeof COMMON_PASSWORDS !== 'undefined') {
  passwordChecklist.classList.add('password-checklist');
  const ruleOrder = ['similarity', 'length', 'common', 'numeric'];
  Array.from(passwordChecklist.children).forEach((item, index) => {
    item.dataset.rule = ruleOrder[index];
  });

  const matchItem = document.createElement('li');
  matchItem.dataset.rule = 'match';
  matchItem.textContent = 'Passwords match';
  passwordChecklist.appendChild(matchItem);

  const confirmField = document.getElementById('id_password2');
  const attributeFields = [
    document.getElementById('id_username'),
    document.getElementById('id_first_name'),
    document.getElementById('id_last_name'),
    document.getElementById('id_email'),
  ].filter(Boolean);

  const quickRatio = (a, b) => {
    if (!a.length && !b.length) return 1;
    const counts = new Map();
    for (const char of b) counts.set(char, (counts.get(char) || 0) + 1);
    let matches = 0;
    for (const char of a) {
      const remaining = counts.get(char) || 0;
      if (remaining > 0) {
        matches += 1;
        counts.set(char, remaining - 1);
      }
    }
    return (2 * matches) / (a.length + b.length);
  };

  const isTooSimilar = (password) => {
    const lowerPassword = password.toLowerCase();
    return attributeFields.some((field) => {
      const value = field.value.toLowerCase();
      if (!value) return false;
      const parts = new Set([...value.split(/\W+/).filter(Boolean), value]);
      return Array.from(parts).some((part) => quickRatio(lowerPassword, part) >= 0.7);
    });
  };

  const setState = (item, state) => {
    item.classList.remove('pc-ok', 'pc-bad');
    if (state === 'ok') item.classList.add('pc-ok');
    if (state === 'bad') item.classList.add('pc-bad');
  };

  const updateChecklist = () => {
    const password = passwordField.value;
    const confirm = confirmField ? confirmField.value : '';
    const touched = password.length > 0;

    const results = {
      length: password.length >= 8,
      numeric: !/^\d+$/.test(password),
      common: !COMMON_PASSWORDS.has(password.trim().toLowerCase()),
      similarity: !isTooSimilar(password),
    };

    passwordChecklist.querySelectorAll('li[data-rule]').forEach((item) => {
      const rule = item.dataset.rule;
      if (rule === 'match') {
        setState(item, confirm.length ? (password === confirm ? 'ok' : 'bad') : 'neutral');
      } else {
        setState(item, touched ? (results[rule] ? 'ok' : 'bad') : 'neutral');
      }
    });
  };

  [passwordField, confirmField, ...attributeFields].forEach((field) => {
    field?.addEventListener('input', updateChecklist);
  });
  updateChecklist();
}

const chatPanel = document.querySelector('[data-chat-panel]');
if (chatPanel) {
  const chatFrame = chatPanel.querySelector('iframe');
  const chatFab = document.querySelector('.chat-fab');
  const openChat = () => {
    if (!chatFrame.src) chatFrame.src = chatFrame.dataset.src;
    chatPanel.hidden = false;
    chatFab.hidden = true;
    document.body.classList.add('chat-open');
    bootstrap.Collapse.getInstance(document.getElementById('nav'))?.hide();
  };
  const closeChat = () => {
    chatPanel.hidden = true;
    chatFab.hidden = false;
    document.body.classList.remove('chat-open');
  };
  document.querySelectorAll('[data-chat-open]').forEach((link) => link.addEventListener('click', (event) => {
    event.preventDefault();
    openChat();
  }));
  window.addEventListener('message', (event) => {
    if (event.origin === window.location.origin && event.data === 'sci-chat-close') closeChat();
  });
  if (new URLSearchParams(window.location.search).get('chat') === '1') openChat();
}

// Installable app (SCI Connect): register the worker and offer "Add to Home Screen".
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
}

// Phones can't add a website to the home screen by themselves, so the guide shows exactly which buttons to tap
// for the visitor's phone and browser, with an arrow pointing at the right spot. sciconnect.net/#get-app opens it.
const appGuide = document.querySelector('[data-app-guide]');
// Preview another device's guide from any computer, e.g. sciconnect.net/#get-app-android
const APP_GUIDE_PREVIEWS = {
  iphone: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
  iphone26: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1',
  ipad: 'Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1',
  'iphone-chrome': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0 Mobile/15E148 Safari/604.1',
  facebook: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/480.0]',
  android: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36',
  samsung: 'Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/26.0 Chrome/122.0 Mobile Safari/537.36',
  windows: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36',
  mac: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15',
  firefox: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
};
const appGuidePreview = () => (window.location.hash.match(/^#get-app-([a-z0-9-]+)$/) || [])[1];
const appGuideSteps = () => {
  const preview = APP_GUIDE_PREVIEWS[appGuidePreview()];
  const ua = preview || window.navigator.userAgent;
  const touchMac = !preview && /macintosh/i.test(ua) && navigator.maxTouchPoints > 1;
  const isIos = /iphone|ipad|ipod/i.test(ua) || touchMac;
  const isIpad = /ipad/i.test(ua) || touchMac;
  const share = '<i class="bi bi-box-arrow-up"></i>';
  const plus = '<i class="bi bi-plus-square"></i>';
  const dots = '<i class="bi bi-three-dots"></i>';
  if (/FBAN|FBAV|FB_IAB|Instagram|Messenger|Snapchat|Line\/|TikTok/i.test(ua)) {
    return { demo: 'inApp', arrow: 'none', steps: [
      `You're inside another app's browser, which can't add apps. Tap ${dots} or the menu and choose <strong>Open in Safari</strong> (or <strong>Open in Chrome</strong>).`,
      'Or copy the link below and paste it into Safari or Chrome: <button type="button" class="btn btn-sm btn-navy ms-1" data-copy-site-link>Copy link</button>',
      'Then tap the fox banner again and follow the steps.',
    ] };
  }
  if (isIos && /CriOS/i.test(ua)) {
    return { demo: 'iosTop', arrow: 'top-right', steps: [
      `Tap the <strong>Share</strong> button ${share} at the top right, next to the web address.`,
      `Tap <strong>Add to Home Screen</strong> ${plus}. You may need to scroll down to see it.`,
      'Tap <strong>Add</strong>.',
    ] };
  }
  if (isIos) {
    const safariVersion = Number((ua.match(/Version\/(\d+)/) || [])[1] || 0);
    if (isIpad) {
      return { demo: 'iosTop', arrow: 'top-right', steps: [
        `Tap the <strong>Share</strong> button ${share} at the top right of the screen.`,
        `Tap <strong>Add to Home Screen</strong> ${plus}.`,
        'Tap <strong>Add</strong>.',
      ] };
    }
    if (safariVersion >= 26) {
      return { demo: 'ios26', arrow: 'bottom-right', steps: [
        `Tap the ${dots} or <i class="bi bi-list"></i> button at the bottom of the screen (whichever you see). If you see the <strong>Share</strong> button ${share} there instead, tap it and skip to step 3.`,
        `Tap <strong>Share</strong> ${share}.`,
        `Scroll down and tap <strong>Add to Home Screen</strong> ${plus}.`,
        'Tap <strong>Add</strong>.',
      ] };
    }
    return { demo: 'ios', arrow: 'bottom', steps: [
      `Tap the <strong>Share</strong> button ${share} at the bottom of the screen (the square with an arrow pointing up).`,
      `Scroll down and tap <strong>Add to Home Screen</strong> ${plus}.`,
      'Tap <strong>Add</strong> at the top right.',
    ] };
  }
  if (/SamsungBrowser/i.test(ua)) {
    return { demo: 'samsung', arrow: 'bottom-right', steps: [
      'Tap the <strong>menu</strong> button <i class="bi bi-list"></i> at the bottom right.',
      'Tap <strong>Add page to</strong>, then <strong>Home screen</strong>.',
      'Tap <strong>Add</strong>.',
    ] };
  }
  if (/android/i.test(ua) && /Firefox/i.test(ua)) {
    return { demo: 'android', arrow: 'top-right', steps: [
      'Tap the <strong>menu</strong> button <i class="bi bi-three-dots-vertical"></i>.',
      'Tap <strong>Add app to Home screen</strong> (or <strong>Add to Home screen</strong>).',
      'Tap <strong>Add</strong>.',
    ] };
  }
  if (/android/i.test(ua)) {
    return { demo: 'android', arrow: 'top-right', steps: [
      'Tap the <strong>menu</strong> button <i class="bi bi-three-dots-vertical"></i> at the top right.',
      'Tap <strong>Install app</strong> or <strong>Add to Home screen</strong>.',
      'Tap <strong>Install</strong>.',
    ] };
  }
  const isMac = /macintosh/i.test(ua);
  const bookmarkKeys = isMac ? '<strong>⌘ Command + D</strong>' : '<strong>Ctrl + D</strong>';
  if (/Firefox/i.test(ua)) {
    return { demo: 'firefox', arrow: 'none', steps: [
      `Firefox can't install apps, so bookmark SCI Connect instead: press ${bookmarkKeys}, or click the star <i class="bi bi-star"></i> in the address bar.`,
      'Click <strong>Save</strong>. SCI Connect is now in your bookmarks.',
      'Want it as an app with its own icon? Open sciconnect.net in Chrome, Edge or Safari and tap the fox banner again.',
    ] };
  }
  if (isMac && /Version\/\d+.*Safari/i.test(ua) && !/Chrome|Edg\//i.test(ua)) {
    return { demo: 'macSafari', arrow: 'none', steps: [
      'In the menu bar at the top of the screen, click <strong>File</strong>.',
      'Click <strong>Add to Dock</strong>, then <strong>Add</strong>. SCI Connect will sit in your Dock with the fox icon.',
      `Older Mac? Bookmark it instead: press ${bookmarkKeys}.`,
    ] };
  }
  return { demo: 'desktop', arrow: 'top-right', steps: [
    'Already installed? Look for <strong>Open in app</strong> at the right end of the address bar, or find SCI Connect in your apps.',
    'Click the <strong>install</strong> icon <i class="bi bi-download"></i> at the right end of the address bar, or open the browser menu and choose <strong>Install SCI Connect</strong>.',
    `Click <strong>Install</strong>. SCI Connect will open in its own window and show up in your ${isMac ? 'Launchpad and Dock' : 'Start menu'}.`,
    `No install icon? Bookmark it instead: press ${bookmarkKeys}.`,
  ] };
};
const openAppGuide = () => {
  if (!appGuide) return;
  const { demo, arrow, steps } = appGuideSteps();
  const stepsList = appGuide.querySelector('[data-app-guide-steps]');
  stepsList.innerHTML = steps.map((step) => `<li>${step}</li>`).join('');
  appGuide.querySelector('[data-app-guide-help]').hidden = !demo.startsWith('ios');
  appGuide.dataset.arrow = arrow;
  appGuide.hidden = false;
  document.body.classList.add('disclaimer-lock');
  window.renderAppDemo?.(appGuide.querySelector('[data-app-demo]'), demo, stepsList);
};
const closeAppGuide = () => {
  if (!appGuide || appGuide.hidden) return;
  appGuide.hidden = true;
  document.body.classList.remove('disclaimer-lock');
  if (window.location.hash.startsWith('#get-app')) history.replaceState(null, '', window.location.pathname + window.location.search);
};
if (appGuide) {
  appGuide.addEventListener('click', async (event) => {
    if (event.target === appGuide || event.target.closest('[data-app-guide-close]')) closeAppGuide();
    const copyButton = event.target.closest('[data-copy-site-link]');
    if (copyButton) {
      try {
        await navigator.clipboard.writeText(window.location.origin);
        copyButton.textContent = 'Copied!';
      } catch (error) {
        copyButton.textContent = window.location.host;
      }
    }
  });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape') closeAppGuide(); });
  const openFromHash = () => { if (window.location.hash === '#get-app' || appGuidePreview()) openAppGuide(); };
  window.addEventListener('hashchange', openFromHash);
  openFromHash();
}

// Chrome and Edge (Windows, Mac, Android) hand us a one-click install prompt; keep it for whenever the visitor
// taps the logo, "Get app" or the footer link. Browsers without one (iPhone, Firefox, Safari) get the guide.
let installPrompt = null;
const appBanner = document.querySelector('[data-app-banner]');
const isInstalled = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  installPrompt = event;
});
const getApp = async () => {
  if (!installPrompt) { openAppGuide(); return; }
  installPrompt.prompt();
  const { outcome } = await installPrompt.userChoice;
  installPrompt = null;
  if (outcome === 'accepted' && appBanner) appBanner.hidden = true;
};
document.querySelectorAll('[data-app-guide-open], [data-app-install]').forEach((link) => link.addEventListener('click', (event) => {
  event.preventDefault();
  getApp();
}));
window.addEventListener('appinstalled', () => { installPrompt = null; if (appBanner) appBanner.hidden = true; });

if (appBanner) {
  const dismissKey = 'sciAppBannerDismissed';
  let dismissed = false;
  try { dismissed = window.localStorage.getItem(dismissKey) === '1'; } catch (error) { dismissed = false; }
  if (!isInstalled && !dismissed) appBanner.hidden = false;
  appBanner.querySelector('[data-app-dismiss]').addEventListener('click', () => {
    appBanner.hidden = true;
    try { window.localStorage.setItem(dismissKey, '1'); } catch (error) { /* banner just comes back next visit */ }
  });
}

// Email alerts: typing in the "Other" box ticks its checkbox; ticking the box jumps to the text field.
document.addEventListener('DOMContentLoaded', () => {
  const other = document.querySelector('[data-alert-other]');
  const words = document.querySelector('[data-alert-keywords]');
  if (!other || !words) return;
  words.addEventListener('input', () => { other.checked = words.value.trim() !== ''; });
  other.addEventListener('change', () => { if (other.checked) words.focus(); });
});

// Responsive top menu: show the links in one row only when they all fit; otherwise use the menu button.
(() => {
  const nav = document.querySelector('[data-auto-nav]');
  if (!nav) return;
  const container = nav.querySelector('.container');
  const fit = () => {
    // Measure the real one-row layout (without the menu-button styles), then pick.
    nav.classList.remove('nav-collapsed');
    nav.classList.add('navbar-expand-xl');
    const wide = window.matchMedia('(min-width: 1200px)').matches;
    const fits = wide && container.scrollWidth <= container.clientWidth + 1;
    nav.classList.toggle('navbar-expand-xl', fits);
    nav.classList.toggle('nav-collapsed', !fits);
  };
  let frame = 0;
  window.addEventListener('resize', () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(fit); });
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
  window.addEventListener('load', fit);
  // Re-check whenever the links change size (for example when the website's font finishes loading).
  if (window.ResizeObserver) {
    const observer = new ResizeObserver(() => { cancelAnimationFrame(frame); frame = requestAnimationFrame(fit); });
    nav.querySelectorAll('.navbar-brand, .navbar-nav .nav-link, .navbar-nav .btn').forEach((el) => observer.observe(el));
  }
  fit();
})();

// Remember the email typed on the login / reset forms on this device, so people don't retype it every time.
(() => {
  const KEY = 'sci-last-email';
  document.querySelectorAll('[data-remember-form]').forEach((form) => {
    const input = form.querySelector('[data-remember-email]');
    if (!input) return;
    try {
      const saved = localStorage.getItem(KEY);
      if (saved && !input.value) {
        input.value = saved;
        const password = form.querySelector('input[type="password"]');
        if (password && !input.hasAttribute('autofocus')) password.focus();
      }
    } catch (e) { /* storage blocked: nothing to fill */ }
    form.addEventListener('submit', () => {
      try { if (input.value.includes('@')) localStorage.setItem(KEY, input.value.trim()); } catch (e) { /* ignore */ }
    });
  });
})();
