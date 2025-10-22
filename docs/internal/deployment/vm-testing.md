# VM Testing Guide

Test deployment procedures in a local VM before deploying to production.

## Why Test in a VM?

Testing in a VM allows you to:
- ✅ Verify deployment procedures work correctly
- ✅ Practice deployment steps before production
- ✅ Test configuration changes safely
- ✅ Train team members on deployment process
- ✅ Debug issues in an isolated environment

## Recommended Approach: Multipass

Multipass provides real Ubuntu VMs on macOS, Windows, and Linux - closest to production environment.

### Prerequisites

- macOS, Windows 10+, or Linux
- 8GB+ RAM available for VM
- 20GB+ free disk space
- Multipass installed

### Install Multipass

```bash
# macOS
brew install multipass

# Windows (PowerShell as Administrator)
# Download from: https://multipass.run/download/windows

# Linux (snap)
sudo snap install multipass
```

## Quick Start with Multipass

### 1. Create Ubuntu VM

```bash
# Create VM with adequate resources
multipass launch --name lab-deploy \
  --cpus 4 \
  --memory 8G \
  --disk 50G \
  22.04

# Wait for VM to be ready (about 30 seconds)
multipass list
```

### 2. Access the VM

```bash
# SSH into the VM
multipass shell lab-deploy

# Or get IP and use regular SSH
multipass info lab-deploy
# Then: ssh ubuntu@<VM_IP>
```

### 3. Setup Inside VM

Once inside the VM:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group (avoid sudo for docker commands)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version

# Install git and other tools
sudo apt update
sudo apt install -y git vim curl
```

### 4. Clone Repository

```bash
# Option A: Clone from Git
cd ~
git clone <your-repo-url> laboratory-system
cd laboratory-system

# Option B: Copy from host (see below)
```

### 5. Deploy Application

```bash
# Inside the VM
cd ~/laboratory-system

# Copy environment file
cp .env.production.example .env

# Edit environment variables
vim .env
# Set DEBUG=false, SECRET_KEY, POSTGRES_PASSWORD, ALLOWED_HOSTS

# Build and start services
docker-compose -f compose.yaml -f compose.production.yaml build
docker-compose -f compose.yaml -f compose.production.yaml up -d postgres redis

# Wait for database
sleep 10

# Run migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Collect static files
./run manage collectstatic --no-input

# Start all services
docker-compose -f compose.yaml -f compose.production.yaml up -d

# Check logs
docker-compose logs -f web
```

### 6. Access from Host

```bash
# Get VM IP address
multipass info lab-deploy
# Look for IPv4 address, something like: 192.168.64.5

# Access from your browser
http://192.168.64.5:8000
```

## Copy Files from Host to VM

If you want to test your local code changes:

```bash
# From your host machine (outside VM)
multipass transfer -r /path/to/laboratory-system lab-deploy:/home/ubuntu/

# Then access the VM and work with the copied files
multipass shell lab-deploy
cd laboratory-system
```

## VM Management Commands

```bash
# List all VMs
multipass list

# Stop VM
multipass stop lab-deploy

# Start VM
multipass start lab-deploy

# Restart VM
multipass restart lab-deploy

# Get VM info
multipass info lab-deploy

# Access VM shell
multipass shell lab-deploy

# Execute command in VM
multipass exec lab-deploy -- ls -la /home/ubuntu

# Delete VM (when done testing)
multipass delete lab-deploy
multipass purge
```

## Testing Scenarios

### Scenario 1: Fresh Production Deployment

Test the complete deployment from scratch:

1. Create fresh VM
2. Follow [Production Deployment Guide](./production-deployment.md)
3. Verify all services start correctly
4. Test application functionality
5. Document any issues encountered

### Scenario 2: Application Update

Test updating an existing deployment:

1. Deploy initial version
2. Make changes to code
3. Test update procedure:
   ```bash
   git pull
   docker-compose build
   ./run manage migrate
   docker-compose restart web
   ```
4. Verify update successful

### Scenario 3: Database Migration

Test schema changes:

1. Deploy current version
2. Create test data
3. Apply new migrations
4. Verify data integrity
5. Test rollback if needed

### Scenario 4: Backup and Restore

Test disaster recovery:

1. Deploy and create test data
2. Create backup:
   ```bash
   ./run db:dump
   ```
3. Destroy database
4. Restore from backup
5. Verify data restored correctly

### Scenario 5: SSL Configuration

Test HTTPS setup (requires domain or hosts file modification):

1. Point test domain to VM IP
2. Follow [SSL Setup Guide](./ssl-certificates.md)
3. Use Let's Encrypt staging environment
4. Verify HTTPS works
5. Test certificate renewal

## Alternative: Docker Desktop

For quick testing without full VM:

```bash
# On your local machine
cd /path/to/laboratory-system

# Use production compose file
docker-compose -f compose.yaml -f compose.production.yaml up -d --build

# Run migrations
./run manage migrate

# Create superuser
./run manage createsuperuser

# Access
open http://localhost:8000
```

**Note:** This doesn't test:
- Nginx configuration
- SSL certificates
- System services (systemd)
- Firewall rules

## Troubleshooting VM Testing

### VM Won't Start

```bash
# Check Multipass status
multipass list

# View logs
multipass info lab-deploy --verbose

# Restart Multipass service
# macOS:
sudo launchctl restart com.canonical.multipassd

# Linux:
sudo systemctl restart multipass
```

### Can't Access VM from Host

```bash
# Check VM IP
multipass info lab-deploy | grep IPv4

# Check if services are running in VM
multipass exec lab-deploy -- docker ps

# Check if port is accessible
multipass exec lab-deploy -- netstat -tlnp | grep 8000
```

### Docker Permission Denied in VM

```bash
# Add user to docker group
multipass exec lab-deploy -- sudo usermod -aG docker ubuntu

# Apply group changes
multipass restart lab-deploy
```

### Out of Disk Space

```bash
# Check disk usage in VM
multipass exec lab-deploy -- df -h

# Clean up Docker resources
multipass exec lab-deploy -- docker system prune -a

# Or increase VM disk size (requires recreation)
multipass delete lab-deploy
multipass launch --name lab-deploy --disk 100G 22.04
```

## Comparison: Testing Options

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Multipass** | Real Ubuntu VM, closest to production, systemd support | Requires VM overhead, slower | Full deployment testing |
| **Docker Desktop** | Fast, uses existing Docker, easy iteration | Not realistic, no systemd | Quick app testing |
| **VirtualBox/VMware** | Full control, snapshots | Manual setup, heavier | Advanced testing, snapshots |
| **Cloud VM (DigitalOcean, AWS)** | Real production environment | Costs money, requires cleanup | Final pre-production testing |

## Best Practices

1. **Snapshot Before Testing**
   ```bash
   # Multipass doesn't have built-in snapshots
   # Use cloud VMs or VirtualBox for snapshot support
   ```

2. **Test with Production-Like Data**
   - Use realistic data volumes
   - Test with actual file sizes
   - Simulate production load

3. **Document Everything**
   - Note commands that failed
   - Record timing for operations
   - Document workarounds needed

4. **Clean Up After Testing**
   ```bash
   multipass delete lab-deploy
   multipass purge
   ```

5. **Automate Common Tests**
   - Create test scripts
   - Use same scripts in production
   - Version control test procedures

## Automated VM Setup Script

Create `scripts/create-test-vm.sh`:

```bash
#!/bin/bash
set -e

VM_NAME="lab-deploy"
REPO_URL="https://github.com/your-username/laboratory-system.git"

echo "Creating test VM..."
multipass launch --name $VM_NAME --cpus 4 --memory 8G --disk 50G 22.04

echo "Installing Docker..."
multipass exec $VM_NAME -- bash -c "
  curl -fsSL https://get.docker.com | sudo sh && \
  sudo usermod -aG docker ubuntu && \
  sudo curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-\$(uname -m) -o /usr/local/bin/docker-compose && \
  sudo chmod +x /usr/local/bin/docker-compose
"

echo "Installing tools..."
multipass exec $VM_NAME -- sudo apt update
multipass exec $VM_NAME -- sudo apt install -y git vim curl

echo "Cloning repository..."
multipass exec $VM_NAME -- git clone $REPO_URL laboratory-system

echo "VM ready!"
echo "Access with: multipass shell $VM_NAME"
VM_IP=$(multipass info $VM_NAME | grep IPv4 | awk '{print $2}')
echo "VM IP: $VM_IP"
```

Make it executable:
```bash
chmod +x scripts/create-test-vm.sh
./scripts/create-test-vm.sh
```

## Next Steps After VM Testing

Once you've successfully tested in a VM:

1. **Document Issues** - Record any problems encountered
2. **Update Procedures** - Refine deployment documentation
3. **Train Team** - Share knowledge with team members
4. **Deploy to Production** - Follow [Production Deployment Guide](./production-deployment.md)
5. **Monitor Closely** - Watch logs during first production deployment

## Related Documentation

- [Production Deployment Guide](./production-deployment.md) - Deploy to production
- [Server Connection](./server-connection.md) - SSH and remote access
- [SSL Certificates](./ssl-certificates.md) - HTTPS setup
- [Troubleshooting](../operations/troubleshooting.md) - Common issues

---

[← Back to Deployment Documentation](./README.md) | [Documentation Home](../README.md)
