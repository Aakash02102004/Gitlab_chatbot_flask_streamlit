"""Quick test of the scraper with a small page limit."""
import sys
sys.path.insert(0, '.')
import gitlab_scrapper.scrape_gitlab

# Override config for quick test
scrape_gitlab.MAX_PAGES = 10
scrape_gitlab.MAX_DEPTH = 2
scrape_gitlab.CONCURRENCY = 3
scrape_gitlab.DELAY = 0.3
scrape_gitlab.OUTPUT_FILE = 'gitlab_data_test.json'
scrape_gitlab.CHECKPOINT_FILE = 'gitlab_data_test_checkpoint.json'

results = scrape_gitlab.crawl()

print("\n=== TEST RESULTS ===")
print(f"Total results: {len(results)}")
if results:
    first = results[0]
    print(f"First URL: {first['url']}")
    print(f"Content length: {len(first['content'])} chars")
    print(f"Content preview: {first['content'][:300]}")

# Validate JSON structure
import json
with open('gitlab_data_test.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    for entry in data:
        assert 'url' in entry, "Missing 'url' key"
        assert 'content' in entry, "Missing 'content' key"
        assert isinstance(entry['url'], str), "'url' must be a string"
        assert isinstance(entry['content'], str), "'content' must be a string"
        assert '<' not in entry['content'][:500] or '>' not in entry['content'][:500], "HTML tags found in content"
    print(f"\n✅ All {len(data)} entries have valid 'url' and 'content' keys")
    print("✅ Content appears clean (no HTML tags)")
