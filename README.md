        _____            __  __
       | ____|_ ____   _|  \/  | __ _ _ __   __ _  __ _  ___
       |  _| | '_ \ \ / / |\/| |/ _` | '_ \ / _` |/ _` |/ _ \
       | |___| | | \ V /| |  | | (_| | | | | (_| | (_| |  __/
       |_____|_| |_|\_/ |_|  |_|\__,_|_| |_|\__,_|\__, |\___|
                                                  |___/
                    AWS Infrastructure Management


### Environment Manage

This is a small Python CLI used to manage AWS environments that have been brought up with some specific naming standards. If your environment conforms to the folliwng tagging/naming standards, you can use this tool:

```
Product - The name of your product (eg. my-awesome-product)
Environment - The name of your product's environment (dev, qa, stg, prod)
```

Secrets are expected to be stored in SSM parameter store using the following structure:

```
/{product_name}/{environment_name}/key
/{product_name}/{environment_name}/prefix/key
```

#### Usage

The `dist` directory contains a built native executable (Mac OSX only right now) that can be used to execute commands. You can see what commands are available by just running the `dist/envmanage` command.

The easiest way to use this tool is to create a set of shell scripts that configure your environment for each of your product/environments. For example, the foo dev environment could have a shell script named `foo-dev.sh` that looked like this:

```bash
#!/bin/bash

export PRODUCT=foo
export ENV=dev
export AWS_PROFILE=foo-dev-aws (this is a profile from ~/.aws/credentials)
export AWS_REGION=us-west-2
export KUBECONFIG=/Users/barry/Customers/BuildingEngines/Git/Cumulus/terraform/products/v2/orchestrator/kubeconfig_v2-dev
```

Source that file in with `source foo-dev.sh`

This CLI will use the environment variables set in that script.

#### Options

This CLI allows you to view your environment's autoscaling groups + instances, scale an environment up/down and manage your environment's secrets.

By default, the CLI will output results in text format. If you'd like to return JSON, either set the environment variable `ENVMANAGE_FORMAT=json` or use the -f/--format parameter.

##### Secrets

To view your environment's secrets:

```bash
./envmanage list-secrets
```

You can view the value of a single secret with:

```bash
./envmanage show-secret -n {secret name}
```

If you need to create or update a secret:

```bash
./envmanage set-secret -n {secret_name} -v {secret_value} -encrypt / -no-encrypt
```

##### Scaling

Each environment will be configured for scaling independently. To see how the environment is configured:

```bash
./envmanage show-env
```

In the text format view you will see your environment's instances as well as its autoscaling groups.

If you need to scale an environment down:

```bash
./envmanage scale-down -a {autoscaling group name} --min {min number of instances} --max {max number of instances} -d {desired number of instances}
```

The default scale down values will bring an environment to a min/max/desired of 0, which means it completely scales down the instances in the environment.

To scale up:

```bash
./envmanage scale-up -a {autoscaling group name} --min {min number of instances} --max {max number of instances} -d {desired number of instances}
```

The default scale up values will bring an environment to a min/max/desired of 1

#### License

You are free to use this code for your own purposes, but I retain copyright to it.

Copyright © 2019 by Barry Walker. All Rights Reserved.
