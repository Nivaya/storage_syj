# -*-coding:utf-8 -*-

from flask import request


class Api:
    def __init__(self):
        pass

    @classmethod
    def reqs(cls, values):
        para = {}
        values = values.split(',')
        for value in values:
            val = request.values.get(value)
            para[value] = val if val else ''
        return para
