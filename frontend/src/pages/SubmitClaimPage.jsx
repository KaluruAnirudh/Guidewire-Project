import { useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "../api/client";
import DecisionBadge from "../components/DecisionBadge";
import { useAuth } from "../context/AuthContext";
import { formatMoney, formatScore } from "../utils/formatters";


function currentLocalDateTime() {
  const date = new Date();
  const timezoneOffset = date.getTimezoneOffset() * 60000;
  return new Date(date - timezoneOffset).toISOString().slice(0, 16);
}


export default function SubmitClaimPage() {
  const { token, user } = useAuth();
  const [form, setForm] = useState({
    incident_at: currentLocalDateTime(),
    reason: "rain",
    description: "",
    lat: user?.location?.lat || "",
    lon: user?.location?.lon || "",
  });
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setResult(null);

    const payload = new FormData();
    payload.append("incident_at", form.incident_at);
    payload.append("reason", form.reason);
    payload.append("description", form.description);
    payload.append("lat", form.lat);
    payload.append("lon", form.lon);
    files.forEach((file) => payload.append("proofs", file));

    try {
      const response = await apiRequest("/claims/submit", {
        method: "POST",
        token,
        body: payload,
      });
      setResult(response.claim);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="stack-lg">
      <section className="panel">
        <p className="eyebrow">Disruption intake</p>
        <h2>Submit a parametric claim</h2>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Incident time
            <input
              required
              type="datetime-local"
              value={form.incident_at}
              onChange={(event) => setForm({ ...form, incident_at: event.target.value })}
            />
          </label>

          <label>
            Reason
            <select
              value={form.reason}
              onChange={(event) => setForm({ ...form, reason: event.target.value })}
            >
              <option value="rain">Rain</option>
              <option value="flood">Flood</option>
              <option value="pollution">Pollution</option>
              <option value="disaster">Disaster</option>
            </select>
          </label>

          <label>
            Latitude
            <input
              required
              value={form.lat}
              onChange={(event) => setForm({ ...form, lat: event.target.value })}
            />
          </label>

          <label>
            Longitude
            <input
              required
              value={form.lon}
              onChange={(event) => setForm({ ...form, lon: event.target.value })}
            />
          </label>

          <label className="full-span">
            Description
            <textarea
              required
              rows="5"
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
          </label>

          <label className="full-span">
            Optional image or video proof
            <input
              multiple
              type="file"
              accept="image/*,video/*"
              onChange={(event) => setFiles(Array.from(event.target.files || []))}
            />
          </label>

          {error ? <p className="error-text full-span">{error}</p> : null}

          <button className="button full-span" disabled={submitting} type="submit">
            {submitting ? "Running AI validation..." : "Submit claim"}
          </button>
        </form>
      </section>

      {result ? (
        <section className="panel">
          <p className="eyebrow">Decision engine output</p>
          <h2>Claim processed</h2>
          <div className="stack-sm">
            <div className="list-row">
              <span>Status</span>
              <DecisionBadge decision={result.decision} />
            </div>
            <div className="list-row">
              <span>Payout</span>
              <strong>{formatMoney(result.payout_amount)}</strong>
            </div>
            <div className="list-row">
              <span>Fraud score</span>
              <strong>{formatScore(result.fraud_score)}</strong>
            </div>
            <p className="muted">{result.decision_reason}</p>
            <Link className="button secondary" to="/claims">
              View all claims
            </Link>
          </div>
        </section>
      ) : null}
    </div>
  );
}

