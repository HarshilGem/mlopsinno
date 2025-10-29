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
        sh 'sg docker -c "docker version" || true'
        sh 'sg docker -c "docker buildx create --use" || true'
      }
    }

    stage('Build Images') {
      steps {
        sh 'sg docker -c "docker-compose build --no-cache"'
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
        sh 'sg docker -c "docker-compose up -d"'
      }
    }
  }

  post {
    always {
      sh 'sg docker -c "docker-compose ps" || true'
      sh 'sg docker -c "docker-compose logs --no-color" || true'
    }
  }
}


