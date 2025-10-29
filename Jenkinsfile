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
          bash -c "newgrp docker <<'EOF'
            docker version || true
            docker buildx create --use || true
          EOF
          " || true
        '''
      }
    }

    stage('Build Images') {
      steps {
        sh '''
          bash -c "newgrp docker <<'EOF'
            cd '${WORKSPACE}' && docker-compose build --no-cache
          EOF
          "
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
          bash -c "newgrp docker <<'EOF'
            cd '${WORKSPACE}' && docker-compose up -d
          EOF
          "
        '''
      }
    }
  }

  post {
    always {
      sh '''
        bash -c "newgrp docker <<'EOF'
          cd '${WORKSPACE}' && docker-compose ps || true
          cd '${WORKSPACE}' && docker-compose logs --no-color || true
        EOF
        " || true
      '''
    }
  }
}


