
import json
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Lock

USAGE_FILE = Path("usage.jsonl")
_file_lock = Lock()



def log_usage(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
) -> dict:
    timestamp = datetime.now(timezone.utc)

    record = {
        "timestamp": timestamp.isoformat(),
        "date": timestamp.date().isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "cost_usd": cost,
    }

    with _file_lock:
        with USAGE_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")

    return record



def get_daily_usage(target_date: date | None = None) -> dict:
    target_date = target_date or datetime.now(timezone.utc).date()

    totals = {
        "date": target_date.isoformat(),
        "requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
    }

    if not USAGE_FILE.exists():
        return totals

    with _file_lock:
        with USAGE_FILE.open("r", encoding="utf-8") as file:
            for line in file:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("date") != target_date.isoformat():
                    continue

                totals["requests"] += 1
                totals["input_tokens"] += record.get("input_tokens", 0)
                totals["output_tokens"] += record.get("output_tokens", 0)
                totals["total_tokens"] += record.get("total_tokens", 0)
                totals["cost_usd"] += record.get("cost_usd", 0.0)

    totals["cost_usd"] = round(totals["cost_usd"], 10)
    return totals
