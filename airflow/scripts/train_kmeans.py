import argparse, io, json, joblib, numpy as np, pandas as pd
from google.cloud import storage
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

NUM_FEATS = ["temperature","humidity","activity_level",
             "heart_rate","rumination_minutes","milk_yield"]
BIN_FEATS = ["is_ruminating"]

def read_json(uri):
    client = storage.Client()
    bucket, blob = uri.replace("gs://","").split("/",1)
    data = client.bucket(bucket).blob(blob).download_as_text()
    return pd.read_json(io.StringIO(data), lines=True)

def write_json(df, uri):
    client = storage.Client()
    bucket, blob = uri.replace("gs://","").split("/",1)
    client.bucket(bucket).blob(blob).upload_from_string(
        df.to_json(orient="records", lines=True))

def main(data_uri, model_uri, out_uri):
    df = read_json(data_uri)

    X = df[NUM_FEATS + BIN_FEATS].to_numpy()

    # choose best k (2-10) by silhouette
    best_k, best_score = 2, -1
    for k in range(2,11):
        kms = KMeans(n_clusters=k, n_init="auto", random_state=42).fit(X)
        score = silhouette_score(X, kms.labels_)
        if score > best_score:
            best_k, best_score = k, score
            best_model = kms

    # assign clusters
    df["cluster_id"] = best_model.labels_
    df["silhouette_score"] = best_score
    write_json(df[["cow_id","hour_ts","cluster_id","silhouette_score"]], out_uri)

    # save model
    local = "/tmp/kmeans.joblib"
    joblib.dump(best_model, local)
    bucket, blob = model_uri.replace("gs://","").split("/",1)
    storage.Client().bucket(bucket).blob(blob).upload_from_filename(local)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--model-out", required=True)
    p.add_argument("--clusters-out", required=True)
    a = p.parse_args()
    main(a.data, a.model_out, a.clusters_out)
