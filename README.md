# GIVE Monitoring Service
Monitoring for GIVE microservices in cloud.gov

## Why this project
The GIVE project is composed of many different microservices, each needing to
be monitored for performance, stability, and uptime. The monitoring
microservice has the following goals:
* Provide monitoring capabilities for GIVE microservices
* Alert GIVE operators/admins on specified metric thresholds

## CI/CD Workflows with GitHub Actions
The most up-to-date information about the CI/CD flows for this repo can be found in the
[GitHub workflows directory](https://github.com/18F/identity-give-monitoring/tree/main/.github/workflows)

## Implementation
GIVE monitoring is a Prometheus server deployed to Cloud.gov and configured to monitor
applications based on DNS querying of the application routes. For all applications we
wish to monitor, adding a `dns_sd_config` for within the [prometheus-config.yml](#prometheus-config.yml)
adds the application to prometheus's monitoring. By using the `dns_sd_config` we are
able to see and query **all** instances of the application, and are not load balanced to
random instances every query.

## Generating the config file
The config file is generic to prevent having to have multiple configuration files
per space (dev, test, prod, etc). The [prometheus-config.yml](#prometheus-config.yml)
file is intended to be fed to `envsubst` after the appropriate environment variable
has been set. The config should be output to `prometheus.yml`.
```shell
envsubst < prometheus-config.yml > prometheus.yml
```

## Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in
[CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright
and related rights in the work worldwide are waived through the
[CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication.
By submitting a pull request, you are agreeing to comply with this waiver of
copyright interest.
