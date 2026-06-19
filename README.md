# Multi-Site Enterprise Network

![Network Config Audit](https://github.com/samuelsaad/multi-site-enterprise-network/actions/workflows/network-audit.yml/badge.svg)

> A documented two-site enterprise network built in Cisco Packet Tracer — VLANs, inter-VLAN routing, 802.1Q trunking, Spanning Tree, DHCP, OSPF, NAT, and ACLs — paired with a small Python NetDevOps toolkit that generates device configs from a data model and audits them against a security baseline in CI.

**Status:** ✅ **Complete** — network built and verified end-to-end across both sites; automation (config generation + compliance auditing) in place and running in CI.


---

## Overview

This project designs, builds, documents, and automates the network for a fictional company with two sites — a head office (**HQ**) and a **Branch** — joined over a WAN, with HQ providing shared internet access for both.

The network is built from the ground up using a **design-first, layered methodology**: address everything on paper, then build bottom-up (Layer 2 → Layer 3 → routing → security), verifying at each step. On top of that sits an **infrastructure-as-code** layer: the access-switch configs can be generated from a single source of truth, and every config is checked against a security baseline automatically on each commit.

## Skills demonstrated

- **Layer 2** — VLAN segmentation, 802.1Q trunking, VLAN pruning, Rapid PVST+ Spanning Tree with deliberate root-bridge selection, loop prevention across redundant links
- **Layer 3** — inter-VLAN routing with SVIs on multilayer switches, hierarchical IP subnetting (/24 user networks + /30 point-to-point links)
- **Services** — DHCP server pools with address exclusions and per-VLAN gateways
- **Routing** — OSPFv2 single-area, default-route origination from the internet edge, passive-interface hardening on host-facing links
- **Edge & security** — NAT/PAT (overload) for shared internet access, a standard ACL restricting management (vty) access to the management subnets, an extended ACL enforcing inter-VLAN policy
- **Automation & IaC** — Python + Jinja2 generating device configs from a YAML source of truth (consistent, drift-free)
- **Tooling & CI** — a Python compliance auditor checking configs against a security baseline, run automatically on every push via GitHub Actions

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

`tk` = trunk; the `HQ-A1 — HQ-A2` link is a redundant trunk that Spanning Tree blocks to prevent a loop.

## Network design

### VLAN plan

| VLAN | Name        | Purpose                  | Site   |
|------|-------------|--------------------------|--------|
| 10   | HQ-Staff    | HQ general staff PCs     | HQ     |
| 20   | HQ-Sales    | HQ sales department PCs  | HQ     |
| 40   | BR-Staff    | Branch staff PCs         | Branch |
| 99   | Management  | Device management        | Both   |

### IP addressing plan

A hierarchical scheme — `10.<site>.<vlan>.0/24` for user networks, `10.255.0.x/30` for point-to-point links.

| Network              | Subnet           | Gateway     | Notes                     |
|----------------------|------------------|-------------|---------------------------|
| HQ-Staff (V10)       | 10.1.10.0/24     | 10.1.10.1   | DHCP to clients           |
| HQ-Sales (V20)       | 10.1.20.0/24     | 10.1.20.1   | DHCP to clients           |
| HQ-Mgmt (V99)        | 10.1.99.0/24     | 10.1.99.1   | static                    |
| BR-Staff (V40)       | 10.2.40.0/24     | 10.2.40.1   | DHCP to clients           |
| BR-Mgmt (V99)        | 10.2.99.0/24     | 10.2.99.1   | static                    |
| HQ-Core ↔ R-HQ       | 10.255.0.0/30    | —           | core .1, router .2        |
| BR-Core ↔ R-BR       | 10.255.0.4/30    | —           | core .5, router .6        |
| WAN R-HQ ↔ R-BR      | 10.255.0.8/30    | —           | R-HQ .9, R-BR .10         |
| Internet R-HQ ↔ ISP  | 203.0.113.0/30   | —           | R-HQ .2 (outside / NAT)   |

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

| Phase | Scope                                            | Status      |
|-------|--------------------------------------------------|-------------|
| A     | Hostnames, SSH, secure management baseline       | ✅ Complete |
| B     | VLANs and access-port assignment                 | ✅ Complete |
| C     | 802.1Q trunking and Rapid PVST+ Spanning Tree    | ✅ Complete |
| D     | Inter-VLAN routing (`ip routing` + SVIs)         | ✅ Complete |
| E     | DHCP server pools                                | ✅ Complete |
| F     | WAN links + OSPF (inter-site routing)            | ✅ Complete |
| G     | NAT/PAT for internet access                      | ✅ Complete |
| H     | Standard & extended ACLs                         | ✅ Complete |

## Automation

A small NetDevOps toolkit lives in `automation/`. It shows the two halves of managing network configs as code — **generating** them from a single source of truth, and **auditing** them against a security baseline — with CI tying the two together.

### Config generation (infrastructure as code)

`generate_configs.py` renders a full access-switch config for each device from a YAML data model (`devices.yml`) and a Jinja2 template (`templates/access_switch.j2`). The *data* (hostnames, VLANs, ports, IPs) is separated from the *shape* of the config, so adding a switch or a VLAN is a data change — not hand-typing — and every device comes out built identically, with no copy-paste drift.

```bash
pip install pyyaml jinja2
python automation/generate_configs.py     # writes automation/generated/*.txt
```

### Config auditing (compliance)

`config_audit.py` reads the exported running-configs and checks each against a security baseline, printing a per-device PASS/FAIL report. It exits non-zero if anything fails, which is what lets CI gate on it.

```bash
python automation/config_audit.py configs/
```

| Baseline check | Why it matters |
|----------------|----------------|
| Hostname set (not default) | devices are identifiable in logs and management |
| Enable secret configured | strong, non-reversible privileged-mode password |
| No weak `enable password` | avoids the legacy reversible password type |
| SSH-only management | no plaintext Telnet logins |
| VTY requires login | management sessions must authenticate |
| Password encryption enabled | no plaintext passwords stored in the config |

`R-ISP` is **deliberately out of audit scope** — it represents an external ISP's router, not equipment under our control — and is documented as an explicit skip inside the script rather than silently omitted.

### Continuous integration

`.github/workflows/network-audit.yml` runs the auditor automatically on every push and pull request. Because the auditor exits non-zero on any failure, an insecure config can't land without turning the check red. The badge at the top of this README reflects the latest run.

## Repository structure

```
multi-site-enterprise-network/
├── README.md
├── multi-site-enterprise-network.pkt    # the Cisco Packet Tracer file
├── configs/                             # exported running-configs (all 8 devices)
│   ├── SW-HQ-Core.txt
│   ├── SW-BR-Core.txt
│   ├── SW-HQ-A1.txt
│   ├── SW-HQ-A2.txt
│   ├── SW-BR-A1.txt
│   ├── R-HQ.txt
│   ├── R-BR.txt
│   └── R-ISP.txt
├── automation/
│   ├── config_audit.py                  # checks configs against a security baseline
│   ├── generate_configs.py              # renders configs from data + template
│   ├── devices.yml                      # the data model (source of truth)
│   ├── templates/
│   │   └── access_switch.j2             # the config template
│   └── generated/                       # generator output
├── docs/
│   └── topology.png                     # network diagram
└── .github/
    └── workflows/
        └── network-audit.yml            # CI: runs the auditor on every push
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
   show ip ospf neighbor          # OSPF adjacencies in FULL state
   show ip route ospf             # remote-site networks + default route learned
   ```
   On R-HQ, `show ip nat translations` shows live PAT entries during a test.
4. End-to-end proofs:
   - A PC in VLAN 10 pings a PC in VLAN 20 — inter-VLAN routing at the L3 core.
   - A PC at HQ pings a PC at the Branch — OSPF across the WAN.
   - Any client reaches the internet host `198.51.100.10` — NAT/PAT at the edge.
   - A Sales (VLAN 20) PC is denied to the management network but still reaches everything else — the ACL policy.

## Roadmap

The network and the file-based automation are complete. The next milestone is **live-device** automation:

- **Lab uplift** — rebuild the topology in a Cisco DevNet sandbox, GNS3, or CML, where devices accept real SSH (Packet Tracer can't).
- **Live backup** — a Netmiko script that connects to each device and pulls a timestamped running-config.
- **Live audit** — point the existing baseline checks at live devices instead of static files.

## Notes

This was built and debugged hands-on, including real troubleshooting — cabling mismatches, a stubborn EtherChannel (ultimately simplified to STP-managed redundant trunks after hitting Packet Tracer's LACP quirks), shut ports, and missing VLANs — diagnosed with `show cdp neighbors`, `show etherchannel summary`, `show interfaces status`, and layered `ping` testing. The audit tool also surfaced a real gap (missing `service password-encryption` across the fleet, plus an unhardened R-ISP), which was remediated before the baseline went green.
