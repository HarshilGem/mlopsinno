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
        sh '''
          docker version || true
          docker buildx create --use || true
        '''
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          cd "${WORKSPACE}"
          docker-compose build --no-cache
        '''
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
        sh '''
          cd "${WORKSPACE}"
          docker-compose up -d
        '''
      }
    }
  }

  post {
    always {
      sh '''
        cd "${WORKSPACE}"
        docker-compose ps || true
        docker-compose logs --no-color || true
      '''
    }
  }
}
