# pylint: disable=wildcard-import,unused-wildcard-import
import json
import datetime
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django_auth_ldap.backend import LDAPBackend
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.status import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from mongoengine.errors import ValidationError
from .models import Request, Person, SubjectAutofill
from .helpers import QuerySetEncoder, get_fields, get_period_choices, get_queries_by_groups
from .writter import UnifiedWritter
from .cases import *


@api_view(["GET"])
@permission_classes((AllowAny,))
def check(request):
    return JsonResponse({"Ok?": "Ok!"}, status=HTTP_200_OK)


@api_view(["POST"])
@permission_classes((AllowAny,))
def login(request):
    # pylint: disable=no-member
    body = json.loads(request.body)
    username = body['username']
    password = body['password']
    if username is None or password is None:
        return JsonResponse({'error': 'Contraseña o usuario vacío o nulo.'},
                            status=HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Error en ActasDB, usuario sin permisos en la aplicación.'},
                            status=HTTP_403_FORBIDDEN)
    user = LDAPBackend().authenticate(request, username=username, password=password)
    if not user:
        return JsonResponse({'error': 'Error en LDAP, contraseña o usuario no válido.'},
                            status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return JsonResponse({'token': token.key, 'group': user.groups.first().name},
                        status=HTTP_200_OK)

@api_view(["GET"])
@permission_classes((IsAuthenticated,))
def api_logout(request):
    request.user.auth_token.delete()
    logout(request)
    return JsonResponse({'successful': 'Logout Success'}, status=HTTP_200_OK)

@api_view(["GET"])
@permission_classes((AllowAny,))
def details(_):
    programs = Request.get_programs()
    programs.update({'periods': [period[0] for period in get_period_choices()]})
    return JsonResponse(programs, status=HTTP_200_OK, safe=False)


@api_view(["GET"])
def info_cases(request):
    if request.GET.get('cls') == '' or request.GET.get('cls') is None:
        return JsonResponse(Request.get_cases(), status=HTTP_200_OK)
    else:
        for type_case in Request.get_subclasses():
            if type_case.__name__ == request.GET.get('cls'):
                return JsonResponse(get_fields(type_case))
        return JsonResponse({'response': 'Not found'}, status=HTTP_404_NOT_FOUND)


@api_view(["GET", "PATCH", "POST"])
def case(request):
    if request.method == 'GET':
        responses = Request.get_cases_by_query(querydict_to_dict(request.GET))
        return JsonResponse(responses, safe=False, encoder=QuerySetEncoder)
    if request.method == 'POST':
        body = json.loads(request.body)
        subs = [c.__name__ for c in Request.get_subclasses()]
        errors = []
        inserted_items = []
        for item_request in body['items']:
            item_request['user'] = str(request.user)
            case = Request.get_subclasses()[subs.index(item_request['_cls'])]
            item_request['_cls'] = case.get_entire_name()
            new_request = case().from_json(case.translate(json.dumps(item_request)))
            try:
                inserted_items += [str(new_request.save().id)]
            except ValidationError as e:
                errors += [e.message]
        return JsonResponse({'inserted_items': inserted_items, 'errors': errors},
                            status=HTTP_200_OK, safe=False)
    if request.method == 'PATCH':
        body = json.loads(request.body)
        subs = [c.__name__ for c in Request.get_subclasses()]
        errors = []
        edited_items = []
        not_found = []
        for item_request in body['items']:
            try:
                req = Request.get_case_by_id(item_request['id'])
            except (ValueError, KeyError):
                not_found += [item_request['id']]
                continue
            item_request['user'] = request.user.username
            case = req.__class__
            item_request['_cls'] = case.get_entire_name()
            new_request = case().from_json(case.translate(
                json.dumps(item_request)), True)
            try:
                new_request.save()
            except ValidationError as e:
                errors += [e.message]
            else:
                edited_items += [new_request]
        return JsonResponse({'edited_items': edited_items,
                             'errors': errors, 'not_found': not_found},
                            status=HTTP_400_BAD_REQUEST if edited_items == [] else HTTP_200_OK,
                            encoder=QuerySetEncoder, safe=False)


def querydict_to_dict(query_dict):
    data = {}
    for key in query_dict.keys():
        v = query_dict.getlist(key)
        if len(v) == 1:
            v = v[0]
        data[key] = v
    return data


@api_view(["GET"])
def get_docx_genquerie(request):
    query_dict = querydict_to_dict(request.GET)
    try:
        precm = query_dict['pre'] == 'true'
        del query_dict['pre']
    except KeyError:
        return JsonResponse({'error': "'pre' Key not provided"}, status=HTTP_400_BAD_REQUEST)

    generator = UnifiedWritter()
    generator.filename = 'public/' + \
        str(request.user) + str(datetime.date.today()) + '.docx'
    generator.generate_document_by_querie(query_dict, precm)
    return JsonResponse({'url': generator.filename}, status=HTTP_200_OK)

@api_view(["POST"])
def autofill(request):
    # pylint: disable=no-member
    body = json.loads(request.body)
    if 'field' not in body:
        return JsonResponse({'error':'"field" key is not in body'}, status=HTTP_400_BAD_REQUEST)
    try:
        if body['field'] == 'name':
            if 'student_dni' not in body:
                return JsonResponse({'error':'"student_dni" key is not in body'}, status=HTTP_400_BAD_REQUEST)
            try:
                student = Person.objects.filter(student_dni=body['student_dni'])[0]
            except IndexError:
                return JsonResponse({'error':'dni not found'}, status=HTTP_204_NO_CONTENT)
            else:
                return JsonResponse({'student_dni': student.student_dni,
                'student_dni_type': student.student_dni_type,
                'student_name': student.student_name}, status=HTTP_200_OK)
        elif body['field'] == 'subject':
            if 'subject_code' not in body:
                return JsonResponse({'error':'"subject_code" key is not in body'}, status=HTTP_400_BAD_REQUEST)
            try:
                subject = SubjectAutofill.objects.filter(subject_code=body['subject_code'])[0]
            except IndexError:
                return JsonResponse({'error':'subject code not found'}, status=HTTP_204_NO_CONTENT)
            else:
                return JsonResponse({'subject_code': subject.subject_code,
                'subject_name': subject.subject_name}, status=HTTP_200_OK)
    except ValueError:
        return JsonResponse({'error':'field "field" no encontrado'}, safe=False, status=HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes((AllowAny,))
def programs_defined(_):
    programs = sorted([plan[1] for plan in Request.PLAN_CHOICES])
    return JsonResponse({'programs': programs})


def querydict_to_dict(query_dict):
    data = {}
    for key in query_dict.keys():
        v = query_dict.getlist(key)
        if len(v) == 1:
            v = v[0]
        data[key] = v
    return data


@api_view(["GET"])
def get_docx_genquerie(request):
    query_dict = querydict_to_dict(request.GET)
    try:
        precm = query_dict['pre'] == 'true'
        del query_dict['pre']
    except KeyError:
        return JsonResponse({'error': "'pre' Key not provided"}, status=HTTP_400_BAD_REQUEST)

    generator = UnifiedWritter()
    generator.filename = 'public/' + \
        str(request.user) + str(datetime.date.today()) + '.docx'
    generator.generate_document_by_querie(query_dict, precm)
    return JsonResponse({'url': generator.filename}, status=HTTP_200_OK)

@api_view(["GET"])
@permission_classes((AllowAny,))
def generate_spec(_):
    return JsonResponse({'': ''})
    
def allow_generate(request):
    groups = [group.name for group in request.user.groups.all()]
    options = get_queries_by_groups(groups)
    return JsonResponse(options, status=HTTP_200_OK, safe=False)

# TODO: Rewrite this code, no mongoengine libraries should be called here
# @api_view(["PATCH"])
# def change_case_type(request):
#     # pylint: disable=no-member
#     id_request = json.loads(request.body)['id']
#     new_type = json.loads(request.body)['new_case']
#     try:
#         this_request = Request.objects.get(id=id_request)
#     except mongoengine.DoesNotExist:
#         return JsonResponse({'error': 'id not found'})
#     except mongoengine.ValidationError:
#         return JsonResponse({'error': 'id not found'})
#     subs = [c.__name__ for c in Request.get_subclasses()]
#     case = Request.get_subclasses()[subs.index(new_type)]
#     shell = json.dumps({'_cls': case.get_entire_name()})
#     new_request = case().from_json(
#         case.translate(shell))
#     new_request.user = this_request.user
#     try:
#         new_request.save()
#     except ValidationError as e:
#         new_request.delete()
#         return HttpResponse(e.message, status=400)
#     for k in this_request._fields:
#         if k in ['_cls', 'id']:
#             continue
#         if k in new_request._fields:
#             new_request[k] = this_request[k]
#     try:
#         new_request.save()
#     except ValidationError as e:
#         new_request.delete()
#         return HttpResponse(e.message, status=400)
#     try:
#         this_request.delete()
#         new_request.save()
#     except ValidationError as e:
#         return HttpResponse(e.message, status=400)
#     return JsonResponse({'Oki :3': 'All changes were applied correctly', 'id': str(new_request.id)})
