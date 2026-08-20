import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
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

function FlyToSpot({ selected }) {
  const map = useMap();

  useEffect(() => {
    if (selected) {
      map.flyTo(selected.position, 15);
    }
  }, [selected, map]);

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

  const admin = adminMode;

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

  const deleteGalleryImage = async (spotIndex, photoId) => {
    if (!window.confirm("Delete this photo?")) return;
    await api.rejectPhoto(spots[spotIndex].id, photoId);
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
                                  setViewer(img.src);
                                  setZoom(1);
                                  setDrag({ x: 0, y: 0 });
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
                            </>
                          )}

                          {img.pending && (
                            <>
                              <div
                                style={styles.pendingBox}
                                onClick={() => {
                                  focusSpot(spot);
                                  setViewer(img.src);
                                  setZoom(1);
                                  setDrag({ x: 0, y: 0 });
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

                        {spot.pending.map((img) => (
                          <div key={img.id} className="mb-2">
                            <img
                              src={img.image}
                              alt="Pending"
                              style={styles.pendingPreview}
                              onClick={() => {
                                setViewer(img.image);
                                setZoom(1);
                                setDrag({ x: 0, y: 0 });
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
        >

          <img
            src={viewer}
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
};
