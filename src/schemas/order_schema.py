from config import ma, db
from marshmallow import fields, validates
from marshmallow.validate import Length, OneOf, And, Regexp
from marshmallow.exceptions import ValidationError


class BookingSchema(ma.Schema):
    class Meta:
        fields = ('id', 'total_price', 'is_paid')
        ordered = True