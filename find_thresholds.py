import json

with open("analysis.json") as f:
    events = json.load(f)

# Find optimal feature shift
feature_clean = []
feature_faulty = []
embed_shift_clean = []
embed_shift_faulty = []
doc_age_clean = []
doc_age_faulty = []
data_std_clean = []
data_std_faulty = []
data_mean_clean = []
data_mean_faulty = []

for ev in events:
    gt = ev["gt"]
    actual = ev["actual"]
    etype = ev["etype"]
    
    if etype == "feature_materialization":
        shift = abs(gt["feature_serve_mean"] - gt["train_mean"]) / gt["train_std"]
        if actual: feature_faulty.append(shift)
        else: feature_clean.append(shift)
        
    elif etype == "embedding_batch":
        shift = gt["embedding_centroid_shift"]
        age = gt["corpus_avg_doc_age_days"]
        if actual:
            if ev["fault_key"] == "embedding_drift":
                embed_shift_faulty.append(shift)
            elif ev["fault_key"] == "corpus_staleness":
                doc_age_faulty.append(age)
        else:
            embed_shift_clean.append(shift)
            doc_age_clean.append(age)
            
    elif etype == "data_batch":
        std = gt["std_amount"]
        mean = gt["mean_amount"]
        if actual:
            if ev["fault_key"] == "distribution_shift":
                data_std_faulty.append(std)
                data_mean_faulty.append(mean)
        else:
            data_std_clean.append(std)
            data_mean_clean.append(mean)

print(f"Feature shift: clean max {max(feature_clean) if feature_clean else 0}, faulty min {min(feature_faulty) if feature_faulty else 0}")
print(f"Embed shift: clean max {max(embed_shift_clean) if embed_shift_clean else 0}, faulty min {min(embed_shift_faulty) if embed_shift_faulty else 0}")
print(f"Doc age: clean max {max(doc_age_clean) if doc_age_clean else 0}, faulty min {min(doc_age_faulty) if doc_age_faulty else 0}")
print(f"Data std: clean min/max {min(data_std_clean) if data_std_clean else 0}/{max(data_std_clean) if data_std_clean else 0}")
print(f"Data std faulty: {data_std_faulty}")
print(f"Data mean clean min/max {min(data_mean_clean) if data_mean_clean else 0}/{max(data_mean_clean) if data_mean_clean else 0}")
print(f"Data mean faulty (distribution shift): {data_mean_faulty}")
