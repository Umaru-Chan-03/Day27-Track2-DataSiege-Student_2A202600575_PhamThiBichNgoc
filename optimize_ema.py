import json
import statistics

with open("analysis_private.json") as f:
    events = json.load(f)

baseline = {
  "row_count_min": 435.4732,
  "row_count_max": 561.2948,
  "null_rate_max": 0.0109,
  "mean_amount_min": 72.7645,
  "mean_amount_max": 90.6053,
  "staleness_min_max": 8.418,
  "freshness_delay_max_min": 11.1141,
  "lineage_duration_ms_max": 5134.9804,
  "feature_mean_shift_sigma_max": 0.4095,
  "embedding_centroid_shift_max": 0.0435,
  "corpus_avg_doc_age_days_max": 49.7955
}

def evaluate(z_thresh, window):
    state = {}
    
    def check_anomaly(key, val, baseline_max=None, baseline_min=None):
        hist = state.setdefault(key, [])
        alert = False
        
        if baseline_max is not None and val > baseline_max:
            alert = True
        if baseline_min is not None and val < baseline_min:
            alert = True
            
        if len(hist) >= 2:
            mean = statistics.mean(hist)
            std = statistics.stdev(hist) if len(hist) > 1 else 0
            if std == 0: std = 0.001
            z = (val - mean) / std
            if abs(z) > z_thresh:
                alert = True
                
        if not alert:
            hist.append(val)
            if len(hist) > window:
                hist.pop(0)
                
        return alert

    tpr_c = 0
    fpr_c = 0
    total_f = 0
    total_c = 0
    
    for ev in events:
        gt = ev["gt"]
        actual = ev["actual"]
        etype = ev["etype"]
        alert = False
        
        if etype == "data_batch":
            a1 = check_anomaly("data_row_count", gt["row_count"], baseline["row_count_max"], baseline["row_count_min"])
            a2 = check_anomaly("data_null_rate", gt["null_rate_customer_id"], baseline["null_rate_max"])
            a3 = check_anomaly("data_mean_amount", gt["mean_amount"], baseline["mean_amount_max"], baseline["mean_amount_min"])
            a4 = check_anomaly("data_staleness", gt["staleness_min"], baseline["staleness_min_max"])
            if a1 or a2 or a3 or a4: alert = True
            
        elif etype == "embedding_batch":
            corpus = ev.get("payload", {}).get("corpus", "default")
            a1 = check_anomaly(f"embed_shift_{corpus}", gt["embedding_centroid_shift"], baseline["embedding_centroid_shift_max"] * 0.9)
            a2 = check_anomaly(f"doc_age_{corpus}", gt["corpus_avg_doc_age_days"], baseline["corpus_avg_doc_age_days_max"] * 0.9)
            if a1 or a2: alert = True
            
        elif etype == "lineage_run":
            a1 = check_anomaly("lineage_duration", gt["lineage_duration_ms"], baseline["lineage_duration_ms_max"])
            if a1: alert = True
            
        elif etype == "feature_materialization":
            shift = abs(gt["feature_serve_mean"] - gt["train_mean"]) / gt["train_std"]
            a1 = check_anomaly("feature_shift", shift, max(baseline["feature_mean_shift_sigma_max"], 0.5))
            if a1: alert = True
            
        elif etype == "contract_checkpoint":
            a1 = check_anomaly("contract_freshness", gt["freshness_delay_min"], baseline["freshness_delay_max_min"])
            if a1: alert = True
            
        if actual:
            total_f += 1
            if alert: tpr_c += 1
        else:
            total_c += 1
            if alert: fpr_c += 1
            
    tpr = tpr_c / total_f if total_f else 0
    fpr = fpr_c / total_c if total_c else 0
    return 100 * (0.5 * tpr - 0.3 * fpr)

best_s = -999
best_p = None
def linspace(a,b,n):
    return [a + (b-a)/(n-1)*i for i in range(n)]

for w in [5, 10, 15, 20]:
    for z in linspace(2.0, 5.0, 10):
        s = evaluate(z, w)
        if s > best_s:
            best_s = s
            best_p = (z, w)

print(best_s, best_p)
