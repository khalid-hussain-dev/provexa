"""Quick sanity checks for parse_crew_result and safe_parse_list."""
import json
from utils import parse_crew_result

# --- Simulate a CrewOutput-like object ---
class FakeCrewOutput:
    def __init__(self, raw):
        self.raw = raw

cases = [
    ("Plain JSON dict",     '{"a": 1}',                          {"a": 1}),
    ("JSON wrapped in ```json",  '```json\n{"b": 2}\n```',       {"b": 2}),
    ("JSON wrapped in ```",      '```\n{"c": 3}\n```',           {"c": 3}),
    ("JSON buried in prose", 'Here is the result:\n{"d": 4}\n',  {"d": 4}),
    ("CrewOutput with raw",  FakeCrewOutput('{"e": 5}'),          {"e": 5}),
    ("Empty string",         "",                                  {}),
    ("None",                 None,                                {}),
    ("JSON array",           '[1,2,3]',                           [1,2,3]),
]

all_passed = True
for name, inp, expected in cases:
    result = parse_crew_result(inp)
    ok = result == expected
    all_passed = all_passed and ok
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: got {result!r}")

# --- safe_parse_list checks (inline) ---
def safe_parse_list(value):
    if not value or not value.strip():
        return []
    text = value.strip()
    if text.startswith("["):
        try:
            result = json.loads(text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            pass
    return [s.strip() for s in text.split(",") if s.strip()]

list_cases = [
    ('["Python","FastAPI"]', ["Python", "FastAPI"]),
    ("Python, FastAPI, SQL",  ["Python", "FastAPI", "SQL"]),
    ("",                      []),
    (None,                    []),
]
for inp, expected in list_cases:
    result = safe_parse_list(inp)
    ok = result == expected
    all_passed = all_passed and ok
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] safe_parse_list({inp!r}) -> {result!r}")

print()
print("All tests passed!" if all_passed else "SOME TESTS FAILED!")
