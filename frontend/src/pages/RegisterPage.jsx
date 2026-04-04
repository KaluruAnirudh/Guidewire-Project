import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";


const initialForm = {
  name: "",
  email: "",
  password: "",
  work_type: "delivery",
  weekly_earnings_estimate: 4500,
  location: {
    lat: "",
    lon: "",
  },
};


export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setForm((previous) => ({
          ...previous,
          location: {
            lat: coords.latitude.toFixed(4),
            lon: coords.longitude.toFixed(4),
          },
        }));
      },
      () => setError("We could not fetch your location. You can still type it manually."),
    );
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await register({
        ...form,
        weekly_earnings_estimate: Number(form.weekly_earnings_estimate),
      });
      navigate("/dashboard");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-card wide">
        <p className="eyebrow">Gig worker onboarding</p>
        <h1>Create your income protection profile.</h1>
        <p className="muted">
          We use your work type, location, and earnings estimate to price a weekly policy and
          monitor disruption risk.
        </p>

        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Full name
            <input
              required
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </label>

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

          <label>
            Work type
            <select
              value={form.work_type}
              onChange={(event) => setForm({ ...form, work_type: event.target.value })}
            >
              <option value="delivery">Delivery</option>
              <option value="driver">Driver</option>
              <option value="courier">Courier</option>
            </select>
          </label>

          <label>
            Weekly earnings estimate
            <input
              min="1"
              required
              type="number"
              value={form.weekly_earnings_estimate}
              onChange={(event) =>
                setForm({ ...form, weekly_earnings_estimate: event.target.value })
              }
            />
          </label>

          <div className="inline-action">
            <button className="button secondary" onClick={useCurrentLocation} type="button">
              Use current location
            </button>
          </div>

          <label>
            Latitude
            <input
              required
              value={form.location.lat}
              onChange={(event) =>
                setForm({
                  ...form,
                  location: { ...form.location, lat: event.target.value },
                })
              }
            />
          </label>

          <label>
            Longitude
            <input
              required
              value={form.location.lon}
              onChange={(event) =>
                setForm({
                  ...form,
                  location: { ...form.location, lon: event.target.value },
                })
              }
            />
          </label>

          {error ? <p className="error-text full-span">{error}</p> : null}

          <button className="button full-span" disabled={submitting} type="submit">
            {submitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="muted">
          Already registered? <Link to="/login">Log in here</Link>.
        </p>
      </section>
    </div>
  );
}
