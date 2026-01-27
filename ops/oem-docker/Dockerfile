FROM oraclelinux:7-slim

# Argument for OEM Version
ARG OEM_VERSION=13.5.0.0.0

# 1. Install Prerequisites
# OEM 13c requires specific packages and OS configurations
RUN yum install -y \
    make \
    binutils \
    gcc \
    libaio \
    glibc-common \
    libstdc++ \
    libXtst \
    sysstat \
    net-tools \
    numactl \
    openssh-server \
    openssh-clients \
    xorg-x11-utils \
    unzip \
    iputils \
    which \
    sudo \
    && yum clean all

# 2. Create Users and Groups
RUN groupadd -g 54321 oinstall && \
    groupadd -g 54322 dba && \
    useradd -u 54321 -g oinstall -G dba oracle && \
    mkdir -p /u01/app/oracle /software/oem /u01/app/oraInventory && \
    chown -R oracle:oinstall /u01 /software /u01/app/oraInventory && \
    chmod -R 775 /u01 /software

# 3. Kernel Limits (Note: These often need to be set on HOST or via --sysctl in Docker)
# We add them to limits.conf just in case
RUN echo "oracle soft nofile 4096" >> /etc/security/limits.conf && \
    echo "oracle hard nofile 65536" >> /etc/security/limits.conf && \
    echo "oracle soft nproc 16384" >> /etc/security/limits.conf && \
    echo "oracle hard nproc 16384" >> /etc/security/limits.conf && \
    echo "oracle soft stack 10240" >> /etc/security/limits.conf

# 4. Environment Variables
USER oracle
ENV ORACLE_BASE=/u01/app/oracle
ENV ORACLE_HOME=/u01/app/oracle/middleware
ENV PATH=$ORACLE_HOME/bin:$PATH
ENV AGENT_BASE_DIR=/u01/app/oracle/agent

# 5. Workdir
WORKDIR /software/oem

# 6. Copy Installation Script (We don't copy binaries, we mount them)
COPY --chown=oracle:oinstall scripts/install_oem.sh /home/oracle/install_oem.sh
RUN chmod +x /home/oracle/install_oem.sh

# 7. Expose Ports
# 7788: HTTP Console
# 7802: HTTPS Console
# 7803: HTTPS Upload
# 4903: HTTP Upload
# 7202: HTTP Port for agent
# 7403: HTTPS Port for agent
EXPOSE 7788 7802 7803 4903 7202 7403

# 8. Entrypoint
# We loop forever to keep container alive, user must run install script manually or via exec
CMD ["/bin/bash", "-c", "echo 'Container Started. Run /home/oracle/install_oem.sh to install.'; tail -f /dev/null"]
