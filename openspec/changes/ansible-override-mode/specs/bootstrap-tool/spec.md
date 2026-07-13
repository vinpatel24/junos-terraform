## ADDED Requirements

### Requirement: Bootstrap tool accepts device IP or XML files
The `jtaf-bootstrap` CLI tool SHALL accept either a device IP address with credentials (to SSH and run `get-config`) or one or more XML configuration files as input. Both paths produce the same output artifacts.

#### Scenario: Bootstrap from live device
- **WHEN** the operator runs `jtaf-bootstrap --host 10.0.0.1 --user root --password pass --yang-path <yang-dir> -t <type>`
- **THEN** the tool SSHs to the device, retrieves the full configuration via NETCONF `get-config`, and feeds it into the JTAF pipeline

#### Scenario: Bootstrap from XML files
- **WHEN** the operator runs `jtaf-bootstrap --xml dc1-leaf1.xml dc1-spine1.xml --yang-path <yang-dir> -t <type>`
- **THEN** the tool uses the provided XML files as input to the JTAF pipeline (same as providing them to `jtaf-yang2ansible` and `jtaf-yang2go`)

### Requirement: Bootstrap generates both Ansible and Terraform artifacts
The `jtaf-bootstrap` tool SHALL generate both Ansible role + vars AND a Terraform provider from the same input in a single invocation.

#### Scenario: Full output from bootstrap
- **WHEN** the operator runs `jtaf-bootstrap` with valid YANG and XML inputs
- **THEN** the tool produces:
  - `ansible-provider-junos-<type>/` — Ansible role with template, tasks, filter_plugins
  - `ansible-deploy/` (or `-d` specified dir) — host_vars, group_vars, inventory
  - `terraform-provider-junos-<type>/` — Go Terraform provider source with trimmed_schema.json

### Requirement: Bootstrap generates host_vars and group_vars from XML
The bootstrap tool SHALL run `jtaf-xml2yaml` to extract YAML variables from the input XML configurations, producing the `host_vars/` and `group_vars/` hierarchy.

#### Scenario: Multiple XML files produce per-host vars
- **WHEN** the operator provides multiple XML files (e.g., one per device)
- **THEN** each XML file produces a `host_vars/<hostname>.yaml` file, and shared values are extracted into `group_vars/all.yaml`

### Requirement: Bootstrap uses mode flag for playbook generation
The bootstrap tool SHALL accept a `--mode group|override` flag that controls whether the generated playbook uses `load replace` (group mode) or `load override` + `commit confirmed` (override mode).

#### Scenario: Bootstrap with override mode
- **WHEN** the operator runs `jtaf-bootstrap --mode override ...`
- **THEN** the generated Ansible role template has no `<groups>` wrapper and the generated playbook includes the commit confirmed safety pattern

#### Scenario: Bootstrap with group mode (default)
- **WHEN** the operator runs `jtaf-bootstrap` without `--mode` or with `--mode group`
- **THEN** the generated Ansible role template wraps config in `<groups>` and the generated playbook uses `load replace`
