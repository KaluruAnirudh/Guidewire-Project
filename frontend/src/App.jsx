import { Navigate, Route, Routes } from "react-router-dom";

import AppShell from "./components/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import BuyPolicyPage from "./pages/BuyPolicyPage";
import ClaimStatusPage from "./pages/ClaimStatusPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SubmitClaimPage from "./pages/SubmitClaimPage";

function HomeRedirect() {
  const { authenticated, loading } = useAuth();

  if (loading) {
    return <div className="page-center">Loading session...</div>;
  }

  return <Navigate to={authenticated ? "/dashboard" : "/login"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/policy" element={<BuyPolicyPage />} />
          <Route path="/claims/new" element={<SubmitClaimPage />} />
          <Route path="/claims" element={<ClaimStatusPage />} />
        </Route>
      </Route>
    </Routes>
  );
}

