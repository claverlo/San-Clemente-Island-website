// Animated "how to install" demos for the Get the app guide. Each demo is a simple drawing of the visitor's
// phone or computer with a finger tapping the buttons in order; the matching numbered step lights up as it goes.
(() => {
  const SHARE_SHEET = { type: 'sheet', at: 'bottom', items: [
    ['bi-files', 'Copy'], ['bi-book', 'Add Bookmark'], ['bi-star', 'Add to Favorites'], ['bi-plus-square', 'Add to Home Screen', 'add'],
  ] };
  const ADD_DIALOG = { type: 'dialog', at: 'top', title: 'Add to Home Screen', fox: true, button: ['Add', 'confirm'], header: true };

  const DEMOS = {
    ios: { device: 'phone', bar: 'bottom', buttons: [['bi-chevron-left'], ['bi-chevron-right'], ['bi-box-arrow-up', 'share'], ['bi-book'], ['bi-copy']], script: [
      { tap: 'share', step: 0 }, { show: SHARE_SHEET }, { tap: 'add', step: 1 }, { show: ADD_DIALOG }, { tap: 'confirm', step: 2 }, { home: 'phone' },
    ] },
    ios26: { device: 'phone', bar: 'bottom', buttons: [['bi-chevron-left'], ['url'], ['bi-three-dots', 'more']], script: [
      { tap: 'more', step: 0 },
      { show: { type: 'menu', at: 'bottom-right', items: [['bi-box-arrow-up', 'Share', 'share'], ['bi-book', 'Add Bookmark'], ['bi-plus-lg', 'New Tab']] } },
      { tap: 'share', step: 1 }, { show: SHARE_SHEET }, { tap: 'add', step: 2 }, { show: ADD_DIALOG }, { tap: 'confirm', step: 3 }, { home: 'phone' },
    ] },
    iosTop: { device: 'phone', bar: 'top', buttons: [['url'], ['bi-box-arrow-up', 'share']], script: [
      { tap: 'share', step: 0 }, { show: SHARE_SHEET }, { tap: 'add', step: 1 }, { show: ADD_DIALOG }, { tap: 'confirm', step: 2 }, { home: 'phone' },
    ] },
    android: { device: 'phone', bar: 'top', buttons: [['bi-house'], ['url'], ['bi-three-dots-vertical', 'more']], script: [
      { tap: 'more', step: 0 },
      { show: { type: 'menu', at: 'top-right', items: [['bi-plus-square', 'New tab'], ['bi-clock-history', 'History'], ['bi-star', 'Bookmarks'], ['bi-phone', 'Install app', 'add']] } },
      { tap: 'add', step: 1 },
      { show: { type: 'dialog', at: 'center', title: 'Install app', fox: true, button: ['Install', 'confirm'] } },
      { tap: 'confirm', step: 2 }, { home: 'phone' },
    ] },
    samsung: { device: 'phone', bar: 'bottom', buttons: [['bi-chevron-left'], ['bi-chevron-right'], ['bi-house'], ['bi-copy'], ['bi-list', 'more']], script: [
      { tap: 'more', step: 0 },
      { show: { type: 'menu', at: 'bottom-right', items: [['bi-star', 'Bookmarks'], ['bi-clock-history', 'History'], ['bi-plus-lg', 'Add page to', 'add']] } },
      { tap: 'add', step: 1 },
      { show: { type: 'menu', at: 'bottom-right', items: [['bi-star', 'Bookmarks'], ['bi-grid', 'Quick access'], ['bi-phone', 'Home screen', 'homescreen']] } },
      { tap: 'homescreen', step: 1 },
      { show: { type: 'dialog', at: 'center', title: 'Add to Home screen', fox: true, button: ['Add', 'confirm'] } },
      { tap: 'confirm', step: 2 }, { home: 'phone' },
    ] },
    inApp: { device: 'phone', bar: 'top', buttons: [['bi-x-lg'], ['text', 'Facebook'], ['bi-three-dots', 'more']], script: [
      { tap: 'more', step: 0 },
      { show: { type: 'menu', at: 'top-right', items: [['bi-compass', 'Open in Safari', 'open'], ['bi-link-45deg', 'Copy link']] } },
      { tap: 'open', step: 0 }, { home: 'browser' },
    ] },
    desktop: { device: 'desktop', bar: 'top', buttons: [['bi-arrow-left'], ['bi-arrow-clockwise'], ['url', 'install', 'bi-download']], script: [
      { tap: 'install', step: 1 },
      { show: { type: 'dialog', at: 'top-right', title: 'Install SCI Connect?', fox: true, button: ['Install', 'confirm'] } },
      { tap: 'confirm', step: 2 }, { home: 'desktop' },
    ] },
    macSafari: { device: 'desktop', bar: 'top', menubar: true, buttons: [['bi-apple'], ['text', 'Safari'], ['text', 'File', 'file'], ['text', 'Edit'], ['text', 'View']], script: [
      { tap: 'file', step: 0 },
      { show: { type: 'menu', at: 'top-left', items: [['', 'New Window'], ['', 'Open File...'], ['bi-plus-square', 'Add to Dock...', 'add']] } },
      { tap: 'add', step: 1 },
      { show: { type: 'dialog', at: 'center', title: 'Add to Dock', fox: true, button: ['Add', 'confirm'] } },
      { tap: 'confirm', step: 1 }, { home: 'dock' },
    ] },
    firefox: { device: 'desktop', bar: 'top', buttons: [['bi-arrow-left'], ['bi-arrow-clockwise'], ['url', 'star', 'bi-star']], script: [
      { tap: 'star', step: 0 },
      { show: { type: 'dialog', at: 'top-right', title: 'Bookmark added', fox: true, button: ['Save', 'confirm'] } },
      { tap: 'confirm', step: 1 }, { home: 'bookmark' },
    ] },
  };

  const icon = (name) => (name ? `<i class="bi ${name}"></i>` : '');
  const buttonHtml = ([kind, a, b]) => {
    if (kind === 'url') return `<span class="demo-url"><i class="bi bi-lock-fill"></i> sciconnect.net${a ? `<span class="demo-btn demo-url-btn" data-key="${a}">${icon(b)}</span>` : ''}</span>`;
    if (kind === 'text') return `<span class="demo-btn demo-text"${b ? ` data-key="${b}"` : ''}>${a}</span>`;
    return `<span class="demo-btn"${a ? ` data-key="${a}"` : ''}>${icon(kind)}</span>`;
  };
  const panelHtml = (panel, foxUrl) => {
    if (panel.type === 'dialog' && panel.header) {
      return `<div class="demo-panel demo-dialog demo-sheet-head at-${panel.at}"><span class="demo-dialog-head"><span>Cancel</span><strong>${panel.title}</strong>`
        + `<span class="demo-head-btn" data-key="${panel.button[1]}">${panel.button[0]}</span></span>`
        + `<span class="demo-dialog-app"><img src="${foxUrl}" alt=""> SCI Connect</span></div>`;
    }
    if (panel.type === 'dialog') {
      return `<div class="demo-panel demo-dialog at-${panel.at}"><strong>${panel.title}</strong>`
        + `${panel.fox ? `<span class="demo-dialog-app"><img src="${foxUrl}" alt=""> SCI Connect</span>` : ''}`
        + `<span class="demo-dialog-btn" data-key="${panel.button[1]}">${panel.button[0]}</span></div>`;
    }
    return `<div class="demo-panel demo-${panel.type} at-${panel.at}">${panel.items.map(([ic, label, key]) => `<span class="demo-item"${key ? ` data-key="${key}"` : ''}>${icon(ic)}<span>${label}</span></span>`).join('')}</div>`;
  };
  const homeHtml = (kind, foxUrl) => {
    const fox = `<span class="demo-app new"><img src="${foxUrl}" alt=""><small>SCI Connect</small></span>`;
    if (kind === 'phone') return `<div class="demo-home">${'<span class="demo-app"><span></span><small></small></span>'.repeat(7)}${fox}</div>`;
    if (kind === 'desktop') return `<div class="demo-taskbar">${'<span class="demo-app"><span></span></span>'.repeat(4)}${fox}</div>`;
    if (kind === 'dock') return `<div class="demo-taskbar dock">${'<span class="demo-app"><span></span></span>'.repeat(4)}${fox}</div>`;
    if (kind === 'bookmark') return `<div class="demo-bookmarks"><span class="demo-app new inline"><img src="${foxUrl}" alt=""><small>SCI Connect</small></span></div>`;
    return '<div class="demo-home browser"><span class="demo-done"><i class="bi bi-compass"></i> Opened in Safari</span></div>';
  };

  let timer = null;
  const wait = (ms) => new Promise((resolve) => { timer = setTimeout(resolve, ms); });

  window.renderAppDemo = (holder, demoName, stepsList) => {
    clearTimeout(timer);
    const demo = DEMOS[demoName];
    if (!holder || !demo) { if (holder) holder.hidden = true; return; }
    holder.hidden = false;
    const foxUrl = holder.dataset.icon;
    const runId = (holder.dataset.run = String(Date.now()));
    const bar = `<div class="demo-bar ${demo.bar}${demo.menubar ? ' menubar' : ''}">${demo.buttons.map(buttonHtml).join('')}</div>`;
    holder.innerHTML = `<div class="demo-device ${demo.device}"><div class="demo-screen">`
      + `<div class="demo-page"><span class="demo-site">SCI LIST</span><span></span><span></span><span class="short"></span></div>`
      + `${bar}<div class="demo-layer"></div><span class="demo-finger"><i class="bi bi-hand-index-thumb-fill"></i></span></div></div>`;
    const screen = holder.querySelector('.demo-screen');
    const layer = holder.querySelector('.demo-layer');
    const finger = holder.querySelector('.demo-finger');
    const steps = stepsList ? [...stepsList.children] : [];
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const stillRunning = () => holder.dataset.run === runId && !holder.closest('[hidden]');

    const play = async () => {
      while (stillRunning()) {
        layer.innerHTML = '';
        finger.classList.remove('show', 'tap');
        steps.forEach((li) => li.classList.remove('is-active'));
        await wait(700);
        for (const action of demo.script) {
          if (!stillRunning()) return;
          if (action.tap) {
            const target = screen.querySelector(`[data-key="${action.tap}"]`);
            if (!target) continue;
            steps.forEach((li, i) => li.classList.toggle('is-active', i === action.step));
            const s = screen.getBoundingClientRect();
            const t = target.getBoundingClientRect();
            finger.style.left = `${t.left - s.left + t.width / 2}px`;
            finger.style.top = `${t.top - s.top + t.height / 2}px`;
            finger.classList.add('show');
            await wait(reduced ? 300 : 900);
            target.classList.add('pressed');
            finger.classList.add('tap');
            await wait(450);
            finger.classList.remove('tap');
            target.classList.remove('pressed');
          } else if (action.show) {
            layer.innerHTML = panelHtml(action.show, foxUrl);
            await wait(reduced ? 200 : 500);
          } else if (action.home) {
            finger.classList.remove('show');
            layer.innerHTML = homeHtml(action.home, foxUrl);
            steps.forEach((li) => li.classList.remove('is-active'));
            await wait(2600);
          }
        }
      }
    };
    play();
  };
})();
