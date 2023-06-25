#!/bin/bash
ECS_CLUSTER_NAME="Your cluster name"
INSTANCE_ID=`curl http://169.254.169.254/latest/meta-data/instance-id`
CONTAINERS=`docker ps|grep -v amazon-ecs-agent|awk '{print $1"\t"$NF}'`
COMMAND='curl -s -o /dev/null -I -w %{http_code} http://169.254.169.254/latest/meta-data/spot/termination-time'
CODE=`${COMMAND}`
while [ ${CODE} -ne 200 ]; do
 sleep 10
 CODE=`${COMMAND}`
done
curl -X POST -H 'Content-type: application/json' --data '{"channel":"#spot_notification","username":"spot-notifier","text":"*```'"${INSTANCE_ID}"' is marked for termination in '"${ECS_CLUSTER_NAME}"'.Below are the containers running on '"${INSTANCE_ID}"'.```*\n*```'"${CONTAINERS}"'```*","icon_emoji":":warning:"}' http://Your_slack_webhook
