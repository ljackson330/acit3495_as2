## ACIT 3495 Project 2

Deploy and manage the containerized web app from Project 1 using Kubernetes.

### Usage

The included deploy script (local) will handle building your Docker images, and run through applying each of the Kubernetes
configurations in ./k8s 

```
chmod +x ./deploy.sh
./deploy.sh
```

The frontend will be available at ``http://localhost:30000/``

The included *AWS* script (`deploy-aws.sh`) is an example of a script that creates ECR (Elastic Container Registry) repositories and pushes the Docker images to them. The script builds images using `buildx` to be compatible with different platform architectures. The rest of the script remains similar to the `deploy.sh` script. 

```
chmod +x ./deploy-aws.sh
./deploy-aws.sh
```

The frontend will be available at ``http://<frontend LoadBalancer EXTERNAL IP>:30000/``

Both scripts expect the following environment variables:

```
# MariaDB Credentials
MYSQL_ROOT_PASSWORD=
MYSQL_DATABASE=
MYSQL_USER=

# MongoDB Credentials
MONGO_INITDB_ROOT_USERNAME=
MONGO_INITDB_ROOT_PASSWORD=
MONGO_INITDB_DATABASE=

# MongoDB URI
MONGO_URI=

# FastAPI Auth Service
SECRET_KEY=

# Backend DB Connection
DB_HOST=
DB_PORT=
DB_USER=
DB_PASSWORD=
DB_NAME=

# Auth test user
TEST_USER_NAME=
TEST_USER_PASSWORD=
```
