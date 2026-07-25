(function () {
  const ISLAND_CENTER = [32.9028812, -118.4980744];
  const ISLAND_BOUNDS = [
    [32.84, -118.62],
    [32.97, -118.38],
  ];

  function MapCard({ poiPoints = [] }) {
    const mapRef = React.useRef(null);

    React.useEffect(() => {
      if (!mapRef.current || typeof window.L === 'undefined') return;

      const map = window.L.map(mapRef.current, {
        zoomControl: true,
        scrollWheelZoom: true,
        dragging: true,
        preferCanvas: true,
        maxBounds: ISLAND_BOUNDS,
        maxBoundsViscosity: 1.0,
      }).setView(ISLAND_CENTER, 13);

      map.createPane('labels');
      map.getPane('labels').style.zIndex = 460;
      map.getPane('labels').style.pointerEvents = 'none';

      window.L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 17,
        minZoom: 11,
        noWrap: true,
        attribution: 'Tiles &copy; Esri',
      }).addTo(map);

      window.L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png', {
        pane: 'labels',
        maxZoom: 17,
        minZoom: 11,
        noWrap: true,
        subdomains: 'abcd',
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      }).addTo(map);

      const poiLayer = window.L.layerGroup().addTo(map);
      const selectedPinLayer = window.L.layerGroup().addTo(map);
      const latitudeInput = document.getElementById('id_latitude');
      const longitudeInput = document.getElementById('id_longitude');
      const mapHelp = document.getElementById('mapPinHelp');

      const updateFormFields = (latitude, longitude) => {
        if (latitudeInput) latitudeInput.value = Number(latitude).toFixed(6);
        if (longitudeInput) longitudeInput.value = Number(longitude).toFixed(6);
        if (mapHelp) mapHelp.textContent = 'Pin placed. Drag it to adjust the location.';
      };

      const placeMarker = (latitude, longitude) => {
        selectedPinLayer.clearLayers();
        const marker = window.L.marker([latitude, longitude], { draggable: true }).addTo(selectedPinLayer);
        marker.on('dragend', () => {
          const position = marker.getLatLng();
          updateFormFields(position.lat, position.lng);
        });
        updateFormFields(latitude, longitude);
      };

      if (latitudeInput && longitudeInput && latitudeInput.value && longitudeInput.value) {
        placeMarker(Number(latitudeInput.value), Number(longitudeInput.value));
      }

      map.on('click', (event) => {
        placeMarker(event.latlng.lat, event.latlng.lng);
      });

      window.L.circleMarker([32.9028812, -118.4980744], {
        radius: 6,
        color: '#ffe07a',
        weight: 2,
        fillColor: '#ffd24d',
        fillOpacity: 0.95,
      }).addTo(poiLayer)
        .bindPopup('San Clemente Island');

      poiPoints.forEach((point) => {
        if (!Number.isFinite(point.latitude) || !Number.isFinite(point.longitude)) return;
        const poiMarker = window.L.circleMarker([point.latitude, point.longitude], {
          radius: 5,
          color: '#0f3b64',
          weight: 2,
          fillColor: '#5ec4ff',
          fillOpacity: 0.9,
        }).addTo(poiLayer)
          .bindPopup(point.title || 'Point of interest');
        poiMarker.on('click', () => {
          map.panTo([point.latitude, point.longitude]);
        });
      });

      return () => {
        map.remove();
      };
    }, [poiPoints]);

    return React.createElement(
      'div',
      {
        className: 'map-shell h-100',
        style: {
          borderRadius: '1rem',
          overflow: 'hidden',
          border: '1px solid rgba(15,59,100,0.10)',
          boxShadow: '0 8px 24px rgba(7,40,82,0.08)',
          minHeight: '320px',
          background: '#ffffff',
        },
      },
      React.createElement(
        'div',
        {
          ref: mapRef,
          style: {
            height: '100%',
            minHeight: '320px',
            position: 'relative',
            background: '#f5f9ff',
          },
        }
      )
    );
  }

  function mountMaps() {
    const roots = document.querySelectorAll('[data-react-map-root="true"]');
    roots.forEach((node) => {
      if (node.hasAttribute('data-mounted')) return;
      node.setAttribute('data-mounted', 'true');
      const poiPoints = node.getAttribute('data-poi-points');
      let parsedPoints = [];
      try {
        parsedPoints = poiPoints ? JSON.parse(poiPoints) : [];
      } catch (error) {
        parsedPoints = [];
      }
      ReactDOM.createRoot(node).render(React.createElement(MapCard, { poiPoints: parsedPoints }));
    });
  }

  function wireMapToggle() {
    const button = document.querySelector('[data-map-toggle="true"]');
    const panel = document.querySelector('[data-map-panel="true"]');
    if (!button || !panel) return;

    button.addEventListener('click', () => {
      const shouldShow = panel.hasAttribute('hidden');
      if (shouldShow) {
        panel.removeAttribute('hidden');
        button.textContent = 'Hide map';
        if (!panel.hasAttribute('data-mounted')) {
          panel.setAttribute('data-react-map-root', 'true');
          panel.setAttribute('data-mounted', 'true');
          ReactDOM.createRoot(panel).render(React.createElement(MapCard));
        }
      } else {
        panel.setAttribute('hidden', 'hidden');
        button.textContent = 'Open map';
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      wireMapToggle();
    });
  } else {
    wireMapToggle();
  }
})();
