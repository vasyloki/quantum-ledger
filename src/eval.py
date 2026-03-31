import json
import os
import re
import time
import random
from src.engine import QuantumEngine
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize the Engine and the Auditor
engine = QuantumEngine()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Using the specific Claude 4.6 Sonnet ID for 2026
JUDGE_MODEL = "claude-sonnet-4-6"

def run_audit(file_path="src/data/golden_set.json"):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        golden_set = json.load(f)

    results = []
    print(f"\n--- 🔬 STARTING QUANTUM LEDGER AUDIT ({len(golden_set)} CASES) ---")

    for case in golden_set:
        # 1. THROTTLING: Prevents 529 Overload by giving the API 2 seconds of breathing room
        time.sleep(2 + random.random()) 
        
        print(f"Testing {case['id']}: {case['question'][:60]}...")
        
        try:
            answer, sources = engine.ask(case['question'], company=case['company'])
        except Exception as e:
            print(f"❌ Engine Error for {case['id']}: {str(e)}")
            results.append(0)
            continue
        
        if not sources or len(sources) == 0:
            print(f"❌ Result: 0/1 | EMPTY CONTEXT: No data found for '{case['company']}' in Qdrant.")
            results.append(0)
            continue

        context_blob = "\n\n".join([f"Source {i+1}:\n{s['content']}" for i, s in enumerate(sources)])
        
        eval_prompt = f"""
        Role: Senior Financial Data Auditor
        Task: Determine if the 'Retrieved Context' contains the specific facts needed to answer the 'User Question'.
        
        User Question: {case['question']}
        Expected Keywords: {", ".join(case['expected_keywords'])}
        
        Retrieved Context (from Qdrant):
        {context_blob[:3500]} 

        ### RESPONSE INSTRUCTIONS:
        You must output ONLY a JSON object. Structure: {{"score": 0 or 1, "reason": "reason"}}
        """

        # 2. RETRY LOGIC: Specifically handles the 529 error
        score, reason = 0, "Unknown Error"
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=JUDGE_MODEL,
                    max_tokens=300,
                    messages=[{"role": "user", "content": eval_prompt}]
                )
                
                raw_text = response.content[0].text
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                
                if match:
                    verdict = json.loads(match.group(0))
                    score = verdict.get("score", 0)
                    reason = verdict.get("reason", "No reason provided.")
                else:
                    score, reason = 0, "Judge failed to return JSON."
                
                # If we get here, the call succeeded; break the retry loop
                break

            except Exception as e:
                error_str = str(e)
                if "529" in error_str or "overloaded" in error_str.lower():
                    wait_time = (attempt + 1) * 10
                    print(f"⚠️ API Overloaded (Attempt {attempt+1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    score, reason = 0, f"Judge Processing Error: {error_str}"
                    break # Critical error, don't retry

        results.append(score)
        icon = "✅" if score == 1 else "❌"
        print(f"{icon} Result: {score}/1 | {reason}\n")

    final_score = (sum(results) / len(results)) * 100
    print(f"--- 📊 FINAL AUDIT RESULTS ---")
    print(f"RETRIEVAL PRECISION: {final_score:.2f}%")
    print(f"------------------------------\n")

if __name__ == "__main__":
    run_audit()