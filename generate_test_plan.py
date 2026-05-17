import json
import os
import random

with open('openapi.json', 'r') as f:
    openapi = json.load(f)

paths = openapi.get("paths", {})
components = openapi.get("components", {}).get("schemas", {})

# Group by tags
groups = {}
for path, methods in paths.items():
    for method, details in methods.items():
        tags = details.get("tags", ["Untagged"])
        tag = tags[0]
        if tag not in groups:
            groups[tag] = []
        groups[tag].append((path, method, details))

# Assign rounds
rounds = []
current_round_tags = []
for tag in sorted(groups.keys()):
    current_round_tags.append(tag)
    if len(current_round_tags) >= 3:
        rounds.append(current_round_tags)
        current_round_tags = []
if current_round_tags:
    rounds.append(current_round_tags)

def resolve_ref(ref):
    if not ref: return {}
    ref_name = ref.split("/")[-1]
    return components.get(ref_name, {})

def get_schema(schema):
    if not schema: return {}
    if "$ref" in schema:
        return resolve_ref(schema["$ref"])
    if "items" in schema and "$ref" in schema["items"]:
        schema["items"] = resolve_ref(schema["items"]["$ref"])
    return schema

def extract_schema_example(schema, override_invalid=False, missing_required=False):
    if not schema:
        return {}
    if "allOf" in schema:
        res = {}
        for sub in schema["allOf"]:
            res.update(extract_schema_example(get_schema(sub), override_invalid, missing_required))
        return res
    
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    example = {}
    
    for prop_name, prop_details in props.items():
        if missing_required and prop_name in required:
            continue # skip to make it missing
            
        prop_details = get_schema(prop_details)
        prop_type = prop_details.get("type", "string")
        
        if override_invalid and prop_name in required:
            # Inject wrong type
            if prop_type == "integer": example[prop_name] = "invalid_int_string"
            elif prop_type == "string": example[prop_name] = 12345
            elif prop_type == "boolean": example[prop_name] = "not_a_bool"
            elif prop_type == "array": example[prop_name] = "not_an_array"
            else: example[prop_name] = None
        else:
            if "example" in prop_details:
                example[prop_name] = prop_details["example"]
            elif "default" in prop_details:
                example[prop_name] = prop_details["default"]
            elif prop_type == "string":
                if "format" in prop_details and prop_details["format"] == "date-time":
                    example[prop_name] = "2023-10-01T12:00:00Z"
                elif "format" in prop_details and prop_details["format"] == "email":
                    example[prop_name] = "test@example.com"
                else:
                    example[prop_name] = f"sample_{prop_name}"
            elif prop_type == "integer":
                example[prop_name] = 1
            elif prop_type == "number":
                example[prop_name] = 1.0
            elif prop_type == "boolean":
                example[prop_name] = True
            elif prop_type == "array":
                example[prop_name] = []
            elif prop_type == "object":
                example[prop_name] = {}
            else:
                example[prop_name] = "sample"
                
    return example

md_lines = []

md_lines.append("# CleanPlates Comprehensive API Testing Plan")
md_lines.append("")
md_lines.append("## Agent Instructions")
md_lines.append("You are an autonomous API testing agent. The user will ask you to **\"Execute round x\"**. When this happens:")
md_lines.append("1. Find the section for **Round x** below.")
md_lines.append("2. Execute all the defined API tests within that round against the local development server (or configured environment).")
md_lines.append("3. You may use `curl`, Python `requests`, or an HTTP client of your choice to execute these tests.")
md_lines.append("4. **Multiple Inputs & Outputs Validation**: For every endpoint, test the **Valid/Happy Path**, **Missing Parameters/Payload**, and **Invalid Data Types/Values**. Observe the outputs and ensure they match the expected response structures (e.g., `200 OK`, `422 Unprocessable Entity`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`).")
md_lines.append("5. Ensure you authenticate properly (obtain JWT via the auth endpoint) before testing secured endpoints.")
md_lines.append("6. **After completing a round**, you MUST generate a detailed markdown report (`round_x_test_report.md`).")
md_lines.append("   - This report must list: **Issues Discovered**, **Test Cases Passed**, **Test Cases Failed**, and **Suggested Fixes** with code snippets if applicable.")
md_lines.append("")

round_num = 1
for round_tags in rounds:
    md_lines.append(f"## Round {round_num}")
    md_lines.append(f"**Endpoints Covered:** {', '.join(round_tags)}")
    md_lines.append("")
    
    for tag in round_tags:
        md_lines.append(f"### Tag: {tag}")
        md_lines.append("")
        
        for path, method, details in groups[tag]:
            md_lines.append(f"#### `[{method.upper()}]` `{path}`")
            if "summary" in details:
                md_lines.append(f"**Summary:** {details['summary']}")
            md_lines.append("")
            
            # Extract Request Parameters (Path / Query)
            params = details.get("parameters", [])
            query_params = [p for p in params if p["in"] == "query"]
            path_params = [p for p in params if p["in"] == "path"]
            
            req_body_schema = {}
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    req_body_schema = get_schema(content["application/json"].get("schema", {}))
                elif "multipart/form-data" in content:
                    req_body_schema = get_schema(content["multipart/form-data"].get("schema", {}))
                    
            # Valid Case
            md_lines.append("**Test Case 1: Valid Input (Happy Path)**")
            if path_params:
                p_ex = {p["name"]: 1 if p.get("schema", {}).get("type") == "integer" else "string_id" for p in path_params}
                md_lines.append(f"- **Path Parameters**: `{json.dumps(p_ex)}`")
            if query_params:
                q_ex = {p["name"]: p.get("schema", {}).get("default", "val") for p in query_params}
                md_lines.append(f"- **Query Parameters**: `{json.dumps(q_ex)}`")
            if req_body_schema:
                body_ex = extract_schema_example(req_body_schema)
                md_lines.append("- **Request Body**:")
                md_lines.append("```json")
                md_lines.append(json.dumps(body_ex, indent=2))
                md_lines.append("```")
            md_lines.append("- **Expected Output**: `200 OK` or `201 Created` with expected response schema.")
            md_lines.append("")
            
            # Invalid Case - Missing Required
            md_lines.append("**Test Case 2: Missing Required Fields/Auth**")
            if req_body_schema and req_body_schema.get("required"):
                body_ex_missing = extract_schema_example(req_body_schema, missing_required=True)
                md_lines.append("- **Request Body (Missing Required)**:")
                md_lines.append("```json")
                md_lines.append(json.dumps(body_ex_missing, indent=2))
                md_lines.append("```")
                md_lines.append("- **Expected Output**: `422 Unprocessable Entity` (Validation Error)")
            else:
                md_lines.append("- **Action**: Perform request without Authorization header.")
                md_lines.append("- **Expected Output**: `401 Unauthorized`")
            md_lines.append("")
            
            # Invalid Case - Wrong Data Type
            if req_body_schema:
                md_lines.append("**Test Case 3: Invalid Data Types**")
                body_ex_invalid = extract_schema_example(req_body_schema, override_invalid=True)
                md_lines.append("- **Request Body (Invalid Types)**:")
                md_lines.append("```json")
                md_lines.append(json.dumps(body_ex_invalid, indent=2))
                md_lines.append("```")
                md_lines.append("- **Expected Output**: `422 Unprocessable Entity`")
                md_lines.append("")
                
            if path_params:
                md_lines.append("**Test Case 4: Not Found**")
                p_ex = {p["name"]: 99999 if p.get("schema", {}).get("type") == "integer" else "non_existent_id" for p in path_params}
                md_lines.append(f"- **Path Parameters**: `{json.dumps(p_ex)}`")
                md_lines.append("- **Expected Output**: `404 Not Found`")
                md_lines.append("")
                
    round_num += 1

with open('api_testing_plan.md', 'w') as f:
    f.write('\n'.join(md_lines))
    
print("Successfully generated api_testing_plan.md")
