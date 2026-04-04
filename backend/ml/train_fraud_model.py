from pathlib import Path

from fraud_model import train_and_save_model


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    dataset_path = base_dir / "sample_claims.csv"
    artifact_path = base_dir / "artifacts" / "fraud_detector.joblib"
    artifact = train_and_save_model(str(dataset_path), str(artifact_path))
    print(f"Fraud model trained. Metrics: {artifact['metrics']}")

