from flask_restx import fields

from . import ModelCreator, create_email_field, create_id_field


class SubunitIdModel(ModelCreator):
    id = create_id_field(
        required=True,
        description="ID of the subunit"
    )


class CommonSubunitModel(ModelCreator):
    name = fields.String(
        required=False,
        description='Name of the SubUnit',
        example='Software development department',
        min_length=2,
        max_length=512
    )
    address = fields.String(
        required=False,
        description='subunit`s address',
        example='vul. Naukova, 13',
        min_length=4,
        max_length=256
    )
    leader = create_id_field(
        required=True,
        description="ID of subunit`s leader"
    )
    phone = fields.String(
        required=False,
        description='SubUnit`s phone number',
        example='(380)333-3333',
        min_length=6,
        max_length=32
    )
    email = create_email_field(
        required=True,
        description="Email of the SubUnit"
    )


class FullSubunitModel(SubunitIdModel, CommonSubunitModel):
    pass