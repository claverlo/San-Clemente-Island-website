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

  // What to check when the device's Face ID / fingerprint window doesn't finish.
  const agent = navigator.userAgent;
  const deviceTip = /iPhone|iPad/.test(agent)
    ? 'On iPhone: make sure Face ID or Touch ID is on (Settings → Face ID & Passcode) and Passwords & Keychain is on (Settings → your name → iCloud). Then try again and tap Continue.'
    : /Android/.test(agent)
      ? 'On Android: make sure a screen lock (fingerprint, face or PIN) is set up and you are signed in to Google on this phone. Then try again.'
      : /Windows/.test(agent)
        ? 'On Windows: set up Windows Hello first (Start → Settings → Accounts → Sign-in options → PIN, Face or Fingerprint). Then try again and confirm in the Windows Security window.'
        : /Macintosh/.test(agent)
          ? 'On a Mac: make sure Touch ID or your login password is set up and iCloud Keychain is on. Then try again.'
          : 'Make sure this device has a screen lock (face, fingerprint or PIN) set up. Then try again.';
  const friendly = (error) => {
    if (error && error.name === 'NotAllowedError') return `It didn't finish. The window was closed, timed out, or Face ID / fingerprint isn't set up on this device. ${deviceTip}`;
    if (error && error.name === 'InvalidStateError') return 'This device is already set up. You can sign in with Face ID / fingerprint.';
    if (error && error.name === 'SecurityError') return 'Open this page at https://www.sciconnect.net and try again.';
    return (error && error.message) || 'Something went wrong. Please try again.';
  };
  const show = (box, text, ok) => {
    if (!box) return;
    box.textContent = text;
    box.hidden = false;
    box.className = `passkey-status small mt-2 ${ok ? 'text-success' : 'text-danger'}`;
  };

  // Show the passkey buttons only on devices that can use them.
  document.querySelectorAll('[data-passkey-only]').forEach((el) => { el.hidden = false; });

  // Fetch the options as soon as the page loads, so tapping the button opens Face ID right away
  // (Safari only allows it straight after a tap, with no waiting in between).
  // Only one set of options is in play at a time: the server keeps just the newest challenge.
  const load = (button, decode) => {
    const pending = post(button.dataset.optionsUrl).then(decode);
    pending.catch(() => {});
    return pending;
  };
  const settle = (promise) => {
    let value = null;
    promise.then((v) => { value = v; }, () => {});
    return () => value;
  };

  document.querySelectorAll('[data-passkey-add]').forEach((button) => {
    const status = button.parentElement.querySelector('[data-passkey-status]');
    const decode = (options) => {
      options.challenge = fromB64(options.challenge);
      options.user.id = fromB64(options.user.id);
      (options.excludeCredentials || []).forEach((c) => { c.id = fromB64(c.id); });
      return options;
    };
    let current = load(button, decode);
    let now = settle(current);
    button.addEventListener('click', async () => {
      button.disabled = true;
      status.hidden = true;
      try {
        const publicKey = now() || await current;
        const credential = await navigator.credentials.create({ publicKey });
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
        current = load(button, decode);
        now = settle(current);
        button.disabled = false;
      }
    });
  });

  document.querySelectorAll('[data-passkey-login]').forEach((button) => {
    const status = button.parentElement.querySelector('[data-passkey-status]');
    const decode = (options) => {
      options.challenge = fromB64(options.challenge);
      (options.allowCredentials || []).forEach((c) => { c.id = fromB64(c.id); });
      return options;
    };
    let current = load(button, decode);
    let now = settle(current);
    button.addEventListener('click', async () => {
      button.disabled = true;
      status.hidden = true;
      try {
        const publicKey = now() || await current;
        const credential = await navigator.credentials.get({ publicKey });
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
        current = load(button, decode);
        now = settle(current);
        button.disabled = false;
      }
    });
  });
})();
