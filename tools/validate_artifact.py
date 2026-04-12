"""
Validation utility for Developer OS artifacts.
Ensures Markdown files with YAML frontmatter adhere to the system contract.
"""

import os
import re
import json
import argparse
from typing import Dict, List, Optional, Tuple

def parse_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    """Parses YAML-like frontmatter from a Markdown string."""
    # Simple regex to find content between --- marks at the start
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return None, content
    
    yaml_str = match.group(1)
    body = content[match.end():]
    
    # Primitive YAML parser (key: value) to keep zero dependencies
    metadata = {}
    for line in yaml_str.split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            metadata[key.strip()] = val.strip().strip('"').strip("'")
            
    # Post-process types
    for key in ['round', 'implementation_round']:
        if key in metadata:
            try: metadata[key] = int(metadata[key])
            except: pass
            
    return metadata, body

def validate_artifact(file_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    if not os.path.exists(schema_path):
        return False, [f"Schema not found: {schema_path}"]
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
        
    metadata, body = parse_frontmatter(content)
    if metadata is None:
        return False, ["Missing YAML frontmatter (between '---' lines)."]
        
    errors = []
    # Validate required fields
    for field in schema.get("required", []):
        if field not in metadata:
            errors.append(f"Missing required field in frontmatter: {field}")
            
    # Validate enums
    for field, rules in schema.get("properties", {}).items():
        if field in metadata and "enum" in rules:
            if metadata[field] not in rules["enum"]:
                errors.append(f"Invalid value for '{field}': {metadata[field]}. Must be one of {rules['enum']}")
                
    # Validate patterns
    for field, rules in schema.get("properties", {}).items():
        if field in metadata and "pattern" in rules:
            if not re.match(rules["pattern"], str(metadata[field])):
                errors.append(f"Field '{field}' does not match required pattern: {rules['pattern']}")

    return len(errors) == 0, errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Artifact file to validate")
    parser.add_argument("schema", help="Schema file to validate against")
    args = parser.parse_args()
    
    success, errors = validate_artifact(args.file, args.schema)
    if success:
        print("Validation Successful")
        exit(0)
    else:
        print("Validation Failed:")
        for err in errors:
            print(f"  - {err}")
        exit(1)
