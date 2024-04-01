db = db.getSiblingDB("admin")

db.createRole({
    role: "readBodyFaceName",
    privileges: [
        { resource: { db: "FaceID", collection: "BodyFaceName" }, actions: ["find"] },
    ],
    roles: []
})

db.createRole({
    role: "readStaffs",
    privileges: [
        { resource: { db: "FaceID", collection: "staffs" }, actions: ["find"] },
    ],
    roles: []
})

db.createUser({
    user: "reportuser",
    pwd: "reportpassword",
    roles: [
        "readBodyFaceName",
        "readStaffs",
        { role: "readWrite", db: "TestReportService" }

    ]
})
db.getUsers()