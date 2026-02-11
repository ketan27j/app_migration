from typing import Dict, List, Optional
import re

class JavaGenerator:
    CONTROLLER_TEMPLATE = '''package {package}.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import lombok.RequiredArgsConstructor;
import java.util.List;

@RestController
@RequestMapping("/{endpoint}")
@RequiredArgsConstructor
public class {class_name} {{

{dependencies}

    @GetMapping
    public ResponseEntity<List<{dto_type}>> getAll() {{
        return ResponseEntity.ok({service_var}.findAll());
    }}

    @GetMapping("/{id}")
    public ResponseEntity<{dto_type}> getById(@PathVariable {id_type} id) {{
        return {service_var}.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }}

    @PostMapping
    public ResponseEntity<{dto_type}> create(@RequestBody {dto_type} dto) {{
        return ResponseEntity.ok({service_var}.save(dto));
    }}

    @PutMapping("/{id}")
    public ResponseEntity<{dto_type}> update(@PathVariable {id_type} id, @RequestBody {dto_type} dto) {{
        return ResponseEntity.ok({service_var}.update(id, dto));
    }}

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable {id_type} id) {{
        {service_var}.delete(id);
        return ResponseEntity.noContent().build();
    }}
}}
'''

    DTO_TEMPLATE = '''package {package}.dto;

import lombok.Data;

@Data
public class {class_name} {{
{fields}
}}
'''

    SERVICE_TEMPLATE = '''package {package}.service;

import org.springframework.stereotype.Service;
import lombok.RequiredArgsConstructor;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class {class_name} {{
    private final {repository} {repository_var};

    public List<{entity}> findAll() {{
        return {repository_var}.findAll();
    }}

    public Optional<{entity}> findById({id_type} id) {{
        return {repository_var}.findById(id);
    }}

    public {entity} save({entity} entity) {{
        return {repository_var}.save(entity);
    }}

    public {entity} update({id_type} id, {entity} entity) {{
        entity.setId(id);
        return {repository_var}.save(entity);
    }}

    public void delete({id_type} id) {{
        {repository_var}.deleteById(id);
    }}
}}
'''

    REPOSITORY_TEMPLATE = '''package {package}.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface {class_name} extends JpaRepository<{entity}, {id_type}> {{
    List<{entity}> findBy{field}({field_type} {field_var});
}}
'''

    def __init__(self, package_base: str):
        self.package_base = package_base

    def generate_controller(self, component: Dict, context: Dict) -> str:
        class_name = self._extract_class_name(component['code_content'])
        endpoint = self._camel_to_kebab(class_name.replace('Controller', ''))
        dto_type = class_name.replace('Controller', 'DTO')
        service_var = self._capitalize_first(dto_type.replace('DTO', ''))[:1].lower() + self._capitalize_first(dto_type.replace('DTO', ''))[1:] + 'Service'
        
        deps = []
        for dep in context.get('dependencies', []):
            if 'Service' in dep['name']:
                deps.append(f"    private final {self.package_base}.service.{dep['name']} {dep['name'][:1].lower() + dep['name'][1:]};")
        
        return self.CONTROLLER_TEMPLATE.format(
            package=self.package_base,
            class_name=class_name,
            endpoint=endpoint,
            dto_type=dto_type,
            id_type='Long',
            dependencies='\n'.join(deps),
            service_var=service_var
        )

    def generate_dto(self, name: str, fields: List[Dict]) -> str:
        field_lines = []
        for field in fields:
            field_lines.append(f"    private {field['type']} {field['name']};")
        
        return self.DTO_TEMPLATE.format(
            package=self.package_base,
            class_name=name,
            fields='\n'.join(field_lines)
        )

    def generate_service(self, name: str, entity: str, repository: str) -> str:
        service_name = name if 'Service' in name else f"{entity}Service"
        repo_var = repository[:1].lower() + repository[1:]
        
        return self.SERVICE_TEMPLATE.format(
            package=self.package_base,
            class_name=service_name,
            entity=entity,
            repository=repository,
            repository_var=repo_var,
            id_type='Long'
        )

    def generate_repository(self, name: str, entity: str, id_type: str = 'Long') -> str:
        return self.REPOSITORY_TEMPLATE.format(
            package=self.package_base,
            class_name=name,
            entity=entity,
            id_type=id_type,
            field='Id',
            field_type=id_type,
            field_var='id'
        )

    def _extract_class_name(self, content: str) -> str:
        match = re.search(r'class\s+(\w+)', content)
        return match.group(1) if match else 'Unknown'

    def _camel_to_kebab(self, name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()

    def _capitalize_first(self, s: str) -> str:
        return s[0].upper() + s[1:] if s else s
