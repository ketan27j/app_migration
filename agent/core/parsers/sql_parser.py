from typing import List, Dict

class SqlParser:
    def parse_schema(self, schema_content: str) -> Dict:
        return {
            'tables': [],
            'procedures': []
        }
