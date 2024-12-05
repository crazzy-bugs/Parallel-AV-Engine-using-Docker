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

#Update windows-defender
docker run --name=windows-defender malice/windows-defender update
docker commit windows-defender malice/windows-defender:updated
docker rm windows-defender

#Update frot
docker run --name=fprot malice/fprot update
docker commit fprot malice/fprot:updated
docker rm fprot