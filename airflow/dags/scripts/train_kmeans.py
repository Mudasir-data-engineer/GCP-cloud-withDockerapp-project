import os
import pandas as pd
import argparse

# These should exactly match the incoming data column names
NUM_FEATS = ['temperature', 'humidity', 'activity_level', 'heart_rate', 'rumination_minutes', 'milk_yield']
BIN_FEATS = ['is_ruminating']

def main(data_path, model_out, clusters_out):
    print(f"📂 Checking if input file exists: {data_path}")
    # This check works for local files; GCS paths should be accessible via gsutil or GCS client
    if data_path.startswith("gs://"):
        print("⚠️ Data is on Google Cloud Storage — ensure gsutil or GCS Python client can access this.")
    else:
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Input data file not found at {data_path}")
        else:
            print("✅ Input file exists locally.")

    print("📢 Loading data from:", data_path)
    df = pd.read_json(data_path, lines=True)  # Assuming newline-delimited JSON format

    print("✅ DataFrame loaded. First few rows:")
    print(df.head())

    print("🧩 Columns in DataFrame:", df.columns.tolist())
    print("🎯 Expected columns:", NUM_FEATS + BIN_FEATS)

    # Check if all expected columns are present
    missing_cols = [col for col in (NUM_FEATS + BIN_FEATS) if col not in df.columns]
    if missing_cols:
        print("❌ Missing columns:", missing_cols)
        raise ValueError(f"Missing expected columns: {missing_cols}")
    else:
        print("✅ All expected columns are present.")

    # Extract the feature matrix as numpy array
    X = df[NUM_FEATS + BIN_FEATS].to_numpy()

    # Placeholder: Add your model training and saving logic here
    print("🔧 Training model with the loaded data...")
    # e.g., train your k-means model here with X

    # Placeholder: Save model and clusters output
    print(f"💾 Saving model to {model_out}")
    print(f"💾 Saving clusters info to {clusters_out}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to input JSON data file")
    parser.add_argument("--model-out", required=True, help="Path to save the trained model")
    parser.add_argument("--clusters-out", required=True, help="Path to save the clusters info")
    args = parser.parse_args()

    main(args.data, args.model_out, args.clusters_out)
