import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


export default function ProtectedRoute() {
  const { authenticated, loading } = useAuth();

  if (loading) {
    return <div className="page-center">Preparing your workspace...</div>;
  }

  return authenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

