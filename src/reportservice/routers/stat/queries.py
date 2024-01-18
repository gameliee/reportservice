from typing import List
from datetime import datetime
from .models import QueryParamters


def query_find_staff(query_params: QueryParamters):
    """find staffs in the database by OR all conditions in `query_params`"""
    query = {
        "$or": [
            {"staff_code": {"$in": query_params.staffcodes}},
            {"full_name": {"$in": query_params.fullnames}},
            {"unit": {"$in": query_params.units}},
            {"department": {"$in": query_params.departments}},
            {"title": {"$in": query_params.titles}},
            {"email": {"$in": query_params.emails}},
            {"cellphone": {"$in": query_params.cellphones}},
            {"$expr": {"$or": query_params.custom_queries}},
        ],
    }
    return query


def pipeline_staffs_inou(
    query_params: QueryParamters,
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
    threshold: float = 0.63,
    has_mask: bool = False,
    bodyfacename_collection_name: str = "BodyFaceName",
):
    """get staffs min and max recognition time within the windows [begin, end]
    All the parameters are optional and will be OR combined.
    """
    query = [
        {
            "$match": query_find_staff(query_params),
        },
        {
            "$lookup": {
                "from": bodyfacename_collection_name,
                "localField": "staff_code",
                "foreignField": "staff_id",
                "as": "found",
                "pipeline": [
                    {
                        "$match": {
                            "image_time": {"$gte": begin, "$lte": end},
                            "face_reg_score": {"$gte": threshold},
                            "has_mask": has_mask,
                            "staff_id": "$staff_code",
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
                "sex": 1,
                "cellphone": 1,
                "email": 1,
                "unit": 1,
                "department": 1,
                "title": 1,
                "sample_state": 1,
                "working_state": 1,
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
