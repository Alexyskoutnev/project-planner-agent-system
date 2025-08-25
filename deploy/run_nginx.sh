
# Install Nginx
sudo apt update
sudo apt install nginx -y

sudo systemctl enable nginx
sudo systemctl start nginx

# echo status of nginx
systemctl status nginx

# Sync nginx config
sudo cp deploy/nginx_config /etc/nginx/sites-available/project
sudo ln -s /etc/nginx/sites-available/project /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx