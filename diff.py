import json

def diff():
    with open("phases/practice_answer_key.json") as f:
        key = json.load(f)
    
    with open("harness/child_env/my_verdicts.json") as f:
        my_v = json.load(f)
        
    for i, (k, v) in enumerate(zip(key, my_v)):
        if k["is_faulty"] and not v:
            print(f"False Negative: seq={i}, type={k['fault_key']}, pillar={k['pillar']}")
        elif not k["is_faulty"] and v:
            print(f"False Positive: seq={i}")

if __name__ == "__main__":
    diff()
