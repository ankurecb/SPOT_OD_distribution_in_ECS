# SPOT_OD_distribution_in_ECS
Managing spot and ondemand instances distribution in AWS ECS

This project is about managing the spot and ondemand instances distribution for the ECS clusters. It consists of two python scripts -
1. This script will increase the ondemand instance distribution gradually if there is any spot instances unavailability at the AWS end.
2. This script will gradually revert back to ondemand instances when the spot avalibility is restored at AWS end and we are able to launch spot instances in our ASG.
