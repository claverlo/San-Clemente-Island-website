const chatLog = document.querySelector('[data-chat-log]');
const inPanel = window.parent !== window;

const scrollToBottom = () => { chatLog.scrollTop = chatLog.scrollHeight; };
const nearBottom = () => chatLog.scrollHeight - chatLog.scrollTop - chatLog.clientHeight < 80;

// Inside the site's chat panel the close button tells the parent page to close it; on its own page it links home.
document.querySelector('[data-chat-close]')?.addEventListener('click', (event) => {
  if (!inPanel) return;
  event.preventDefault();
  window.parent.postMessage('sci-chat-close', window.location.origin);
});

if (chatLog.hasAttribute('data-live')) {
  scrollToBottom();
  window.addEventListener('load', scrollToBottom);
  let lastId = Number(chatLog.dataset.lastId) || 0;
  const bottom = document.getElementById('chat-bottom');
  const poll = async () => {
    if (document.hidden) return;
    try {
      const response = await fetch(`${chatLog.dataset.updatesUrl}?after=${lastId}`, { headers: { Accept: 'application/json' } });
      if (!response.ok) return;
      const data = await response.json();
      if (!data.html) return;
      const stick = nearBottom();
      chatLog.querySelector('.chat-empty')?.remove();
      const holder = document.createElement('div');
      holder.innerHTML = data.html;
      holder.querySelectorAll('.chat-msg').forEach((message) => {
        if (!document.getElementById(message.id)) chatLog.insertBefore(message, bottom);
      });
      lastId = data.last_id;
      if (stick) scrollToBottom();
    } catch (error) {
      // Network hiccup: try again on the next tick.
    }
  };
  setInterval(poll, 8000);
}

const search = document.querySelector('[data-chat-search]');
search?.addEventListener('submit', () => search.classList.add('loading'));

const compose = document.querySelector('[data-chat-compose]');
if (compose) {
  const textarea = compose.querySelector('textarea');
  const photoInput = compose.querySelector('input[type="file"]');
  const picked = compose.querySelector('[data-photo-picked]');
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  });
  textarea.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && window.matchMedia('(hover: hover)').matches) {
      event.preventDefault();
      compose.requestSubmit();
    }
  });
  photoInput.addEventListener('change', () => {
    const file = photoInput.files[0];
    picked.hidden = !file;
    picked.querySelector('span').textContent = file ? file.name : '';
  });
  picked.querySelector('[data-photo-clear]').addEventListener('click', () => {
    photoInput.value = '';
    picked.hidden = true;
  });
  compose.addEventListener('submit', () => compose.querySelector('.chat-send').disabled = true);
}

const lightbox = document.querySelector('[data-lightbox]');
const lightboxImage = lightbox.querySelector('img');
chatLog.addEventListener('click', (event) => {
  const photo = event.target.closest('.chat-photo');
  if (!photo) return;
  lightboxImage.src = photo.dataset.full;
  lightboxImage.alt = photo.querySelector('img').alt;
  lightbox.hidden = false;
});
const closeLightbox = () => { lightbox.hidden = true; lightboxImage.src = ''; };
lightbox.addEventListener('click', closeLightbox);
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  if (!lightbox.hidden) closeLightbox();
  else if (inPanel) window.parent.postMessage('sci-chat-close', window.location.origin);
});
