from pathlib import Path

from pricing_model import train_and_save_model


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    dataset_path = base_dir / "sample_pricing_features.csv"
    artifact_path = base_dir / "artifacts" / "pricing_model.joblib"
    artifact = train_and_save_model(str(dataset_path), str(artifact_path))
    print(f"Pricing model trained. Metrics: {artifact['metrics']}")

