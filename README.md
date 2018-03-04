# Distributed websocket server

## Project created as a part of interview.

### How to run:
  1. git clone git@github.com:cheeeee/distributed_ws_cluster_docker.git
  2. cd distributed_ws_cluster_docker/cluster
  3. docker-compose build
  4. docker-compose up

### To add more clients and simulate load:
  1. cd distributed_ws_cluster_docker/cluster
  2. docker-compose scale client=**n**  
  where n = desired number of clients.
  3. Check terminal with main docker-compose output.

### To activate monitor for scaling:  
Monitor will automatically add new container if load more then 75% (users / limit).
  1. cd distributed_ws_cluster_docker/cluster
  2. python3 service_monitor.py

### To manually change limits for desired websocket server:
  1. Go to http://localhost/api/v1/limits/
  2. Fill field with desired limit and press enter.
  3. In 5-7 second control app will recieve new limit from websocket server.

### Requirments on docker host:
  1. request library for monitor.
  2. Free 10.5.0.0/24 subnet.
  3. Last docker.
