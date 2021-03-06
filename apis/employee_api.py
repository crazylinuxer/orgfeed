from flask_restx.namespace import Namespace
from flask import request, abort
from flask_jwt_extended import (jwt_required, get_jwt_identity, jwt_refresh_token_required,
                                create_access_token, create_refresh_token)

from services import employee_service, get_uuid
from .utils import OptionsResource
from models import required_query_params, query_param_to_set
from models.employee_model import (AuthModel, FullEmployeeModel, EmployeeRegistrationModel,
                                   TokenModel, EmployeeEditModel, EmployeeIdModel, EmployeeType)


api = Namespace('employee', description='Employees-related actions')

auth = api.model(
    'auth_model',
    AuthModel(),
)

token = api.model(
    'token_model',
    TokenModel()
)

employee_registration = api.model(
    'employee_registration_model',
    EmployeeRegistrationModel()
)

full_employee = api.model(
    'full_employee_model',
    FullEmployeeModel()
)

employee_edit = api.model(
    'employee_edit_model',
    EmployeeEditModel()
)

id_model = api.model(
    'id_model',
    EmployeeIdModel()
)


@api.route('')
class Employee(OptionsResource):
    @api.doc('get_employee', security='apikey', params=required_query_params({'id': 'employee ID'}))
    @api.marshal_with(full_employee, code=200)
    @api.response(404, description="Employee not found")
    @jwt_required
    def get(self):
        """Get employee`s account info"""
        return employee_service.get_employee(get_uuid(request)), 200

    @api.doc('edit_employee', security='apikey', params=required_query_params({'id': 'employee ID'}))
    @api.marshal_with(full_employee, code=201)
    @api.response(404, description="Employee or subunit not found")
    @api.response(403, description="Not allowed to edit this employee's info")
    @api.response(409, description="Employee with given email already exists")
    @api.response(422, description="All fields are null")
    @api.expect(employee_edit, validate=True)
    @jwt_required
    def put(self):
        """Edit employee`s account info (only for admins)"""
        return employee_service.edit_employee(get_jwt_identity(), get_uuid(request), **api.payload), 201

    @api.doc('employee_register', security='apikey')
    @api.expect(employee_registration, validate=True)
    @api.marshal_with(full_employee, code=201)
    @api.response(403, description="Non-admins can not register new employees")
    @api.response(404, description="SubUnit not found")
    @api.response(409, description="Employee with given email already exists")
    @api.response(422, description="Incorrect password given")
    @jwt_required
    def post(self):
        """Register a new employee (only for admins)"""
        return employee_service.register_employee(get_jwt_identity(), **api.payload), 201


@api.route('/auth')
class Auth(OptionsResource):
    @api.doc('employee_auth')
    @api.marshal_with(token, code=200)
    @api.expect(auth, validate=True)
    @api.response(401, description="Invalid credentials")
    def post(self):
        """Log into an account"""
        return employee_service.get_token(**api.payload), 200


@api.route('/id')
class EmployeeId(OptionsResource):
    @api.doc('get_employee_id', security='apikey')
    @api.response(200, description="Success", model=id_model)
    @jwt_required
    def get(self):
        """Get an ID by JWT token"""
        return {"id": get_jwt_identity()}, 200


@api.route('/auth/refresh')
class AuthRefresh(OptionsResource):
    @api.doc('employee_auth_refresh', security='apikey')
    @api.marshal_with(token, code=200)
    @jwt_refresh_token_required
    def post(self):
        """Refresh pair of tokens"""
        identity = get_jwt_identity()
        return {
               'access_token': create_access_token(identity=identity),
               'refresh_token': create_refresh_token(identity=identity),
               'user_id': identity
        }, 200


@api.route('/fired')
class AuthRefresh(OptionsResource):
    @api.doc('fired_employees_of_subunit', security='apikey', params=required_query_params(
        {'id': 'SubUnit ID', "types": "Types of employees, separated by commas"}
    ))
    @api.marshal_with(full_employee, code=200, as_list=True)
    @api.response(404, description="SubUnit not found")
    @jwt_required
    def get(self):
        """Get fired users of the subunit"""
        types_raw = query_param_to_set("types")
        types = set()
        for employee_type in types_raw:
            try:
                types.add(EmployeeType(employee_type))
            except ValueError:
                abort(400, f"Incorrect employee type '{employee_type}'")
        return employee_service.get_fired_moderators(get_uuid(request), types), 200


@api.route('/multiple')
class AuthRefresh(OptionsResource):
    @api.doc('get_multiple_employees', security='apikey', params=required_query_params(
        {'ids': 'Employee IDs, separated by commas'}
    ))
    @api.marshal_with(full_employee, code=200, as_list=True)
    @jwt_required
    def get(self):
        """Get multiple employees at a time"""
        ids = query_param_to_set("ids")
        for employee_id in ids:
            get_uuid(employee_id)
        return employee_service.get_multiple_employees(ids), 200
