// Face ID / fingerprint sign-in (passkeys). Works on iPhone, iPad, Android, Mac (Touch ID) and Windows (Windows Hello).
(() => {
  if (!window.PublicKeyCredential || !navigator.credentials) return;

  const csrf = () => (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1]
    || (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || '';
  const fromB64 = (value) => {
    const base64 = value.replace(/-/g, '+').replace(/_/g, '/');
    const raw = atob(base64 + '==='.slice((base64.length + 3) % 4));
    return Uint8Array.from(raw, (c) => c.charCodeAt(0)).buffer;
  };
  const toB64 = (buffer) => btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  const post = async (url, body) => {
    const response = await fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify(body || {}),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Something went wrong. Please try again.');
    return data;
  };
  const friendly = (error) => (error && error.name === 'NotAllowedError'
    ? 'Cancelled. Tap the button to try again.'
    : (error && error.name === 'InvalidStateError' ? 'This device is already set up.' : (error && error.message) || 'Something went wrong.'));
  const show = (box, text, ok) => { if (box) { box.textContent = text; box.hidden = false; box.className = `passkey-status small mt-2 ${ok ? 'text-success' : 'text-danger'}`; } };

  // Show the passkey buttons only on devices that can use them.
  document.querySelectorAll('[data-passkey-only]').forEach((el) => { el.hidden = false; });

  // Turn on (dashboard).
  document.querySelectorAll('[data-passkey-add]').forEach((button) => {
    const status = button.parentElement.querySelector('[data-passkey-status]');
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        const options = await post(button.dataset.optionsUrl);
        options.challenge = fromB64(options.challenge);
        options.user.id = fromB64(options.user.id);
        (options.excludeCredentials || []).forEach((c) => { c.id = fromB64(c.id); });
        const credential = await navigator.credentials.create({ publicKey: options });
        const result = await post(button.dataset.verifyUrl, {
          id: credential.id, rawId: toB64(credential.rawId), type: credential.type,
          response: {
            clientDataJSON: toB64(credential.response.clientDataJSON),
            attestationObject: toB64(credential.response.attestationObject),
            transports: credential.response.getTransports ? credential.response.getTransports() : [],
          },
          clientExtensionResults: credential.getClientExtensionResults ? credential.getClientExtensionResults() : {},
        });
        window.location.href = result.redirect;
      } catch (error) {
        show(status, friendly(error), false);
        button.disabled = false;
      }
    });
  });

  // Sign in (login page).
  document.querySelectorAll('[data-passkey-login]').forEach((button) => {
    const status = button.parentElement.querySelector('[data-passkey-status]');
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        const options = await post(button.dataset.optionsUrl);
        options.challenge = fromB64(options.challenge);
        (options.allowCredentials || []).forEach((c) => { c.id = fromB64(c.id); });
        const credential = await navigator.credentials.get({ publicKey: options });
        const result = await post(button.dataset.verifyUrl, {
          id: credential.id, rawId: toB64(credential.rawId), type: credential.type,
          response: {
            clientDataJSON: toB64(credential.response.clientDataJSON),
            authenticatorData: toB64(credential.response.authenticatorData),
            signature: toB64(credential.response.signature),
            userHandle: credential.response.userHandle ? toB64(credential.response.userHandle) : null,
          },
          clientExtensionResults: credential.getClientExtensionResults ? credential.getClientExtensionResults() : {},
          next: button.dataset.next || '',
        });
        window.location.href = result.redirect;
      } catch (error) {
        show(status, friendly(error), false);
        button.disabled = false;
      }
    });
  });
})();
