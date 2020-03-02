import datetime
import json
from mongoengine import DynamicDocument, EmbeddedDocument, DateField, StringField, BooleanField
from mongoengine import ListField, IntField, EmbeddedDocumentField, EmbeddedDocumentListField
from mongoengine import LazyReferenceField, DictField, DateTimeField
from mongoengine.errors import ValidationError, DoesNotExist
from mongoengine.fields import BaseField
from .helpers import get_period_choices
from .request_types import REQUEST_TYPE_CHOICES

class Subject(EmbeddedDocument):

    meta = {'allow_inheritance': True}

    TIP_PRE_FUND_OBLIGATORIA = 'PB'
    TIP_PRE_FUND_OPTATIVA = 'PO'
    TIP_PRE_DISC_OBLIGATORIA = 'PC'
    TIP_PRE_DISC_OPTATIVA = 'PT'
    TIP_PRE_TRAB_GRADO = 'PP'
    TIP_PRE_LIBRE_ELECCION = 'PL'
    TIP_PRE_NIVELACION = 'PE'
    TIP_MOF_OBLIGATORIA = 'MO'
    TIP_MOF_ACTIV_ACADEMICA = 'MC'
    TIP_MOF_TRAB_GRADO = 'MP'
    TIP_MOF_ELEGIBLE = 'ML'
    TIP_DOC_ACTIV_ACADEMICA = 'DF'
    TIP_DOC_TESIS = 'DS'
    TIP_DOC_ELEGIBLE = 'DU'

    TIP_CHOICES = (
        (TIP_PRE_FUND_OBLIGATORIA, 'Fundamentación Obligatoria (B)'),
        (TIP_PRE_FUND_OPTATIVA, 'Fundamentación Optativa (O)'),
        (TIP_PRE_DISC_OBLIGATORIA, 'Disciplinar Obligatoria (C)'),
        (TIP_PRE_DISC_OPTATIVA, 'Disciplinar Optativa (T)'),
        (TIP_PRE_TRAB_GRADO, 'Trabajo de Grado Pregrado (P)'),
        (TIP_PRE_LIBRE_ELECCION, 'Libre Elección (L)'),
        (TIP_PRE_NIVELACION, 'Nivelación (E)'),
        (TIP_MOF_OBLIGATORIA, 'Obligatoria Maestría (O)'),
        (TIP_MOF_ACTIV_ACADEMICA, 'Actividad Académica Maestría (C)'),
        (TIP_MOF_TRAB_GRADO, 'Tesis o Trabajo Final de Maestría (P)'),
        (TIP_MOF_ELEGIBLE, 'Elegible Maestría (L)'),
        (TIP_DOC_ACTIV_ACADEMICA, 'Actividad Académica Doctorado (F)'),
        (TIP_DOC_TESIS, 'Tesis de Doctorado (S)'),
        (TIP_DOC_ELEGIBLE, 'Elegible Doctorado (U)'),
    )

    name = StringField(required=True, display='Nombre Asignatura')
    code = StringField(required=True, display='Código')
    credits = IntField(required=True, display='Créditos')
    group = StringField(required=True, display='Grupo')
    tipology = StringField(
        required=True, choices=TIP_CHOICES, display='Tipología')

    @staticmethod
    def subjects_to_array(subjects):
        """
        A function that converts a List of Subjects into a classic array.
        : param subjects: EmbeddedDocumentListField of Subjects to be converted
        """
        data = []
        for subject in subjects:
            data.append([
                subject.code,
                subject.name,
                subject.group,
                subject.tipology[-1],
                str(subject.credits)
            ])
        return data

    @staticmethod
    def creds_summary(subjects):
        """
        A function that returns a summary of credits by tipology.
        : param subjects: EmbeddedDocumentListField of Subjects to be computed
        """
        data = [0, 0, 0, 0, 0]
        for sbj in subjects:
            if sbj.tipology == Subject.TIP_PRE_FUND_OBLIGATORIA:
                data[0] += sbj.credits
            elif sbj.tipology == Subject.TIP_PRE_FUND_OPTATIVA:
                data[1] += sbj.credits
            elif sbj.tipology == Subject.TIP_PRE_DISC_OBLIGATORIA:
                data[2] += sbj.credits
            elif sbj.tipology == Subject.TIP_PRE_DISC_OPTATIVA:
                data[3] += sbj.credits
            elif sbj.tipology == Subject.TIP_PRE_LIBRE_ELECCION:
                data[4] += sbj.credits
        return data


class Request(DynamicDocument):

    meta = {'allow_inheritance': True}

    full_name = 'Petición sin tipo'

    decision_makers = (
        'Consejo de Facultad',
        'Comité Asesor',
        'Director de Tesis',
        'Comité de Matricula',
        'Consejo de Sede',
        'Consejo Superior Universitario',
    )
    decision_maker = decision_makers[0]

    #Request is in cm, pcm (or not)
    in_cm = True
    in_pcm = True

    # AS Approval Status
    AS_APLAZA = 'AL'
    AS_APRUEBA = 'AP'
    AS_EN_TRAMITE = 'ET'
    AS_EN_ESPERA = 'EE'
    AS_NO_APRUEBA = 'NA'
    AS_SE_INHIBE = 'SI'
    AS_CONSEJO_RECOMIENDA = 'FR'
    AS_CONSEJO_NO_RECOMIENDA = 'FN'
    AS_ANULADA = 'AN'
    AS_RENUNCIA = 'RN'
    AS_CHOICES = (
        (AS_APLAZA, 'Aplaza'),
        (AS_APRUEBA, 'Aprueba'),
        (AS_EN_TRAMITE, 'En trámite'),
        (AS_EN_ESPERA, 'En espera'),
        (AS_NO_APRUEBA, 'No Aprueba'),
        (AS_SE_INHIBE, 'Se Inhibe'),
        (AS_CONSEJO_RECOMIENDA, 'Consejo Recomienda'),
        (AS_CONSEJO_NO_RECOMIENDA, 'Consejo No Recomienda'),
        (AS_ANULADA, 'Anular'),
        (AS_RENUNCIA, 'Desistir'),
    )
    # ARCR Advisor Response - Committee Recommends
    ARCR_APROBAR = 'CAP'
    ARCR_NO_APROBAR = 'CNA'
    ARCR_RECOMENDAR = 'CRR'
    ARCR_NO_RECOMENDAR = 'CRN'
    ARCR_EN_ESPERA = 'CEE'
    ARCR_CHOICES = (
        (ARCR_APROBAR, 'Aprobar'),
        (ARCR_NO_APROBAR, 'No Aprobar'),
        (ARCR_RECOMENDAR, 'Recomendar'),
        (ARCR_NO_RECOMENDAR, 'No recomendar'),
        (ARCR_EN_ESPERA, 'En espera'),
    )

    DNI_TYPE_CEDULA_DE_CIUDADANIA = 'CC'
    DNI_TYPE_PASAPORTE = 'PS'
    DNI_TYPE_TARJETA_DE_IDENTIDAD = 'TI'
    DNI_TYPE_CEDULA_DE_EXTRANJERIA = 'CE'
    DNI_TYPE_OTRO = 'OT'
    DNI_TYPE_CHOICES = (
        (DNI_TYPE_OTRO, 'Otro'),
        (DNI_TYPE_PASAPORTE, 'Pasaporte'),
        (DNI_TYPE_CEDULA_DE_EXTRANJERIA, 'Cédula de extranjería'),
        (DNI_TYPE_CEDULA_DE_CIUDADANIA, 'Cédula de Ciudadanía colombiana'),
        (DNI_TYPE_TARJETA_DE_IDENTIDAD, 'Tarjeta de Identidad colombiana'),
    )
    # P Pregrado
    # E Especializacion
    # M Maestria
    # D Doctorado
    # BAP Bogota Asignaturas de Posgrado
    P_ADMINISTRACION_EMPRESAS = '2520'
    P_CONTADURIA_PUBLICA = '2521'
    P_ECONOMIA = '2522'
    M_ADMINISTRACION = '2869'
    M_CIENCIAS_ECONOMICAS = '2938'
    M_CONTABILIDAD_FINANZAS = '2864'
    D_ADMINISTRACION = '2973'
    D_CIENCIAS_ECONOMICAS = '2951'

    PLAN_CHOICES = (
        (P_ADMINISTRACION_EMPRESAS, 'Administración de Empresas'),
        (P_CONTADURIA_PUBLICA, 'Contaduría Pública'),
        (P_ECONOMIA, 'Economía'),
        (M_ADMINISTRACION, 'Maestría en Administración'),
        (M_CIENCIAS_ECONOMICAS, 'Maestría en Ciencias Económicas'),
        (M_CONTABILIDAD_FINANZAS, 'Maestría en Contabilidad  y Finanzas'),
        (D_ADMINISTRACION, 'Doctorado en Administración'),
        (D_CIENCIAS_ECONOMICAS, 'Doctorado en Ciencias Económicas'),
    )

    # DP Departamento
    DP_CIVIL_AGRICOLA = 'DCA'
    DP_ELECTRICA_ELECTRONICA = 'DEE'
    DP_MECANICA_MECATRONICA = 'DMM'
    DP_SISTEMAS_INDUSTRIAL = 'DSI'
    DP_QUIMICA_AMBIENTAL = 'DQA'
    DP_EXTERNO_FACULTAD = 'EFA'
    DP_EMPTY = ''
    DP_CHOICES = (
        (DP_CIVIL_AGRICOLA, 'Departamento de Ingeniería Civil y Agrícola'),
        (DP_ELECTRICA_ELECTRONICA, 'Departamento de Ingeniería Eléctrica y Electrónica'),
        (DP_MECANICA_MECATRONICA, 'Departamento de Ingeniería Mecánica y Mecatrónica'),
        (DP_SISTEMAS_INDUSTRIAL, 'Departamento de Ingeniería de Sistemas e Industrial'),
        (DP_QUIMICA_AMBIENTAL, 'Departamento de Ingeniería Química y Ambiental'),
        (DP_EXTERNO_FACULTAD, 'Externo a la Facultad de Ingeniería'),
        (DP_EMPTY, ''),
    )

    PROFILE_INVE = 'I'
    PROFILE_PROF = 'P'
    PROFILE_CHOICES = (
        (PROFILE_INVE, 'Investigación'),
        (PROFILE_PROF, 'Profundización')
    )

    GRADE_OPTION_TRABAJO_FINAL_MAESTRIA = 'TFM'
    GRADE_OPTION_TESIS_MAESTRIA = 'TSM'
    GRADE_OPTION_TESIS_DOCTORADO = 'TSD'
    GRADE_OPTION_CHOICES = (
        (GRADE_OPTION_TRABAJO_FINAL_MAESTRIA, 'Trabajo Final de Maestría'),
        (GRADE_OPTION_TESIS_MAESTRIA, 'Tesis de Maestría')
    )

    PERIOD_CHOICES = get_period_choices()
    PERIOD_DEFAULT = PERIOD_CHOICES[0][0] if datetime.date.today().month <= 6 else PERIOD_CHOICES[1][0]

    _cls = StringField(required=True)
    date_stamp = DateTimeField(default=datetime.datetime.now)
    user = StringField(max_length=255, required=True)
    consecutive_minute = IntField(
        min_value=0, default=0, display='Número del Acta de Consejo de Facultad')
    consecutive_minute_ac = IntField(
        min_value=0, default=0, display='Número del Acta de Comité Asesor') #ac stands for advisory committe
    year = IntField(
        min_value=2000, max_value=2100, display='Año del Acta', default=datetime.date.today().year)
    to_legal = BooleanField(default=False, display='Sugerir remitir caso a legataria')
    date = DateTimeField(default=datetime.date.today,
                     display='Fecha de radicación')
    academic_program = StringField(
        min_length=4, max_length=4, choices=PLAN_CHOICES,
        display='Programa Académico', default=P_ECONOMIA)
    student_dni_type = StringField(
        min_length=2, choices=DNI_TYPE_CHOICES,
        default=DNI_TYPE_CEDULA_DE_CIUDADANIA, display='Tipo de Documento')
    student_dni = StringField(
        max_length=22, display='Documento', default='')
    student_name = StringField(
        max_length=512, display='Nombre del Estudiante', default='')
    academic_period = StringField(
        max_length=10, display='Periodo', choices=PERIOD_CHOICES, default=PERIOD_DEFAULT)
    approval_status = StringField(
        min_length=2, max_length=2, choices=AS_CHOICES,
        default=AS_EN_ESPERA, display='Estado de Aprobación')
    advisor_response = StringField(
        min_length=3, max_length=3, choices=ARCR_CHOICES,
        default=ARCR_EN_ESPERA, display='Respuesta del Comité')
    council_decision = StringField(
        max_length=255, default='justifica debidamente la solicitud', display='Justificación del Consejo')
    student_justification = StringField(
        default='', display='Justificación del Estudiante')
    supports = StringField(default='', display='Soportes')
    extra_analysis = ListField(
        StringField(), display='Analisis Extra')
    request_tipology = StringField(choices=REQUEST_TYPE_CHOICES, 
                                    default=REQUEST_TYPE_CHOICES[0][0],
                                    display='Tipo - Subtipo de solicitud')
    received_date = DateTimeField() #Date when advisor recieves a case from secretary

    regulations = {
        '008|2008|CSU': ('Acuerdo 008 de 2008 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=34983'),
        '026|2012|CSU': ('Acuerdo 026 de 2012 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=47025'),
        '032|2010|CSU': ('Acuerdo 032 de 2010 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=39424'),
        '040|2017|CSU': ('Acuerdo 40 de 2012 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=89183'),
        '051|2003|CSU': ('Resolución 051 de 2003 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=35163'),
        '056|2012|CSU': ('Acuerdo 056 de 2012 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=48208'),
        '102|2013|CSU': ('Acuerdo 102 de 2013 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=56987'),
        '230|2016|CSU': ('Acuerdo 230 de 2016 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=87737'),
        '014|2008|CAC': ('Acuerdo 014 de 2008 del Consejo Académico',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=34127'),
        '016|2011|CAC': ('Acuerdo 016 de 2011 del Consejo Academico',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=44965'),
        '070|2009|CAC': ('Acuerdo 070 de 2009 de Consejo Académico',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=35443'),
        '089|2014|CAC': ('Acuerdo 089 de 2014 del Consejo Académico',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=66330'),
        '002|2012|CFA': ('Acuerdo 002 de 2012 de Consejo de Facultad',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=50509'),
        '002|2011|CFA': ('Acuerdo 002 de 2011 de Consejo de Facultad',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=42724'),
        '040|2017|CFA': ('Acuerdo 40 de 2017 del Consejo de Facultad',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=89183'),
        '001|2016|VAC': ('Circular 01 de 2016 de la Vicerectoría Académica',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=86414#0'),
        '012|2014|VAC': ('Resolución 012 de 2014 de Vicerrectoría Académica',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=62849'),
        '035|2014|VAC': ('Resolución 035 de 2018 de La Vicerrectoría Académica',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=69990'),
        '239|2009|VAC': ('Resolución 239 de 2009 de Vicerrectoría Académica',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=34644'),
        '241|2009|VAC': ('Resolución 241 DE 2009 de la Vicerrectoría Académica',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=34651'),
        '001|2019|VSB': ('Circular 001 de 2019 de Vicerrectoría de Sede Bogotá',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=92579'),
        '1416|2013|RE': ('Resolución 1416 de 2013 de Rectoría',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=60849'),
        '070|2012|CSU': ('Acuerdo 70 de 2018 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=50105'),
        '155|2014|CSU': ('Acuerdo 155 de 2014 del Consejo Superior Universitario',
                         'http://www.legal.unal.edu.co/rlunal/home/doc.jsp?d_i=69337'),
    }

    assertionerror = {
        'CHOICES': '{} is not in choices list.'
    }

    str_analysis = 'Análisis'
    str_answer = 'Concepto'
    str_council_header = 'El Consejo de Facultad'
    str_comittee_header = 'El Comité Asesor recomienda al Consejo de Facultad'

    def is_affirmative_response_approval_status(self):
        return self.approval_status in (self.AS_APRUEBA, self.AS_CONSEJO_RECOMIENDA)

    def is_affirmative_response_advisor_response(self):
        return self.advisor_response in (self.ARCR_RECOMENDAR, self.ARCR_APROBAR)

    def is_pre(self):
        return self.academic_program in (self.P_ECONOMIA, 
                                            self.P_CONTADURIA_PUBLICA, 
                                            self.P_ADMINISTRACION_EMPRESAS)

    def safe_save(self):
        try:
            self.save()
        except ValidationError as e:
            raise ValueError(e.message)

    @staticmethod
    def get_cases_by_query(query):
        # pylint: disable=no-member
        return Request.objects(**query).filter(approval_status__nin=[Request.AS_ANULADA, Request.AS_RENUNCIA])

    @staticmethod
    def get_case_by_id(caseid):
        try:
            # pylint: disable=no-member
            return Request.objects.get(id=caseid)
        except ValidationError as e:
            raise ValueError(e.message)
        except DoesNotExist as e:
            raise KeyError('ID {} does not exist')

    @staticmethod
    def get_programs():
        return {
            'programs': sorted([plan[1] for plan in Request.PLAN_CHOICES])
        }

    @staticmethod
    def get_cases():
        return {
            'cases': [
                {'code': type_case.__name__, 'name': type_case.full_name}
                for type_case in Request.get_subclasses()]
        }

    @classmethod
    def translate(cls, data):
        data_json = json.loads(data)
        for key in data_json:
            try:
                # pylint: disable=no-member
                choices = cls._fields[key].choices
                if choices:
                    for item in choices:
                        if item[1] == data_json[key]:
                            data_json[key] = item[0]
                            break
                elif isinstance(cls._fields[key], EmbeddedDocumentListField):
                    _cls = cls._fields[key].field.document_type_obj
                    for field in _cls._fields:
                        choices = _cls._fields[field].choices
                        if choices:
                            _dict = dict((y, x) for x, y in choices)
                            for element in data_json[key]:
                                if element[field] in _dict:
                                    element[field] = _dict[element[field]]

            except KeyError:
                pass
        return json.dumps(data_json)

    @classmethod
    def get_entire_name(cls):
        parents = cls.mro()
        index = parents.index(Request)
        name = 'Request.'
        for _cls in reversed(parents[:index]):
            name += _cls.__name__ + '.'
        return name[:-1]

    @classmethod
    def get_subclasses(cls):
        subs = []
        for subclass in cls.__subclasses__():
            subs.append(subclass)
            subs += subclass.get_subclasses()
        return subs


class Professor(EmbeddedDocument):

    name = StringField(required=True, default='Nombre profesor', display='Nombre')
    department = StringField(
        display='Departamento', choices=Request.DP_CHOICES, default=Request.DP_EXTERNO_FACULTAD)
    institution = StringField(display='Institución')
    country = StringField(display='País')


class Person(DynamicDocument):
    student_dni_type = StringField(
        min_length=2, choices=Request.DNI_TYPE_CHOICES,
        default=Request.DNI_TYPE_CEDULA_DE_CIUDADANIA, display='Tipo de Documento')
    student_dni = StringField(
        max_length=22, display='Documento', default='')
    student_name = StringField(
        max_length=512, display='Nombre del Estudiante', default='')

class SubjectAutofill(DynamicDocument):
    subject_code = StringField(
        display='Código de la Asignatura')
    subject_name = StringField(
        max_length=512, display='Nombre de la Asignatura', default='')
        
class RequestChanges(DynamicDocument):
    request_id = LazyReferenceField(Request, required=True)
    user = StringField(required=True)
    date_stamp = DateTimeField(default=datetime.datetime.now)
    changes = DictField(required=True)
