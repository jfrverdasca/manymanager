docker-compose up -d
docker exec -it manymanager_postgres_1 psql -U postgres
$ create database manymanager;
$ \q

docker-compose restart


Service should be now ready to use:
http://<server_ip>:2048/

