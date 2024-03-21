def projectName = "testreportservice${UUID.randomUUID().toString()}"
def registry = '172.23.111.200:5001'
pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                script {
                    docker.build('reportservice/test', '-f ./tests/Dockerfile .')
                }
            }
        }
        stage('Setup Dependencies') {
            steps {
                script {
                    sh "cd tests && docker compose -p ${projectName} \
                        -f docker-compose-mongo.yml \
                        -f docker-compose-smtp.yml \
                        up -d"
                }
            }
        }
        stage('Test') {
            steps {
                script {
                    sh "cd tests && docker compose -p ${projectName} \
                        -f docker-compose-mongo.yml \
                        -f docker-compose-smtp.yml \
                        -f docker-compose.yml \
                        up reportservice --abort-on-container-exit --exit-code-from reportservice"
                }
            }
        }
        stage('Coverage') {
            steps {
                script {
                    sh "docker compose -p ${projectName} cp reportservice:/usr/src/app/coverage.xml ."
                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'coverage.xml']],
                           qualityGates: [[threshold: 95.0, metric: 'LINE', baseline: 'PROJECT', unstable: true]])
                    echo '${branchCoverage}'
                    echo 'Coverage results embeddable build status build URL is:\n' +
                        env.BUILD_URL + '/badge/icon' +
                        '?subject=Coverage&status=${branchCoverage}&color=${colorBranchCoverage}'
                    echo 'Coverage results embeddable build status job URL is:\n' +
                        env.JOB_URL + '/badge/icon' +
                        '?subject=Coverage&status=${branchCoverage}&color=${colorBranchCoverage}'
                    // cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
        stage('Publish') {
            steps {
                script {
                    def scmTag = sh(script: 'git describe --tags --abbrev=0', returnStdout: true).trim()
                    def version = scmTag ?: env.BUILD_NUMBER
                    def image = docker.build("${registry}/reportservice:jenkins_${version}", '-f ./tests/Dockerfile .')
                    println("Create image ${registry}/reportservice:jenkins_${version}, do not push yet")
                // docker.withRegistry(registry) {
                //     image.push("jenkins_${version}")
                //     // image.push("latest")
                // }
                }
            }
        }
    }
    post {
        always {
            sh "docker compose -p ${projectName} down --volumes --remove-orphans"
        }
    }
}
