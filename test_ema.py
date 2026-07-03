import json
import statistics

with open("analysis_private.json") as f:
    events = json.load(f)

# we will simulate state
state = {}
window = 10

def check_anomaly(key, val, baseline_max=None, baseline_min=None):
    hist = state.setdefault(key, [])
    alert = False
    
    if baseline_max is not None and val > baseline_max:
        alert = True
    if baseline_min is not None and val < baseline_min:
        alert = True
        
    if len(hist) >= 3:
        mean = statistics.mean(hist)
        std = statistics.stdev(hist) if len(hist) > 1 else 0
        if std == 0: std = 0.001
        z = (val - mean) / std
        
        # Determine threshold based on metric
        # Let's say Z > 3 is anomaly
        if abs(z) > 4.0: 
            alert = True
            
    if not alert:
        hist.append(val)
        if len(hist) > window:
            hist.pop(0)
            
    return alert, hist

tpr_count = 0
fpr_count = 0
fn_count = 0
total_faulty = 0
total_clean = 0

for ev in events:
    gt = ev["gt"]
    actual = ev["actual"]
    etype = ev["etype"]
    fault_key = ev["fault_key"]
    
    alert = False
    
    if etype == "data_batch":
        a1, _ = check_anomaly("data_row_count", gt["row_count"])
        a2, _ = check_anomaly("data_null_rate", gt["null_rate_customer_id"])
        a3, _ = check_anomaly("data_mean_amount", gt["mean_amount"])
        a4, _ = check_anomaly("data_staleness", gt["staleness_min"])
        if a1 or a2 or a3 or a4: alert = True
        
    elif etype == "embedding_batch":
        corpus = ev.get("payload", {}).get("corpus", "default")
        a1, _ = check_anomaly(f"embed_shift_{corpus}", gt["embedding_centroid_shift"])
        a2, _ = check_anomaly(f"doc_age_{corpus}", gt["corpus_avg_doc_age_days"])
        if a1 or a2: alert = True
        
    elif etype == "lineage_run":
        a1, _ = check_anomaly("lineage_duration", gt["lineage_duration_ms"])
        a2 = False
        # wait, we didn't dump actual_upstream to analysis_private.json, let's skip lineage for now in this test
        if a1: alert = True
        
    elif etype == "feature_materialization":
        shift = abs(gt["feature_serve_mean"] - gt["train_mean"]) / gt["train_std"]
        a1, _ = check_anomaly("feature_shift", shift)
        if a1: alert = True
        
    elif etype == "contract_checkpoint":
        a1, _ = check_anomaly("contract_freshness", gt["freshness_delay_min"])
        if a1: alert = True

    if actual:
        total_faulty += 1
        if alert: tpr_count += 1
        else: fn_count += 1
    else:
        total_clean += 1
        if alert: fpr_count += 1

print(f"TPR: {tpr_count}/{total_faulty} ({(tpr_count/total_faulty if total_faulty else 0):.2f})")
print(f"FPR: {fpr_count}/{total_clean} ({(fpr_count/total_clean if total_clean else 0):.2f})")
