import argparse, io, json, joblib
import pandas as pd
from google.cloud import storage
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

NUM_FEATS = ["temperature","humidity","activity_level",
             "heart_rate","rumination_minutes","milk_yield"]
BIN_FEATS = ["is_ruminating"]

def download_json(uri):
    """load NDJSON from GCS to pandas DataFrame"""
    client = storage.Client()
    bucket, blob_name = uri.replace("gs://","").split("/",1)
    data = client.bucket(bucket).blob(blob_name).download_as_text()
    return pd.read_json(io.StringIO(data), lines=True)

def upload_json(df, uri):
    client = storage.Client()
    bucket, blob_name = uri.replace("gs://","").split("/",1)
    client.bucket(bucket).blob(blob_name).upload_from_string(
        df.to_json(orient="records", lines=True)
    )

def main(input_uri, output_uri, scaler_uri):
    df = download_json(input_uri)

    # numeric scaler pipeline
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("sc", StandardScaler())
    ])

    ct = ColumnTransformer(
        [("num", pipe, NUM_FEATS)],
        remainder="passthrough"
    )

    scaled = ct.fit_transform(df)
    cols_out = NUM_FEATS + BIN_FEATS + ["cow_id","hour_ts"]
    out_df = pd.DataFrame(scaled, columns=cols_out)

    upload_json(out_df, output_uri)

    # save the fitted transformer
    bucket, blob_name = scaler_uri.replace("gs://","").split("/",1)
    joblib_file = "/tmp/scaler.joblib"
    joblib.dump(ct, joblib_file)
    storage.Client().bucket(bucket).blob(blob_name).upload_from_filename(joblib_file)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--scaler", required=True)
    a = p.parse_args()
    main(a.input, a.output, a.scaler)
