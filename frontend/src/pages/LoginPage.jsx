import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await login(form);
      navigate("/dashboard");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-card">
        <p className="eyebrow">AI-enabled parametric insurance</p>
        <h1>Log in to protect your delivery income.</h1>
        <p className="muted">
          Track policy pricing, file disruption claims, and review AI fraud signals in one place.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            Email
            <input
              required
              type="email"
              value={form.email}
              onChange={(event) => setForm({ ...form, email: event.target.value })}
            />
          </label>

          <label>
            Password
            <input
              required
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button className="button" disabled={submitting} type="submit">
            {submitting ? "Signing in..." : "Log in"}
          </button>
        </form>

        <p className="muted">
          Need an account? <Link to="/register">Create one here</Link>.
        </p>
      </section>
    </div>
  );
}
