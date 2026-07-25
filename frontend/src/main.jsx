import React from 'react';
import { createRoot } from 'react-dom/client';

const MapApp = ({ points }) => {
  const openDirections = (latitude, longitude, title) => {
    const lat = Number(latitude);
    const lng = Number(longitude);
    const isApple = /iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    const isAndroid = /Android/i.test(navigator.userAgent);
    const destination = `${lat},${lng}`;
    const label = encodeURIComponent(title || 'Destination');
    let url = isApple ? `https://maps.apple.com/?daddr=${destination}&dirflg=d` : isAndroid ? `https://www.google.com/maps/dir/?api=1&destination=${destination}&travelmode=driving` : `https://www.google.com/maps/search/?api=1&query=${destination}`;
    if (label) {
      url += `&query=${label}`;
    }
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="card shadow-sm border-0">
      <div className="card-body">
        <h3 className="h5">React-powered island map</h3>
        <p className="text-muted mb-3">This React view renders the current points and opens directions when you choose one.</p>
        <div className="list-group">
          {points.map((point) => (
            <button
              key={point.id}
              type="button"
              className="list-group-item list-group-item-action d-flex justify-content-between align-items-start"
              onClick={() => openDirections(point.latitude, point.longitude, point.title)}
            >
              <span>
                <strong>{point.title}</strong>
                <div className="text-muted small">{point.description || 'Community point of interest.'}</div>
              </span>
              <span className="badge bg-primary rounded-pill">Directions</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

const mountNode = document.querySelector('[data-react-map-root="true"]');
if (mountNode) {
  const points = JSON.parse(mountNode.dataset.points || '[]');
  createRoot(mountNode).render(<MapApp points={points} />);
}
