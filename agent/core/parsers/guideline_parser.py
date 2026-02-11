import re
from typing import Dict

class GuidelineParser:
    def extract_guidelines(self, readme_content: str) -> Dict:
        guidelines = {
            'coding_standards': '',
            'naming_conventions': {},
            'package_structure': {},
            'design_patterns': [],
            'best_practices': []
        }
        
        standards_match = re.search(
            r'##\s*Coding Standards\s*\n(.*?)(?=\n##|\Z)',
            readme_content, re.DOTALL | re.IGNORECASE
        )
        if standards_match:
            guidelines['coding_standards'] = standards_match.group(1).strip()
        
        naming_match = re.search(
            r'##\s*Naming Conventions\s*\n(.*?)(?=\n##|\Z)',
            readme_content, re.DOTALL | re.IGNORECASE
        )
        if naming_match:
            guidelines['naming_conventions'] = naming_match.group(1).strip()
        
        return guidelines
