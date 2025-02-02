from flask import Flask, render_template  
  
app = Flask(__name__, template_folder='.')  
  
@app.route("/")  
def web():  
    return render_template('index.html')  
  
if __name__ == "__main__":  
    app.run(debug=True, host="0.0.0.0", port='3000')  



    worker_processes 1;

events { worker_connections 1024; }

http {
	ssl_session_cache shared:SSL:10m;
	ssl_session_timeout 5m;
	ssl_prefer_server_ciphers on;
	ssl_stapling on;
	resolver 8.8.8.8;
    sendfile on;
	gzip            on;
    gzip_types      text/plain application/xml text/css application/javascript;
    gzip_min_length 1000;
    upstream static {
        server 0.0.0.0:8000;
		keepalive 32;
    }

server_tokens off;

server {
        listen 80;
		listen 443 ssl;
		server_name choribot.ru;
		ssl_certificate /etc/nginx/certificate_full_chain.pem;
		ssl_certificate_key /etc/nginx/private_key.pem;
		location ~ /ws/* {
			proxy_set_header Upgrade $http_upgrade;
			proxy_set_header Connection "upgrade";
			client_max_body_size 50M;
			proxy_set_header Host $http_host;
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
			proxy_set_header X-Forwarded-Proto $scheme;
			proxy_set_header X-Frame-Options SAMEORIGIN;
			proxy_buffers 256 16k;
			proxy_buffer_size 16k;
			client_body_timeout 60;
			send_timeout 300;
			lingering_timeout 5;
			proxy_connect_timeout 1d;
			proxy_send_timeout 1d;
			proxy_read_timeout 1d;
			proxy_pass http://focalboard;
		}

		location / {
			client_max_body_size 50M;
			proxy_set_header Connection "";
			proxy_set_header Host $http_host;
			proxy_set_header X-Real-IP $remote_addr;
			proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
			proxy_set_header X-Forwarded-Proto $scheme;
			proxy_set_header X-Frame-Options SAMEORIGIN;
			proxy_buffers 256 16k;
			proxy_buffer_size 16k;
			proxy_read_timeout 600s;
			proxy_cache_revalidate on;
			proxy_cache_min_uses 2;
			proxy_cache_use_stale timeout;
			proxy_cache_lock on;
			proxy_http_version 1.1;
			proxy_pass http://focalboard;
		}

}
}
