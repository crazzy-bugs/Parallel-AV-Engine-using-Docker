#!/bin/bash

# Update escan
docker run --name=escan malice/escan update
docker commit escan malice/escan:updated
docker rm escan

# Update mcafee
docker run --name=mcafee malice/mcafee update
docker commit mcafee malice/mcafee:updated
docker rm mcafee

# Update comodo
docker run --name=comodo malice/comodo update
docker commit comodo malice/comodo:updated
docker rm comodo