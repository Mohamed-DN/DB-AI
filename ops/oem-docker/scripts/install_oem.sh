#!/bin/bash
# ==============================================================================
# OEM 13c Silent Installation Script for Docker
# ==============================================================================

INSTALLER_DIR="/software/oem/installers"
RESPONSE_FILE="/home/oracle/response/install.rsp"
LOG_DIR="/u01/app/oracle/logs"

mkdir -p $LOG_DIR

echo "----------------------------------------------------------------------"
echo "Starting OEM 13c Installation Wrapper"
echo "----------------------------------------------------------------------"

# 1. Check for Installers
count=$(ls $INSTALLER_DIR/*.bin 2>/dev/null | wc -l)
if [ "$count" -eq "0" ]; then
    echo "ERROR: No installer binaries (.bin) found in $INSTALLER_DIR"
    echo "Please download the OEM 13c linux x64 installers and place them in ops/oem-docker/installers on host."
    echo "Files usually named: em13500_linux64.bin, em13500_linux64-2.bin, ..."
    exit 1
fi

# 2. Grant Permissions
echo "Ensuring permissions..."
sudo chown -R oracle:oinstall /u01
sudo chown -R oracle:oinstall /software

# 3. Validation
if [ ! -f "$RESPONSE_FILE" ]; then
    echo "ERROR: Response file not found at $RESPONSE_FILE"
    exit 1
fi

echo "Installer found. Response file found."
echo "Prerequisite checks..."

# 4. Run Installer
# We assume the first .bin file is the launcher
LAUNCHER=$(ls $INSTALLER_DIR/*.bin | head -n 1)
chmod +x $LAUNCHER

echo "Launching: $LAUNCHER"
echo "This will take a significant amount of time (1-2 hours typically)."
echo "Tail the log files in $LOG_DIR if needed."

$LAUNCHER -silent -responseFile $RESPONSE_FILE \
    -invPtrLoc /u01/app/oraInventory/oraInst.loc \
    NOTE:SYS_PASSWORD="password123" \
    NOTE:SYSMAN_PASSWORD="password123" \
    NOTE:AGENT_REGISTRATION_PASSWORD="password123" \
    ORACLE_HOSTNAME=oemserver

# 5. Root Script Handling
# In Docker, we can't interactively run root.sh usually unless we have a separate exec session
echo "----------------------------------------------------------------------"
echo "Installation process finished (or backgrounded)."
echo "Check for root.sh scripts in /u01/app/oracle/middleware/allroot.sh"
echo "You must execute them as root inside the container manually:"
echo "  docker exec -u 0 -it oem_server_13c /u01/app/oracle/middleware/allroot.sh"
echo "----------------------------------------------------------------------"
