docker-compose up -d<br>
docker exec -it manymanager_postgres_1 psql -U postgres<br>
$ create database manymanager;<br>
$ \q<br>

docker-compose restart


Service should be now ready to use:<br>
http://<server_ip>:2048/

