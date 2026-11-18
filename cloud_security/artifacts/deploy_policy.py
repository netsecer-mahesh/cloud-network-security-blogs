
from pathlib import Path
import json
import argparse
import subprocess
import tempfile



PROJECT_ROOT = Path(__file__).resolve().parent





# ============================================================
# SECTION 1: AZURE CONTEXT VALIDATION
# Purpose: Verify the active Azure subscription and confirm access to the target Management Group.
# ============================================================

parser = argparse.ArgumentParser()
parser.add_argument("--policy-name", required=True)
parser.add_argument("--management-group", required=True)
args = parser.parse_args()

az_command_path = ["az"]

def run_az_command(command):
    full_command = az_command_path + command
    result = subprocess.run(
        full_command,
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    if result.returncode != 0:
        raise SystemExit(f"Azure CLI command failed: {result.stderr}")
    return result

account_result = run_az_command(["account", "show", "--output", "json"])
account_details = json.loads(account_result.stdout)

print("\nActive Azure Subscription:", account_details.get("name"))
confirm_account = input("Confirm active subscription? (yes/no): ").strip().lower()
if confirm_account != "yes":
    raise SystemExit("Active subscription not confirmed. Deployment stopped.")

management_group = args.management_group

mg_result = run_az_command([
    "account", "management-group", "show",
    "--name", management_group,
    "--output", "json"
])
mg_details = json.loads(mg_result.stdout)

print("\nTarget Management Group:", mg_details.get("displayName"))
confirm_mg = input("Confirm target Management Group? (yes/no): ").strip().lower()
if confirm_mg != "yes":
    raise SystemExit("Management Group not confirmed. Deployment stopped.")

print("[SUCCESS] Azure context validation completed.")


# ============================================================
# SECTION 2: POLICY FILE VALIDATION
# Purpose: Identify and validate the policy definition and parameter files.
# ============================================================

selected_policy_definition_path = (
    PROJECT_ROOT / f"{args.policy_name}_policy.json"
)

selected_parameter_path = (
    PROJECT_ROOT / f"{args.policy_name}_policy_parameters.json"
)

if not selected_policy_definition_path.is_file():
    raise SystemExit("Policy definition file not found. Deployment stopped.")

if not selected_parameter_path.is_file():
    raise SystemExit("Policy parameter file not found. Deployment stopped.")

print("[SUCCESS] Policy files validated successfully.")

# ============================================================
# SECTION 3: POLICY JSON LOADING
# Purpose: Load the policy definition and assignment parameter JSON files.
# ============================================================

def load_policy_definition(policy_definition_path):
    with open(policy_definition_path, "r") as policy_file:
        policy_definition = json.load(policy_file)
    return policy_definition

def load_parameter_file(parameter_path):
    with open(parameter_path, "r") as parameter_file:
        parameters = json.load(parameter_file)
    return parameters

Policy_definition = load_policy_definition(selected_policy_definition_path)
Parameters = load_parameter_file(selected_parameter_path)

print("[SUCCESS] Policy JSON files loaded successfully.")

# ============================================================
# SECTION 4: AZURE POLICY LOOKUP
# Purpose: Check whether the selected policy definition already exists at the Management Group scope.
# ============================================================

def identify_policy(policy_name, management_group):
    policy_lookup_command = [
        "policy", "definition", "list",
        "--management-group", management_group,
        "--query",
        f"[?displayName=='{policy_name}'].{{Name:name, DisplayName:displayName, ID:id, Type:policyType}}",
        "--output", "json"
    ]
    command_result = run_az_command(policy_lookup_command)
    existing_policies = json.loads(command_result.stdout)
    return existing_policies

existing_policy = identify_policy(args.policy_name, args.management_group)

print("[SUCCESS] Azure policy lookup completed.")

# ============================================================
# SECTION 5: POLICY DEPLOYMENT
# Purpose: Prepare temporary JSON files and deploy the custom policy definition to Azure.
# ============================================================

def push_policy(policy_name, management_group):
    policy_definition_file = load_policy_definition(selected_policy_definition_path)
    policy_rule = policy_definition_file["properties"]["policyRule"]
    policy_parameters = policy_definition_file["properties"]["parameters"]
    
    temp_files = []

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as rules_file:
            json.dump(policy_rule, rules_file)
        rules_path = rules_file.name
        temp_files.append(rules_path)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", encoding="utf-8", delete=False
        ) as params_file:
            json.dump(policy_parameters, params_file)
        params_path = params_file.name
        temp_files.append(params_path)

        policy_create_command = [
            "policy", "definition", "create",
            "--name", policy_name,
            "--management-group", management_group,
            "--display-name", policy_name,
            "--description", "Temporary NSG audit policy for deployment testing",
            "--mode", "All",
            "--rules", f"@{rules_path}",
            "--params", f"@{params_path}",
            "--output", "json"
        ]

        command_result = run_az_command(policy_create_command)
        return command_result
    finally:
        for path in temp_files:
            Path(path).unlink(missing_ok=True)


if len(existing_policy) == 0:
    confirm_deployment = input("Proceed with policy deployment? (yes/no): ").strip().lower()
    if confirm_deployment != "yes":
        raise SystemExit("Deployment not confirmed. Deployment stopped.")

    deployed_policy = push_policy(args.policy_name, args.management_group)
    print("[SUCCESS] Policy deployment completed successfully.")

elif len(existing_policy) == 1:
    raise SystemExit("Policy already exists. Existing-policy workflow not implemented.")
else:
    raise SystemExit("Multiple matching policies found. Deployment stopped.")
