#!/bin/sh
mongoimport --db FaceID --collection BodyFaceName --type json --file /docker-entrypoint-initdb.d/data.json
mongoimport --db FaceID --collection staffs --type json --file /docker-entrypoint-initdb.d/staff.json