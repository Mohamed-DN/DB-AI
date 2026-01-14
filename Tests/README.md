# 🧪 Tests

> Integration and System Validation tests.

This directory contains the testing suite for ensuring the stability and correctness of the Nexi DBA AI system.

## 📂 Directory Contents

| File/Directory | Description |
|----------------|-------------|
| **`Integration/`** | Contains Python test scripts that verify end-to-end flows (e.g., Agent -> DB -> Mongo). |
| **`validate_system.py`** | A main validation script that runs a series of checks against the active environment to report health status. |

## 🚀 Running Tests

To run the system validation:

```powershell
python Tests/validate_system.py
```
