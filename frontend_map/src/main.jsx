import React from 'react';
import ReactDOM from 'react-dom/client';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'bootstrap/dist/css/bootstrap.min.css';

const points = [
  {
    name: 'San Clemente Island',
    position: [32.9028812, -118.4980744],
    description: 'Island map destination',
  },
];

const createIcon = () => new L.DivIcon({
  html: '<div style="width:14px;height:14px;border-radius:999px;background:#0d6efd;border:2px solid white;box-shadow:0 0 8px rgba(0,0,0,0.25);"></div>',
  className: '',
  iconSize: [14, 14],
});

function MapPreview() {
  return (
    <div className="card shadow-sm border-0 h-100">
      <div className="card-body p-0">
        <div className="p-3 border-bottom bg-light">
          <h3 className="h5 mb-1">Island map preview</h3>
          <p className="text-muted mb-0">Open the full Google Maps view for San Clemente Island.</p>
        </div>
        <div style={{ height: '320px' }}>
          <MapContainer center={[32.9028812, -118.4980744]} zoom={8} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
            {points.map((point) => (
              <Marker key={point.name} position={point.position} icon={createIcon()}>
                <Popup>
                  <div>
                    <strong>{point.name}</strong>
                    <div className="text-muted small">{point.description}</div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}

const mountNode = document.querySelector('[data-react-map-root="true"]');
if (mountNode) {
  ReactDOM.createRoot(mountNode).render(<MapPreview />);
}
