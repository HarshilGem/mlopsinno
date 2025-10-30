// pipeline {
//   agent any

//   environment {
//     COMPOSE_PROJECT_NAME = 'mlopsassi'
//   }

//   stages {
//     stage('Checkout') {
//       steps {
//         checkout scm
//       }
//     }

//     stage('Set up Docker Buildx') {
//       steps {
//         sh '''
//           docker version || true
//           docker buildx create --use || true
//         '''
//       }
//     }

//     stage('Build Images') {
//       steps {
//         sh '''
//           cd "${WORKSPACE}"
//           docker-compose build --no-cache
//         '''
//       }
//     }

//     stage('Unit Tests') {
//       when {
//         expression { return false }
//       }
//       steps {
//         echo 'No tests configured.'
//       }
//     }

//     stage('Deploy (Compose Up)') {
//       steps {
//         sh '''
//           cd "${WORKSPACE}"
//           docker-compose up -d
//         '''
//       }
//     }
//   }

//   post {
//     always {
//       sh '''
//         cd "${WORKSPACE}"
//         docker-compose ps || true
//         docker-compose logs --no-color || true
//       '''
//     }
//   }
// }

pipeline {
  agent any

  environment {
    COMPOSE_PROJECT_NAME = 'mlopsassi'
    PROMETHEUS_CONFIG = '/var/jenkins_home/workspace/mlops-pipeline/monitoring/prometheus.yml'
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

    stage('Fix Prometheus Path (for Jenkins)') {
      steps {
        sh '''
          echo "Ensuring Prometheus config path exists:"
          ls -l "${PROMETHEUS_CONFIG}" || (echo "❌ prometheus.yml missing!" && exit 1)

          # Patch docker-compose.yml temporarily with absolute path for Jenkins
          echo "Patching docker-compose.yml..."
          sed -i "s|\\./monitoring/prometheus.yml|${PROMETHEUS_CONFIG}|g" docker-compose.yml
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
