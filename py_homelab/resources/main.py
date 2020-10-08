import datetime
from flask import request
from ..database.models import User, roles
from flask_restx import Resource, Namespace
from flask_jwt_extended import create_access_token, jwt_required, jwt_optional, exceptions, get_jwt_identity
from ..pm import pm
from throw_out_py import Map
import flask_mongoalchemy

api = Namespace('api', description='Api related operations')


@api.route("/auth/signup")
@jwt_optional
class SignupApi(Resource):
    def post(self):
        try:
            current_user = get_jwt_identity()
            body = request.get_json()
            user = User(**body)
            ls = User.query.paginate(1, per_page=5, error_out=False)
            if ls.total == 0:
                user.role = roles.admin
                user.hash_password()
                user.save()
                return {'id': str(user.id)}, 200
            else:
                if not current_user or (current_user and current_user.role != roles.admin):
                    return {"msg": "You cannot signup at this time. Access is restricted to admins."}, 400
                user.role = roles.member
                user.hash_password()
                user.save()
                return {'id': str(user.id)}, 200
        except flask_mongoalchemy.exceptions.BadValueException as err:
            return {"msg": f"One or more fields have an error: {str(err)}"}, 400


@api.route("/auth/login")
class LoginApi(Resource):
    def post(self):
        body = request.get_json()
        user = User.query.filter(User.email == body.get('email')).first()
        authorized = user.check_password(body.get('password'))

        if not authorized:
            return {'msg': 'Email or password invalid'}, 401

        expires = datetime.timedelta(days=7)
        access_token = create_access_token(
            identity=str(user.id), expires_delta=expires)
        return {'token': access_token}, 200


@api.route("/app/deploy")
class DeployApi(Resource):
    @jwt_required
    def post(self):
        try:
            body = Map(request.get_json())

            return pm.deploy(body), 200
        except exceptions.NoAuthorizationError as err:
            return err, 403
