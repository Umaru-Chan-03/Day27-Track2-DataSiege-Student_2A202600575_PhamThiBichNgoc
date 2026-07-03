import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path("harness").resolve()))
import crypto
from isolation import IsolatedRun

BUDGET = 220.0

def analyze():
    key = Path("phases/public.key").read_bytes()
    ciphertext = Path("phases/public_schedule.json.enc").read_bytes()
    schedule = crypto.decrypt_schedule(ciphertext, key)
    
    events = schedule["events"]
    truths = schedule["ground_truth"]
    labels = schedule["labels"]
    gt_by_key = {(t["type"], t["batch_id_or_ref"]): t["gt"] for t in truths}
    
    baseline_path = str(Path("data/baselines.json").resolve())
    run = IsolatedRun("solution/defense.py", baseline_path, gt_by_key, budget=BUDGET)
    
    fp_details = []
    fn_details = []
    
    out = []
    try:
        for i, (ev, label) in enumerate(zip(events, labels)):
            verdict = run.dispatch(ev)
            actual = label["is_faulty"]
            fault_key = label.get("fault_key")
            
            etype = ev["type"]
            ref = ev["payload"].get("batch_id") or ev["payload"].get("checkpoint_batch_id") or ev["payload"].get("run_id") or ev["payload"].get("chunk_batch_id")
            gt = gt_by_key.get((etype, ref))
            
            out.append({
                "seq": i,
                "etype": etype,
                "actual": actual,
                "fault_key": fault_key,
                "gt": gt
            })
    finally:
        run.shutdown()
        
    import json
    with open("analysis.json", "w") as f:
        json.dump(out, f, indent=2)

if __name__ == "__main__":
    analyze()

