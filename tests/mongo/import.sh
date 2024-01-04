#!/bin/sh
mongoimport --host localhost --username foo --password password --authenticationDatabase admin --db FaceID --collection BodyFaceName --type json --file /docker-entrypoint-initdb.d/data.json