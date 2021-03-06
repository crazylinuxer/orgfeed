from flask_restx.namespace import Namespace
from flask_restx import fields
from flask import request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from services import post_service, get_uuid, get_page
from .utils import OptionsResource
from models import pages_count_model, required_query_params, update_dict, query_param_to_set
from models.post_model import PostCreateModel, PostFullModel, PostStatus, PostEditModel


api = Namespace("post", "Endpoints for news posts")

post_create = api.model(
    "post_create_model",
    PostCreateModel()
)

post_edit = api.model(
    "post_edit_model",
    PostEditModel()
)

full_post = api.model(
    "full_post_model",
    PostFullModel()
)

counted_posts_list = api.model(
    'counted_list_of_posts',
    {
        "posts":
            fields.List(
                fields.Nested(full_post)
            ),
        "pages_count": pages_count_model
    }
)

posts_statistics = api.model(
    'posts_statistics_model',
    {
        "IT department": fields.Raw(example={'2020-11': 10}),
        "Marketing department": fields.Raw(example={'2020-12': 0})
    }
)


@api.route('')
class Post(OptionsResource):
    @api.doc("create_post", security='apikey')
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Attachment not found")
    @api.expect(post_create, validate=True)
    @jwt_required
    def post(self):
        """Create a post"""
        return post_service.create_post(get_jwt_identity(), **api.payload), 201

    @api.doc("edit_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post or attachment not found")
    @api.response(403, description="Have no privileges to edit this post")
    @api.response(422, description="All fields are null")
    @api.expect(post_edit, validate=True)
    @jwt_required
    def put(self):
        """Edit a post"""
        return post_service.edit_post(get_jwt_identity(), get_uuid(request), **api.payload), 201

    @api.doc("get_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=200)
    @api.response(404, description="Post not found")
    @jwt_required
    def get(self):
        """Get a post by ID"""
        return post_service.get_post(get_uuid(request)), 200

    @api.doc("delete_post", security='apikey', params=required_query_params(
        {"id": "Post ID", "with_attachments": "Delete also every attachment of the post"}
    ))
    @api.response(201, description="Success")
    @api.response(403, description="Can not remove other users` posts or attachments")
    @api.response(404, description="Post not found")
    @jwt_required
    def delete(self):
        """Remove a post"""
        return post_service.delete_post(get_jwt_identity(), get_uuid(request)), 201


@api.route('/approve')
class ApprovePost(OptionsResource):
    @api.doc("approve_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post not found")
    @api.response(403, description="Have no privileges to approve this post")
    @jwt_required
    def post(self):
        """Approve a post (only for moderators and admins)"""
        return post_service.set_post_status(get_jwt_identity(), get_uuid(request), PostStatus.posted), 201

    @api.doc("disapprove_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post not found")
    @api.response(403, description="Have no privileges to disapprove this post")
    @jwt_required
    def delete(self):
        """Disapprove a post (only for moderators and admins)"""
        return post_service.set_post_status(get_jwt_identity(), get_uuid(request), PostStatus.under_consideration), 201


@api.route('/return')
class ApprovePost(OptionsResource):
    @api.doc("return_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post not found")
    @api.response(403, description="Have no privileges to return this post")
    @jwt_required
    def post(self):
        """Return a post for further improvements (only for moderators and admins)"""
        return post_service.set_post_status(get_jwt_identity(), get_uuid(request), PostStatus.returned_for_improvement), 201


@api.route('/reject')
class ApprovePost(OptionsResource):
    @api.doc("reject_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post not found")
    @api.response(403, description="Have no privileges to reject this post")
    @jwt_required
    def post(self):
        """Totally reject a post (only for moderators and admins)"""
        return post_service.set_post_status(get_jwt_identity(), get_uuid(request), PostStatus.rejected), 201


@api.route('/archive')
class ArchivePost(OptionsResource):
    @api.doc("archive_post", security='apikey', params=required_query_params({"id": "Post ID"}))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post not found")
    @api.response(403, description="Have no privileges to archive this post")
    @jwt_required
    def post(self):
        """Archive a post (only for moderators and admins)"""
        return post_service.set_post_status(get_jwt_identity(), get_uuid(request), PostStatus.archived), 201

    @api.doc("get_archived_posts", security='apikey', params=required_query_params({'page': 'page number'}))
    @api.marshal_with(counted_posts_list, code=200)
    @jwt_required
    def get(self):
        """Get archived posts"""
        return post_service.get_archived_posts(get_page(request)), 200

    @api.doc("unarchive_post", security='apikey', params=required_query_params({
        "id": "Post ID",
        "status": {
            'description': "Status to give after unarchiving",
            "enum": [i.name for i in PostStatus if i != PostStatus.archived]
        }
    }))
    @api.marshal_with(full_post, code=201)
    @api.response(404, description="Post not found")
    @api.response(403, description="Have no privileges to unarchive this post")
    @api.response(400, description="Incorrect status value")
    @jwt_required
    def delete(self):
        """Unarchive a post (only for moderators and admins)"""
        try:
            new_status = PostStatus[request.args.get('status', '')]
            if new_status == PostStatus.archived:
                raise KeyError
        except KeyError:
            return abort(400, "Incorrect status value")
        return post_service.set_post_status(get_jwt_identity(), get_uuid(request), new_status), 201


@api.route('/of_employee')
class Post(OptionsResource):
    @api.doc("get_employee_posts", security='apikey', params=required_query_params({"id": "Employee ID"}))
    @api.marshal_with(full_post, code=200, as_list=True)
    @api.response(404, description="Employee not found")
    @jwt_required
    def get(self):
        """Get all employee's posts"""
        return post_service.get_all_employee_posts(get_uuid(request)), 200


@api.route('/statistics')
class PostStat(OptionsResource):
    @api.doc("get_posts_statistics", security='apikey', params=update_dict(required_query_params({
        "start_year": "Year to start from",
        "start_month": "Month to start from",
        "end_year": "Year to finish with",
        "end_month": "Month to finish with"
    }), {"ids": "SubUnit IDs, separated by commas"}))
    @api.response(code=200, description="Success", model=posts_statistics)
    @api.response(code=400, description="Incorrect (non-integer) date parameters")
    @api.response(code=422, description="Invalid date given")
    @jwt_required
    def get(self):
        """Get statistics of posts of the each subunit"""
        start_year = request.args.get("start_year", '')
        start_month = request.args.get("start_month", '')
        end_year = request.args.get("end_year", '')
        end_month = request.args.get("end_month", '')
        ids_raw = query_param_to_set("ids")
        if not all(param.isdigit() for param in (start_year, start_month, end_year, end_month)):
            abort(400, "Date values must be integers")
        return post_service.get_statistics(*(int(param) for param in (
            start_year,
            start_month,
            end_year,
            end_month,
        )), subunit_ids=[get_uuid(e_id) for e_id in ids_raw] if ids_raw and all(ids_raw) else None), 200


@api.route('/moderation')
class PostModeration(OptionsResource):
    @api.doc("get_posts_moderation", security='apikey', params={
        'page': {"description": 'page number', "required": True},
        'statuses': {
            "description":
                f"Post statuses to return, separated with commas (allowed values: {[status.name for status in PostStatus]})",
            "required": True
        },
        "reverse": {'description': "Reverse output (by date) or not. True by default.", "enum": ['true', 'false']}
    })
    @api.marshal_with(counted_posts_list, code=200)
    @api.response(code=403, description="Have no privileges to moderate posts")
    @api.response(code=422, description="Incorrect status value")
    @jwt_required
    def get(self):
        """Get posts of given types and statuses by given subunit or whole organization (only for admins and moderators)"""
        statuses_raw = query_param_to_set("statuses")
        statuses = set()
        for status in statuses_raw:
            if status:
                try:
                    statuses.add(PostStatus[status])
                except KeyError:
                    abort(422, f"Incorrect status value '{status}'")
        return post_service.get_all_posts(
            get_jwt_identity(),
            get_page(request),
            statuses,
            reverse=(request.args.get('reverse', 'true') == 'true')
        ), 200
