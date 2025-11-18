# Deployment

This document explains how to deploy the AI backend unified dashboard.

## Prerequisites

- Python 3.8 or higher
- `venv` module (usually included with Python)

## Deployment

To deploy the dashboard, run the `deploy.sh` script from the `scripts` directory:

```bash
./scripts/deploy.sh
```

This script will:

1.  Create a virtual environment in the `.venv` directory.
2.  Install the dependencies from `requirements.txt`.

## Running the Dashboard

To run the dashboard, activate the virtual environment and run the following command:

```bash
source .venv/bin/activate
python3 -m scripts.dashboard
```
