# Exit if any command fails
set -e

cleanup() {
    echo "--- Shutting down containers ---"
    sudo docker compose down
}

# make cleanup function get called on script exit
trap cleanup ERR INT TERM

# cleanup any running version
cleanup

echo "--- Building Docker image ---"
# 'build' uses your Dockerfile and docker-compose.yml to build the image
sudo docker compose build

echo "--- starting container in background ---"
# up -d starts it detached 
sudo docker compose up -d

echo "---"
echo "Now running in the background"
echo "To stop it, run: sudo docker compose down"
