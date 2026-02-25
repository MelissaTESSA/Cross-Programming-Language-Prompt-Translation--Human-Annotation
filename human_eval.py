import os
import json
import csv

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

data_dir = os.path.join(BASE_DIR, "Data")
result_dir = os.path.join(BASE_DIR, "results")
languages = ["Python", "JavaScript", "Java", "Php"]
questions = [
    "Faithfulness to the original prompt (✅ Yes, completely / 🟡 Partially / ❌ No, the meaning is altered)",
    "Package existence (✅ Good equivalent and verified / 🟡 Exists but not the best choice / ❌ Wrong equivalent or not found)",
    "Overall quality (⭐⭐⭐ Good — ready to use as-is / ⭐⭐ Average — needs minor corrections / ⭐ Poor — needs to be redone)"
]

# TEST MODE: set to True to only evaluate the first two prompts of each dataset/language
TEST_MODE = False  # Set to False for full evaluation

os.makedirs(result_dir, exist_ok=True)

# List datasets from the Python folder
def list_datasets():
    return [f for f in os.listdir(os.path.join(data_dir, "Python")) if f.endswith(".json")]

def load_prompts(dataset, lang):
    path = os.path.join(data_dir, lang, dataset)
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Clean up lines
    prompts = [line.strip().strip(',').strip('"') for line in lines if line.strip()]
    return prompts

def clean_prompt(text):
    # Cleans up escape sequences and stray quotes
    return text.replace('\\n', '\n').replace('\\"', '"').replace('"', '').replace('  ', ' ').strip()

def get_validated_answer(qtype):
    if qtype == "faithfulness":
        while True:
            ans = input("Faithfulness to the original prompt (✅ Yes / ❌ No):\nYour answer: ").strip().lower()
            if ans in ["yes", "no"]:
                return ans
            print("Please enter 'yes' or 'no'.")
    elif qtype == "package":
        while True:
            ans = input("Package existence (✅ Yes / ❌ No):\nYour answer: ").strip().lower()
            if ans == "yes":
                return ans, None
            elif ans == "no":
                while True:
                    missing = input("Which packages are missing? (comma-separated): ").strip()
                    # Check for semicolons or other separators
                    if ";" in missing or ":" in missing or " " in missing:
                        print("Please use only commas to separate package names (e.g. package1,package2). No spaces or semicolons.")
                        continue
                    if missing == "":
                        print("Please enter at least one package name.")
                        continue
                    # If more than one, must be comma-separated
                    if "," in missing or missing.count(",") == 0:
                        return ans, missing
                print("Please enter 'yes' or 'no'.")
    elif qtype == "quality":
        while True:
            ans = input("Overall quality (⭐⭐⭐ Good / ⭐⭐ Average / ⭐ Poor):\nYour answer: ").strip().lower()
            if ans in ["good", "average", "poor"]:
                return ans
            print("Please enter 'good', 'average', or 'poor'.")


def evaluate_entry(py_prompt, translations, dataset_idx, dataset_total, prompt_idx, prompt_total):
    print(f"\n{'='*60}")
    print(f"Dataset {dataset_idx}/{dataset_total} — Prompt {prompt_idx}/{prompt_total}")
    results = {}
    for lang, trans in translations.items():
        print("--- Original Python prompt ---")
        print(clean_prompt(py_prompt))
        print(f"\n--- Translation in {lang} ---")
        print(clean_prompt(trans))
        print("-"*40)
        answers = {}
        answers["faithfulness"] = get_validated_answer("faithfulness")
        pkg_ans, missing = get_validated_answer("package")
        answers["package_existence"] = pkg_ans
        if missing:
            answers["missing_packages"] = missing
        answers["quality"] = get_validated_answer("quality")
        results[lang] = answers
        print("-"*40)
    print("="*60)
    return results

def load_existing_results(dataset, lang):
    out_path = os.path.join(result_dir, f"human_eval_{dataset.replace('.json','')}_{lang}.json")
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def main():
    datasets = list_datasets()
    dataset_total = len(datasets)
    for lang in [l for l in languages if l != "Python"]:
        print(f"\n=== Evaluating all datasets for language: {lang} ===")
        for dataset_idx, dataset in enumerate(datasets, 1):
            print(f"\n=== Evaluating dataset: {dataset} ({dataset_idx}/{dataset_total}) ===")
            py_prompts = load_prompts(dataset, "Python")
            trans_prompts = load_prompts(dataset, lang)
            out_path = os.path.join(result_dir, f"human_eval_{dataset.replace('.json','')}_{lang}.json")
            existing = load_existing_results(dataset, lang)
            start_idx = len(existing)
            prompt_total = min(len(py_prompts), len(trans_prompts)-1)
            if TEST_MODE:
                prompt_total = min(prompt_total, 2)
            print(f"\n[Language: {lang}] Already completed: {start_idx}/{prompt_total}")
            for prompt_idx in range(start_idx, prompt_total):
                py_prompt = py_prompts[prompt_idx]
                trans = trans_prompts[prompt_idx+1]  # translation index +1
                entry_result = evaluate_entry(py_prompt, {lang: trans}, dataset_idx, dataset_total, prompt_idx+1, prompt_total)
                existing.append({
                    "prompt_number": prompt_idx+1,
                    "python_prompt": py_prompt,
                    "translation": trans,
                    "evaluation": entry_result[lang]
                })
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(existing, f, indent=2, ensure_ascii=False)
                print(f"[Saved progress for {lang} — prompt {prompt_idx+1}/{prompt_total}]")
            print(f"Results saved to {out_path}")

if __name__ == "__main__":
    main()
