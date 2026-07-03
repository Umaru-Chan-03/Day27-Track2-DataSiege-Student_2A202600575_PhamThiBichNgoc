import json

events = json.load(open('analysis_private.json'))
hist = []
for e in events:
    if e['etype'] == 'lineage_run':
        actual = e['actual']
        dur = e['gt']['lineage_duration_ms']
        
        alert = False
        if len(hist) >= 3:
            avg_dur = sum(hist[-5:]) / len(hist[-5:])
            if dur > avg_dur * 1.1:
                alert = True
                
        print(f"Dur: {dur:.1f}, Alert: {alert}, Actual: {actual}, Fault: {e['fault_key']}")
        
        if not alert:
            hist.append(dur)
