import { useEffect, useState } from "react";

import { apiRequest } from "../api/client";
import DecisionBadge from "../components/DecisionBadge";
import { useAuth } from "../context/AuthContext";
import { formatDate, formatMoney, formatScore } from "../utils/formatters";


export default function ClaimStatusPage() {
  const { token } = useAuth();
  const [claims, setClaims] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let ignore = false;

    apiRequest("/claims/mine", { token })
      .then((data) => {
        if (!ignore) {
          setClaims(data.claims);
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
    return <div className="page-center">Loading claim history...</div>;
  }

  if (error) {
    return <div className="error-panel">{error}</div>;
  }

  return (
    <section className="panel">
      <p className="eyebrow">Claim ledger</p>
      <h2>Automated decisions and fraud signals</h2>
      <div className="stack-sm">
        {claims.length ? (
          claims.map((claim) => (
            <article className="claim-card" key={claim.id}>
              <div className="claim-card-head">
                <div>
                  <h3>{claim.reason}</h3>
                  <p className="muted">{formatDate(claim.incident_at)}</p>
                </div>
                <DecisionBadge decision={claim.decision} />
              </div>

              <p>{claim.description}</p>

              <div className="claim-metrics">
                <span>Payout {formatMoney(claim.payout_amount)}</span>
                <span>Fraud {formatScore(claim.fraud_score)}</span>
                <span>Risk {formatScore(claim.risk_score)}</span>
                <span>Zone {claim.zone_id}</span>
              </div>

              <div className="claim-subgrid">
                <div>
                  <p className="muted">Decision reasoning</p>
                  <strong>{claim.decision_reason}</strong>
                </div>
                <div>
                  <p className="muted">Weather validation confidence</p>
                  <strong>{formatScore(claim.ai_validation.weather.confidence)}</strong>
                </div>
                <div>
                  <p className="muted">Group fraud cluster score</p>
                  <strong>{formatScore(claim.group_fraud.cluster_score)}</strong>
                </div>
                <div>
                  <p className="muted">GPS spoofing detected</p>
                  <strong>
                    {claim.fraud_signals.signals.gps_spoofing_detected ? "Yes" : "No"}
                  </strong>
                </div>
              </div>
            </article>
          ))
        ) : (
          <p className="muted">No claims submitted yet.</p>
        )}
      </div>
    </section>
  );
}
