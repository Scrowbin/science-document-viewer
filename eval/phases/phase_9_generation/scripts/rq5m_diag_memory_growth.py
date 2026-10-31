import sys, time, json, requests, psutil
sys.path.insert(0, r"C:\DACNTT\eval\phases\phase_9_generation\scripts")
from rq5_resource_profile import unload_all
from evaluate_rq5_llm_generation import build_prompt
U="http://localhost:11434"
def tree():
    out=[]
    for p in psutil.process_iter(["name"]):
        if (p.info["name"] or "").lower()=="ollama.exe":
            for q in [p]+p.children(recursive=True):
                try:
                    mi=q.memory_full_info(); out.append((q.name(), q.pid, round(mi.rss/2**20), round(mi.uss/2**20), round(mi.private/2**20) if hasattr(mi,"private") else None))
                except psutil.Error: pass
    return out
unload_all(); time.sleep(2)
items = json.load(open(r"C:\DACNTT\eval\phases\phase_9_generation\artifacts\eval_sample_manifest_500q.json", encoding="utf-8"))["selected_eval_items"][::8][:30]
for i,it in enumerate(items):
    p = build_prompt(it.get("paper_title","Scientific Document"), "\n\n".join(it["ground_truth_evidence"]), it["question_text"])
    d=requests.post(U+"/api/generate", json={"model": "llama3.2:3b", "prompt": p, "stream": False, "options": {"temperature": 0, "num_predict": 256}}).json()
    if i in (0,1,2,5,10,20,29): print(i, d.get("prompt_eval_count"), tree(), flush=True)
ps=requests.get(U+"/api/ps").json()["models"]; print([(x["name"], round(x["size"]/2**20), x.get("context_length")) for x in ps])
unload_all()
