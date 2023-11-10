# CSPI QE Dev Tools

## Installation

Install the prerequisites:

```bash
sudo dnf install -y python3.11 python3.11-pip git podman
```

Clone the repo:

```bash
git clone https://github.com/amp-rh/cspi-qe-dev.git
```

Install using Pip:

```bash
pip install cspi-qe-dev
```

## Ref-Sandbox

Quickly test changes to Openshift CI registry steps in a local container and mock the expected live CI environment. The
primary goal of this project is to help developers detect as many issues as possible through local testing before moving
on to live rehearsal runs.

- Mock vaulted secrets
- Create low-privileged user
- Copy default environment variables from step registry refs
- Create common mounts, such as the "shared" and "artifact" directories
- Quickly override the image used by refs

### Examples

Run the entrypoint of the ref in the current working directory:

```bash
ref-sandbox run
```

Start an interactive session using the ref in the current working directory:

```bash
ref-sandbox
```

