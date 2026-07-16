FROM ubuntu:22.04

# Installazione OpenSSH Server
RUN apt-get update && apt-get install -y \
    openssh-server \
    postgresql-client \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Configurazione SSH
RUN mkdir /var/run/sshd
RUN echo 'root:pippopippo_1234' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Creazione utente service_audit (read-only)
RUN useradd -m -s /bin/bash service_audit
RUN echo 'service_audit:audit2024' | chpasswd

# Creazione directory per chiavi
RUN mkdir -p /home/service_audit/.ssh
RUN chown -R service_audit:service_audit /home/service_audit/.ssh
RUN chmod 700 /home/service_audit/.ssh

# Script di test per simulare comandi Oracle
COPY scripts/ /opt/scripts/
RUN chmod +x /opt/scripts/*

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
