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
  };

  let timer;
  const startTimer = () => {
    window.clearInterval(timer);
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      timer = window.setInterval(() => showSlide(current + 1), 4000);
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
});

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
    image.addEventListener('mouseenter', () => showPreview(image));
    image.addEventListener('mouseleave', hidePreview);
  });
}

const poiMapContainer = document.getElementById('poiMap');
if (poiMapContainer) {
  const poiPoints = Array.from(document.querySelectorAll('[data-poi-latitude]'));
  const latitudeInput = document.getElementById('id_latitude');
  const longitudeInput = document.getElementById('id_longitude');
  const mapHelp = document.getElementById('mapPinHelp');

  const openDirections = (latitude, longitude, title) => {
    const lat = Number(latitude);
    const lng = Number(longitude);
    const isAppleDevice = /iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isAndroidDevice = /Android/i.test(navigator.userAgent);
    const destination = `${lat},${lng}`;
    const label = encodeURIComponent(title || 'Destination');

    let mapsUrl = '';
    if (isAppleDevice) {
      mapsUrl = `https://maps.apple.com/?daddr=${destination}&dirflg=d`;
    } else if (isAndroidDevice) {
      mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${destination}&travelmode=driving`;
    } else {
      mapsUrl = `https://www.google.com/maps/search/?api=1&query=${destination}`;
    }

    if (label) {
      mapsUrl += `&query=${label}`;
    }

    window.open(mapsUrl, '_blank', 'noopener,noreferrer');
  };

  if (typeof google !== 'undefined' && google.maps && google.maps.Map) {
    const map = new google.maps.Map(poiMapContainer, {
      center: { lat: 33.0, lng: -118.4 },
      zoom: 10,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true,
    });

    const infoWindow = new google.maps.InfoWindow();
    const markers = [];
    const placeMarker = (position) => {
      if (markers.length) {
        markers[0].setMap(null);
        markers.length = 0;
      }
      const marker = new google.maps.Marker({
        position,
        map,
        draggable: true,
        title: 'Selected point',
      });
      marker.addListener('dragend', () => {
        if (latitudeInput) latitudeInput.value = marker.getPosition().lat().toFixed(6);
        if (longitudeInput) longitudeInput.value = marker.getPosition().lng().toFixed(6);
      });
      markers.push(marker);
      if (latitudeInput) latitudeInput.value = position.lat.toFixed(6);
      if (longitudeInput) longitudeInput.value = position.lng.toFixed(6);
      if (mapHelp) mapHelp.textContent = 'Pin placed. Drag it to adjust the location.';
    };

    if (latitudeInput && longitudeInput && latitudeInput.value && longitudeInput.value) {
      placeMarker({ lat: Number(latitudeInput.value), lng: Number(longitudeInput.value) });
    }

    map.addListener('click', (event) => placeMarker(event.latLng));

    poiPoints.forEach((point) => {
      const marker = new google.maps.Marker({
        position: { lat: Number(point.dataset.poiLatitude), lng: Number(point.dataset.poiLongitude) },
        map,
        title: point.dataset.poiTitle,
      });

      marker.addListener('click', () => {
        const content = `
          <div style="max-width:260px;">
            <strong>${point.dataset.poiTitle}</strong>
            <p style="margin:6px 0 8px;">${point.dataset.poiDescription || 'Community point of interest.'}</p>
            <div style="display:flex; flex-direction:column; gap:6px;">
              <button type="button" class="btn btn-sm btn-outline-dark w-100" data-directions-trigger="true">Open directions</button>
            </div>
          </div>`;
        infoWindow.setContent(content);
        infoWindow.open({ map, anchor: marker });

        google.maps.event.addListenerOnce(infoWindow, 'domready', () => {
          const trigger = document.querySelector('[data-directions-trigger="true"]');
          if (trigger) {
            trigger.addEventListener('click', () => {
              openDirections(point.dataset.poiLatitude, point.dataset.poiLongitude, point.dataset.poiTitle);
            });
          }
        });
      });
    });

    if (!markers.length) {
      const bounds = new google.maps.LatLngBounds();
      poiPoints.forEach((point) => bounds.extend({ lat: Number(point.dataset.poiLatitude), lng: Number(point.dataset.poiLongitude) }));
      if (!bounds.isEmpty()) map.fitBounds(bounds);
    }
  } else if (typeof L !== 'undefined') {
    const islandCenter = [32.9028812, -118.4980744];
    const islandBounds = [
      [32.84, -118.62],
      [32.97, -118.38],
    ];
    const map = L.map(poiMapContainer, {
      zoomControl: true,
      maxBounds: islandBounds,
      maxBoundsViscosity: 1.0,
      worldCopyJump: false,
    }).setView(islandCenter, 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 17,
      minZoom: 11,
      noWrap: true,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    const pointMarkers = [];
    const selectedMarkerLayer = L.layerGroup().addTo(map);
    const updateCoordinates = (latitude, longitude) => {
      if (latitudeInput) latitudeInput.value = Number(latitude).toFixed(6);
      if (longitudeInput) longitudeInput.value = Number(longitude).toFixed(6);
    };
    const placeMarker = (latitude, longitude) => {
      selectedMarkerLayer.clearLayers();
      const marker = L.marker([latitude, longitude], { draggable: true, title: 'Selected point' }).addTo(selectedMarkerLayer);
      marker.on('dragend', () => {
        const position = marker.getLatLng();
        updateCoordinates(position.lat, position.lng);
        if (mapHelp) mapHelp.textContent = 'Pin placed. Drag it to adjust the location.';
      });
      updateCoordinates(latitude, longitude);
      if (mapHelp) mapHelp.textContent = 'Pin placed. Drag it to adjust the location.';
      map.panTo([latitude, longitude]);
    };

    map.on('click', (event) => placeMarker(event.latlng.lat, event.latlng.lng));

    if (latitudeInput && longitudeInput && latitudeInput.value && longitudeInput.value) {
      placeMarker(Number(latitudeInput.value), Number(longitudeInput.value));
    }

    poiPoints.forEach((point) => {
      const latitude = Number(point.dataset.poiLatitude);
      const longitude = Number(point.dataset.poiLongitude);
      const marker = L.marker([latitude, longitude], { title: point.dataset.poiTitle }).addTo(map);
      pointMarkers.push(marker);
      marker.bindPopup(`
        <div style="min-width:220px;">
          <strong>${point.dataset.poiTitle}</strong>
          <p style="margin:6px 0 8px;">${point.dataset.poiDescription || 'Community point of interest.'}</p>
          <button type="button" class="btn btn-sm btn-outline-dark w-100" data-directions-trigger="true">Open directions</button>
        </div>
      `);
      marker.on('popupopen', () => {
        const popupElement = marker.getPopup()?.getElement();
        const trigger = popupElement?.querySelector('[data-directions-trigger="true"]');
        if (trigger) {
          trigger.addEventListener('click', () => {
            openDirections(latitude, longitude, point.dataset.poiTitle);
          });
        }
      });
    });

    if (!selectedMarkerLayer.getLayers().length && pointMarkers.length) {
      map.fitBounds(L.featureGroup(pointMarkers).getBounds());
    }
  } else {
    poiMapContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-center p-4"><div><strong>Map preview ready</strong><p class="mb-0 text-muted">The map location will appear once the page is loaded on a browser with mapping support.</p></div></div>';
  }
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
