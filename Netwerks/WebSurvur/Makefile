.PHONY: all transfer up caddy mailu 0xadd1e code
all: transfer
transfer:
	rsync -rv . root@116.203.64.22:/docker_conf/uni/webserver
	ssh root@116.203.64.22 "cd /docker_conf/uni/webserver && make up"
up: server
	docker exec caddy-gen pkill -USR1 caddy
server:
	docker-compose up -d --build
