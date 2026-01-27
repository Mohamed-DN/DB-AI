# Oracle Enterprise Manager 13c on Docker

## 🚀 Quick Start Guide

You are attempting to build the "Beast" - OEM 13c inside Docker.
Follow these steps carefully.

### 1. Prerequisites
You must download the **OEM 13.5 (Linux x86-64)** binaries from the Oracle eDelivery or OTN.
Files are typically named:
- `em13500_linux64.bin`
- `em13500_linux64-2.bin`
- `em13500_linux64-3.bin`
- ...

👉 **Action**: Place all `.bin` files in the `installers/` folder alongside this README.

### 2. Prepare the Repository Database
Your existing Oracle DB container (`ol7-orcl`) must be configured.
1. Connect to `ol7-orcl` as SYS.
2. Run the cleanup/setup script:
   ```bash
   cat scripts/repo_setup.sql | docker exec -i ol7-orcl sqlplus sys/password@ORCLCDB as sysdba
   ```

### 3. Build the Image
```bash
docker build -t my-oem-13c .
```
*Note: This builds the OS layer and dependencies. It does NOT install OEM yet.*

### 4. Run the Container
```bash
docker-compose up -d
```
The container `oem_server_13c` will start. It will sit in a loop doing nothing initially.

### 5. Install OEM (The Long Part)
1. Enter the container:
   ```bash
   docker exec -it oem_server_13c bash
   ```
2. Run the installation wrapper:
   ```bash
   /home/oracle/install_oem.sh
   ```
   *This takes 1-2 hours.* Monitor logs in `/u01/app/oracle/logs`.

3. **Root Scripts**:
   At the end, the installer asks to run root scripts. Do this from a **new** terminal on the host:
   ```bash
   docker exec -u 0 -it oem_server_13c /u01/app/oracle/middleware/allroot.sh
   ```

### 6. Access
Once finished, access the console at:
- **HTTPS**: `https://localhost:7802/em`
- **Login**: `sysman` / `password123` (or whatever you set in `install.rsp`)
