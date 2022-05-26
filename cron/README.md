# Job Scheduler

This application provides the ability to run jobs on a schedule in the CF environment. It is based on [Supercronic](https://github.com/aptible/supercronic). It has the ability to run Cloud Foundry Tasks using the [CF v8 CLI](https://github.com/cloudfoundry/cli) using the [run-task](https://cli.cloudfoundry.org/en-US/v8/run-task.html) command.

Task are described in the [crontab](crontab) file.
