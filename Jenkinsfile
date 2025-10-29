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
          newgrp docker <<'DOCKER_EOF'
            docker version || true
            docker buildx create --use || true
          DOCKER_EOF
        '''
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          newgrp docker <<'DOCKER_EOF'
            docker-compose build --no-cache
          DOCKER_EOF
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
          newgrp docker <<'DOCKER_EOF'
            docker-compose up -d
          DOCKER_EOF
        '''
      }
    }
  }

  post {
    always {
      sh '''
        newgrp docker <<'DOCKER_EOF'
          docker-compose ps || true
          docker-compose logs --no-color || true
        DOCKER_EOF
      ''' || true
    }
  }
}


