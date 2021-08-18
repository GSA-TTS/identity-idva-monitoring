# GitHub Actions CI/CD workflows

## Check Config
The check-config workflow will run the Prometheus 'promtool check config'
command to validate the configuration file.

## Deploy
Deploys the project to the correct IDVA environment within Cloud.gov. The
deploy workflow will run a check on the config file and only deploy if that
test are successful. Deployment will also only be triggered in the 18F
repository. This will prevent forks from needlessly running workflows that
will always fail (forks won't be able to authenticate into the dev environment).
