---
layout: post
title: "Secure Azure Application Hosting Using Azure Front Door, FortiGate and Application Gateway"
date: 2026-11-05
categories: [Azure Networking, Cloud Security, Fortinet, Architecture]
---

# Secure Azure Application Hosting Using Azure Front Door, FortiGate and Application Gateway

## 1. Introduction

Securing application hosting in Microsoft Azure requires multiple layers of protection, including edge security, network-level inspection, application-layer routing and backend segmentation.

This architecture demonstrates an application hosting design using:

- **Azure Front Door (AFD):** Global application entry point, edge WAF protection and traffic acceleration.
- **Fortinet FortiGate NGFW:** Centralized network security inspection, firewall policy enforcement and destination NAT.
- **Azure Application Gateway:** Internal Layer 7 application delivery, HTTP/S routing and backend load balancing.
- **Azure Web Application Servers:** Hosting the application workloads.
- **Backend Services:** Database and storage services.

The design separates internet-facing application access from internal application workloads while providing centralized network security controls.

## 2. Architecture Overview

### 2.1 High-Level Architecture Diagram (HLD)

![Azure Front Door FortiGate Application Gateway HLD](../assets/images/azure-afd-fortigate-appgw-hld.png)

[View full-size HLD diagram](../assets/images/azure-afd-fortigate-appgw-hld.png)

The architecture follows a hub-and-spoke model:

- Azure Front Door provides the global entry point.
- FortiGate provides network-level security inspection in the hub VNet.
- Application Gateway provides internal application delivery in the application spoke VNet.
- Web, application and data workloads are segmented into separate subnets.

### 2.2 Low-Level Design Diagram (LLD)

![Azure Front Door FortiGate Application Gateway LLD](../assets/images/azure-afd-fortigate-appgw-lld.png)

[View full-size LLD diagram](../assets/images/azure-afd-fortigate-appgw-lld.png)

The LLD illustrates the subnet boundaries, traffic direction, network interfaces, listener configuration, firewall policies and backend connectivity.

*Note: Network ranges and subnet allocations shown in architecture diagrams are illustrative and must be replaced with the actual deployment values.*

## 3. Architecture Components

### 3.1 Azure Front Door

Azure Front Door acts as the global application entry point.

Key responsibilities:

- Global application delivery and traffic acceleration.
- Web Application Firewall (WAF) policy enforcement.
- TLS termination or end-to-end TLS, depending on the selected design.
- Origin health monitoring.
- Routing requests to the configured origin.
- Restricting origin access to authorized Front Door traffic.

Azure Front Door Standard or Premium can be selected based on the required feature set. Premium is relevant when Private Link connectivity to supported origins is required.

### 3.2 Fortinet FortiGate NGFW

FortiGate is deployed in the hub VNet to provide centralized network security inspection.

Key responsibilities:

- Stateful firewall inspection.
- Security policy enforcement.
- Source and destination NAT, where required.
- Application and threat inspection.
- Controlled connectivity between hub and spoke networks.
- Centralized logging and security monitoring.

For production high availability, a FortiGate active/passive deployment can be considered, subject to the selected Azure deployment model and failover design.

### 3.3 Azure Application Gateway

Application Gateway is deployed in the application VNet and acts as the internal Layer 7 application delivery component.

Key responsibilities:

- HTTP/HTTPS listener configuration.
- Host-based and path-based routing.
- Backend pool management.
- Health probes.
- TLS termination or end-to-end TLS.
- Web Application Firewall protection, if the Application Gateway WAF SKU is selected.

Application Gateway provides application-layer routing between incoming requests and the backend web application servers.

### 3.4 Application and Backend Tiers

The application spoke contains the workload subnets:

- **Web Tier:** Web-facing application workloads.
- **Application Tier:** Application processing services, where applicable.
- **Data Tier:** Database services and associated backend resources.

Network Security Groups and FortiGate policies should enforce the required communication paths between these tiers.

## 4. End-to-End Traffic Flow

The following describes the intended inbound request path.

**Step 1 – User to Azure Front Door**

External users access the application using HTTPS over TCP 443.

Azure Front Door receives the request and applies the configured edge security and WAF policies.

**Step 2 – Azure Front Door to FortiGate**

Azure Front Door forwards the request to its configured FortiGate origin endpoint over HTTPS.

The origin must be reachable from Azure Front Door. Where a public FortiGate endpoint is used, restrict inbound access to authorized Front Door traffic and validate the expected Front Door identity.

**Step 3 – FortiGate Security Inspection**

FortiGate receives the request and applies the configured security policies.

Depending on the design, FortiGate performs destination NAT to the private frontend IP of the Application Gateway.

The firewall policy must permit only the required source, destination and service combinations.

**Step 4 – FortiGate to Application Gateway**

The translated traffic is forwarded to the Application Gateway frontend over the configured listener port, typically TCP 443.

Routing between the hub and application spoke must be configured to support the required connectivity.

**Step 5 – Application Gateway to Web Application Servers**

Application Gateway evaluates the HTTP/S request and forwards it to the appropriate backend pool.

Backend health probes determine whether the application instances are available to receive traffic.

**Step 6 – Application to Backend Services**

Web and application workloads communicate with database and storage services using explicitly permitted application ports.

Access should be restricted according to workload requirements.

## 5. Port and Traffic Translation Summary

The following is an illustrative traffic mapping for an HTTPS-based deployment.

| Traffic stage | Incoming port | Forwarded port |
|---|---:|---:|
| User to Azure Front Door | 443 | 443 |
| Azure Front Door to FortiGate origin | 443 | 443 |
| FortiGate DNAT to Application Gateway | 443 | 443 |
| Application Gateway to web servers | 443 | Application-defined |
| Web/application tier to database | Application-defined | Application-defined |

Actual port translation depends on the listener, NAT and backend configurations.

## 6. Security Design Considerations

### 6.1 Edge Security

- Configure Azure Front Door WAF policies.
- Use HTTPS for client-to-edge and origin connectivity.
- Restrict direct access to the origin.
- Validate the expected Front Door identifier at the origin.
- Configure appropriate TLS certificates and minimum TLS versions.

### 6.2 Network Security

- Deploy FortiGate in the hub security VNet.
- Use explicit firewall policies for inbound and outbound traffic.
- Restrict access between hub and spoke networks.
- Use UDRs where traffic must traverse FortiGate.
- Validate routing symmetry, especially when NAT is involved.

### 6.3 Application Security

- Configure Application Gateway listeners and backend pools.
- Use health probes to monitor application availability.
- Apply WAF policies at Application Gateway if additional application-layer inspection is required.
- Restrict backend access to the Application Gateway subnet and approved application sources.

### 6.4 Backend Segmentation

- Separate web, application and data workloads.
- Use NSGs to enforce subnet-level access controls.
- Permit only required application-to-database connectivity.
- Avoid unrestricted communication between workload tiers.

## 7. High Availability and Resilience

High availability must be considered across each architecture layer.

- **Azure Front Door:** Global edge service with origin health monitoring and routing capabilities.
- **FortiGate:** Active/passive HA can be implemented using an Azure-supported deployment model.
- **Application Gateway:** Use an appropriate SKU and zone-redundant configuration where supported and required.
- **Application workloads:** Deploy multiple backend instances where application design supports it.
- **Backend services:** Implement service-specific availability and recovery mechanisms.

High availability should be validated through controlled failover and application connectivity testing rather than assumed from component deployment alone.

## 8. Validation and Testing

The following tests should be completed before production rollout.

| Test area | Validation |
|---|---|
| Azure Front Door | Confirm HTTPS access and WAF policy enforcement |
| Origin security | Verify only authorized Front Door traffic can reach the origin |
| FortiGate | Validate firewall policies, NAT and traffic logs |
| Hub-spoke routing | Verify forward and return traffic paths |
| Application Gateway | Validate listeners, routing rules and backend health |
| Application tier | Confirm application availability and backend connectivity |
| Database/storage | Verify only approved workloads can access backend services |
| HA | Test FortiGate failover and application recovery, where implemented |
| Monitoring | Confirm logs, alerts and health monitoring |

## 9. Troubleshooting Guide

**Azure Front Door cannot reach the origin**

- Verify origin hostname/IP and port.
- Check origin health status.
- Validate FortiGate inbound policies.
- Confirm the origin permits authorized Front Door traffic.

**FortiGate receives traffic but Application Gateway is unreachable**

- Review DNAT and firewall policies.
- Validate hub-spoke peering.
- Check UDRs and effective routes.
- Verify the Application Gateway frontend and listener configuration.
- Confirm return-path routing.

**Application Gateway reports unhealthy backend servers**

- Review backend pool configuration.
- Validate health probe settings.
- Check NSGs and application listener ports.
- Confirm backend application health.

**Application is reachable but backend services fail**

- Review application-to-database and application-to-storage policies.
- Validate DNS resolution.
- Check NSGs, routing and service-side access controls.

## 10. Architecture Takeaways

This architecture combines three distinct security and delivery layers:

1. **Azure Front Door:** Global edge security and application delivery.
2. **Fortinet FortiGate:** Network security inspection and controlled traffic forwarding.
3. **Azure Application Gateway:** Internal Layer 7 application routing and backend load balancing.

The hub-and-spoke model provides centralized network security while maintaining workload separation within the application environment.

The result is a layered Azure application hosting design that combines global edge protection, centralized network security and internal application delivery.

---

*Practical engineering \ Cloud Security \ Azure Networking \ Architecture & Design*
