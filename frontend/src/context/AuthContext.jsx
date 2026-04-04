import { createContext, useContext, useEffect, useState } from "react";

import { apiRequest } from "../api/client";


const AuthContext = createContext(null);


export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("routerelief_token"));
  const [user, setUser] = useState(() => {
    const rawUser = localStorage.getItem("routerelief_user");
    return rawUser ? JSON.parse(rawUser) : null;
  });
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return undefined;
    }

    let ignore = false;
    apiRequest("/auth/me", { token })
      .then((data) => {
        if (!ignore) {
          setUser(data.user);
          localStorage.setItem("routerelief_user", JSON.stringify(data.user));
        }
      })
      .catch(() => {
        if (!ignore) {
          setToken(null);
          setUser(null);
          localStorage.removeItem("routerelief_token");
          localStorage.removeItem("routerelief_user");
        }
      })
      .finally(() => {
        if (!ignore) {
          setLoading(false);
        }
      });

    return () => {
      ignore = true;
    };
  }, [token]);

  const saveAuthState = (payload) => {
    setToken(payload.token);
    setUser(payload.user);
    localStorage.setItem("routerelief_token", payload.token);
    localStorage.setItem("routerelief_user", JSON.stringify(payload.user));
  };

  const login = async (credentials) => {
    const response = await apiRequest("/auth/login", {
      method: "POST",
      body: credentials,
    });
    saveAuthState(response);
    return response;
  };

  const register = async (payload) => {
    const response = await apiRequest("/auth/register", {
      method: "POST",
      body: payload,
    });
    saveAuthState(response);
    return response;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("routerelief_token");
    localStorage.removeItem("routerelief_user");
  };

  const refreshUser = async () => {
    if (!token) {
      return null;
    }

    const response = await apiRequest("/auth/me", { token });
    setUser(response.user);
    localStorage.setItem("routerelief_user", JSON.stringify(response.user));
    return response.user;
  };

  const value = {
    token,
    user,
    loading,
    authenticated: Boolean(token),
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}


export function useAuth() {
  return useContext(AuthContext);
}
