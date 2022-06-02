pipeline { 
    options {
        disableConcurrentBuilds()
        parallelsAlwaysFailFast()
        timestamps()
        withCredentials([sshUserPrivateKey(credentialsId: 'gcp-user', keyFileVariable: 'SSH_KEY', passphraseVariable: '', usernameVariable: 'USERNAME')])
    }
    
    agent {
        label {
            label "${JENKINS_AGENT_LABEL}"
        }
    }

    parameters {
        string(name: 'BRANCH', defaultValue: 'main', description: 'Enter the branch to be deployed', trim: true)
        choice(name: 'JENKINS_AGENT_LABEL', choices: ['master'], description: '')
        choice(name: 'SERVICE_NAME', choices: ['PYTHON-BTC-PRICE-API'], description: '')
    }
    
    environment {
        DATE = sh (script: "date +\"%F-Time-%H-%M\"", returnStdout: true ).trim()

        GITHUB_REPO_URL = "https://github.com/vkommanaboina/python-btc-price-rest-api.git"
        BRANCH = "${BRANCH}"
        BUILD_COMMAND = 'echo "No Build Creating Required. Only Repo Zip Needs To Be Copied After Taking The Checkout"'

        STAGING_ENV_IP = "34.168.253.147"
        PROD_ENV_IP = "34.86.170.102"

        ARTIFACT_NAME = "${BRANCH}-${DATE}"
        REMOTE_COPY_ARTIFACT_DIR = "/home/gcp-user/JENKINS-TEMP-BUILDS/${SERVICE_NAME}"
        REMOTE_DEPLOY_DIR = "/opt/python-btc-price-api"
        SSH_CONNECTION_CMD = 'ssh -i $SSH_KEY -t -q -o StrictHostKeyChecking=no $USERNAME@'
        SCP_CONNECTION_CMD = 'scp -i $SSH_KEY -P 22 -q -o StrictHostKeyChecking=no'
        USER_PERMISSION = "gcp-user"
        SYSTEMD_SERVICE_NAME = "python-btc-price-api.service"
    }
    
    stages { 
        stage('Cleaning Workspace Before Build Creation') {
            steps {
                cleanWs()
            }
        }

        stage('Build Checkout') {
            steps {
                echo "BRANCH = ${BRANCH}"	            
                checkout([$class: 'GitSCM',
                branches: [[name: "${BRANCH}"]],
                doGenerateSubmoduleConfigurations: false,
                extensions: [[$class: 'CloneOption', timeout: 60]],
                submoduleCfg: [],
                userRemoteConfigs: [[url: "$GITHUB_REPO_URL"]]])
            }
        }

        stage('Build Creation') {
            steps {
                sh """
                mkdir -p $WORKSPACE
                cd $WORKSPACE/
                git status
                ${BUILD_COMMAND}
                ls -ltrh
                """
            }
        }

        stage('Zip and MD5SUM Creation') {
            steps {
                sh """
                cd ${WORKSPACE}
                mkdir ${BRANCH}
                rsync -av --progress ${WORKSPACE}/ ${WORKSPACE}/${BRANCH}/ --exclude ${BRANCH}
                cd ${BRANCH}
                zip -r ${BRANCH}-${DATE}.zip .
                md5sum ${BRANCH}-${DATE}.zip > ${BRANCH}-${DATE}.md5sum_local
                ls -ltrh ${BRANCH}*
                """
            }
        }

		stage('STAGING: Copying Artifacts') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${STAGING_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    sudo rm -rf ${REMOTE_COPY_ARTIFACT_DIR}
                    sudo mkdir -p ${REMOTE_COPY_ARTIFACT_DIR}
                    sudo chown -R ${USER_PERMISSION}:${USER_PERMISSION} ${REMOTE_COPY_ARTIFACT_DIR}
                    ls -ltrh
                    set +e
                    exit
                    EOSSH
                """
                sh """
                cd ${WORKSPACE}/${BRANCH}
                ${SCP_CONNECTION_CMD} ${BRANCH}-${DATE}.zip ${BRANCH}-${DATE}.md5sum_local ${USERNAME}@${STAGING_ENV_IP}:${REMOTE_COPY_ARTIFACT_DIR}
                """
            }
        }

		stage('STAGING: Check MD5Sum of Artifacts') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${STAGING_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    cd ${REMOTE_COPY_ARTIFACT_DIR}
                    md5sum ${ARTIFACT_NAME}.zip > ${ARTIFACT_NAME}.md5sum_remote
                    unzip ${ARTIFACT_NAME}.zip -d ${ARTIFACT_NAME}
                    ls -ltrh
                    set +e
                    exit
                    EOSSH
                """
                script {
                    LOCAL_ARTIFACT_MD5SUM = sh (script: "${SSH_CONNECTION_CMD}${STAGING_ENV_IP} cat ${REMOTE_COPY_ARTIFACT_DIR}/${ARTIFACT_NAME}.md5sum_local | awk \'{print \$1}\'", returnStdout: true ).trim()
                    REMOTE_ARTIFACT_MD5SUM = sh (script: "${SSH_CONNECTION_CMD}${STAGING_ENV_IP} cat ${REMOTE_COPY_ARTIFACT_DIR}/${ARTIFACT_NAME}.md5sum_remote | awk \'{print \$1}\'", returnStdout: true ).trim()
                    
                    echo "LOCAL_ARTIFACT_MD5SUM = ${LOCAL_ARTIFACT_MD5SUM}"
                    echo "REMOTE_ARTIFACT_MD5SUM = ${REMOTE_ARTIFACT_MD5SUM}"
                    
                    sh (returnStdout: true, script: """#!/bin/bash -xe
                        if [[ "${LOCAL_ARTIFACT_MD5SUM}" = "${REMOTE_ARTIFACT_MD5SUM}" ]]; then
                            echo "Artifacts MD5SUM Check Passed !!! Copy Successfull"
                        else
                            echo "Artifacts MD5SUM Check Failed !!! Please Re-Deploy"
                            exit 1
                        fi
                        """.stripIndent())
                }
            }
        }

		stage('STAGING: Deployment') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${STAGING_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    sudo systemctl stop ${SYSTEMD_SERVICE_NAME}
                    sudo mkdir -p ${REMOTE_DEPLOY_DIR}
                    sudo chown -R ${USER_PERMISSION}:${USER_PERMISSION} ${REMOTE_DEPLOY_DIR}
                    rm -rf ${REMOTE_DEPLOY_DIR}/*
                    mv ${REMOTE_COPY_ARTIFACT_DIR}/${ARTIFACT_NAME}/* ${REMOTE_DEPLOY_DIR}/
                    sudo ls -ltrh ${REMOTE_DEPLOY_DIR}
                    sudo systemctl start ${SYSTEMD_SERVICE_NAME}
                    set +e
                    exit
                    EOSSH
                """
            }
        }

		stage('STAGING: Running Unit Tests') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${STAGING_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    /usr/bin/nosetests3 /opt/python-btc-price-api/tests
                    set +e
                    exit
                    EOSSH
                """
            }
        }

		stage('PRODUCTION: Copying Artifacts') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${PROD_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    sudo rm -rf ${REMOTE_COPY_ARTIFACT_DIR}
                    sudo mkdir -p ${REMOTE_COPY_ARTIFACT_DIR}
                    sudo chown -R ${USER_PERMISSION}:${USER_PERMISSION} ${REMOTE_COPY_ARTIFACT_DIR}
                    ls -ltrh
                    set +e
                    exit
                    EOSSH
                """
                sh """
                cd ${WORKSPACE}/${BRANCH}
                ${SCP_CONNECTION_CMD} ${BRANCH}-${DATE}.zip ${BRANCH}-${DATE}.md5sum_local ${USERNAME}@${PROD_ENV_IP}:${REMOTE_COPY_ARTIFACT_DIR}
                """
            }
        }

		stage('PRODUCTION: Check MD5Sum of Artifacts') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${PROD_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    cd ${REMOTE_COPY_ARTIFACT_DIR}
                    md5sum ${ARTIFACT_NAME}.zip > ${ARTIFACT_NAME}.md5sum_remote
                    unzip ${ARTIFACT_NAME}.zip -d ${ARTIFACT_NAME}
                    ls -ltrh
                    set +e
                    exit
                    EOSSH
                """
                script {
                    LOCAL_ARTIFACT_MD5SUM = sh (script: "${SSH_CONNECTION_CMD}${STAGING_ENV_IP} cat ${REMOTE_COPY_ARTIFACT_DIR}/${ARTIFACT_NAME}.md5sum_local | awk \'{print \$1}\'", returnStdout: true ).trim()
                    REMOTE_ARTIFACT_MD5SUM = sh (script: "${SSH_CONNECTION_CMD}${STAGING_ENV_IP} cat ${REMOTE_COPY_ARTIFACT_DIR}/${ARTIFACT_NAME}.md5sum_remote | awk \'{print \$1}\'", returnStdout: true ).trim()
                    
                    echo "LOCAL_ARTIFACT_MD5SUM = ${LOCAL_ARTIFACT_MD5SUM}"
                    echo "REMOTE_ARTIFACT_MD5SUM = ${REMOTE_ARTIFACT_MD5SUM}"
                    
                    sh (returnStdout: true, script: """#!/bin/bash -xe
                        if [[ "${LOCAL_ARTIFACT_MD5SUM}" = "${REMOTE_ARTIFACT_MD5SUM}" ]]; then
                            echo "Artifacts MD5SUM Check Passed !!! Copy Successfull"
                        else
                            echo "Artifacts MD5SUM Check Failed !!! Please Re-Deploy"
                            exit 1
                        fi
                        """.stripIndent())
                }
            }
        }

		stage('PRODUCTION: Deployment') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${PROD_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    sudo systemctl stop ${SYSTEMD_SERVICE_NAME}
                    sudo mkdir -p ${REMOTE_DEPLOY_DIR}
                    sudo chown -R ${USER_PERMISSION}:${USER_PERMISSION} ${REMOTE_DEPLOY_DIR}
                    rm -rf ${REMOTE_DEPLOY_DIR}/*
                    mv ${REMOTE_COPY_ARTIFACT_DIR}/${ARTIFACT_NAME}/* ${REMOTE_DEPLOY_DIR}/
                    sudo ls -ltrh ${REMOTE_DEPLOY_DIR}
                    sudo systemctl start ${SYSTEMD_SERVICE_NAME}
                    set +e
                    exit
                    EOSSH
                """
            }
        }

		stage('PRODUCTION: Running Unit Tests') {
            steps {
                sh """
		        ${SSH_CONNECTION_CMD}${PROD_ENV_IP} <<'EOSSH'
                    #!/bin/bash
                    set -xe
                    /usr/bin/nosetests3 /opt/python-btc-price-api/tests
                    set +e
                    exit
                    EOSSH
                """
            }
        }
    }
}
