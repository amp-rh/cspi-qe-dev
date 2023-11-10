from enum import Enum


class ImageSourceType(Enum):
    NONE = 0
    PIPELINE_IMAGE = 1
    IMAGE_STREAM_TAG = 2