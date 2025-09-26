import re
from typing import List, Any, Optional
from fastapi import UploadFile
from pydantic import BaseModel, Field, validator

from src.database.enums import ProductAttributeDataType

class ProductAttributeParam(BaseModel):
    attr_id:int |None=None
    attr_key: str
    attr_value: List[Any]
    attr_value_datatype: ProductAttributeDataType
    sort: int 

