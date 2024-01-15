from typing import List
from datetime import datetime
from .models import StaffCodeStr


def pipeline_staffs_inou(
    staffcodes: List[StaffCodeStr] = [],
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
    threshold: float = 0.63,
    has_mask: bool = False,
    bodyfacename_collection: str = "BodyFaceName",
):
    """get staffs min and max recognition time within the windows [begin, end]"""
    query = [
        {"$match": {"staff_code": {"$in": staffcodes}}},
        {
            "$lookup": {
                "from": bodyfacename_collection,
                "localField": "staff_code",
                "foreignField": "staff_id",
                "as": "found",
                "pipeline": [
                    {
                        "$match": {
                            "image_time": {"$gte": begin, "$lte": end},
                            "face_reg_score": {"$gte": threshold},
                            "has_mask": has_mask,
                            "staff_id": {"$in": staffcodes},
                        }
                    },
                    {"$project": {"staff_id": 1, "image_time": 1}},
                    {"$sort": {"image_time": 1}},
                    {
                        "$group": {
                            "_id": "$staff_id",
                            "firstDocument": {"$first": "$image_time"},
                            "lastDocument": {"$last": "$image_time"},
                        }
                    },
                ],
            }
        },
        {"$unwind": {"path": "$found", "includeArrayIndex": "string", "preserveNullAndEmptyArrays": True}},
        {
            "$project": {
                "_id": 0,
                "staff_code": "$staff_code",  # fixed field name, do not change it
                "full_name": 1,  # fixed field name, do not change it
                "email": 1,
                "unit": 1,
                "department": 1,
                "title": 1,
                "state": "$state",  # fixed field name, do not change it
                "first_record": "$found.firstDocument",  # fixed field name, do not change it
                "last_record": "$found.lastDocument",  # fixed field name, do not change it
            }
        },
    ]
    return query


def pipeline_count(begin: datetime, end: datetime, threshold: float, has_mask: bool = False):
    pipeline = [
        {
            "$match": {
                "image_time": {
                    "$gte": begin,
                    "$lte": end,
                },
                "face_reg_score": {"$gte": threshold},
                "has_mask": has_mask,
            }
        },
        {"$group": {"_id": "$staff_id"}},
        {"$group": {"_id": None, "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "count": 1}},
    ]
    return pipeline
