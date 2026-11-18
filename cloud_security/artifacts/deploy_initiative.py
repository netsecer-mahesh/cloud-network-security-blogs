
# ============================================================
# SECTION 1: IMPORTS AND PROJECT INITIALIZATION
# Purpose: Import required libraries and identify policy and initiative directories.
# ============================================================

from pathlib import Path
import json
import argparse
import subprocess
import tempfile
import shutil

ROOT = Path(__file__).resolve().parent

AZ = shutil.which("az") or "az"

print("[SUCCESS] Project initialization completed.")

# ============================================================
# SECTION 2: INPUT AND DEPLOYMENT SCOPE
# Purpose: Collect initiative name, policy name and target Management Group.
# ============================================================

parser = argparse.ArgumentParser()
parser.add_argument("--initiative-name", required=True)
parser.add_argument("--policy-name", required=True)
parser.add_argument("--management-group", required=True)

args = parser.parse_args()

management_group = args.management_group

print("[SUCCESS] Deployment inputs collected.")

# ============================================================
# SECTION 3: AZURE CONTEXT AND SCOPE VALIDATION
# Purpose: Validate active Azure subscription and target Management Group access.
# ============================================================

def run_az(command):
    result = subprocess.run(
        [AZ] + command,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    if result.returncode != 0:
        raise SystemExit(f"Azure CLI command failed: {result.stderr}")

    return result

# Retrieve active Azure context

context_result = run_az([
    "account", "show",
    "--output", "json"
])

context = json.loads(context_result.stdout)

tenant_id = context.get("tenantId")
subscription_name = context.get("name")
subscription_id = context.get("id")

if not tenant_id or not subscription_id:
    raise SystemExit("Unable to identify active Azure context.")

print("\nActive Azure Subscription:", subscription_name)

confirmation = input(
    "Confirm active subscription? (yes/no): "
).strip().lower()

if confirmation != "yes":
    raise SystemExit("Deployment aborted by user.")

# Validate Management Group existence and access

mg_result = run_az([
    "account", "management-group", "show",
    "--name", management_group,
    "--output", "json"
])

mg_details = json.loads(mg_result.stdout)

print("\nTarget Management Group:", mg_details.get("displayName"))

confirmation = input(
    "Confirm target Management Group? (yes/no): "
).strip().lower()

if confirmation != "yes":
    raise SystemExit("Deployment aborted by user.")

# Final deployment scope confirmation

confirmation = input(
    "\nProceed with initiative deployment? (yes/no): "
).strip().lower()

if confirmation != "yes":
    raise SystemExit("Deployment aborted by user.")

print("[SUCCESS] Azure context validation completed.")


# ============================================================
# SECTION 4: INITIATIVE AND POLICY FILE VALIDATION
# Purpose: Identify and validate the initiative and policy definition files.
# ============================================================

policy_file = (
    ROOT / f"{args.policy_name}_policy.json"
)

initiative_file = (
    ROOT / f"{args.initiative_name}_initiative.json"
)



if not initiative_file.is_file():
    raise SystemExit("Initiative definition file not found.")

if not policy_file.is_file():
    raise SystemExit("Policy definition file not found.")

print("[SUCCESS] Initiative and policy files validated.")

# ============================================================
# SECTION 5: JSON LOADING AND DYNAMIC INITIATIVE GENERATION
# Purpose: Load JSON definitions and dynamically generate policy references and parameter mappings.
# ============================================================

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot load {path}: {error}")

initiative = load_json(initiative_file)
policy = load_json(policy_file)

initiative_properties = initiative.get("properties")
policy_properties = policy.get("properties")

if not isinstance(initiative_properties, dict):
    raise SystemExit("Invalid initiative properties.")

if not isinstance(policy_properties, dict):
    raise SystemExit("Invalid policy properties.")

policy_parameters = policy_properties.get("parameters", {})

if not isinstance(policy_parameters, dict):
    raise SystemExit("Invalid policy parameter definitions.")

policy_id = (
    f"/providers/Microsoft.Management/managementGroups/{management_group}"
    f"/providers/Microsoft.Authorization/policyDefinitions/{args.policy_name}"
)

parameter_definitions = {}
parameter_mappings = {}

for name, definition in policy_parameters.items():

    parameter_definitions[name] = definition

    parameter_mappings[name] = {
        "value": f"[parameters('{name}')]"
    }

initiative_properties["policyDefinitions"] = [{
    "policyDefinitionReferenceId": args.policy_name,
    "policyDefinitionId": policy_id,
    "parameters": parameter_mappings
}]

initiative_properties["parameters"] = parameter_definitions

print("[SUCCESS] Initiative definition generated successfully.")

# ============================================================
# SECTION 6: AZURE CLI COMMAND EXECUTION
# Purpose: Verify that the referenced policy definition exists at the target Management Group.
# ============================================================

run_az([
    "policy", "definition", "show",
    "--name", args.policy_name,
    "--management-group", management_group,
    "--output", "json"
])

print("[SUCCESS] Policy definition validated successfully.")

# ============================================================
# SECTION 7: EXISTING INITIATIVE IDENTIFICATION
# Purpose: Check whether the initiative already exists at the target Management Group.
# ============================================================

result = run_az([
    "policy", "set-definition", "list",
    "--management-group", management_group,
    "--query", f"[?name=='{args.initiative_name}']",
    "--output", "json"
])

try:
    existing = json.loads(result.stdout)

except json.JSONDecodeError:
    raise SystemExit("Could not parse initiative lookup response.")

print("[SUCCESS] Azure initiative lookup completed.")

# ============================================================
# SECTION 8: INITIATIVE DEFINITION DEPLOYMENT
# Purpose: Prepare temporary JSON files and create the initiative using Azure CLI.
# ============================================================

def deploy_initiative():

    properties = initiative["properties"]
    temp_files = []

    def temp_json(data):

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
            encoding="utf-8"
        ) as file:

            json.dump(data, file, indent=4)
            temp_files.append(file.name)

            return file.name

    try:

        definitions = temp_json(properties["policyDefinitions"])
        parameters = temp_json(properties.get("parameters", {}))
        metadata = temp_json(properties.get("metadata", {}))
        groups = temp_json(properties.get("policyDefinitionGroups", []))

        command = [
            "policy", "set-definition", "create",
            "--name", args.initiative_name,
            "--management-group", management_group,
            "--display-name", properties.get(
                "displayName", args.initiative_name
            ),
            "--description", properties.get("description", ""),
            "--definitions", f"@{definitions}",
            "--params", f"@{parameters}",
            "--metadata", f"@{metadata}",
            "--definition-groups", f"@{groups}",
            "--output", "json"
        ]

        if properties.get("version"):
            command.extend([
                "--version",
                str(properties["version"])
            ])

        run_az(command)

    finally:

        for path in temp_files:
            Path(path).unlink(missing_ok=True)

# ============================================================
# SECTION 9: DEPLOYMENT CONTROLLER
# Purpose: Prevent duplicate initiative creation and execute deployment when no existing initiative is found.
# ============================================================

if existing:

    raise SystemExit(
        "Initiative already exists. Existing-initiative workflow not implemented."
    )

deploy_initiative()

print("[SUCCESS] Initiative deployment completed successfully.")
