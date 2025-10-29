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
        powershell 'docker version | Out-Host; exit 0'
        powershell 'docker buildx create --use | Out-Host; exit 0'
      }
    }

    stage('Build Images') {
      steps {
        powershell 'docker compose build --no-cache'
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
        powershell 'docker compose up -d'
      }
    }
  }

  post {
    always {
      powershell 'docker compose ps';
      powershell 'docker compose logs --no-color'
    }
  }
}


