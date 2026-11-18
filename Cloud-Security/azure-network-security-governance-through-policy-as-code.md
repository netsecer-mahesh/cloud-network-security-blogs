---
layout: default
title: "Azure Network Security Governance through policy as code"
permalink: /cloud-security/azure-network-security-governance-through-policy-as-code/
---



# Azure Network Security Governance Through Policy as Code


### Why Azure Policy when we already have a stack of security solutions?

Azure Policy is not another security product in the stack; it is a governance layer that helps make the rest of the security stack more effective.

### How does it fit into the existing security stack?

We already have a stack of security solutions protecting our cloud environments — Defender for Cloud, WAF, firewalls, endpoint protection and many other cloud-native and third-party services. So why do we need Azure Policy? Doesn't Defender for Cloud already identify security risks? Doesn't a WAF protect our applications? They do, but they solve different problems. A WAF protects applications, Defender for Cloud provides security posture visibility and recommendations, and firewalls control network traffic. But who ensures that the underlying Azure resources are consistently configured in the first place? Who prevents an NSG from exposing management ports to the internet, or an unexpected public IP from being deployed? That's where Azure Policy comes in — not to replace existing security solutions, but to establish the guardrails that help prevent poor configurations from becoming security risks.

---
<br>
<br>

In this article, we will walk through building a foundational Azure network security governance baseline using Azure Policy.

In this article, we will explore how to:

- **Define five foundational security controls:** Govern restricted NSG inbound ports, public IP tagging, storage public access, subnet default routes and broad NSG CIDR rules.
- **Build a deployment pipeline:** Use JSON, Python and Azure CLI to deploy custom policy definitions and initiatives.
- **Group and assign policies:** Combine the five controls into a single initiative and assign it to the target Azure subscription.
- **Evaluate compliance:** Review Azure Policy compliance results and identify resources that require remediation.
- **Monitor the baseline:** Use Azure Resource Graph and KQL to query compliance, and extend visibility through Microsoft Defender for Cloud.

<br>
<br>

### Prerequisites

Before following the implementation, ensure you have:

- **Azure Subscription:** An active Azure subscription for deploying and testing Azure Policy.
- **Management Group Access:** Appropriate permissions to create policy definitions and initiatives at the target management group.
- **Azure CLI:** Installed and authenticated to the target Azure environment.
- **Python:** Python environment available to execute the policy deployment scripts.
- **Azure Resource Graph:** Access to query Azure Policy compliance data using KQL.
- **GitHub Repository:** A repository to maintain policy definitions, parameter files, initiatives and deployment scripts.

<br>
<br>

## Part 1 — Defining the Basic Network Security Hygiene Baseline

The objective is to establish a small set of foundational network security controls for Azure-native resources. Rather than attempting to address every possible security scenario, this MVP focuses on five practical controls that can be implemented through custom Azure Policy definitions, with configurable parameters and an audit-first enforcement approach.

| # | Custom policy / control | Framework alignment | Control lifecycle |
|---|---|---|---|
| 1 | **NSG – Restricted Inbound Ports**: Audit IPv4 inbound access to TCP 21, 22 and 3389. | NIST: AC-4, SC-7; CIS: Network Infrastructure Management; MCSB: NS-1 | **Audit → Review → Deny** |
| 2 | **Public IP – Approved Tag Governance**: Audit public IP resources without approved tags. | NIST: CM-6, CM-7; CIS: Secure Configuration; MCSB: NS-2 | **Audit → Tag approved resources → Deny** |
| 3 | **Storage – Public Access Governance**: Audit storage accounts with public network access enabled. | NIST: SC-7, AC-4; CIS: Data Protection; MCSB: DP-3 | **Audit → Review → Exempt approved resources → Deny** |
| 4 | **Subnet – Default Route Governance**: Audit subnet route-table association and default route pointing to approved Hub/NVA next-hop IPs. | NIST: SC-7, AC-4; CIS: Network Infrastructure Management; MCSB: NS-1 | **Audit → Review → Correct routing** |
| 5 | **NSG – CIDR Governance**: Identify overly broad `Any` source/destination definitions and replace them with approved company CIDRs. | NIST: AC-4, CM-6; CIS: Network Infrastructure Management; MCSB: NS-1 | **Audit → Review → Replace with approved CIDRs → Deny** |

*Note: Framework references are provisional, high-level mappings and should be validated against the relevant official framework catalogues before publication.*

### Implementing the baseline

Each control will be implemented as an independent custom Azure Policy definition. Configurable parameters will be used for values such as restricted ports, approved tags, company CIDRs and designated next-hop IPs.

We will begin with Audit to understand the existing environment and identify deviations. Based on the findings, we will review configurations, apply corrections and define legitimate exceptions using Azure Policy Exemptions. Where appropriate, controls will then progress to Deny enforcement.

The objective is not to introduce restrictions blindly, but to establish a consistent and measurable network security baseline that can be progressively enforced across the Azure environment.

### Policy Enforcement Lifecycle

<!-- DIAGRAM INSERTION POINT: Policy Enforcement Lifecycle -->

*The lifecycle follows a continuous improvement approach: audit, review findings, remediate or document approved exemptions, and progressively enforce controls. Compliance is monitored continuously, and exemptions remain subject to review rather than becoming permanent blind spots.*
<br>
<div class="policy-lifecycle-diagram">
  <img src="https://netsecer-mahesh.github.io/cloud-network-security-blogs/assets/images/Azure-Policy-Enforcement-Lifecycle.png"
       alt="Azure Policy Enforcement Lifecycle">
</div>
*The Azure Policy enforcement lifecycle follows a continuous improvement approach: audit existing configurations, review compliance findings, remediate deviations, document approved exemptions and progressively enforce security controls.*
<br>
<br>
<br>

## Part 2 — Building the Azure Policy Deployment Pipeline

Our implementation uses a simple combination of JSON, Python and Azure CLI. Policy definitions and initiatives are maintained as JSON files, while Python scripts handle deployment and validation.

### Deployment scope

Our current Azure hierarchy:


Tenant Root Group
       |
   MG-Foundation
       |
   sub-edge-sec


Both policy definitions and initiatives are deployed at `MG-Foundation`. Assignments are managed separately at the subscription scope.

### Policy Deployment Architecture

The following flow illustrates how custom policy definitions are deployed,
grouped into an initiative and assigned to the target subscription.


  <pre class="mermaid">
    ```mermaid
   flowchart TD
    A["Policy JSON<br/>Definitions and Parameters"]
    B["Python Deployment<br/>Azure CLI"]
    C["MG-Foundation<br/>Policy Definitions and Initiative"]
    D["INIT-001 — Network Security"]
    E["Subscription Assignment<br/>sub-edge-sec"]
  </pre>
  ``

<br>


Note - Policy definitions and initiatives are deployed at MG-Foundation, while
the initiative assignment is performed separately at subscription scope.

### Deployment scripts

We use two Python scripts:

- **deploy_policy.py** — Deploys individual custom policy definitions.
- **deploy_initiative.py** — Groups policy definitions into an initiative and deploys it.

Before deployment, the scripts validate the active Azure context, target management group, required JSON files and existing policy or initiative definitions. They also request confirmation before making changes.

### Implementation artifacts

The deployment package contains:

| Artifact | Purpose |
|---|---|
| Policy JSON | Custom policy definition |
| Policy parameters JSON | Configurable policy parameters |
| Initiative JSON | Groups individual policies |
| Initiative parameters JSON | Parameters used during initiative assignment |
| Python scripts | Deployment automation |



Explore the actual [deployment scripts and JSON artifacts](#artifact-reference).

The package has been tested locally and through Azure Cloud Shell. GitHub Actions and Terraform integration remain future enhancements.

---
<br>
<br>
<br>
<br>

## Part 3 — Implementing the Azure Network Security Baseline

With the five controls defined, the next step is to bring them together through Azure Policy. Each control is maintained as an independent JSON policy definition with configurable parameters. These policies are grouped into one initiative and assigned to `sub-edge-sec`.

### From definition to enforcement

**Define → Group → Assign → Evaluate**

- **Define:** Create five custom policy definitions and parameter files.
- **Group:** Combine them into `INIT-001 — Network Security`.
- **Assign:** Apply the initiative to the target subscription.
- **Evaluate:** Review compliance results and address non-compliant resources.

### Example — POL-001: NSG Restricted Inbound Ports

The policy checks IPv4 inbound NSG rules for TCP ports 21, 22 and 3389. It starts with Audit, allowing us to review existing configurations before moving towards Deny.

[View policy definition](#artifact-reference) | [View policy parameters](#artifact-reference)

### Deployment and compliance

Once assigned, Azure Policy evaluates the resources against the initiative. We review the compliance results, address findings and manage approved exemptions before introducing enforcement.

<!-- SCREENSHOT INSERTION POINT: Azure Policy initiative compliance results -->

### Explore the implementation

[Policy definitions](#artifact-reference) · [Policy parameters](#artifact-reference) · [Initiative JSON](#artifact-reference) · [Deployment scripts](#artifact-reference)

---
<br>
<br>
<br>
<br>

## Part 4 — Monitoring Network Security Compliance with KQL

With all five custom policies grouped under a single network security initiative, we need a consolidated view of how the assigned baseline is performing. Azure Resource Graph allows us to query Azure Policy compliance data using KQL.

### Query 1 — Initiative Compliance Overview

```KQL
PolicyResources
| where type =~ "microsoft.policyinsights/policystates"
| extend
    AssignmentName = tostring(properties.policyAssignmentName),
    State = tostring(properties.complianceState)
| where AssignmentName == "INIT-001-Network-Security"
| summarize
    Total = count(),
    Compliant = countif(State == "Compliant"),
    NonCompliant = countif(State == "NonCompliant")
```
  

**What it achieves**

Provides an overall compliance view of `INIT-001 — Network Security`, showing compliant and non-compliant policy-state records evaluated under the initiative.

### Query 2 — Initiative Compliance Findings

```KQL
PolicyResources
| where type =~ "microsoft.policyinsights/policystates"
| extend
    AssignmentName = tostring(properties.policyAssignmentName),
    Resource = tostring(properties.resourceId),
    Policy = tostring(properties.policyDefinitionName),
    State = tostring(properties.complianceState)
| where AssignmentName == "INIT-001-Network-Security"
| where State == "NonCompliant"
| project Resource, Policy, State
| order by Policy asc
```

**What it achieves**

Identifies non-compliant resources evaluated under the initiative, along with the policy responsible for each finding. This helps prioritize remediation.

### Bringing the results together

| Query | Purpose |
|---|---|
| Initiative overview | Understand overall network security baseline compliance. |
| Initiative findings | Identify resources requiring corrective action. |

The objective is to monitor the complete network security baseline through one initiative rather than maintaining separate compliance views for individual policies.

*Implementation note: Replace the example assignment name with the actual policy assignment resource name used in your environment. The overview counts policy-state records, which can include multiple records for a resource; it should not be interpreted as a unique-resource compliance percentage.*

---
<br>
<br>
<br>
<br>



## Extending Visibility with Microsoft Defender for Cloud

Azure Policy establishes the governance baseline, while Microsoft Defender for Cloud provides centralized security posture and compliance visibility.

Our `INIT-001 — Network Security` initiative can be mapped to a custom standard in Defender for Cloud. This allows the five custom network security controls to be monitored alongside other security and compliance requirements.

<!-- DIAGRAM INSERTION POINT: Azure Policy to Defender for Cloud integration -->

*From Azure Policy governance to centralized compliance visibility in Microsoft Defender for Cloud.*

<br>
<div class="policy-to-security-posture-diagram">
  <img src="https://netsecer-mahesh.github.io/cloud-network-security-blogs/assets/images/Azure-Policy-to-Stronger-Security.png"
       alt="Policy to Security-Posture">
</div>
*Azure Policy establishes the governance baseline, while Microsoft Defender for Cloud extends visibility through centralized security posture and compliance monitoring.*
<br>

### What does this give us?

- **Centralized visibility:** View the initiative's compliance status through Defender for Cloud.
- **Compliance tracking:** Identify compliant and non-compliant resources across the network security baseline.
- **Improved security posture:** Use Defender recommendations to identify and remediate additional security gaps.

**An important distinction:** Mapping a custom initiative to Defender for Cloud does not directly increase Secure Score. Secure Score improvements depend on remediating applicable Defender recommendations. Custom initiative compliance and Secure Score are separate measurements.

---

## Artifact Reference

---
<h3 id="artifact-reference">Artifact Reference</h3>

<table>
  <thead>
    <tr>
      <th>Artifact</th>
      <th>Description</th>
      <th>Repository Link</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Custom Policy Definition</td>
      <td>NSG Restricted Inbound Ports</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/POL-001-NSG-Restricted-Inbound-Ports_policy.json" target="_blank">View JSON</a></td>
    </tr>
    <tr>
      <td>Policy Parameters</td>
      <td>Restricted inbound ports configuration</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/POL-001-NSG-Restricted-Inbound-Ports_policy_parameters.json" target="_blank">View JSON</a></td>
    </tr>
    <tr>
      <td>Initiative Definition</td>
      <td>Network Security Initiative</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/INIT-001-network-security_initiative.json" target="_blank">View JSON</a></td>
    </tr>
    <tr>
      <td>Initiative Assignment Parameters</td>
      <td>Initiative assignment configuration</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/INIT-001-network-security_initiative_parameters.json" target="_blank">View JSON</a></td>
    </tr>
    <tr>
      <td>Policy Deployment Script</td>
      <td>Deploys custom policy definitions</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/deploy_policy.py" target="_blank">View Python Script</a></td>
    </tr>
    <tr>
      <td>Initiative Deployment Script</td>
      <td>Groups and deploys policy initiatives</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/deploy_initiative.py" target="_blank">View Python Script</a></td>
    </tr>
    <tr>
      <td>Policy Inventory</td>
      <td>Other Policies and policy parameter inventory</td>
      <td><a href="https://github.com/netsecer-mahesh/cloud-network-security-blogs/blob/main/Cloud-Security/artifacts/Policy_definations" target="_blank">View Policy Inventory</a></td>
    </tr>
  </tbody>
</table>

## Closing Thoughts

Azure Policy provides a practical way to move from individual security controls to a consistent governance baseline. By defining controls as code, grouping them into initiatives and progressively enforcing them, we can make security requirements repeatable and measurable across Azure environments.

Combining Azure Policy with Azure Resource Graph and Microsoft Defender for Cloud adds visibility into compliance and security posture, helping teams identify gaps, prioritize remediation and continuously improve their cloud security baseline.

This is a starting point — the same approach can be extended to additional governance domains, policy initiatives and automated deployment pipelines as the Azure environment evolves.
