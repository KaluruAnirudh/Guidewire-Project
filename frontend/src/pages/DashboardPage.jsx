import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "../api/client";
import DecisionBadge from "../components/DecisionBadge";
import StatCard from "../components/StatCard";
import { useAuth } from "../context/AuthContext";
import { formatDate, formatMoney, formatScore } from "../utils/formatters";


export default function DashboardPage() {
  const { token } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    apiRequest("/dashboard/summary", { token })
      .then((data) => {
        if (!ignore) {
          setSummary(data);
        }
      })
      .catch((requestError) => {
        if (!ignore) {
          setError(requestError.message);
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

  if (loading) {
    return <div className="page-center">Loading portfolio intelligence...</div>;
  }

  if (error) {
    return <div className="error-panel">{error}</div>;
  }

  const platform = summary?.platform_metrics;
  const mine = summary?.my_metrics;

  return (
    <div className="stack-lg">
      <section className="panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">Operations snapshot</p>
            <h2>Platform metrics and active policy state</h2>
          </div>
          <div className="section-actions">
            <Link className="button secondary" to="/policy">
              Reprice policy
            </Link>
            <Link className="button" to="/claims/new">
              Submit disruption claim
            </Link>
          </div>
        </div>

        <div className="stats-grid">
          <StatCard accent="warm" label="Total claims" value={platform?.total_claims || 0} />
          <StatCard accent="cool" label="Approved claims" value={platform?.approved_claims || 0} />
          <StatCard accent="alert" label="Flagged claims" value={platform?.flagged_claims || 0} />
          <StatCard label="Model rows" value={platform?.fraud_model_metrics?.rows || 0} />
        </div>
      </section>

      <section className="two-column">
        <article className="panel">
          <p className="eyebrow">Current cover</p>
          <h3>Weekly subscription status</h3>
          {mine?.active_policy ? (
            <div className="stack-sm">
              <p>
                Premium: <strong>{formatMoney(mine.active_policy.weekly_premium)}</strong>
              </p>
              <p>
                Coverage: <strong>{formatMoney(mine.active_policy.coverage_amount)}</strong>
              </p>
              <p>Renews until {formatDate(mine.active_policy.current_term_end)}</p>
              <p>Zone risk score {formatScore(mine.active_policy.risk_score)}</p>
            </div>
          ) : (
            <div className="stack-sm">
              <p className="muted">No active policy yet.</p>
              <Link className="button" to="/policy">
                Buy your first policy
              </Link>
            </div>
          )}
        </article>

        <article className="panel">
          <p className="eyebrow">Fraud alerts</p>
          <h3>Latest high-risk claims</h3>
          <div className="stack-sm">
            {platform?.fraud_alerts?.length ? (
              platform.fraud_alerts.map((alert) => (
                <div className="list-row" key={alert.claim_id}>
                  <div>
                    <strong>{alert.reason}</strong>
                    <p className="muted">Claim {alert.claim_id.slice(-6)}</p>
                  </div>
                  <div className="align-right">
                    <DecisionBadge decision={alert.decision} />
                    <p className="muted">Fraud {formatScore(alert.fraud_score)}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">No elevated fraud alerts yet.</p>
            )}
          </div>
        </article>
      </section>

      <section className="two-column">
        <article className="panel">
          <p className="eyebrow">Recent claims</p>
          <h3>Your latest decisions</h3>
          <div className="stack-sm">
            {mine?.recent_claims?.length ? (
              mine.recent_claims.map((claim) => (
                <div className="claim-row" key={claim.id}>
                  <div>
                    <strong>{claim.reason}</strong>
                    <p className="muted">{formatDate(claim.incident_at)}</p>
                  </div>
                  <div className="align-right">
                    <DecisionBadge decision={claim.decision} />
                    <p className="muted">{formatMoney(claim.payout_amount)}</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">No claims filed yet.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <p className="eyebrow">Micro-zones</p>
          <h3>Highest risk regions</h3>
          <div className="stack-sm">
            {platform?.high_risk_zones?.map((zone) => (
              <div className="zone-row" key={zone.zone_id}>
                <div>
                  <strong>{zone.label}</strong>
                  <p className="muted">
                    Zone {zone.zone_id} | Weather {formatScore(zone.weather_risk)}
                  </p>
                </div>
                <div className="align-right">
                  <strong>{formatScore(zone.overall_risk)}</strong>
                  <p className="muted">{zone.active_alerts?.join(", ") || "Stable"}</p>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

