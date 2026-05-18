# Static site deployment to Cloud Run
FROM nginx:alpine

# Copy static HTML files
COPY signup.html ./
COPY index.html ./
COPY *.html ./

# Copy nginx config for SPA routing
COPY gcp/nginx-static.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]