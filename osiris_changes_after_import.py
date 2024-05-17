import firestore_db as fs

db = fs.Database()
# stap 1:
# kopieer 8BA050 ,8BE070 en 8BE080:
# for course_id in ['8BA050','8BE070','8BE080']:
#     db.copy_doc(f'osiris2/{course_id}',f'osiris2/{course_id}(1)')
#     db.copy_doc(f'osiris2/{course_id}', f'osiris2/{course_id}(2)')
#     db.delete(f'osiris2/{course_id}')

# stap 2:
# non_bmt_courses =['0LVX10','2DBM90', '2WBB0', '4CBLW00', '6BER02']
# aanvangsblok	<->	block		        'aanvangsblok':old_dict['block'],
# bbt_optional	<->	bbt_optional		'bbt_optional':old_dict['bbt_optional'],
# categorie	    <->	category		    'categorie':old_dict['category'],
# cursustype	<->	coursetype		    'cursustype':old_dict['coursetype'],
# doel_en	    <->	aim_en		        'doel_en':old_dict['aim_en'],
# doel_nl	    <->	aim_nl		        'doel_nl':old_dict['aim_nl'],
# examen_doel
# faculteit
# id	        <->	code		        'id':old_dict['code'],
# ingangseisen	<->	requirements		'ingangseisen':old_dict['requirements'],
# inhoud	    <->	contents		    'inhoud':old_dict['contents'],
# inhoud_engels	<->	contents_en		    'inhoud_engels':old_dict['contents_en'],
# lange_naam	<->	long_name		    'lange_naam':old_dict['long_name'],
# learninglines	<->	learninglines		'learninglines':old_dict['learninglines'],
# lecturer	    <->	lecturer		    'lecturer':old_dict['lecturer'],
# minimum_punten<->	ec		            'minimum_punten':old_dict['ec'],
# mwt_optional	<->	mwt_optional		'mwt_optional':old_dict['mwt_optional'],
# naam	        <->	name		        'naam':old_dict['name'],
# omschrijving_en	<->	descr_en		'omschrijving_en':old_dict['descr_en'],
# omschrijving_nl	<->	descr_nl		'omschrijving_nl':old_dict['descr_nl'],
# year	        <->	year		        'year':old_dict['year'],
# 		bbt_path
# 		timeslot
# 		path
# 		mwt_path
#
# for course_id in non_bmt_courses:
#     old_dict = db.get_doc_data(f'osiris/{course_id}')
#     edit_dict={'aanvangsblok':old_dict['block'],
#                 'bbt_optional':old_dict['bbt_optional'],
#                 'categorie':old_dict['category'],
#                 'cursustype':old_dict['coursetype'],
#                 'doel_en':old_dict['aim_en'],
#                 'doel_nl':old_dict['aim_nl'],
#                 'id':old_dict['code'],
#                 'ingangseisen':old_dict['requirements'],
#                 'inhoud':old_dict['contents'],
#                 'inhoud_engels':old_dict['contents_en'],
#                 'lange_naam':old_dict['long_name'],
#                 'learninglines':old_dict['learninglines'],
#                 'lecturer':old_dict['lecturer'],
#                 'minimum_punten':old_dict['ec'],
#                 'mwt_optional':old_dict['mwt_optional'],
#                 'naam':old_dict['name'],
#                 'omschrijving_en':old_dict['descr_en'],
#                 'omschrijving_nl':old_dict['descr_nl'],
#                 'year':old_dict['year'],
#                 }
#     db.set_doc_data(edit_dict,f'osiris2/{course_id}')


# haal info uit oude complete osiris en zet in nieuwe import:
# for course_dict in db.get_coll_doc_data('osiris'):
# try:
#     bbt_optional = course_dict['bbt_optional']
# except Exception:
#     bbt_optional = ""
# try:
#     mwt_optional = course_dict['mwt_optional']
# except Exception:
#     mwt_optional = ""
# try:
#     learninglines = course_dict['learninglines']
# except Exception:
#     learninglines = ""
# try:
#     lecturer = course_dict['lecturer']
# except Exception:
#     lecturer = ""
# try:
#     year = course_dict['year']
# except Exception:
#     year = ""
# try:
#     blok = course_dict['block']
# except Exception:
#     blok = ""
# edit_dict = {'aanvangsblok': blok}
# db.update_doc_fields(edit_dict, f'osiris2/{course_dict['id']}')

for course_name in db.get_coll_doc_names('osiris2'):
    # try:
    #     db.rename_doc_keys(['id', 'naam'], ['code', 'volledige_naam'], f'osiris2/{course_dict['id']}')
    #     # ecs = course_dict['minimum_punten']
    #     # ecs = ecs.replace(' ','')
    # except:
    #     pass
    try:
        path = f'osiris2/{course_name}/docenten'
        for docent in db.get_coll_doc_data(path):
            docent_path = path + '/' + docent['id']
            try:
                opm = docent['opmerking:']
            except:
                opm = ''
            db.update_doc_fields({'opmerking': opm}, docent_path)


    except KeyError as e:
        print(f'Error {e}')
