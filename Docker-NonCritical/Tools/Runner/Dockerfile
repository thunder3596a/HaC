FROM gitea/act_runner:latest

# Install Node.js and other useful dependencies
RUN apk add --no-cache \
    nodejs \
    npm \
    git \
    curl

# Ensure proper working directory
WORKDIR /data

# Keep the original entrypoint but ensure we run from /data
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["sh", "-c", "cd /data && exec act_runner daemon"]
