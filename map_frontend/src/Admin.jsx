import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import App from "./App.jsx";
import { adminStatus } from "./api.js";

export default function Admin() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    adminStatus()
      .then((res) => {
        if (res.isAdmin) {
          setIsAdmin(true);
        } else {
          navigate("/");
        }
      })
      .catch(() => navigate("/"))
      .finally(() => setChecking(false));
  }, [navigate]);

  if (checking || !isAdmin) return null;

  return <App adminMode={true} />;
}
