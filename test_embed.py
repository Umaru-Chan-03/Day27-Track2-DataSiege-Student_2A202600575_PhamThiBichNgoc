import json

events = json.load(open('analysis_private.json'))
hist_shift = {}
hist_age = {}

tpr = 0
fpr = 0
total_f = 0
total_c = 0

for e in events:
    if e['etype'] == 'embedding_batch':
        actual = e['actual']
        corpus = e['payload']['corpus']
        shift = e['gt']['embedding_centroid_shift']
        age = e['gt']['corpus_avg_doc_age_days']
        
        hs = hist_shift.setdefault(corpus, [])
        ha = hist_age.setdefault(corpus, [])
        
        alert = False
        
        if len(hs) >= 2:
            avg_shift = sum(hs[-5:]) / len(hs[-5:])
            if shift > avg_shift * 1.5:  # shift spiked by 50%
                alert = True
        
        if len(ha) >= 2:
            avg_age = sum(ha[-5:]) / len(ha[-5:])
            if age > avg_age * 1.2:
                alert = True
                
        if actual:
            total_f += 1
            if alert: tpr += 1
        else:
            total_c += 1
            if alert: fpr += 1
            
        if not alert:
            hs.append(shift)
            ha.append(age)
            
print(f"TPR: {tpr}/{total_f}, FPR: {fpr}/{total_c}")
