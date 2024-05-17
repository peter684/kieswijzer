COL_B = '#CC4400'
COL_CT = "#4DFF6A"
COL_CB = '#009919'
COL_BSM = "#000099"
COL_MI = "#19B2FF"
COL_BM = '#FFD500'
COL_MIMME = '#1DCECE'

learning_lines = [
    {"abbr": "B", "name": "Base courses", "color": COL_B},
    {"abbr": "BSM", "name": "Biomedical Systems Modelling", "color": COL_BSM},
    {"abbr": "MI", "name": "Measurements & Imaging", "color": COL_MI},
    {"abbr": "MImme", "Key": "B", "name": "Measurements & Imaging (master ME)", "color": COL_MIMME},
    {"abbr": "BM", "name": "Biomechanics", "color": COL_BM},
    {"abbr": "CB", "name": "Chemical Biology", "color": COL_CB},
    {"abbr": "CT", "name": "Cells & Tissues", "color": COL_CT},
]

themes = {
    "free": {
        "tile": {"backgroundcolor": "#4A7000", "color": "white", "bordercolor": "#2F4700", "fontcolor": "white"},
        "container": {"backgroundcolor": "#79B800", "color": "black", "bordercolor": "#4A7000"},
        "button": {"backgroundcolor": "#314A00", "color": "white", "bordercolor": "#1D2B00"},
    },
    "fixed": {
        "tile": {"backgroundcolor": "#486078", "color": "white", "bordercolor": "#001C54", "fontcolor": "#93C4F5"},
        "container": {"backgroundcolor": "#7ca5cf", "color": "white", "bordercolor": "#526E8A"},
        "button": {"backgroundcolor": "#333399", "color": "white", "bordercolor": "#000066"},
    },
}


def ll_name(ll_id):
    return learning_lines[ll_id][name]


def ll_color(ll_id):
    return learning_lines[ll_id]["color"]


def ll_id(ll_id):
    return learning_lines[ll_id][id]


def learning_line_colors():
    colors = []
    for ll_dict in learning_lines:
        colors.append(ll_dict["color"])
    return colors


# state strings
df_current = 'df_current'
current_course_id = 'current_course_id'
database = 'database'
username = 'username'
saved_selections = 'saved_selections'
df_osiris = 'df_osiris'
rename_text_value = 'rename_text_value'
current_selection = 'current_selection'
user_path = 'user_path'
study_stream = 'study_stream'
year = 'year'
id = 'id'
ctr = 'ctr'
abbr = 'abbr'
previous_page = 'previous_page'
study_stream_select = 'study_stream_select'
year_radio = 'year_radio'
name = 'name'
current_selection_selectbox = 'current_selection_selectbox'
rename_expanded = 'rename_expanded'
rename_selection_text = 'rename_selection_text'
add_expanded = 'add_expanded'
add_selection_text = 'add_selection_text'
add_text_value = 'add_text_value'
tgl_show_hide_options = 'tgl_show_hide_options'
authentication_status = 'authentication_status'
config = 'config'
system = 'system'

# database strings
created_by = 'created_by'
coll_users = 'users'
coll_course_selections = 'course_selections'
user_system = 'system'
coll_courses = 'courses'
path = 'path'
osiris = 'osiris2'
bbt_optional = 'bbt_optional'
mwt_optional = 'mwt_optional'
learninglines = 'learninglines'
ec = 'minimum_punten'
block = 'aanvangsblok'
code = 'code'
long_name = 'lange_naam'
volledige_naam = 'volledige_naam'
lecturer = 'lecturer'
stream = 'stream'
contents_en = 'inhoud_engels'
requirements = 'voorkennis'
docenten = 'docenten'
docent_naam = 'naam'
rol = 'rol'
opmerking = 'opmerking'
timeslots = 'timeslots'
timeslot = 'timeslot'
omschrijving_docenten = 'omschrijving'
toetsen = 'toetsen'
gelegenheden = 'aantal_gelegenheden'
min_cijfer = 'minimum_cijfer'
omschrijving_toetsen = 'omschrijving'
verplicht = 'verplicht'
weging = 'weging'
overig_toetsen = 'miscellaneous'
werkvormen = 'werkvormen'
aantal_bijeenk = 'aantal_bijeenkomsten'
frequentie = 'frequentie'
aanw_plicht = 'aanwezigheidsplicht'
omschrijving_werkvormen = 'omschrijving'
contactduur = 'contactduur_(min)'
materialen = 'materialen'
materiaal_verplicht = 'aanbevolen_verplicht'
materiaal = 'materiaal'
materiaal_omschrijving = 'omschrijving'
materiaal_overige_informatie = 'overige_informatie'
