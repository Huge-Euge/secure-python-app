# Exit if any command fails
set -e

cleanup() {
    echo "--- Shutting down containers ---"
    sudo docker compose down
}

# make cleanup function get called on script exit
trap cleanup ERR INT TERM

echo "--- installing build deps ---"
pip install -r requirements-dev.txt

echo "--- Linting app code with pylint ---"
pylint --fail-under=6.0 app/*.py

echo "--- Linting tests with pylint ---"
pylint --load-plugins pylint_pytest --fail-under=6.0 tests/*.py

echo "--- Building Docker image ---"
# 'build' uses your Dockerfile and docker-compose.yml to build the image
sudo docker compose build

echo "--- starting container in background ---"
# up -d starts it detached 
sudo docker compose up -d

echo "--- spinning up the app ---"
sleep 4

echo "--- testing with pytest ---"
pytest ./tests/integration_tests.py

echo "--- All steps passed successfully! ---"
echo "---"
echo "Now running in the background"
echo "To stop it, run: sudo docker compose down"
