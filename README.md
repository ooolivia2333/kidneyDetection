# SW4ML-cw3

## docker
assume the simulator will run outside of docker
when switching between running local or docker, remember to change the ip address
  * listener.py
  * pager_system.py
  * and the path in app.py
* docker build -t cw3 .
* docker run -p 8440:8440 -p 8441:8441 cw3
* test: 1155