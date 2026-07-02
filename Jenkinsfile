pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "rutai-backend"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        CONTAINER_NAME = "rutai_api"
        NGINX_CONTAINER = "rutai_nginx"
        NETWORK_NAME = "rutai_net"
    }

    stages {
        stage('Build') {
            steps {
                script {
                    sh """
                        docker build \\
                            --target runtime \\
                            -t ${DOCKER_IMAGE}:${DOCKER_TAG} \\
                            -t ${DOCKER_IMAGE}:latest \\
                            .
                    """
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([file(credentialsId: 'remembergo-env', variable: 'REMEMBERGO_ENV_FILE')]) {
                    sh '''
                        cp "$REMEMBERGO_ENV_FILE" .env

                        docker compose down --remove-orphans || true

                        docker compose up -d --build
                    '''
                }
            }
        }

        stage('Health Check') {
            steps {
                script {
                    def retries = 12
                    def healthy = false
                    for (def i = 0; i < retries; i++) {
                        try {
                            sh "curl -sSf http://localhost:8000/health"
                            healthy = true
                            break
                        } catch (Exception e) {
                            echo "Health check attempt ${i + 1}/${retries} failed, retrying in 10s..."
                            sleep(10)
                        }
                    }
                    if (!healthy) {
                        error("Health check failed after ${retries} attempts")
                    }
                }
            }
        }
    }

    post {
        failure {
            echo "Deploy failed. Check Jenkins logs for details."
        }
        success {
            echo "Deploy completed successfully."
        }
    }
}
