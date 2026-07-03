import json

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

def evaluate(m_row, m_null, m_mean, m_stale, m_fresh, m_lineage, m_feat, m_embed, m_age):
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
            if gt["row_count"] < baseline["row_count_min"] * (2 - m_row) or gt["row_count"] > baseline["row_count_max"] * m_row:
                alert = True
            if gt["null_rate_customer_id"] > baseline["null_rate_max"] * m_null:
                alert = True
            if gt["mean_amount"] < baseline["mean_amount_min"] * (2 - m_mean) or gt["mean_amount"] > baseline["mean_amount_max"] * m_mean:
                alert = True
            if gt["staleness_min"] > baseline["staleness_min_max"] * m_stale:
                alert = True
                
        elif etype == "embedding_batch":
            if gt["embedding_centroid_shift"] > baseline["embedding_centroid_shift_max"] * m_embed:
                alert = True
            if gt["corpus_avg_doc_age_days"] > baseline["corpus_avg_doc_age_days_max"] * m_age:
                alert = True
                
        elif etype == "lineage_run":
            if gt["lineage_duration_ms"] > baseline["lineage_duration_ms_max"] * m_lineage:
                alert = True
                
        elif etype == "feature_materialization":
            shift = abs(gt["feature_serve_mean"] - gt["train_mean"]) / gt["train_std"]
            if shift > max(baseline["feature_mean_shift_sigma_max"] * m_feat, 0.5):
                alert = True
                
        elif etype == "contract_checkpoint":
            if gt["freshness_delay_min"] > baseline["freshness_delay_max_min"] * m_fresh:
                alert = True
                
        if actual:
            total_f += 1
            if alert: tpr_c += 1
        else:
            total_c += 1
            if alert: fpr_c += 1
            
    tpr = tpr_c / total_f if total_f else 0
    fpr = fpr_c / total_c if total_c else 0
    score = 100 * (0.5 * tpr - 0.3 * fpr)
    return score, tpr, fpr

# Grid search
best_score = -999
best_params = None

import itertools
def linspace(start, stop, n):
    if n == 1:
        return [stop]
    step = (stop - start) / (n - 1)
    return [start + step * i for i in range(n)]

for m_row in linspace(1.0, 1.0, 1): # row_count was better at 1.0
    for m_null in linspace(0.9, 1.0, 3):
        for m_mean in linspace(0.9, 0.95, 10):
            for m_stale in linspace(0.7, 0.9, 5):
                for m_embed in linspace(0.65, 0.75, 5):
                    for m_age in linspace(0.55, 0.65, 5):
                        # fixed for others that don't need heavy tuning
                        score, tpr, fpr = evaluate(m_row, m_null, m_mean, m_stale, 1.0, 0.85, 1.0, m_embed, m_age)
                        if score > best_score:
                            best_score = score
                            best_params = (m_row, m_null, m_mean, m_stale, m_embed, m_age)
                            print(f"New best: {best_score:.2f} | TPR: {tpr:.2f}, FPR: {fpr:.2f} | Params: {best_params}")

print(f"Final best: {best_score}")
print(best_params)
