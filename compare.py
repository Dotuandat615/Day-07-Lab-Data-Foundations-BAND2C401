import json
from pathlib import Path
from src.chunking import ChunkingStrategyComparator

def main():
    docs = [
        "Working Remotely.md",
        "Vacation and Sick Leave.md",
        "Code of Conduct in the Community.md"
    ]
    base_path = Path("data/Company Policies")
    comparator = ChunkingStrategyComparator()
    results = {}
    
    for doc in docs:
        file_path = base_path / doc
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        comp_res = comparator.compare(text, chunk_size=500)
        
        results[doc] = {
            "fixed_size": {
                "count": comp_res["fixed_size"]["count"],
                "avg_length": comp_res["fixed_size"]["avg_length"],
                "sample_chunk": comp_res["fixed_size"]["chunks"][0][:100] if comp_res["fixed_size"]["chunks"] else ""
            },
            "by_sentences": {
                "count": comp_res["by_sentences"]["count"],
                "avg_length": comp_res["by_sentences"]["avg_length"],
                "sample_chunk": comp_res["by_sentences"]["chunks"][0][:100] if comp_res["by_sentences"]["chunks"] else ""
            },
            "recursive": {
                "count": comp_res["recursive"]["count"],
                "avg_length": comp_res["recursive"]["avg_length"],
                "sample_chunk": comp_res["recursive"]["chunks"][0][:100] if comp_res["recursive"]["chunks"] else ""
            }
        }
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
