# Ticket Pool Deployment Guide

## 1. Clone the Repository

```bash
cd ~
git clone https://github.com/bluemonkeydev/ticket-pool.git
cd ticket-pool
```

## 2. Create Production Environment File

```bash
nano .env
```

Paste this content (update values as needed):

```env
SECRET_KEY=GENERATE_A_NEW_RANDOM_KEY_HERE
MAIL_ENABLED=true
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_KEY
SES_SENDER_EMAIL=noreply@bluemonkeydev.com
APP_NAME=Ticket Pool
APP_URL=https://ticket-pool.bluemonkeydev.com
COOKIE_SECURE=true
```

To generate a secure SECRET_KEY:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 3. Build and Start the Container

```bash
docker compose up -d --build
```

Verify it's running:
```bash
docker compose ps
docker compose logs -f
```

## 4. Configure Nginx + SSL

Run certbot interactively - it will create the nginx config and set up SSL for you:

```bash
sudo certbot --nginx -d ticket-pool.bluemonkeydev.com
```

Certbot will prompt you to:
1. Enter your email (for renewal notices)
2. Agree to terms of service
3. Choose whether to redirect HTTP to HTTPS (recommended: yes)

It automatically creates the nginx server block and configures SSL.

After certbot completes, manually add the proxy settings:

```bash
sudo nano /etc/nginx/sites-available/ticket-pool.bluemonkeydev.com
```

Add this inside the `location /` block (or replace the existing one):

```nginx
location / {
    proxy_pass http://127.0.0.1:5100;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then reload nginx:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 6. Useful Commands

```bash
# View logs
docker compose logs -f

# Restart the app
docker compose restart

# Stop the app
docker compose down

# Update to latest code
cd ~/ticket-pool
git pull
docker compose up -d --build

# Access the database (if needed)
docker compose exec web python -c "import sqlite3; conn = sqlite3.connect('/data/tickets.db'); print('Connected')"
```

## 7. Initialize Database (First Time Only)

The database will be created automatically on first run. If you need to reinitialize:

```bash
docker compose exec web python docker-init-db.py
```
