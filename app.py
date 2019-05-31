from flask import Flask, Blueprint, url_for, jsonify, current_app, abort
from flask_restplus import Api, Resource, reqparse
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import requests
import json

import os

app = Flask(__name__)
url = "https://uniparthenope.esse3.cineca.it/e3rest/api/"
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

import models


class BaseConfig(object):
    DATA_FOLDER="data_folder"


config = {
    "default": BaseConfig
}


def configure_app(app):
    config_name = os.getenv('FLASK_CONFIGURATION', 'default')
    app.config.from_object(config[config_name]) # object-based default configuration
    app.config.from_pyfile('config.cfg', silent=True) # instance-folders configuration


configure_app(app)

api = Api(app)


@api.route('/api/uniparthenope/login/<token>',methods=['GET'])
class Login(Resource):
    def get(self, token):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url+"login", headers=headers)
        if response.status_code == 401:
            tok = User.query.filter_by(token=token).first()
            if tok is None:
                print('Auth Failed')
                return jsonify({'statusCode': 401, 'errMsg':"Invalid Username or Password!"})
            else:
                print('Auth Bar')
                return jsonify({'statusCode': 600})
        else:
            print('Auth Stu/Doc')
            return jsonify({'response': response.json()})


@api.route('/api/uniparthenope/totalexams/<token>/<matId>', methods=['GET'])
class TotalExams(Resource):
    def get(self, token, matId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        
            }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/stats", headers=headers)
        _response = response.json()
        totAdSuperate = _response['numAdSuperate'] + _response['numAdFrequentate']
        return jsonify({'totAdSuperate': totAdSuperate,
                        'numAdSuperate': _response['numAdSuperate'],
                        'cfuPar': _response['umPesoSuperato'],
                        'cfuTot': _response['umPesoPiano']})


@api.route('/api/uniparthenope/average/<token>/<matId>/<value>', methods=['GET'])
class TotalExams(Resource):
    def get(self, token, matId, value):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/medie", headers=headers)

        _response = response.json()
        for i in range(0,len(_response)):
            if _response[i]['tipoMediaCod']['value'] is value:
                if _response[i]['base'] is 30:
                    base_trenta = 30
                    media_trenta = _response[i]['media']
                if _response[i]['base'] is 110:
                    base_centodieci = 110
                    media_centodieci = _response[i]['media']

        return jsonify({'trenta': media_trenta,
                            'base_trenta': base_trenta,
                            'base_centodieci': base_centodieci,
                            'centodieci': media_centodieci})


@api.route('/api/uniparthenope/current_aa/<token>/<cdsId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/sessioni?cdsId=" + cdsId, headers=headers)
        _response = response.json()

        date = datetime.today()
        curr_day = datetime(date.year, date.month, date.day)

        if curr_day.day <= 15 and curr_day.month >= 9:
            academic_year = str(curr_day.year) + " - " + str(curr_day.year+1)
        else:
            academic_year = str(curr_day.year - 1) + " - " + str(curr_day.year)

        max_year = 0
        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] > max_year:
                max_year = _response[i]['aaSesId']

        for i in range(0, len(_response)):
            if _response[i]['aaSesId'] == max_year:
                startDate = extractData(_response[i]['dataInizio'])
                endDate = extractData(_response[i]['dataFine'])
                
                print("Inizio: " + str(startDate))
                print("Fine: " + str(endDate))
                print("Oggi: " + str(curr_day))

                if (curr_day >= startDate and curr_day <= endDate):
                    curr_sem = _response[i]['des']
                    if (curr_sem == "Sessione Anticipata" or curr_sem == "Sessione Estiva"):
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Secondo Semestre",
                                        'aa_accad': academic_year
                                        })
                    else:
                        return jsonify({'curr_sem': _response[i]['des'],
                                        'semestre': "Primo Semestre",
                                        'aa_accad': academic_year})


@api.route('/api/uniparthenope/pianoId/<token>/<stuId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, stuId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId, headers=headers)
        _response = response.json()
        pianoId = _response[0]['pianoId']

        return jsonify({'pianoId': pianoId})


@api.route('/api/uniparthenope/exams/<token>/<stuId>/<pianoId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, stuId, pianoId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId + "/" + pianoId, headers=headers)
        _response = response.json()
        my_exams = []

        for i in range(0, len(_response['attivita'])):
            if _response['attivita'][i]['sceltaFlg'] == 1:

                actual_exam = {}
                actual_exam.update({'nome':_response['attivita'][i]['adLibDes'],
                                    'codice': _response['attivita'][i]['adLibCod'],
                                    'adId': _response['attivita'][i]['chiaveADContestualizzata']['adId'],
                                    'CFU': _response['attivita'][i]['peso'],
                                    'annoId': _response['attivita'][i]['scePianoId'],
                                    'adsceId': _response['attivita'][i]['adsceAttId']
                                 })

                my_exams.append(actual_exam)

        return jsonify(my_exams)


@api.route('/api/uniparthenope/checkExam/<token>/<matId>/<examId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, matId, examId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + examId, headers=headers)
        _response = response.json()

        if response.status_code == 500:
            return jsonify({'stato': "Indefinito",
                            'tipo': "",
                            'data': "",
                            'lode': 0,
                            'voto': "OK",
                            })
        elif _response['statoDes'] == "Superata":
            return jsonify({'stato': _response['statoDes'],
                            'tipo': _response['tipoInsDes'],
                            'data': _response['esito']['dataEsa'].split()[0],
                            'lode': _response['esito']['lodeFlg'],
                            'voto': _response['esito']['voto'],
                            })
        else:
            return jsonify({'stato': _response['statoDes'],
                            'tipo': _response['tipoInsDes'],
                            'data': _response['esito']['dataEsa'],
                            'lode': _response['esito']['lodeFlg'],
                            'voto': _response['esito']['voto'],
                            })


@api.route('/api/uniparthenope/checkAppello/<token>/<cdsId>/<adId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, token, cdsId, adId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "calesa-service-v1/appelli/" + cdsId + "/" + adId, headers=headers)
        _response = response.json()

        my_exams = []
        for i in range(0, len(_response)):
            if _response[i]['stato'] == "I" or _response[i]['stato'] == "P":
                actual_exam = {}
                actual_exam.update({'esame': _response[i]['adDes'],
                                    'appId': _response[i]['appId'],
                                    'stato': _response[i]['stato'],
                                    'statoDes': _response[i]['statoDes'],
                                    'docente': _response[i]['presidenteCognome'].capitalize(),
                                    'docente_completo': _response[i]['presidenteCognome'].capitalize() + " " + _response[i]['presidenteNome'].capitalize(),
                                    'numIscritti': _response[i]['numIscritti'],
                                    'note': _response[i]['note'],
                                    'descrizione': _response[i]['desApp'],
                                    'dataFine': _response[i]['dataFineIscr'].split()[0],
                                    'dataInizio': _response[i]['dataInizioIscr'].split()[0],
                                    'dataEsame': _response[i]['dataInizioApp'].split()[0],
                                    })

                my_exams.append(actual_exam)

        return jsonify(my_exams)


@api.route('/api/uniparthenope/RecentAD/<adId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, adId):
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("GET", url + "logistica-service-v1/logistica?adId=" + adId, headers=headers)
        _response = response.json()

        max_year = 0
        if response.status_code == 200:
            for i in range(0, len(_response)):
                if _response[i]['chiaveADFisica']['aaOffId'] > max_year:
                    max_year = _response[i]['chiaveADFisica']['aaOffId']

            for i in range(0, len(_response)):
                if _response[i]['chiaveADFisica']['aaOffId'] == max_year:
                    return jsonify({'adLogId': _response[i]['chiavePartizione']['adLogId'],
                                    'inizio': _response[i]['dataInizio'].split()[0],
                                    'fine': _response[i]['dataFine'].split()[0],
                                    'ultMod': _response[i]['dataModLog'].split()[0]
                                    })
        else:
            return jsonify({'stsErr': "N"})


@api.route('/api/uniparthenope/infoCourse/<adLogId>', methods=['GET'])
class CurrentAA(Resource):
    def get(self, adLogId):
        headers = {
            'Content-Type': "application/json"
        }
        response = requests.request("GET", url + "logistica-service-v1/logistica/" + adLogId + "/adLogConSyllabus", headers=headers)
        _response = response.json()

        if response.status_code == 200:
            return jsonify({'contenuti': _response[0]['SyllabusAD'][0]['contenuti'],
                        'metodi': _response[0]['SyllabusAD'][0]['metodiDidattici'],
                        'verifica': _response[0]['SyllabusAD'][0]['modalitaVerificaApprendimento'],
                        'obiettivi': _response[0]['SyllabusAD'][0]['obiettiviFormativi'],
                        'prerequisiti': _response[0]['SyllabusAD'][0]['prerequisiti'],
                        'testi': _response[0]['SyllabusAD'][0]['testiRiferimento'],
                        'altro': _response[0]['SyllabusAD'][0]['altreInfo']
                        })

@api.route('/api/uniparthenope/segreteria', methods=['GET'])
class CurrentAA(Resource):
    def get(self):
        studenti = [{'giorno': "LUN", 'orario_inzio': "09:00", 'orario_fine': "12:00"},
                     {'giorno': "MER", 'orario_inzio': "09:00", 'orario_fine': "12:00"},
                     {'giorno': "MAR", 'orario_inzio': "09:00 - 12:30", 'orario_fine': "14:00 - 15.30"},
                     {'giorno': "GIO", 'orario_inzio': "09:00 - 12:30", 'orario_fine': "14:00 - 15.30"},
                     {'giorno': "VEN", 'orario_inzio': "09:00", 'orario_fine': "12:00"}]

        didattica = [{'giorno': "LUN", 'orario_inzio': "10:00", 'orario_fine': "13:00"},
                     {'giorno': "MER", 'orario_inzio': "10:00", 'orario_fine': "13:00"},
                     {'giorno': "VEN", 'orario_inzio': "10:00", 'orario_fine': "13:00"},
                     {'giorno': "MAR", 'orario_inzio': "0", 'orario_fine': "0"},
                     {'giorno': "GIO", 'orario_inzio': "0", 'orario_fine': "0"}
                     ]

        return jsonify({'didattica': didattica,
                        'studenti': studenti})


@api.route('/api/uniparthenope/examsToFreq/<token>/<stuId>/<pianoId>/<matId>', methods=['GET'])
class CurrentAA(Resource):
     def get(self, token, stuId, pianoId, matId):
        headers = {
            'Content-Type': "application/json",
            "Authorization": "Basic " + token
        }
        response = requests.request("GET", url + "piani-service-v1/piani/" + stuId + "/" + pianoId, headers=headers)
        _response = response.json()
        my_exams = []
        for i in range(0, len(_response['attivita'])):
            if _response['attivita'][i]['sceltaFlg'] == 1:
                adId = str(_response['attivita'][i]['chiaveADContestualizzata']['adId'])
                adSceId = _response['attivita'][i]['adsceAttId']
                response_2 = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + str(adSceId), headers=headers)
                _response2 = response_2.json()

                if response_2.status_code == 500:
                    print('ERRORE 500')

                elif _response2['statoDes'] != "Superata":

                    response_3 = requests.request("GET", url + "libretto-service-v1/libretti/" + matId + "/righe/" + str(
                                                      adSceId)+"/partizioni", headers=headers)
                    _response3 = response_3.json()
                    if response_3.status_code == 500 or response_3.status_code == 404:
                        print('ERRORE 500')
                    else:
                        response_4 = requests.request("GET", url + "logistica-service-v1/logistica?adId=" + adId,
                                                    headers=headers)
                        _response4 = response_4.json()

                        max_year = 0
                        if response_4.status_code == 200:
                            for x in range(0, len(_response4)):
                                if _response4[x]['chiaveADFisica']['aaOffId'] > max_year:
                                    max_year = _response4[x]['chiaveADFisica']['aaOffId']

                            for x in range(0, len(_response4)):
                                if _response4[x]['chiaveADFisica']['aaOffId'] == max_year:
                                    actual_exam = ({
                                        'nome': _response['attivita'][i]['adLibDes'],
                                        'codice': _response['attivita'][i]['adLibCod'],
                                        'adId': _response['attivita'][i]['chiaveADContestualizzata']['adId'],
                                        'CFU': _response['attivita'][i]['peso'],
                                        'annoId': _response['attivita'][i]['scePianoId'],
                                        'docente': _response3[0]['cognomeDocTit'].capitalize() + " " + _response3[0]['nomeDoctit'].capitalize(),
                                        'docenteID': _response3[0]['docenteId'],
                                        'semestre': _response3[0]['partEffCod'],
                                        'adLogId': _response4[x]['chiavePartizione']['adLogId'],
                                        'inizio': _response4[x]['dataInizio'].split()[0],
                                        'fine': _response4[x]['dataFine'].split()[0],
                                        'ultMod': _response4[x]['dataModLog'].split()[0]
                                    })
                                    my_exams.append(actual_exam)
        return jsonify(my_exams)

'''
AREA RISTORANTI
'''
from models import User,Food

##TODO inserire token
@api.route('/api/uniparthenope/foods/login/<username>/<password>', methods=['GET', 'POST'])
class Login(Resource):
    def get(self, username, password):
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return jsonify({"message": "User/Passworda errata!", "code": 500})
        else:
            return jsonify({"message": "OK", "code": 200})

import base64


@api.route('/api/uniparthenope/foods/register/<username>/<password>/<email>/<nomeLocale>/<pwd_admin>', methods=['POST'])
class Login(Resource):
    def post(self, username, password, email, nomeLocale, pwd_admin):
        if pwd_admin == "besteming":
            usern = User.query.filter_by(username=username).first()
            if usern is None:
                token_start = username+":"+password
                token = base64.b64encode(bytes(str(token_start).encode("utf-8")))
                user = User(username=username, email=email, token=token, nome_bar=nomeLocale)

                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                return jsonify({"code": 200, "message": "OK"})
            else:
                return error_response(500, "User already exists!")
        else:
            return error_response(500, "You are not admin!")

##TODO inserire token
from flask import request
@api.route('/api/uniparthenope/foods/addMenu/<username>', methods=['POST'])
class Login(Resource):
    def post(self, username):
        content = request.json

        usern = User.query.filter_by(username=username).first()
        if usern is not None:
            nome_bar = usern.nome_bar

            print(nome_bar)
            primo = content['primo']
            secondo = content['secondo']
            contorno = content['contorno']
            altro = content['altro']
            menu = Food(primo_piatto=primo, secondo_piatto=secondo, contorno=contorno, altro=altro, nome_food=nome_bar)
            db.session.add(menu)
            db.session.commit()
            return jsonify({"code": 200, "menu_code": menu.id})
        else:
            return error_response(500, "You are not admin!")


@api.route('/api/uniparthenope/foods/menuSearchData/<data>', methods=['GET'])
class Login(Resource):
    def get(self, data):

        array = []
        day = data[0:2]
        month = data[2:4]
        year = data[4:8]

        foods = Food.query.all()
        for f in foods:
            if str(f.data.year) == year and str('{:02d}'.format(f.data.month)) == month and str('{:02d}'.format(f.data.day)) == day:
                menu = ({'nome': f.nome_food,
                         'primo': f.primo_piatto,
                         'secondo': f.secondo_piatto,
                         'contorno': f.contorno,
                         'altro': f.altro,
                         'apertura': f.orario_apertura})
                array.append(menu)

        return jsonify(array)


'''
FINE AREA RISTORANTI
'''


def extractData(data):
    data_split = data.split()[0]
    export_data = datetime.strptime(data_split, '%d/%m/%Y')

    return export_data


from werkzeug.http import HTTP_STATUS_CODES


def error_response(status_code, message=None):
    payload = {'error': HTTP_STATUS_CODES.get(status_code, 'Unknown error')}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


if __name__ == '__main__':
    app.run(ssl_context='adhoc')

