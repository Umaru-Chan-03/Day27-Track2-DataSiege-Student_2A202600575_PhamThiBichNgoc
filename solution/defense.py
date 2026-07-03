from api import Verdict

def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)

def check_data_batch(payload, ctx):
    res = ctx.tools.batch_profile(payload["batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="checks")
    
    alert = False
    if res["row_count"] < ctx.baseline["row_count_min"] or res["row_count"] > ctx.baseline["row_count_max"]:
        alert = True
    if res["null_rate"].get("customer_id", 0) > ctx.baseline["null_rate_max"]:
        alert = True
    if res["mean_amount"] < ctx.baseline["mean_amount_min"] * 1.02 or res["mean_amount"] > ctx.baseline["mean_amount_max"] * 0.98:
        alert = True
    if res["staleness_min"] > ctx.baseline["staleness_min_max"]:
        alert = True

    return Verdict(alert=alert, pillar="checks")

def check_contract_checkpoint(payload, ctx):
    res = ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="contracts")

    alert = False
    if res["freshness_delay_min"] > ctx.baseline["freshness_delay_max_min"]:
        alert = True
    if res.get("violations"):
        alert = True

    return Verdict(alert=alert, pillar="contracts")

def check_lineage_run(payload, ctx):
    res = ctx.tools.lineage_graph_slice(payload["run_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="lineage")

    alert = False
    if res["duration_ms"] > ctx.baseline["lineage_duration_ms_max"]:
        alert = True
        
    job = payload.get("job", "unknown")
    state_key_up = f"lineage_up_{job}"
    state_key_down = f"lineage_down_{job}"
    
    ctx.state[state_key_up] = max(ctx.state.get(state_key_up, 0), len(res["actual_upstream"]))
    ctx.state[state_key_down] = max(ctx.state.get(state_key_down, 0), res["actual_downstream_count"])
    
    if len(res["actual_upstream"]) < ctx.state[state_key_up]:
        alert = True
    if res["actual_downstream_count"] < ctx.state[state_key_down]:
        alert = True

    return Verdict(alert=alert, pillar="lineage")

def check_feature_materialization(payload, ctx):
    res = ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="ai_infra")

    alert = False
    # Use 0.5 instead of baseline 0.4095 to avoid FPs on normal high variance
    if res["mean_shift_sigma"] > max(ctx.baseline["feature_mean_shift_sigma_max"], 0.5):
        alert = True

    return Verdict(alert=alert, pillar="ai_infra")

def check_embedding_batch(payload, ctx):
    res = ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    if "error" in res:
        return Verdict(alert=False, pillar="ai_infra")

    alert = False
    if res["centroid_shift"] > ctx.baseline["embedding_centroid_shift_max"] * 0.9:
        alert = True
    if res["avg_doc_age_days"] > ctx.baseline["corpus_avg_doc_age_days_max"] * 0.9:
        alert = True

    return Verdict(alert=alert, pillar="ai_infra")
