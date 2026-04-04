import { useEffect, useState } from "react";

import { apiRequest } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { formatDate, formatMoney, formatScore } from "../utils/formatters";


export default function BuyPolicyPage() {
  const { token } = useAuth();
  const [quote, setQuote] = useState(null);
  const [currentPolicy, setCurrentPolicy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let ignore = false;

    Promise.all([
      apiRequest("/policies/quote", { token }),
      apiRequest("/policies/current", { token }).catch(() => ({ policy: null })),
    ])
      .then(([quoteResponse, policyResponse]) => {
        if (!ignore) {
          setQuote(quoteResponse.quote);
          setCurrentPolicy(policyResponse.policy);
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

  const buyPolicy = async () => {
    setBuying(true);
    setMessage("");
    setError("");

    try {
      const response = await apiRequest("/policies/buy", {
        method: "POST",
        token,
      });
      setCurrentPolicy(response.policy);
      setMessage(response.created ? "Policy activated successfully." : "Existing policy is already active.");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBuying(false);
    }
  };

  if (loading) {
    return <div className="page-center">Calculating premium...</div>;
  }

  return (
    <div className="stack-lg">
      <section className="panel">
        <p className="eyebrow">Pricing engine</p>
        <h2>Weekly parametric coverage quote</h2>
        {quote ? (
          <div className="two-column compact">
            <div className="quote-card">
              <p className="muted">Weekly premium</p>
              <h3>{formatMoney(quote.weekly_premium)}</h3>
              <p className="muted">Coverage amount {formatMoney(quote.coverage_amount)}</p>
              <button className="button" disabled={buying} onClick={buyPolicy} type="button">
                {buying ? "Activating..." : "Buy policy"}
              </button>
            </div>

            <div className="stack-sm">
              <div className="list-row">
                <span>Composite risk</span>
                <strong>{formatScore(quote.risk_score)}</strong>
              </div>
              <div className="list-row">
                <span>Weather risk</span>
                <strong>{formatScore(quote.weather_risk)}</strong>
              </div>
              <div className="list-row">
                <span>Historical disruption risk</span>
                <strong>{formatScore(quote.historical_risk)}</strong>
              </div>
              <div className="list-row">
                <span>Location risk</span>
                <strong>{formatScore(quote.zone_risk)}</strong>
              </div>
              <div className="list-row">
                <span>Base premium</span>
                <strong>{formatMoney(quote.pricing_breakdown.base_premium)}</strong>
              </div>
            </div>
          </div>
        ) : (
          <p className="muted">Quote unavailable.</p>
        )}

        {message ? <p className="success-text">{message}</p> : null}
        {error ? <p className="error-text">{error}</p> : null}
      </section>

      <section className="panel">
        <p className="eyebrow">Current subscription</p>
        <h2>Auto-renewal status</h2>
        {currentPolicy ? (
          <div className="stack-sm">
            <div className="list-row">
              <span>Status</span>
              <strong>{currentPolicy.status}</strong>
            </div>
            <div className="list-row">
              <span>Renews through</span>
              <strong>{formatDate(currentPolicy.current_term_end)}</strong>
            </div>
            <div className="list-row">
              <span>Renewal count</span>
              <strong>{currentPolicy.renewal_count}</strong>
            </div>
            <div className="list-row">
              <span>Active alerts</span>
              <strong>
                {currentPolicy.pricing_breakdown.zone_snapshot.active_alerts?.join(", ") || "Stable"}
              </strong>
            </div>
          </div>
        ) : (
          <p className="muted">No active policy on file yet.</p>
        )}
      </section>
    </div>
  );
}
