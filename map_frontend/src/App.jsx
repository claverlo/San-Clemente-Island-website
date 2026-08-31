import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";
import * as api from "./api.js";

function makeIcon(image, active, hasPending) {
  const safeImage =
    image && image !== "" ? image : "https://picsum.photos/200?random=99";

  return L.divIcon({
    html: `
      <div class="${active || hasPending ? "blink-marker" : ""}" style="
        width:60px;
        height:60px;
        border-radius:10px;
        overflow:hidden;
        border:3px solid ${hasPending ? "orange" : active ? "red" : "white"};
        box-shadow:0 0 8px black;
        background:#fff;
        position:relative;
      ">
        <img
          src="${safeImage}"
          style="width:100%;height:100%;object-fit:cover;"
          onerror="this.src='https://picsum.photos/200?random=100';"
        />

        ${
          hasPending
            ? `<div style="
                position:absolute;
                bottom:0;
                left:0;
                width:100%;
                background:orange;
                color:black;
                font-size:10px;
                font-weight:bold;
                text-align:center;
              ">PENDING</div>`
            : ""
        }
      </div>
    `,
    className: "",
    iconSize: [60, 60],
  });
}

function makeUserLocationIcon(heading, accuracyMeters) {
  const rotation = typeof heading === "number" ? heading : 0;
  const accuracyFeet =
    typeof accuracyMeters === "number" && !Number.isNaN(accuracyMeters)
      ? Math.round(accuracyMeters * 3.28084)
      : null;
  const accuracyText =
    accuracyFeet !== null
      ? `Location may be off by up to ${accuracyFeet} ft`
      : "Location accuracy varies";

  return L.divIcon({
    html: `
      <div style="
        width:170px;
        display:flex;
        flex-direction:column;
        align-items:center;
      ">
        <div style="
          background:rgba(0,0,0,0.72);
          color:#fff;
          font-size:11px;
          padding:3px 10px;
          border-radius:6px;
          white-space:nowrap;
          margin-bottom:4px;
        ">${accuracyText}</div>

        <div style="
          background:#1a73e8;
          color:#fff;
          font-weight:800;
          font-size:15px;
          letter-spacing:0.02em;
          padding:6px 14px;
          border-radius:8px;
          white-space:nowrap;
          box-shadow:0 2px 6px rgba(0,0,0,0.45);
          margin-bottom:6px;
        ">YOU ARE HERE</div>

        <div style="
          width:52px;
          height:52px;
          display:flex;
          align-items:center;
          justify-content:center;
          transform: rotate(${rotation}deg);
          transition: transform 0.15s ease;
        ">
          <svg width="52" height="52" viewBox="0 0 48 48" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.55));">
            <polygon points="24,3 41,43 24,33 7,43" fill="#1a73e8" stroke="white" stroke-width="2.5" stroke-linejoin="round" />
          </svg>
        </div>
      </div>
    `,
    className: "",
    iconSize: [170, 122],
    iconAnchor: [85, 96],
  });
}

function extractCompassHeading(event) {
  if (typeof event.webkitCompassHeading === "number") {
    return event.webkitCompassHeading;
  }
  if (typeof event.alpha === "number") {
    return 360 - event.alpha;
  }
  return null;
}

function FlyToSpot({ selected }) {
  const map = useMap();

  useEffect(() => {
    if (selected) {
      map.flyTo(selected.position, 15);
    }
  }, [selected, map]);

  return null;
}

function FlyToUserLocation({ trigger, userLocation }) {
  const map = useMap();

  useEffect(() => {
    if (trigger && userLocation) {
      map.flyTo([userLocation.lat, userLocation.lng], 16);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trigger]);

  return null;
}

function ClickToPlace({ enabled, onPlace }) {
  useMapEvents({
    click(e) {
      if (!enabled) return;
      onPlace(e.latlng.lat, e.latlng.lng);
    },
  });

  return null;
}

function Controls() {
  const map = useMap();

  return (
    <>
      <div style={styles.zoom}>
        <button style={styles.btn} onClick={() => map.zoomIn()}>
          +
        </button>

        <button style={styles.btn} onClick={() => map.zoomOut()}>
          −
        </button>
      </div>

      <div style={styles.move}>
        <button style={styles.btn} onClick={() => map.panBy([0, -100])}>
          ↑
        </button>

        <div>
          <button style={styles.btn} onClick={() => map.panBy([-100, 0])}>
            ←
          </button>

          <button style={styles.btn} onClick={() => map.panBy([100, 0])}>
            →
          </button>
        </div>

        <button style={styles.btn} onClick={() => map.panBy([0, 100])}>
          ↓
        </button>
      </div>
    </>
  );
}

export default function App({ adminMode = false }) {
  const navigate = useNavigate();
  const markerRefs = useRef({});

  const [spots, setSpots] = useState([]);

  const [selected, setSelected] = useState(null);
  const [name, setName] = useState("");
  const [pending, setPending] = useState(null);
  const [viewer, setViewer] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [drag, setDrag] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [uploadIndex, setUploadIndex] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);
  const [userLocation, setUserLocation] = useState(null);
  const [heading, setHeading] = useState(null);
  const [compassNeedsPermission, setCompassNeedsPermission] = useState(false);
  const [flyToMyLocationTick, setFlyToMyLocationTick] = useState(0);
  const [locationError, setLocationError] = useState(null);

  const admin = adminMode;

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError("This browser does not support location.");
      return;
    }

    const watchId = navigator.geolocation.watchPosition(
      (pos) => {
        setLocationError(null);
        setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });

        if (typeof pos.coords.heading === "number" && !Number.isNaN(pos.coords.heading)) {
          setHeading((prev) => (prev === null ? pos.coords.heading : prev));
        }
      },
      (err) => {
        setUserLocation(null);
        setLocationError(err.message || "Could not get your location.");
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  useEffect(() => {
    const handleOrientation = (event) => {
      const compassHeading = extractCompassHeading(event);
      if (compassHeading !== null && !Number.isNaN(compassHeading)) {
        setHeading(compassHeading);
      }
    };

    const needsIOSPermission =
      typeof DeviceOrientationEvent !== "undefined" &&
      typeof DeviceOrientationEvent.requestPermission === "function";

    if (needsIOSPermission) {
      setCompassNeedsPermission(true);
    } else if (typeof window !== "undefined" && window.DeviceOrientationEvent) {
      window.addEventListener("deviceorientationabsolute", handleOrientation, true);
      window.addEventListener("deviceorientation", handleOrientation, true);
    }

    return () => {
      window.removeEventListener("deviceorientationabsolute", handleOrientation, true);
      window.removeEventListener("deviceorientation", handleOrientation, true);
    };
  }, []);

  const enableCompass = () => {
    if (
      typeof DeviceOrientationEvent === "undefined" ||
      typeof DeviceOrientationEvent.requestPermission !== "function"
    ) {
      return;
    }

    DeviceOrientationEvent.requestPermission()
      .then((response) => {
        if (response === "granted") {
          window.addEventListener(
            "deviceorientation",
            (event) => {
              const compassHeading = extractCompassHeading(event);
              if (compassHeading !== null && !Number.isNaN(compassHeading)) {
                setHeading(compassHeading);
              }
            },
            true
          );
          setCompassNeedsPermission(false);
        }
      })
      .catch(() => {});
  };

  const handleAdminLogin = async () => {
    setLoginError("");
    setLoggingIn(true);
    try {
      await api.adminLogin(loginUsername, loginPassword);
      setShowAdminLogin(false);
      setLoginUsername("");
      setLoginPassword("");
      navigate("/admin");
    } catch (err) {
      setLoginError(err.message || "Invalid username or password.");
    } finally {
      setLoggingIn(false);
    }
  };

  const refreshSpots = async () => {
    const data = await api.getSpots();
    setSpots(data);
  };

  useEffect(() => {
    refreshSpots();
  }, []);

  const touchStartX = useRef(null);

  const openViewer = (images, index) => {
    setViewer({ images, index });
    setZoom(1);
    setDrag({ x: 0, y: 0 });
  };

  const goToViewerImage = (delta) => {
    setViewer((prev) => {
      if (!prev) return prev;
      const nextIndex =
        (prev.index + delta + prev.images.length) % prev.images.length;
      return { ...prev, index: nextIndex };
    });
    setZoom(1);
    setDrag({ x: 0, y: 0 });
  };

  useEffect(() => {
    if (!viewer) return;

    const handleKey = (e) => {
      if (e.key === "ArrowLeft") goToViewerImage(-1);
      else if (e.key === "ArrowRight") goToViewerImage(1);
      else if (e.key === "Escape") {
        setViewer(null);
        setZoom(1);
        setDrag({ x: 0, y: 0 });
      }
    };

    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [viewer]);

  const openSpotPopup = (spot) => {
    setSelected(spot);

    setTimeout(() => {
      const marker = markerRefs.current[spot.name];
      if (marker) marker.openPopup();
    }, 600);
  };

  const focusSpot = (spot) => {
    setSelected(null);
    setMenuOpen(false);

    setTimeout(() => {
      openSpotPopup(spot);
    }, 50);
  };

  const goToMyLocation = () => {
    if (!userLocation) return;
    setSelected(null);
    setMenuOpen(false);
    setFlyToMyLocationTick((tick) => tick + 1);
  };

  const saveSpot = async () => {
    if (!name || !pending) {
      alert("Type a spot name, then click the map.");
      return;
    }

    const newSpot = await api.createSpot(name, pending.lat, pending.lng);
    await refreshSpots();
    setSelected(newSpot);
    setName("");
    setPending(null);
    setMenuOpen(false);
  };

  const deleteSpot = async (index) => {
    if (!window.confirm("Delete this spot?")) return;
    await api.deleteSpot(spots[index].id);
    await refreshSpots();
    setSelected(null);
  };

  const moveSpot = async (spot, event) => {
    const { lat, lng } = event.target.getLatLng();
    await api.moveSpot(spot.id, lat, lng);
    await refreshSpots();
  };

  const renameSpot = async (index) => {
    const spot = spots[index];
    const newName = window.prompt("Enter new name:", spot.name);
    if (newName === null) return;

    const trimmed = newName.trim();
    if (!trimmed || trimmed === spot.name) return;

    await api.renameSpot(spot.id, trimmed);
    await refreshSpots();
  };

  const deleteGalleryImage = async (spotIndex, photoId) => {
    if (!window.confirm("Delete this photo?")) return;
    await api.rejectPhoto(spots[spotIndex].id, photoId);
    await refreshSpots();
  };

  const reportGalleryImage = async (spotIndex, photoId) => {
    if (
      !window.confirm(
        "Report this photo as inappropriate? It will be sent to admin for review."
      )
    )
      return;
    await api.reportPhoto(spots[spotIndex].id, photoId);
    await refreshSpots();
  };

  const deletePendingImage = async (spotIndex, photoId) => {
    if (!window.confirm("Delete this pending photo?")) return;
    await api.rejectPhoto(spots[spotIndex].id, photoId);
    await refreshSpots();
  };

  const uploadToPending = async (index, file) => {
    if (!file) return;
    await api.uploadPhoto(spots[index].id, file);
    await refreshSpots();
  };

  const approveImage = async (spotIndex, photoId) => {
    await api.approvePhoto(spots[spotIndex].id, photoId);
    await refreshSpots();
  };

  const rejectImage = async (spotIndex, photoId) => {
    await api.rejectPhoto(spots[spotIndex].id, photoId);
    await refreshSpots();
  };

  const changeMain = async (index, file) => {
    if (!file) return;
    await api.changeMainImage(spots[index].id, file);
    await refreshSpots();
  };

  const sortedSpots = [...spots].sort((a, b) =>
    (a.name || "").localeCompare(b.name || "")
  );

  const pendingCount = spots.reduce(
    (total, spot) => total + spot.pending.length,
    0
  );

  return (
    <div className="app-container">
      <button className="mobile-menu-btn" onClick={() => setMenuOpen(true)}>
        ☰ Menu
      </button>

      {menuOpen && (
        <div className="mobile-backdrop" onClick={() => setMenuOpen(false)} />
      )}

      <div
        className={`sidebar app-sidebar ${menuOpen ? "open" : ""}`}
        style={styles.sidebar}
      >
        <button
          className="btn btn-danger w-100 mb-2 mobile-close-btn"
          onClick={() => setMenuOpen(false)}
        >
          Close Menu
        </button>

        {compassNeedsPermission && (
          <button
            className="btn btn-outline-light w-100 mb-2"
            onClick={enableCompass}
          >
            Enable Compass
          </button>
        )}

        {!admin && (
          <button
            className="btn btn-success w-100 mb-2"
            onClick={() => setShowAdminLogin(true)}
          >
            ADMIN ACCESS
          </button>
        )}

        {admin && (
          <button
            className="btn btn-secondary w-100 mb-2"
            onClick={async () => {
              await api.adminLogout();
              navigate("/");
            }}
          >
            Back to User Page
          </button>
        )}

        <h5 style={{ color: "white", fontWeight: "bold" }}>Locations</h5>

        <div
          style={{
            ...styles.item,
            background: "#1a73e8",
            color: "#ffffff",
            opacity: userLocation ? 1 : 0.5,
            cursor: userLocation ? "pointer" : "default",
          }}
          onClick={goToMyLocation}
        >
          <span
            style={{
              color: "#ffffff",
              fontSize: "18px",
              fontWeight: "700",
              display: "inline-block",
            }}
          >
            📍 My Location
          </span>
        </div>

        {sortedSpots.map((spot) => (
          <div
            key={spot.name}
            style={{
              ...styles.item,
              background:
                selected?.name === spot.name ? "#0d6efd" : "#6c757d",
              color: "#ffffff",
            }}
            onClick={() => focusSpot(spot)}
          >
            <span
              style={{
                color: "#ffffff",
                fontSize: "18px",
                fontWeight: "700",
                display: "inline-block",
              }}
            >
              {spot.name || "Unnamed Location"}
            </span>

            {admin && spot.pending.length > 0 && (
              <span style={styles.pendingBadge}>{spot.pending.length}</span>
            )}
          </div>
        ))}

        <hr />

        {admin && (
          <>
            <p style={{ fontSize: "13px", color: "#ccc" }}>
              Click the map to place a new spot. Drag an existing marker to move it.
            </p>

            <input
              className="form-control mb-2"
              placeholder="Spot name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />

            {pending && (
              <div className="alert alert-info p-2">
                Lat: {pending.lat.toFixed(5)} <br />
                Lng: {pending.lng.toFixed(5)}
              </div>
            )}

            <button className="btn btn-success w-100" onClick={saveSpot}>
              Save Spot
            </button>

            {pendingCount > 0 && (
              <div className="alert alert-warning mt-2 p-2 text-center">
                Pending Images: {pendingCount}
              </div>
            )}

            {spots
              .filter((spot) => spot.pending.length > 0)
              .map((spot) => (
                <button
                  key={spot.name}
                  className="btn btn-warning btn-sm w-100 mt-2"
                  onClick={() => focusSpot(spot)}
                >
                  Go to pending: {spot.name}
                </button>
              ))}
          </>
        )}
      </div>

      <div className="map-area">
        {!userLocation && (
          <div style={styles.locationHint}>
            {locationError
              ? `Location error: ${locationError}`
              : 'Don’t see your location? Refresh the page and click "Allow" when your browser asks for your location.'}
          </div>
        )}

        <MapContainer
          center={[32.9, -118.5]}
          zoom={11}
          zoomControl={false}
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
            maxZoom={19}
          />

          <FlyToSpot selected={selected} />

          <FlyToUserLocation trigger={flyToMyLocationTick} userLocation={userLocation} />

          <ClickToPlace
            enabled={admin}
            onPlace={(lat, lng) => setPending({ lat, lng })}
          />

          <Controls />

          {spots.map((spot, i) => {
            const active = selected?.name === spot.name;
            const hasPending = admin && spot.pending.length > 0;

            const allImages = [
              {
                src: spot.mainImage,
                pending: false,
                type: "main",
                id: null,
              },
              ...spot.gallery.map((img) => ({
                src: img.image,
                pending: false,
                type: "gallery",
                id: img.id,
              })),
              ...spot.pending.map((img) => ({
                src: img.image,
                pending: true,
                type: "pending",
                id: img.id,
              })),
            ];

            return (
              <Marker
                key={`${spot.name}-${i}`}
                ref={(ref) => {
                  if (ref) markerRefs.current[spot.name] = ref;
                }}
                position={spot.position}
                icon={makeIcon(spot.mainImage, active, hasPending)}
                draggable={admin}
                eventHandlers={{
                  click: () => focusSpot(spot),
                  dragend: (e) => moveSpot(spot, e),
                }}
              >
                <Popup>
                  <div style={{ width: "280px" }}>
                    <h5 className="text-center">{spot.name}</h5>

                    <div style={styles.galleryScroll}>
                      {allImages.map((img, index) => (
                        <div key={index} style={{ position: "relative" }}>
                          {!img.pending && (
                            <>
                              <img
                                src={img.src}
                                alt={`${spot.name} ${index}`}
                                style={styles.galleryImage}
                                onClick={() => {
                                  const viewable = allImages.filter(
                                    (im) => !im.pending
                                  );
                                  const viewIndex = viewable.findIndex(
                                    (im) => im === img
                                  );
                                  openViewer(
                                    viewable.map((im) => im.src),
                                    viewIndex
                                  );
                                }}
                              />

                              {admin && img.type === "gallery" && (
                                <button
                                  style={styles.deleteImageBtn}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    deleteGalleryImage(i, img.id);
                                  }}
                                >
                                  ✕
                                </button>
                              )}

                              {!admin && img.type === "gallery" && (
                                <button
                                  style={styles.reportImageBtn}
                                  title="Report inappropriate"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    reportGalleryImage(i, img.id);
                                  }}
                                >
                                  🚩
                                </button>
                              )}
                            </>
                          )}

                          {img.pending && (
                            <>
                              <div
                                style={styles.pendingBox}
                                onClick={() => {
                                  focusSpot(spot);
                                  openViewer([img.src], 0);
                                }}
                              >
                                <div>
                                  <div>Pending Image</div>
                                  <small>Click to view</small>
                                </div>
                              </div>

                              {admin && (
                                <button
                                  style={styles.deleteImageBtn}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    deletePendingImage(i, img.id);
                                  }}
                                >
                                  ✕
                                </button>
                              )}
                            </>
                          )}
                        </div>
                      ))}
                    </div>

                    <input
                      id={`g-${i}`}
                      type="file"
                      hidden
                      accept="image/*"
                      onChange={(e) => uploadToPending(i, e.target.files[0])}
                    />

                    <button
                      className="btn btn-primary btn-sm w-100 mt-2"
                      onClick={() => {
                        if (admin) {
                          document.getElementById(`g-${i}`).click();
                        } else {
                          setUploadIndex(i);
                          setShowWarning(true);
                        }
                      }}
                    >
                      Add More Photos
                    </button>

                    {admin && spot.pending.length > 0 && (
                      <div className="mt-3">
                        <h6>Pending Approval</h6>

                        {spot.pending.map((img, pendingIndex) => (
                          <div key={img.id} className="mb-2">
                            <img
                              src={img.image}
                              alt="Pending"
                              style={styles.pendingPreview}
                              onClick={() => {
                                openViewer(
                                  spot.pending.map((p) => p.image),
                                  pendingIndex
                                );
                              }}
                            />

                            <button
                              className="btn btn-success btn-sm w-100 mt-1"
                              onClick={() => approveImage(i, img.id)}
                            >
                              Approve
                            </button>

                            <button
                              className="btn btn-danger btn-sm w-100 mt-1"
                              onClick={() => rejectImage(i, img.id)}
                            >
                              Reject
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {admin && (
                      <>
                        <input
                          id={`m-${i}`}
                          type="file"
                          hidden
                          accept="image/*"
                          onChange={(e) => changeMain(i, e.target.files[0])}
                        />

                        <button
                          className="btn btn-warning btn-sm w-100 mt-2"
                          onClick={() =>
                            document.getElementById(`m-${i}`).click()
                          }
                        >
                          Change Main Photo
                        </button>

                        <button
                          className="btn btn-outline-secondary btn-sm w-100 mt-2"
                          onClick={() => renameSpot(i)}
                        >
                          Rename Spot
                        </button>

                        <button
                          className="btn btn-danger btn-sm w-100 mt-2"
                          onClick={() => deleteSpot(i)}
                        >
                          Delete Spot
                        </button>
                      </>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {admin && pending && <Marker position={[pending.lat, pending.lng]} />}

          {userLocation && (
            <>
              <Circle
                center={[userLocation.lat, userLocation.lng]}
                radius={userLocation.accuracy}
                pathOptions={{
                  color: "#1a73e8",
                  fillColor: "#1a73e8",
                  fillOpacity: 0.15,
                  weight: 1,
                }}
              />
              <Marker
                position={[userLocation.lat, userLocation.lng]}
                icon={makeUserLocationIcon(heading, userLocation.accuracy)}
                zIndexOffset={1000}
              >
                <Popup>You are here</Popup>
              </Marker>
            </>
          )}
        </MapContainer>
      </div>

      {viewer && (
        <div
          style={styles.viewer}
          onWheel={(e) => {
            e.preventDefault();
            const newZoom = zoom + e.deltaY * -0.001;
            setZoom(Math.min(Math.max(1, newZoom), 5));
          }}
          onMouseDown={() => setDragging(true)}
          onMouseUp={() => setDragging(false)}
          onMouseLeave={() => setDragging(false)}
          onMouseMove={(e) => {
            if (!dragging) return;
            setDrag((old) => ({
              x: old.x + e.movementX,
              y: old.y + e.movementY,
            }));
          }}
          onDoubleClick={() => {
            setZoom((old) => (old === 1 ? 2 : 1));
            setDrag({ x: 0, y: 0 });
          }}
          onTouchStart={(e) => {
            touchStartX.current = e.touches[0].clientX;
          }}
          onTouchEnd={(e) => {
            if (touchStartX.current === null) return;
            const deltaX = e.changedTouches[0].clientX - touchStartX.current;
            touchStartX.current = null;
            if (zoom > 1 || Math.abs(deltaX) < 50) return;
            goToViewerImage(deltaX > 0 ? -1 : 1);
          }}
        >

          <img
            src={viewer.images[viewer.index]}
            alt="Full view"
            draggable="false"
            style={{
              transform: `translate(${drag.x}px, ${drag.y}px) scale(${zoom})`,
              maxWidth: "90%",
              maxHeight: "90%",
              cursor: dragging ? "grabbing" : "grab",
              borderRadius: "10px",
              userSelect: "none",
            }}
          />

          {viewer.images.length > 1 && (
            <>
              <button
                style={styles.viewerNavLeft}
                onClick={(e) => {
                  e.stopPropagation();
                  goToViewerImage(-1);
                }}
              >
                ‹
              </button>

              <button
                style={styles.viewerNavRight}
                onClick={(e) => {
                  e.stopPropagation();
                  goToViewerImage(1);
                }}
              >
                ›
              </button>

              <div style={styles.viewerCounter}>
                {viewer.index + 1} / {viewer.images.length}
              </div>
            </>
          )}

          <div style={styles.viewerButtons}>
            <button
              className="btn btn-light btn-sm"
              onClick={() => setZoom((old) => Math.min(old + 0.25, 5))}
            >
              Zoom In
            </button>

            <button
              className="btn btn-light btn-sm"
              onClick={() => setZoom((old) => Math.max(old - 0.25, 1))}
            >
              Zoom Out
            </button>

            <button
              className="btn btn-warning btn-sm"
              onClick={() => {
                setZoom(1);
                setDrag({ x: 0, y: 0 });
              }}
            >
              Reset
            </button>
          </div>

          <button
            onClick={() => {
              setViewer(null);
              setZoom(1);
              setDrag({ x: 0, y: 0 });
            }}
            style={styles.closeViewer}
          >
            ✕
          </button>
        </div>
      )}

      {showAdminLogin && (
        <div style={styles.warningOverlay}>
          <div style={styles.warningBox}>
            <h5>Admin Login</h5>

            <input
              className="form-control mb-2"
              placeholder="Username"
              autoFocus
              value={loginUsername}
              onChange={(e) => setLoginUsername(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAdminLogin();
              }}
            />

            <input
              className="form-control mb-2"
              type="password"
              placeholder="Password"
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAdminLogin();
              }}
            />

            {loginError && (
              <div className="alert alert-danger p-2">{loginError}</div>
            )}

            <button
              className="btn btn-success w-100 mb-2"
              disabled={loggingIn}
              onClick={handleAdminLogin}
            >
              {loggingIn ? "Logging in…" : "Log In"}
            </button>

            <button
              className="btn btn-secondary w-100"
              onClick={() => {
                setShowAdminLogin(false);
                setLoginError("");
                setLoginUsername("");
                setLoginPassword("");
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {showWarning && (
        <div style={styles.warningOverlay}>
          <div style={styles.warningBox}>
            <h5>Upload Guidelines</h5>

            <p style={{ fontSize: "14px" }}>
              Please make sure your image is appropriate and no senstive informations.
              <br />
              <strong>All uploads are subject to approval.</strong>
            </p>

            <button
              className="btn btn-success w-100 mb-2"
              onClick={() => {
                setShowWarning(false);

                const input = document.getElementById(`g-${uploadIndex}`);
                if (input) input.click();
              }}
            >
              I Understand
            </button>

            <button
              className="btn btn-secondary w-100"
              onClick={() => {
                setShowWarning(false);
                setUploadIndex(null);
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <style>
        {`
          .app-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            overflow: hidden;
          }

          .map-area {
            flex: 1;
            height: 100vh;
            width: 100%;
            position: relative;
          }

          .mobile-menu-btn {
            display: block;
            position: fixed;
            top: 12px;
            left: 12px;
            z-index: 5000;
            background: #111;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 14px;
            font-weight: bold;
            box-shadow: 0 2px 8px rgba(0,0,0,0.35);
          }

          .mobile-close-btn {
            display: none;
          }

          .mobile-backdrop {
            display: none;
          }

          .leaflet-container {
            cursor: pointer !important;
          }

          .blink-marker {
            animation: blink 1.2s infinite;
          }

          @keyframes blink {
            0% {
              opacity: 1;
              transform: scale(1);
            }

            50% {
              opacity: 0.4;
              transform: scale(1.12);
            }

            100% {
              opacity: 1;
              transform: scale(1);
            }
          }

          @media (max-width: 768px) {
            .app-container {
              height: 100dvh;
              width: 100vw;
            }

            .map-area {
              height: 100dvh;
              width: 100vw;
              flex: 1;
            }

            .mobile-close-btn {
              display: block;
            }

            .mobile-backdrop {
              display: block;
              position: fixed;
              top: 0;
              left: 0;
              width: 100vw;
              height: 100dvh;
              background: rgba(0,0,0,0.45);
              z-index: 3999;
            }

            .app-sidebar {
              position: fixed !important;
              top: 0;
              left: 0;
              height: 100dvh !important;
              width: 82vw !important;
              max-width: 340px;
              z-index: 5001 !important;
              transform: translateX(-105%);
              transition: transform 0.25s ease;
              overflow-y: auto !important;
            }

            .app-sidebar.open {
              transform: translateX(0);
            }

            .leaflet-popup-content-wrapper {
              max-width: 92vw;
            }

            .leaflet-popup-content {
              margin: 10px;
              width: 260px !important;
            }
          }
        `}
      </style>
    </div>
  );
}

const styles = {
  sidebar: {
    width: "260px",
    background: "#111",
    color: "white",
    padding: "10px",
    overflowY: "auto",
    zIndex: 5001,
  },
  item: {
    padding: "10px",
    marginBottom: "5px",
    cursor: "pointer",
    borderRadius: "5px",
    position: "relative",
    color: "white",
    fontWeight: "bold",
    minHeight: "38px",
    display: "flex",
    alignItems: "center",
  },
  pendingBadge: {
    position: "absolute",
    right: "8px",
    top: "8px",
    background: "orange",
    color: "black",
    borderRadius: "50%",
    width: "22px",
    height: "22px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: "bold",
  },
  zoom: {
    position: "absolute",
    top: "10px",
    right: "10px",
    zIndex: 1000,
    display: "flex",
    flexDirection: "column",
    gap: "5px",
  },
  move: {
    position: "absolute",
    bottom: "20px",
    left: "10px",
    zIndex: 1000,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "5px",
  },
  btn: {
    width: "38px",
    height: "38px",
    fontSize: "20px",
    borderRadius: "6px",
  },
  galleryScroll: {
    display: "flex",
    overflowX: "auto",
    gap: "8px",
    paddingBottom: "8px",
  },
  galleryImage: {
    width: "90px",
    height: "90px",
    objectFit: "cover",
    borderRadius: "8px",
    cursor: "pointer",
    flexShrink: 0,
  },
  pendingBox: {
    width: "90px",
    height: "90px",
    background: "orange",
    color: "black",
    border: "2px solid #000",
    borderRadius: "8px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    textAlign: "center",
    fontSize: "12px",
    fontWeight: "bold",
    flexShrink: 0,
    cursor: "pointer",
  },
  pendingPreview: {
    width: "100%",
    borderRadius: "8px",
    marginBottom: "5px",
    cursor: "pointer",
  },
  deleteImageBtn: {
    position: "absolute",
    top: "2px",
    right: "2px",
    background: "red",
    color: "white",
    border: "none",
    borderRadius: "4px",
    fontSize: "10px",
    width: "20px",
    height: "20px",
    lineHeight: "18px",
    cursor: "pointer",
    zIndex: 10,
  },
  reportImageBtn: {
    position: "absolute",
    top: "2px",
    right: "2px",
    background: "rgba(0,0,0,0.6)",
    color: "white",
    border: "none",
    borderRadius: "4px",
    fontSize: "11px",
    width: "22px",
    height: "22px",
    lineHeight: "20px",
    cursor: "pointer",
    zIndex: 10,
  },
  viewer: {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100vw",
    height: "100vh",
    background: "rgba(0,0,0,0.9)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 9999,
    overflow: "hidden",
  },
  viewerHelp: {
    position: "absolute",
    top: "20px",
    left: "50%",
    transform: "translateX(-50%)",
    color: "white",
    background: "rgba(0,0,0,0.6)",
    padding: "8px 14px",
    borderRadius: "8px",
    fontSize: "14px",
  },
  viewerButtons: {
    position: "absolute",
    bottom: "25px",
    left: "50%",
    transform: "translateX(-50%)",
    display: "flex",
    gap: "8px",
  },
  viewerNavLeft: {
    position: "absolute",
    top: "50%",
    left: "12px",
    transform: "translateY(-50%)",
    background: "rgba(255,255,255,0.15)",
    color: "white",
    border: "none",
    borderRadius: "50%",
    width: "48px",
    height: "48px",
    fontSize: "28px",
    lineHeight: "1",
    cursor: "pointer",
    zIndex: 2,
  },
  viewerNavRight: {
    position: "absolute",
    top: "50%",
    right: "12px",
    transform: "translateY(-50%)",
    background: "rgba(255,255,255,0.15)",
    color: "white",
    border: "none",
    borderRadius: "50%",
    width: "48px",
    height: "48px",
    fontSize: "28px",
    lineHeight: "1",
    cursor: "pointer",
    zIndex: 2,
  },
  viewerCounter: {
    position: "absolute",
    top: "20px",
    left: "50%",
    transform: "translateX(-50%)",
    background: "rgba(0,0,0,0.6)",
    color: "white",
    padding: "4px 12px",
    borderRadius: "999px",
    fontSize: "13px",
  },
  closeViewer: {
    position: "absolute",
    top: 20,
    right: 20,
    fontSize: "20px",
    padding: "6px 12px",
    borderRadius: "6px",
    border: "none",
    cursor: "pointer",
  },
  warningOverlay: {
    position: "fixed",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    background: "rgba(0,0,0,0.7)",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    zIndex: 10000,
  },
  warningBox: {
    background: "white",
    padding: "20px",
    borderRadius: "10px",
    width: "320px",
    textAlign: "center",
  },
  locationHint: {
    position: "absolute",
    top: "10px",
    left: "50%",
    transform: "translateX(-50%)",
    zIndex: 1000,
    background: "rgba(17,17,17,0.85)",
    color: "white",
    fontSize: "13px",
    padding: "8px 14px",
    borderRadius: "8px",
    maxWidth: "90%",
    textAlign: "center",
    boxShadow: "0 2px 8px rgba(0,0,0,0.4)",
  },
};
