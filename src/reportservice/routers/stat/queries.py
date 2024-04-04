from datetime import datetime
from typing import Optional, Dict
from pydantic import AwareDatetime
from .models import QueryParamters, StaffCodeStr, MongoSampleStateOfStaffModel, MongoStateOfStaffModel


def query_find_staff(query_params: QueryParamters):
    """find staffs in the database by OR all conditions in `query_params`"""
    pipline = [
        {
            "$match": {
                "$or": [
                    {"staff_code": {"$in": query_params.staffcodes}},
                    {"full_name": {"$in": query_params.fullnames}},
                    {"unit": {"$in": query_params.units}},
                    {"department": {"$in": query_params.departments}},
                    {"title": {"$in": query_params.titles}},
                    {"email": {"$in": query_params.emails}},
                    {"cellphone": {"$in": query_params.cellphones}},
                    {"$expr": query_params.custom_query},
                ],
            }
        },
        {
            "$project": {
                "_id": 0,
                "straight_img": 0,
                "left_img": 0,
                "right_img": 0,
                "embeddings": 0,
            },
        },
    ]
    return pipline


def query_find_staff_inout(
    staffcodes: list[StaffCodeStr],
    begin: datetime = "2023-12-27T00:00:00.000+00:00",
    end: datetime = "2023-12-27T23:59:59.999+00:00",
    threshold: float = 0.63,
    has_mask: bool = False,
):
    """create a query to find in-out information which related to staffcodes"""
    pipeline = [
        {
            "$match": {
                "image_time": {
                    "$gte": begin,
                    "$lte": end,
                },
                "face_reg_score": {
                    "$gte": threshold,
                },
                "has_mask": has_mask,
                "staff_id": {
                    "$in": staffcodes,
                },
            },
        },
        {
            "$project": {
                "staff_id": 1,
                "image_time": 1,
            },
        },
        {
            "$sort": {
                "image_time": 1,
            },
        },
        {
            "$group": {
                "_id": "$staff_id",
                "firstDocument": {
                    "$first": "$image_time",
                },
                "lastDocument": {
                    "$last": "$image_time",
                },
            },
        },
        {
            "$project": {
                "_id": 0,
                "staff_code": "$_id",
                "firstDocument": 1,
                "lastDocument": 1,
            },
        },
    ]
    return pipeline


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
                "let": {"staff_code_var": "$staff_code"},
                "as": "found",
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {
                                        "$eq": [
                                            "$staff_id",
                                            "$$staff_code_var",
                                        ],
                                    },
                                    {
                                        "$gte": [
                                            "$image_time",
                                            begin,
                                        ],
                                    },
                                    {
                                        "$lte": [
                                            "$image_time",
                                            end,
                                        ],
                                    },
                                    {
                                        "$gte": ["$face_reg_score", threshold],
                                    },
                                    {"$eq": ["$has_mask", has_mask]},
                                ],
                            },
                        },
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
        {"$unwind": {"path": "$found", "includeArrayIndex": "arrayIndex", "preserveNullAndEmptyArrays": True}},
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


def pipeline_count_shoulddiemdanh():
    pipeline = [
        {
            "$match": {
                "working_state": MongoStateOfStaffModel.active,
            },
        },
        {
            "$group": {
                "_id": "staff_code",
                "count": {
                    "$sum": 1,
                },
            },
        },
        {
            "$project": {
                "_id": 0,
            },
        },
    ]
    return pipeline


def pipeline_count_has_sample():
    pipeline = [
        {
            "$match": {
                "sample_state": MongoSampleStateOfStaffModel.ready_to_checkin_checkout,
            },
        },
        {
            "$group": {
                "_id": "staff_code",
                "count": {
                    "$sum": 1,
                },
            },
        },
        {
            "$project": {
                "_id": 0,
            },
        },
    ]
    return pipeline


def condition_count_record_by_id(
    begin: AwareDatetime,
    end: AwareDatetime,
    staff_id: Optional[StaffCodeStr] = None,
    threshold: float = 0.63,
    has_mark: bool = False,
) -> Dict:
    """return the count condition"""
    condition = {
        "image_time": {"$gte": begin, "$lte": end},
        "face_reg_score": {"$gte": threshold},
        "has_mask": has_mark,
    }

    if staff_id is not None:
        condition["staff_id"] = staff_id

    return condition


def pipeline_get_record_by_id(
    begin: AwareDatetime,
    end: AwareDatetime,
    staff_id: Optional[StaffCodeStr] = None,
    threshold: float = 0.63,
    has_mark: bool = False,
    offset: int = 0,
    limit: int = 10,
):
    pipeline = [
        {
            "$match": {
                "image_time": {"$gte": begin, "$lte": end},
                "face_reg_score": {"$gte": threshold},
                "has_mask": has_mark,
            },
        },
        {
            "$sort": {
                "image_time": -1,
            },
        },
        {
            "$skip": offset,
        },
        {
            "$limit": limit,
        },
        {
            "$project": {
                "image_time": 1,
                "staff_id": 1,
                "camera_id": 1,
                "face_reg_score": 1,
                "img_link": 1,
                "sub_id": 1,
            },
        },
    ]

    if staff_id is not None:
        pipeline[0]["$match"]["staff_id"] = staff_id

    return pipeline


def pipeline_stat_by_camera(
    begin: AwareDatetime,
    end: AwareDatetime,
    staff_id: Optional[StaffCodeStr] = None,
    threshold: float = 0.63,
    has_mark: bool = False,
    timezone: str = "Asia/Ho_Chi_Minh",
):
    """pipeline for counting the number of records by camera_id and by date"""
    pipeline = [
        {
            "$match": {
                "image_time": {"$gte": begin, "$lte": end},
                "face_reg_score": {"$gte": threshold},
                "has_mask": has_mark,
            },
        },
        {
            "$group": {
                "_id": {
                    "camera_id": "$camera_id",
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$image_time",
                            "timezone": timezone,
                        },
                    },
                },
                "count": {
                    "$sum": 1,
                },
            },
        },
        {
            "$project": {"_id": 0, "date": "$_id.date", "camera_id": "$_id.camera_id", "count": 1},
        },
    ]
    if staff_id is not None:
        pipeline[0]["$match"]["staff_id"] = staff_id

    return pipeline
