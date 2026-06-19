# Multi-Site Enterprise Network

> A documented two-site enterprise network built in Cisco Packet Tracer — VLANs, inter-VLAN routing, 802.1Q trunking, Spanning Tree, and DHCP, extending to OSPF, NAT, and ACLs over a WAN, with Python tooling for config backup and auditing.

**Status:** Actively building — **Phases A–E complete** (switched + routed LAN fully operational across both sites). WAN routing (OSPF), NAT, ACLs, and Python automation in progress.

---

## Overview

This project designs, builds, and documents the network for a fictional company with two sites — a head office (**HQ**) and a **Branch** — joined over a WAN, with HQ providing shared internet access for both.

It's built from the ground up in Cisco Packet Tracer using a **design-first, layered methodology**: address everything on paper, then build bottom-up (Layer 2 → Layer 3 → routing → security), verifying at each layer before moving on. The aim is a realistic, defensible build rather than a tutorial clone — every decision (VLAN segmentation, /30 point-to-point links, deterministic root-bridge placement, ACL positioning) is intentional and documented.

## Skills demonstrated

- **Layer 2** — VLAN segmentation, 802.1Q trunking, VLAN pruning, Rapid PVST+ Spanning Tree with deliberate root-bridge selection, loop prevention across redundant links
- **Layer 3** — inter-VLAN routing with SVIs on multilayer switches, hierarchical IP subnetting (/24 user networks + /30 point-to-point links)
- **Services** — DHCP server pools with address exclusions and per-VLAN gateways
- **Routing** *(in progress)* — OSPFv2 single-area, default-route origination from the internet edge
- **Edge & security** *(in progress)* — NAT/PAT for internet access, standard and extended ACLs
- **Automation** *(planned)* — Python (Netmiko / Nornir) for config backup, compliance auditing, and Jinja2-based config templating
- **Operations** — structured `show`-command verification and layered, isolate-the-failing-layer troubleshooting

## Topology

```
                INTERNET
                   |
            [ R-ISP ]  198.51.100.10
                   | 203.0.113.0/30
      [ R-HQ ]===== WAN =====[ R-BR ]
     edge + NAT |                |
   10.255.0.0/30            10.255.0.4/30
     [ SW-HQ-Core ]        [ SW-BR-Core ]
     SVIs V10/V20/V99      SVIs V40/V99
     DHCP + OSPF           DHCP + OSPF
         /      \                |
    [HQ-A1]-tk-[HQ-A2]        [BR-A1]
       |         |               |
     PC-A      PC-B           PC-C
     V10       V20            V40
```

Redundant HQ trunks (`HQ-A1 — HQ-A2`) are managed by Spanning Tree, which blocks the loop. The `===` between R-HQ and R-BR is the WAN; `tk` = trunk.

*(For a more polished look, swap this block for the rendered diagram — save a screenshot as `docs/topology.png` and embed it with `![Network topology](docs/topology.png)`.)*

## Network design

### VLAN plan

| VLAN | Name        | Purpose                  | Site   |
|------|-------------|--------------------------|--------|
| 10   | HQ-Staff    | HQ general staff PCs     | HQ     |
| 20   | HQ-Sales    | HQ sales department PCs  | HQ     |
| 40   | BR-Staff    | Branch staff PCs         | Branch |
| 99   | Management  | Device management        | Both   |

### IP addressing plan

A hierarchical scheme — `10.<site>.<vlan>.0/24` for user networks, `10.255.0.x/30` for point-to-point links, so any address tells you where it lives.

| Network              | Subnet           | Gateway     | Notes                          |
|----------------------|------------------|-------------|--------------------------------|
| HQ-Staff (V10)       | 10.1.10.0/24     | 10.1.10.1   | DHCP to clients                |
| HQ-Sales (V20)       | 10.1.20.0/24     | 10.1.20.1   | DHCP to clients                |
| HQ-Mgmt (V99)        | 10.1.99.0/24     | 10.1.99.1   | static                         |
| BR-Staff (V40)       | 10.2.40.0/24     | 10.2.40.1   | DHCP to clients                |
| BR-Mgmt (V99)        | 10.2.99.0/24     | 10.2.99.1   | static                         |
| HQ-Core ↔ R-HQ       | 10.255.0.0/30    | —           | core .1, router .2             |
| BR-Core ↔ R-BR       | 10.255.0.4/30    | —           | core .5, router .6             |
| WAN R-HQ ↔ R-BR      | 10.255.0.8/30    | —           | R-HQ .9, R-BR .10              |
| Internet R-HQ ↔ ISP  | 203.0.113.0/30   | —           | R-HQ .2 (outside / NAT)        |

### Devices

| Device         | Model           | Role                                              |
|----------------|-----------------|---------------------------------------------------|
| SW-HQ-Core     | Catalyst 3650   | HQ L3 core — inter-VLAN routing, DHCP, OSPF       |
| SW-BR-Core     | Catalyst 3650   | Branch L3 core — inter-VLAN routing, DHCP, OSPF   |
| SW-HQ-A1 / A2  | Catalyst 2960   | HQ access layer                                   |
| SW-BR-A1       | Catalyst 2960   | Branch access layer                               |
| R-HQ           | ISR 2911        | HQ edge — WAN, internet, NAT/PAT                  |
| R-BR           | ISR 2911        | Branch edge                                       |
| R-ISP          | ISR 2911        | Simulated internet / ISP                          |

## Build phases

| Phase | Scope                                            | Status        |
|-------|--------------------------------------------------|---------------|
| A     | Hostnames, SSH, secure management baseline       | ✅ Complete    |
| B     | VLANs and access-port assignment                 | ✅ Complete    |
| C     | 802.1Q trunking and Rapid PVST+ Spanning Tree    | ✅ Complete    |
| D     | Inter-VLAN routing (`ip routing` + SVIs)         | ✅ Complete    |
| E     | DHCP server pools                                | ✅ Complete    |
| F     | WAN links + OSPF (inter-site routing)            | ⏳ In progress |
| G     | NAT/PAT for internet access                      | ⏳ Planned     |
| H     | Standard & extended ACLs                         | ⏳ Planned     |
| —     | Python automation (backup / audit / templating)  | ⏳ Planned     |

## Repository structure

```
multi-site-enterprise-network/
├── README.md
├── multi-site-enterprise-network.pkt    # the Cisco Packet Tracer file
├── configs/                             # exported running-configs (plain text, diffable)
│   ├── SW-HQ-Core.txt
│   ├── SW-BR-Core.txt
│   ├── SW-HQ-A1.txt
│   ├── SW-HQ-A2.txt
│   ├── SW-BR-A1.txt
│   └── ...
└── docs/
    ├── topology.png                     # network diagram
    └── build-guide.md                   # the why-first, phase-by-phase build walkthrough
```

## Opening the lab

1. Open `multi-site-enterprise-network.pkt` in **Cisco Packet Tracer 8.x**.
2. Device CLI login (lab only — not real credentials): user `admin`, password `Admin!Pass1`, enable secret `Enable!Pass1`.
3. Quick health check on a core switch:
   ```
   show ip interface brief        # SVIs up/up
   show interfaces trunk          # trunks carrying the right VLANs
   show spanning-tree vlan 10     # deterministic root, redundant links blocked
   show ip dhcp binding           # leased client addresses
   ```
4. End-to-end proof: a PC in VLAN 10 can `ping` a PC in VLAN 20 — traffic routed by the L3 core, confirming inter-VLAN routing, trunking, and DHCP all working together.

## Roadmap

- **Phase F — WAN + OSPF:** cable and configure the three routers, bring up the WAN link, and run single-area OSPF so HQ and Branch learn each other's networks and the internet default route.
- **Phase G — NAT/PAT:** translate the private LANs to a single public address at R-HQ for shared internet access.
- **Phase H — ACLs:** standard ACLs restricting management access, extended ACLs enforcing inter-VLAN/inter-site policy.
- **Automation:** rebuild the topology in GNS3/CML (real SSH), then add Python scripts to back up every device config, audit a security baseline, and generate access-switch configs from Jinja2 templates.

## Notes

This was built and debugged hands-on, including real troubleshooting — cabling mismatches, a stubborn EtherChannel (ultimately simplified to STP-managed redundant trunks after hitting Packet Tracer's LACP quirks), shut ports, and missing VLANs — diagnosed with `show cdp neighbors`, `show etherchannel summary`, `show interfaces status`, and layered `ping` testing. The build guide in `docs/` walks through the *why* behind every configuration decision, not just the commands.
