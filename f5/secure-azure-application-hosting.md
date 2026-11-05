---
layout: default
title: "Secure Azure Application Hosting Using F5 and Palo Alto Firewalls"
permalink: /f5/secure-azure-application-hosting/
---

# Secure Azure Application Hosting Using F5 and Palo Alto Firewalls

## 1. Introduction

Hosting business-critical applications in the cloud requires more than simply exposing an application through a public endpoint. The architecture must provide controlled traffic flow, application-layer protection, network security enforcement and resilient application delivery.

This article explores an Azure application-hosting architecture integrating F5 load balancers with Palo Alto Networks firewalls. It demonstrates how Azure-native load balancing, firewall NAT and F5 application delivery can work together to provide a layered security architecture.

## 2. Architecture Overview 

The solution uses the following components:

- **Web Application Firewall (WAF):** Imperva or F5 Distributed Cloud (XC) provides the external web application protection layer.
- **Azure Public Load Balancer (Untrust-LB):** Receives incoming traffic and translates the destination port from TCP 443 to TCP 8801.
- **Palo Alto Networks Firewall:** Enforces network security policies and performs destination NAT.
- **Azure Internal Load Balancer (F5-LB):** Distributes traffic to the F5 load-balancer pair. Floating IP is enabled.
- **F5 Load Balancers:** Provide application delivery and forward requests to the backend Web Application Servers (WAS).
- **Backend Services:** Application servers communicate with database and storage services within the application VNet.

### 2.1 High-Level Architecture Diagram (HLD)  
<img width="1144" height="4046" alt="mermaid-diagram (1)" src="https://github.com/user-attachments/assets/fa2660bc-35d9-4e49-80a6-a8d8126c2433" />




The application components are hosted within the Azure VNet:

`cls-prd-ext-app-vnet01`

## 3. End-to-End Traffic Flow
## 3.1 Low-Level Design (LLD)

The following diagram illustrates the complete traffic path, network boundaries, load-balancing configuration, firewall NAT and backend connectivity.

![Azure F5 Palo Alto Application Hosting LLD](https://netsecer-mahesh.github.io/cloud-network-security-blogs/assets/images/azure-f5-paloalto-lld.png)

*Figure 1: Azure application hosting LLD – F5 and Palo Alto integration.*

---
### Step 1 – External Access and WAF Protection

Users access the application through a browser or mobile device. Incoming web traffic first passes through the WAF layer, where applicable web application security controls are enforced.

### Step 2 – Azure Public Load Balancer

After WAF inspection, traffic reaches the Azure public load balancer named `Untrust-LB`.

The load-balancing rule performs port translation:

| Source / Destination | Port |
|---|---:|
| Incoming HTTPS | 443 |
| Forwarded to firewall | 8801 |

The translated traffic is forwarded to the Palo Alto firewall's internet-facing interface.

### Step 3 – Palo Alto Firewall Inspection and NAT

The Palo Alto firewall enforces the applicable security policies and performs destination NAT.

The destination is translated to the private IP address hosted on the Azure internal load balancer named `F5-LB`.

This ensures that traffic is directed through the intended firewall security boundary before reaching the application delivery layer.

### Step 4 – Azure Internal Load Balancer

The internal load balancer `F5-LB` receives the translated traffic.

Its configuration includes:

- Floating IP enabled.
- A backend pool containing the two F5 load balancers in the HA pair.
- A load-balancing rule translating TCP 8801 to TCP 443.

This allows the F5 application delivery layer to receive HTTPS traffic on its expected service port.

### Step 5 – F5 Application Delivery

The F5 load balancers process incoming application traffic and provide the configured application delivery functions.

The F5 layer forwards requests to the backend Web Application Servers (WAS), providing a controlled path between the external access layer and the application tier.

### Step 6 – Backend Application Connectivity

The WAS servers communicate with the required backend services, including database and storage services, within the application VNet.

This separates external access, application delivery and backend service connectivity into distinct architectural layers.

## 4. Port Translation Summary

The following table summarizes the port translations described in this architecture.

| Traffic stage | Port |
|---|---:|
| External HTTPS access | TCP 443 |
| Public LB to Palo Alto | TCP 8801 |
| Palo Alto to internal LB | TCP 8801 |
| Internal LB to F5 | TCP 443 |

Port translation at the Azure load-balancing layers allows the firewall-facing and application-facing service ports to differ while maintaining the intended traffic path.

## 5. Security and Availability Considerations

Several design considerations are important when implementing this architecture.

**Layered security enforcement**

The WAF and Palo Alto firewall serve different security purposes. The WAF focuses on web application protection, while the firewall enforces network-level security policies and NAT.

**Controlled traffic path**

External application traffic follows the intended path through the WAF, Azure public load balancer, Palo Alto firewall, internal load balancer and F5 application delivery layer.

**F5 high availability**

The F5 deployment uses a two-device HA pair. The Azure internal load-balancer configuration and F5 HA design must be validated together to ensure traffic reaches the active service instance as intended.

**Backend segmentation**

Application servers, database services and storage should have appropriately scoped network access. Only required communication flows should be permitted.

## 6. Validation and Testing

Before production deployment, validate the following:

- External HTTPS access through the WAF.
- Public load-balancer port translation.
- Palo Alto NAT and security policy matching.
- Internal load-balancer backend health and Floating IP configuration.
- F5 application availability and HA behaviour.
- WAS connectivity to database and storage services.
- Application availability during an F5 failover event.
- End-to-end connectivity after failover.

Actual failover behaviour should be confirmed through testing rather than assumed from the presence of an HA pair.

## 7. Architecture Takeaways

This design demonstrates how native Azure networking services can be integrated with enterprise firewall and application delivery platforms.

The key architectural principle is the separation of responsibilities:

- WAF for web application protection.
- Azure Load Balancer for traffic distribution and port translation.
- Palo Alto for network security enforcement and NAT.
- F5 for application delivery and high availability.
- Backend services for application data and storage.

A well-defined traffic path, clear security boundaries and coordinated failover design are essential when deploying enterprise applications in Azure.

---

*Cloud Network & Security Architecture \ F5 \ Azure \ Palo Alto*

