from typing import Dict, List
import re

class AngularGenerator:
    COMPONENT_TEMPLATE = '''import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { {service_name} } from '../../services/{service_file}';
import { {model_name} } from '../../models/{model_file}';

@Component({{
  selector: 'app-{selector}',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './{template_file}',
  styleUrls: ['./{style_file}']
}})
export class {class_name}Component implements OnInit {{
  items: {model_name}[] = [];
  loading = false;

  constructor(private {service_var}: {service_name}) {{}}

  ngOnInit(): void {{
    this.loadItems();
  }}

  loadItems(): void {{
    this.loading = true;
    this.{service_var}.getAll().subscribe({{
      next: (data) => {{ this.items = data; this.loading = false; }},
      error: (err) => {{ console.error('Error loading items', err); this.loading = false; }}
    }});
  }}

  delete(id: number): void {{
    if (confirm('Are you sure?')) {{
      this.{service_var}.delete(id).subscribe({{
        next: () => this.loadItems(),
        error: (err) => console.error('Error deleting', err)
      }});
    }}
  }}
}}
'''

    SERVICE_TEMPLATE = '''import { Injectable } from '@angular/core';
import {{ HttpClient }} from '@angular/common/http';
import {{ Observable }} from 'rxjs';
import {{ {model_name} }} from '../models/{model_file}';
import {{ environment }} from '../../../environments/environment';

@Injectable({{
  providedIn: 'root'
}})
export class {class_name}Service {{
  private apiUrl = `\${{environment.apiUrl}}/{endpoint}`;

  constructor(private http: HttpClient) {{}}

  getAll(): Observable<{model_name}[]> {{
    return this.http.get<{model_name}[]>(this.apiUrl);
  }}

  getById(id: number): Observable<{model_name}> {{
    return this.http.get<{model_name}>(`\${{this.apiUrl}}/${{id}}`);
  }}

  create(item: {model_name}): Observable<{model_name}> {{
    return this.http.post<{model_name}>(this.apiUrl, item);
  }}

  update(id: number, item: {model_name}): Observable<{model_name}> {{
    return this.http.put<{model_name}>(`\${{this.apiUrl}}/${{id}}`, item);
  }}

  delete(id: number): Observable<void> {{
    return this.http.delete<void>(`\${{this.apiUrl}}/${{id}}`);
  }}
}}
'''

    MODEL_TEMPLATE = '''export interface {class_name} {{
{id_fields}
}}
'''

    HTML_TEMPLATE = '''<div class="{component}-container">
  <h2>{title}</h2>
  
  <button routerLink="/{create_route}/new" class="btn btn-primary">
    Add New
  </button>

  <div *ngIf="loading" class="loading">Loading...</div>

  <table *ngIf="!loading && items.length > 0" class="table">
    <thead>
      <tr>
        <th>ID</th>
{html_headers}
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      <tr *ngFor="let item of items">
        <td>{{ item.id }}</td>
{html_cells}
        <td>
          <button [routerLink]="['/{edit_route}', item.id]" class="btn btn-sm">Edit</button>
          <button (click)="delete(item.id)" class="btn btn-sm btn-danger">Delete</button>
        </td>
      </tr>
    </tbody>
  </table>

  <div *ngIf="!loading && items.length === 0" class="no-data">
    No items found.
  </div>
</div>
'''

    def __init__(self, project_path: str):
        self.project_path = project_path

    def generate_component(self, component: Dict, context: Dict) -> str:
        class_name = self._extract_class_name(component['code_content'])
        selector = self._to_kebab_case(class_name)
        service_name = context.get('service', {}).get('name', 'ApiService')
        service_var = service_name[:1].lower() + service_name[1:]
        service_file = self._to_kebab_case(service_name)
        model_name = context.get('model', 'BaseModel')
        model_file = self._to_kebab_case(model_name)
        
        return self.COMPONENT_TEMPLATE.format(
            class_name=class_name,
            selector=selector,
            service_name=service_name,
            service_var=service_var,
            service_file=service_file,
            model_name=model_name,
            model_file=model_file,
            template_file=f"{selector}.html",
            style_file=f"{selector}.scss"
        )

    def generate_service(self, name: str, model: str, endpoint: str) -> str:
        class_name = name if 'Service' in name else f"{model}Service"
        endpoint = endpoint or self._to_kebab_case(model)
        
        return self.SERVICE_TEMPLATE.format(
            class_name=class_name,
            model_name=model,
            model_file=self._to_kebab_case(model),
            endpoint=endpoint
        )

    def generate_model(self, name: str, fields: List[Dict]) -> str:
        field_lines = []
        for field in fields:
            optional = '?' if field.get('nullable') else ''
            field_lines.append(f"  {field['name']}{optional}: {field['type']};")
        
        return self.MODEL_TEMPLATE.format(
            class_name=name,
            id_fields='\n'.join(field_lines)
        )

    def generate_html(self, component: Dict, fields: List[Dict]) -> str:
        class_name = self._extract_class_name(component['code_content'])
        title = class_name.replace('Component', '').replace('Controller', '')
        create_route = self._to_kebab_case(title)
        edit_route = self._to_kebab_case(title)
        
        headers = []
        cells = []
        for field in fields:
            if field['name'] != 'id':
                headers.append(f"        <th>{self._to_title_case(field['name'])}</th>")
                cells.append(f"        <td>{{ item.{field['name']} }}</td>")
        
        return self.HTML_TEMPLATE.format(
            component=self._to_kebab_case(title),
            title=title,
            create_route=create_route,
            edit_route=edit_route,
            html_headers='\n'.join(headers),
            html_cells='\n'.join(cells)
        )

    def _extract_class_name(self, content: str) -> str:
        match = re.search(r'class\s+(\w+)', content)
        return match.group(1) if match else 'Unknown'

    def _to_kebab_case(self, name: str) -> str:
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '-', name).lower()

    def _to_title_case(self, name: str) -> str:
        import re
        return re.sub(r'([A-Z])', r' \1', name).strip()
