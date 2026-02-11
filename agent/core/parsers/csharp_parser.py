from typing import List, Dict, Optional

class CSharpParser:
    def __init__(self):
        pass
    
    def parse_code(self, content: str, file_path: str) -> Dict:
        return {
            'file_path': file_path,
            'content': content,
            'type': self._detect_type(file_path),
            'name': self._extract_class_name(content),
            'namespace': self._extract_namespace(content),
            'methods': self._extract_methods(content),
            'properties': self._extract_properties(content),
            'dependencies': self._extract_dependencies(content)
        }
    
    def _detect_type(self, file_path: str) -> str:
        if 'Controller' in file_path:
            return 'controller'
        elif 'Service' in file_path:
            return 'service'
        elif 'Repository' in file_path:
            return 'repository'
        elif 'Model' in file_path or 'Entity' in file_path:
            return 'model'
        return 'other'
    
    def _extract_class_name(self, content: str) -> str:
        import re
        match = re.search(r'class\s+(\w+)', content)
        return match.group(1) if match else ''
    
    def _extract_namespace(self, content: str) -> str:
        import re
        match = re.search(r'namespace\s+([\w.]+)', content)
        return match.group(1) if match else ''
    
    def _extract_methods(self, content: str) -> List[str]:
        import re
        return re.findall(r'public\s+\w+\s+(\w+)\s*\(', content)
    
    def _extract_properties(self, content: str) -> List[str]:
        import re
        return re.findall(r'public\s+\w+\s+(\w+)\s*\{', content)
    
    def _extract_dependencies(self, content: str) -> List[str]:
        import re
        pattern = r'new\s+(\w+Repository|\w+Service|\w+Controller)'
        return re.findall(pattern, content)
