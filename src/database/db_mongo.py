import datetime

import mongoengine as db
from mongoengine import DateTimeField
from pymongo import UpdateOne, InsertOne

from src.api.customer_exception import ValidationException

# db.connect(db="test", host="mongodb://localhost:27017")

"""
pip install pymongo
pip install mongoengine

pymongo 文档： https://www.mongodb.com/zh-cn/docs/languages/python/pymongo-driver/current/read/specify-a-query/
mongoengine 文档：https://docs.mongoengine.org/guide/querying.html
                 https://www.cnblogs.com/zhenyauntg/p/13201826.html
mongo 一对多数据 ：https://cloud.tencent.com/developer/ask/sof/101750948
                 https://deepinout.com/mongoengine/mongoengine-questions/217_mongoengine_mongoengine_listfield_within_a_embeddeddocument_throws_typeerror_on_validation.html
"""


class MongoDbModel(db.Document):
    meta = {
        'abstract': True,
        'allow_inheritance': True
    }
    deleted_at = DateTimeField(default=None, null=True)

    @classmethod
    def connect(cls, db_name=None, username=None, password=None, host='mongodb://localhost:27017'):
        """链接数据库"""
        if not db_name:
            db_name = 'test'
        if not username and not password:
            db.connect(host=host, db=db_name, username=username, password=password)
        else:
            db.connect(host=host, db=db_name)

    @classmethod
    def disconnect(cls):
        """断开数据库"""
        db.disconnect()

    @classmethod
    def mongo_add(cls, **kwargs):
        return cls(**kwargs).save()

    @classmethod
    def find_one(cls, **kwargs):
        return cls.find_many(**kwargs).first()

    @classmethod
    def find_many(cls, **kwargs):
        kwargs['deleted_at'] = None
        return cls.objects(**kwargs)
        # return cls.objects.filter(**kwargs)

    @classmethod
    def find_add_paginate(cls, page, per_page, order_by=None, asc=True, **kwargs):
        skip = (page - 1) * per_page
        kwargs['deleted_at'] = None
        total = cls.find_many(**kwargs).count()
        total_pages = total // per_page + (1 if total % per_page > 0 else 0)
        if order_by:
            if asc:
                items = cls.find_many(**kwargs).order_by(order_by).skip(skip).limit(per_page)
            else:
                items = cls.find_many(**kwargs).order_by(f'-{order_by}').skip(skip).limit(per_page)
        else:
            items = cls.find_many(**kwargs).skip(skip).limit(per_page)
        return total, total_pages, items

    @classmethod
    def add_or_update_many(cls, objects):
        cls_collection = cls._get_collection()
        operations = []
        for obj in objects:
            if obj.id:
                tmp_obj = cls.find_one(id=obj.id)
                if tmp_obj is None:
                    raise ValidationException(f'数据[{obj.id}]不存在')
                operations.append(UpdateOne({'_id': obj.id}, {'$set': obj.to_mongo()}))
            else:
                operations.append(InsertOne(obj.to_mongo()))
        if operations:
            result = cls_collection.bulk_write(operations)
            if result.inserted_count or result.matched_count:
                return True
            else:
                return False
        else:
            return False

    @classmethod
    def delete_many_by_objects(cls, objects):
        ids = [obj.id for obj in objects]
        return cls.delete_many_by_ids(ids)

    @classmethod
    def delete_many_by_ids(cls, ids):
        cls_collection = cls._get_collection()
        # result = cls_collection.delete_many({'_id': {'$in': ids}})
        # return result.deleted_count > 0
        cls_collection.update_many({'_id': {'$in': ids}}, {'$set': {'deleted_at': datetime.datetime.now()}})

    @classmethod
    def delete_many_by_condition(cls, **kwargs):
        cls_collection = cls._get_collection()
        filter_dict = {}
        for key, value in kwargs.items():
            field, operator = key.split('__', 1)
            if operator == 'in':
                filter_dict[field] = {'$in': value}
            elif operator == 'gt':
                filter_dict[field] = {'$gt': value}
            elif operator == 'eq':
                filter_dict[field] = value
            elif operator == 'gte':
                filter_dict[field] = {'$gte': value}
            elif operator == 'lt':
                filter_dict[field] = {'$lt': value}
            elif operator == 'lte':
                filter_dict[field] = {'$lte': value}
            elif operator == 'ne':
                filter_dict[field] = {'$ne': value}
            elif operator == 'like':
                filter_dict[field] = {'$regex': f'^{value}$', '$options': 'i'}
            elif operator == 'ilike':
                filter_dict[field] = {'$regex': f'^{value}$', '$options': 'i'}
            elif operator == 'notlike':
                filter_dict[field] = {'$not': {'$regex': f'^{value}$', '$options': 'i'}}
            elif operator == 'notilike':
                filter_dict[field] = {'$not': {'$regex': f'^{value}$', '$options': 'i'}}
            else:
                filter_dict[key] = value
        # result = cls_collection.delete_many(filter_dict)
        # return result.deleted_count > 0
        cls_collection.update_many(filter_dict, {'$set': {'deleted_at': datetime.datetime.now()}})

    @classmethod
    def delete_many_by_dict(cls, **kwargs):
        cls.objects.filter(**kwargs).update(set__deleted_at=datetime.datetime.now())

    def mongo_update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self.save()

    def mongo_delete(self):
        self.deleted_at = datetime.datetime.now()
        self.save()
        return True

    @classmethod
    def mongo_drop(cls):
        cls.objects.update(set__deleted_at=datetime.datetime.now())
        # cls._get_collection().drop()

    def mongo_close(self):
        self.disconnect()
