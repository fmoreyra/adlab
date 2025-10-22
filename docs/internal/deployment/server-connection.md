# Server Connection Guide

This guide explains how to connect to your production server using the new `server:connect` command.

## Setup

1. **Add the server IP to your .env file:**
   ```bash
   # Add these lines to your .env file
   SERVER_IP=10.0.0.1
   SERVER_USER=root
   ```

2. **If you don't have a .env file, create one:**
   ```bash
   # Copy from example if available, or create manually
   cp .env.example .env
   # Then edit .env and add the server configuration
   ```

## Usage

Connect to your server:
```bash
./run server:connect
```

This will:
- Check that the `SERVER_IP` environment variable is set
- Display a connection message
- Establish an SSH connection to your server

## Security Notes

- **Never commit the actual IP address** to version control
- The IP address is stored in the .env file (which is gitignored), not in the code
- Make sure your SSH keys are properly configured on the server
- Consider using a non-root user for better security practices

## Troubleshooting

If you get a "SERVER_IP is not set in .env file" error:
1. Make sure you have a .env file in your project root
2. Check that SERVER_IP is defined in your .env file
3. Verify the .env file syntax (no spaces around the = sign)

If SSH connection fails:
1. Verify your SSH keys are added to the server
2. Check that the IP address is correct
3. Ensure the server is accessible from your network
