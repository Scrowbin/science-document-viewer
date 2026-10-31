import sys, time, json, requests
sys.path.insert(0, r"C:\DACNTT\eval\phases\phase_9_generation\scripts")
from profile_generation_resources import TreeSampler
from evaluate_generation import build_prompt
U="http://localhost:11434"
def unload_all():
    for m in [x["name"] for x in requests.get(U+"/api/ps").json()["models"]]:
        requests.post(U+"/api/generate", json={"model": m, "keep_alive": 0})
    for _ in range(30):
        if not requests.get(U+"/api/ps").json()["models"]: return True
        time.sleep(1)
    return False
it = json.load(open(r"C:\DACNTT\eval\phases\phase_9_generation\artifacts\eval_sample_manifest_500q.json", encoding="utf-8"))["selected_eval_items"][0]
p = build_prompt(it.get("paper_title","Scientific Document"), "\n\n".join(it["ground_truth_evidence"]), it["question_text"])
for m in ["llama3.2:1b", "qwen2.5:0.5b", "llama3.2:3b"]:
    print("empty before:", unload_all()); time.sleep(2)
    s = TreeSampler(); time.sleep(0.5)
    for _ in range(3):
        requests.post(U+"/api/generate", json={"model": m, "prompt": p, "stream": False, "options": {"temperature": 0, "num_predict": 256}})
    ps = requests.get(U+"/api/ps").json()["models"]
    print(m, s.stop(), [(x["name"], round(x["size"]/2**20), x.get("context_length")) for x in ps])
unload_all()
