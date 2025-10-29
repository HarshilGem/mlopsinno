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
          bash -c 'newgrp docker << ENDG
            docker version
            docker buildx create --use || true
          ENDG
          ' || true
        '''
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          bash -c 'newgrp docker << ENDG
            cd ${WORKSPACE}
            docker-compose build --no-cache
          ENDG
          '
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
          bash -c 'newgrp docker << ENDG
            cd ${WORKSPACE}
            docker-compose up -d
          ENDG
          '
        '''
      }
    }
  }

  post {
    always {
      sh '''
        bash -c 'newgrp docker << ENDG
          cd ${WORKSPACE}
          docker-compose ps || true
          docker-compose logs --no-color || true
        ENDG
        ' || true
      '''
    }
  }
}


