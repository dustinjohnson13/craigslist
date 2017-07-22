#!groovy

stage('Run') {
    node {

        def build = "${env.JOB_NAME} - #${env.BUILD_NUMBER}".toString()

        currentBuild.result = "SUCCESS"

        try {

            checkout scm

            def urls = [
//                'https://omaha.craigslist.org/search/sss?query=progressive+press&format=rss',
//                'https://omaha.craigslist.org/search/sss?query=turret+press&format=rss',
//                'https://omaha.craigslist.org/search/sss?query=table+saw&excats=7-13-22-2-24-1-23-1-1-1-1-1-1-9-10-2-1-2-2-8-1-1-1-1-1-4-1-3-1-3-1-1-1-1-7-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-2-1-1-1-1-1-1-2-1-1-1-1-3-1-1-1-1-1-1-1-1-1-1-1&sort=rel&search_distance=30&postal=68118&format=rss',
//                'https://omaha.craigslist.org/search/sss?query=miter%20saw&format=rss',
'https://omaha.craigslist.org/search/sss?sort=date&query=canoe&format=rss'
            ]

            def command = 'python3 src/main.py'
            for (String url : urls) {
                command += " \"$url\""
            }

            sh command

        } catch (err) {
            currentBuild.result = "FAILURE"

            emailext body: "${env.JOB_NAME} failed! See ${env.BUILD_URL} for details.", recipientProviders: [[$class: 'DevelopersRecipientProvider']], subject: "$build failed!"

            throw err
        }
    }
}