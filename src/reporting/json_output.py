import os
import json
from typing import Dict, Any

class JsonOutputGenerator:
    """Generates machine-readable daily analysis JSON output with a stable schema."""

    @staticmethod
    def generate_json_output(data: Dict[str, Any], output_path: str):
        """Writes structured analysis dictionary to data/analysis/daily/YYYY-MM-DD.json."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
