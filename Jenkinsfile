pipeline {
  agent any

  environment {
    COMPOSE_PROJECT_NAME = 'mlopsassi'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Set up Docker Buildx') {
      steps {
        sh 'echo "docker version" | newgrp docker || true'
        sh 'echo "docker buildx create --use" | newgrp docker || true'
      }
    }

    stage('Build Images') {
      steps {
        sh 'echo "docker-compose build --no-cache" | newgrp docker'
      }
    }

    stage('Unit Tests') {
      when {
        expression { return false }
      }
      steps {
        echo 'No tests configured.'
      }
    }

    stage('Deploy (Compose Up)') {
      steps {
        sh 'echo "docker-compose up -d" | newgrp docker'
      }
    }
  }

  post {
    always {
      sh 'echo "docker-compose ps" | newgrp docker || true'
      sh 'echo "docker-compose logs --no-color" | newgrp docker || true'
    }
  }
}


