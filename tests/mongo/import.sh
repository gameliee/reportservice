#!/bin/sh
mongoimport --username foo --password password --authenticationDatabase admin --db FaceID --collection BodyFaceName --type json --file /docker-entrypoint-initdb.d/data.json
mongoimport --username foo --password password --authenticationDatabase admin --db FaceID --collection staffs --type json --file /docker-entrypoint-initdb.d/staff.json