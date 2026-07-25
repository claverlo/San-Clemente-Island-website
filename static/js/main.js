document.querySelectorAll('.alert:not(.form-error-summary)').forEach((alert) => setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert).close(), 5000));
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
