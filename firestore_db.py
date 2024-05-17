import json
from datetime import datetime
from os import remove

from google.cloud import firestore
from google.oauth2 import service_account
from streamlit import secrets

import constants as cs


class Database:
    def __init__(self) -> None:
        key_dict = json.loads(secrets["textkey"])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        self.client = firestore.Client(credentials=creds, project="kieswijzer-63c52")

    def count_nr_docs(self, coll_path):
        try:
            query = self.client.collection(coll_path).count()
            query_result = query.get()
            return int(query_result[0][0].value)
        except:
            return 0

    def count_nr_colls(self, doc_path):
        nr = 0
        for c in self.client.document(doc_path).collections():
            nr += 1
        return nr

    def set_doc_data(self, doc_dict, doc_path):
        '''
        Stores a document dict in an existiing document, or creates a new one if the document does not yet exist.
        :param doc_dict: dict with document info
        :param doc_path: str describing path to doc. Must contain even nr of elements, e.g. "base_coll/doc_holding_coll/dest_coll/docname"\n
        If path contains odd nr elements ("base_coll/doc_holding_coll/dest_coll") a document with auto_ID is added.
        :return: firestore document ID
        '''
        try:
            # path points to collection if nr of forward slashes is even, to document if odd:
            if divmod(doc_path.count('/'), 2)[1]:
                ref = self.client.document(doc_path)
            else:
                ref = self.client.collection(doc_path).document()
            ref.set(doc_dict)
            return ref.id
        except Exception as e:
            print(f'Error storing document: {e}')

    def rename_doc_keys(self, old_names, new_names, doc_path):
        '''
        takes two same-length lists with old and new field names and changes field name by copying field to new field with new_name,
         and then deleting field old_name)
        :param old_names: list of str
        :param new_names: list of str
        :param doc_path: pathto document
        :return:
        '''
        doc_dict = self.get_doc_data(doc_path)
        edit_dict = {}
        for old_name, new_name in zip(old_names, new_names):
            edit_dict[new_name] = doc_dict[old_name]
            edit_dict[old_name] = firestore.DELETE_FIELD
        doc_ref = self.client.document(doc_path)
        doc_ref.update(edit_dict)

    def update_doc_fields(self, edit_dict, doc_path):
        try:
            doc_ref = self.client.document(doc_path)
            doc_ref.update(edit_dict)
        except Exception as e:
            print(f'Error updating document: {e}')

    def delete_doc_fields(self, del_field_names, doc_path):
        for field_name in del_field_names:
            self.client.document(doc_path).update({field_name: firestore.DELETE_FIELD})

    def get_doc_data(self, doc_path, include_id=True):
        '''
        Retrieves document fields in a document as a dict (not subcollections)
        :param include_id: add reference ID to returned dict
        :param doc_path: str describing path to doc. Must contain even nr of elements, e.g. "base_coll/doc_holding_coll/dest_coll/docname"
        :return :  dict with document info
        '''
        ref = self.client.document(doc_path).get()
        d = ref.to_dict()
        if include_id:
            d[cs.id] = ref.id
        return d

    def delete(self, path):
        '''
        recursively deletes either document of collection.\n.
        Note: If the collection holding the document
        is empty afterward, it too will be deleted!

        :param path: absolute path to doc or coll
        :return:
        '''
        # determine whether path points to doc or coll
        if divmod(path.count('/'), 2)[1]:
            ref = self.client.document(path)
        else:
            ref = self.client.collection(path)
        self.client.recursive_delete(ref)

    def copy_doc(self, src_doc_path, dest_doc_path):
        '''
        recursively copies all data into new doc
        :param dest_doc_path:
        :param src_doc_path:
        :return: None
        '''
        for coll in self.get_doc_coll_names(src_doc_path, False):
            docs = self.get_coll_doc_names(coll_path=src_doc_path + '/' + coll, include_path=False)
            for doc in docs:
                self.copy_doc(src_doc_path + '/' + coll + '/' + doc, dest_doc_path + '/' + coll + '/' + doc)
        self.set_doc_data(self.get_doc_data(src_doc_path), dest_doc_path)

    def copy_coll(self, src_path, dest_path, relative_path=True):
        '''
        copies documents in coll to another collection. If relative_path is true contents are copied to a collection
        in the same parent document. Otherwise, absolute path is used
        :param src_path: str: Full path to collection to be copied. Must contain odd nr of elements.
        :param dest_path: str: path of collection destination. Must contain odd nr of elements
        :param relative_path: bool: if true, absolute path=path_to_parent_document +'/'+dest_path. If False,absolute path = 'dest_path'
        :return: None
        '''
        if relative_path:
            parent_doc_path = src_path[:src_path.rfind('/')] if src_path.rfind('/') >= 0 else ''
            dest_path = parent_doc_path + '/' + dest_path if parent_doc_path != '' else dest_path
        for doc_name in self.get_coll_doc_names(src_path, include_path=False):
            self.copy_doc(src_path + '/' + doc_name, dest_path + '/' + doc_name)

    def get_coll_doc_data(self, coll_path, include_id=True):
        '''
        Returns a list of docs in a collection as dicts.
        Nested documents are not returned.
        :param include_id: include document ID in returned dicts as key cs.id
        :param coll_path: string describing full path to collection with odd nr elements,  e.g. "base_coll/doc_holding_coll/dest_coll"
        :return: list of documents as dicts
        '''
        return self.query_coll(coll_path=coll_path, include_id=include_id)

    def set_coll_doc_data(self, coll_path, doc_data):
        '''
        creates collection in coll_path or overwrites existing coll
        fills collection with dicts in list doc_data
        :param coll_path: str: path to new or existing collection
        :param doc_data: [dict]: list of document dicts
        :return: None
        '''
        for doc in doc_data:
            self.set_doc_data(doc, coll_path + '/' + doc[cs.id])

    def query_coll(self, *, coll_path, doc_fields=None, include_id=True, where_conditions=None):
        '''
        Queries a collection based on where_condition(s). When supplied,
        where_conditions must be a list of  3-element lists supplying field, operator, value
        as per Firestore requirements. See also https://firebase.google.com/docs/firestore/query-data/queries. \n
        Example: query_coll(coll_path='osiris', doc_fields=['code', 'block'],where_conditions=[['year', '==', '1'], ['block','==','2']]) returns \n
        [{'code': '8BA030', 'block': '2'}, {'code': '8BA040', 'block': '2'}, {'code': '8BA050_blok1', 'block': '2'}]
        :param include_id: include reference ID in returned dicts
        :param coll_path: path to collection to be queried
        :param doc_fields: optional list of str with field IDs
        :param where_conditions: list(s) of 3 elements, describing query condition
        :return: list of dicts containing all document fields if fields is None, or list of dicts with {field1:val1,...,fieldN:valN}
        '''
        if where_conditions is None:
            where_conditions = []
        ref = self.client.collection(coll_path)
        for where in where_conditions:
            ref = ref.where(
                filter=firestore.FieldFilter(where[0], where[1], where[2]))
        dict_list = []
        for doc in ref.stream():
            doc_dict = doc.to_dict()
            return_dict = doc_dict.copy()
            if doc_fields is not None:
                for key in doc_dict.keys():
                    if key not in doc_fields:
                        return_dict.pop(key)
            if include_id:
                return_dict[cs.id] = doc.id
            dict_list.append(return_dict)
        return dict_list

    def get_doc_coll_names(self, doc_path, include_path=False):
        '''
        Returns list of collection names (IDs in FS) in a document
        :param doc_path: str: path to document
        :param include_path: bool: include docpath in returned collection name
        :return: [str]
        '''
        return [doc_path + '/' + coll.id if include_path else coll.id for coll in
                self.client.document(doc_path).collections()]

    def get_coll_doc_names(self, coll_path, include_path=False):
        '''
        Returns list of document names (IDs in FS) in a collection
        :param coll_path: str: path to collection
        :param include_path: bool: include coll_path in returned collection name
        :return: [str]
        '''
        return [coll_path + '/' + doc.id if include_path else doc.id for doc in
                list(self.client.collection(coll_path).list_documents())]

    def osiris_import(self, source_file, collection_name):
        '''
        Custom handler for Osiris exports.
        Word document containing Osiris export must be saved as a text file with UTF-8 encoding.
        Quotes (") in text will be replaced by left and if possible right quotes.
        Will overwrite pre-existing collections with the same name. NOTE: to avoid issues with HTML,
        check text for presence of symbols with special meaning in HTML, notably & and :
        :param source_file: text file in UTF-8 format generated by saving Osiris Word export as txt.
        :param collection_name: base collection name in Firestorm db to hold data.
        :return:
        '''
        replace_dict = {
            '\r\n\r\n8': '}\n{\n$$$naam$$&8',
            'Lange naam': '$$$lange_naam$$&',
            'Cursustype\r': '$$$cursustype$$&',
            'Minimum punten\r': '$$$minimum_punten$$&',
            'Categorie\r': '$$$categorie$$&',
            'Examendoel': '$$$examen_doel$$&',
            'Voertaal\rOmschrijving\r': '^^$voertaal|omschrijving|^^&',
            'Voertaal\r\n': '$$$voertaal$$&',
            'Vrije velden\r': '',
            'Vrij veld\rInhoud\r': '',
            'Korte wervende omschrijving van de cursus\r': '$$$omschrijving_nl$$&',
            'Short promotional description of the course\r': '$$$omschrijving_en$$&',
            'Faculteit die het vak roostert\r': '$$$faculteit$$&',
            'Werkvormen\r\n': '$$$werkvormen$$&',
            'Werkvorm\rOmschrijving\rAanw. plicht?\rAantal bijeenk.\rFrequentie\rContactduur (min)\r\r\r\r\r\r\r': '^^$werkvorm|omschrijving||aanwezigheidsplicht|aantal_bijeenkomsten|frequentie|contactduur_(min)||description|||^^&',
            'Toetsen\r\n': '$$$toetsen$$&',
            'Toets\rOmschrijving\rToetsvorm\rWeging\rPunten\rMinimum cijfer\rVerplicht\rToetsduur\rAantal gelegen heden\rTermijn bewaking resultaten\r\r': '^^$toets|omschrijving|toetsvorm|weging|punten|minimum_cijfer|verplicht|toetsduur|aantal_gelegenheden|termijn_bewaking_resultaten|^^&',
            'Blokken\r\nAanvangsblok\r': '$$$aanvangsblok$$&',
            'Timeslots\r\n': '$$$timeslots$$&',
            'Aanvangsblok\rTimeslot\rOmschrijving\r': '^^$aanvangsblok|timeslot|omschrijving|^^&',
            'Syllabus doelgroepen\r\n': '$$$syllabus_doelgroepen$$&',
            'Aanvangs-blok\rSyllabus doelgroep\rOmschrijving\r': '^^$aanvangs_blok|syllabus_doelgroep|omschrijving|^^&',
            'Docenten\r\n': '$$$docenten$$&',
            'Naam\rRol\rOpmerking\r': '^^$naam|rol|opmerking|^^&',
            'Doel\r\n': '$$$doel_nl$$&',
            'Doel (Engels)\r\n': '$$$doel_en$$&',
            'Inhoud\r\n': '$$$inhoud$$&',
            'Inhoud (Engels)\r\n': '$$$inhoud_engels$$&',
            'Materialen\r\n': '$$$materialen$$&',
            'Materiaal\rAanbevolen/\r\nverplicht\rOverige informatie\rOmschrijving\r': '^^$materiaal|aanbevolen_verplicht|overige_informatie|omschrijving|^^&',
            'Ingangseisen\r\n': '$$$ingangseisen$$&',
            'Veronderstelde voorkennis\r\n': '$$$voorkennis$$&',
        }
        toetsvormen = [
            "DIGI_01",
            "DIGI_02",
            "JAARTOETS",
            "MOND_01",
            "MOND_02",
            "MOND_03",
            "OVERIG_01",
            "OVERIG_02",
            "OVERIG_03",
            "OVERIG_04",
            "OVERIG_05",
            "OVERIG_06",
            "OVERIG_07",
            "PRODUCT_01",
            "PRODUCT_02",
            "PRODUCT_03",
            "PRODUCT_04",
            "PRODUCT_05",
            "PRODUCT_06",
            "PRODUCT_07",
            "PRODUCT_08",
            "PRODUCT_09",
            "PRV_01",
            "PRV_02",
            "PRV_03",
            "PRV_04",
            "PRV_05",
            "PRV_06",
            "SCHRIFT_01",
            "SCHRIFT_02",
            "SCHRIFT_03",
            "SCHRIFT_04",
            "SCHRIFT_05",
        ]
        werkvormen = [
            "COLLEGE_01",
            "COLLEGE_02",
            "COLLEGE_03",
            "COLLEGE_04",
            "COLLEGE_05",
            "COLLEGE_06",
            "COLLEGE_07",
            "COLLEGE_08",
            "COLLEGE_09",
            "COLLEGE_10",
            "COLLEGE_11",
            "COLLEGE_20",
            "COLLEGE_21",
            "COLLEGE_22",
            "COLLEGE_23",
            "COLLEGE_24",
            "INSTRUCT_01",
            "INSTRUCT_02",
            "INSTRUCT_03",
            "INSTRUCT_04",
            "INSTRUCT_05",
            "INSTRUCT_06",
            "INSTRUCT_07",
            "INSTRUCT_08",
            "INSTRUCT_09",
            "INSTRUCT_10",
            "INSTRUCT_11",
            "INSTRUCT_12",
            "INSTRUCT_13",
            "INSTRUCT_14",
            "INSTRUCT_20",
            "INSTRUCT_21",
            "INSTRUCT_22",
            "INSTRUCT_23",
            "INSTRUCT_24",
            "INSTRUCT_25",
            "INSTRUCT_26",
            "INSTRUCT_27",
            "LIVESTREAM",
            "OVERIG_02",
            "OVERIG_03",
            "OVERIG_04",
            "OVERIG_05",
            "OVERIG_06",
            "OVERIG_07",
            "OVERIG_08",
            "OVERIG_09",
            "OVERIG_10",
            "OVERIG_11",
            "OVERIG_12",
            "OVERIG_20",
            "OVERIG_21",
            "OVERIG_22",
            "OVERIG_23",
            "OVERIG_24",
            "PRACT_01",
            "PRACT_02",
            "PRACT_03",
            "PRACT_04",
            "PRACT_05",
            "PRACT_06",
            "PRACT_07",
            "PRACT_08",
            "PRACT_09",
            "PRACT_10",
            "PRACT_11",
            "PRACT_12",
            "PRACT_20",
            "PRACT_21",
            "PRACT_22",
            "PRACT_23",
            "SCHR_NB_STEP",
            "WERKCOL_01",
            "WERKCOL_02",
            "WERKCOL_03",
            "WERKCOL_04",
            "WERKCOL_05",
            "WERKCOL_06",
            "WERKCOL_07",
            "WERKCOL_08",
            "WERKCOL_09",
            "WERKCOL_10",
            "WERKCOL_11",
            "WERKCOL_20",
            "WERKCOL_21",
            "WERKCOL_22",
            "WERKCOL_23",
            "WERKCOL_24",
            "WERKCOL_25",
            "WERKVORM-01",
            "WERKVORM-02",
            "WERKVORM-03",
            "WERKVORM-04",
            "WERKVORM-05",
            "WERKVORM-06",
            "WERKVORM-07",
            "WERKVORM-08",
            "WERKVORM-09",
            "WERKVORM-10",
            "WERKVORM-11",
            "WERKVORM-12",
            "WERKVORM-13",
            "WERKVORM-14",
            "WERKVORM-15",
            "WERKVORM-16",
            "WERKVORM-17",
            "WERKVORM-18",
            "WERKVORM-19",
            "WERKVORM-20",
        ]

        def replace_quotes(str):
            """
            Returns a string starting and ending with standard quote (" or \u0022).
            Replaces pre-existing standard quotes by left quotes
            \u0201c and any matching second standard quote by \u0201d if found
            """
            # replace pre-existing quotes
            quotes_present = True
            while quotes_present:
                quotes_present = False
                left_quote = str.find('"')
                if left_quote > -1:
                    str = str.replace('"', '\u201c', 1)
                    quotes_present = True
                right_quote = str.find('"')
                if right_quote > -1:
                    str = str.replace('"', '\u201d', 1)
                    quotes_present = True
            # return word in normal quotes
            return str

        def create_encoded_lines(source_file, target_file):
            f = open(source_file, encoding="UTF-8", newline='')
            data = f.read()
            # check for double quotes 
            data = replace_quotes(data)
            for (src, dst) in replace_dict.items():
                data = data.replace(src, dst)
            data = data.replace('\r', '|')
            data = data.replace('\n', '')
            data = data.replace('$$$', '\n$$$')
            data = data.replace('$$&', '$$&\n')
            data = data.replace('}{', '\n}\n{')
            data = "{\n$$$naam$$&\n" + data + "\n}"
            f.close()
            f = open(target_file, mode="w", encoding="UTF-8")
            f.write(data)
            f.close()

        def get_substr(string, sub1, sub2):
            try:
                val = string[string.index(sub1) + len(sub1): string.index(sub2)]
            except:
                val = ""
            return val

        def to_dict_str(format_str, val_str, ignore_emptylines, var_type):
            def quote(word):
                return ('"' + word + '"')

            def get_words(strip_leading_pipes, string):
                try:
                    words = []
                    if strip_leading_pipes:
                        while string[0] == "|":  # remove leading pipes
                            string = string[1:]
                    word = ''
                    for i in range(len(string)):
                        if string[i] != "|":
                            word += string[i]
                        else:
                            words.append(word)
                            word = ''
                    if string[-1:] != "|":  # format string may not end with pipe
                        words.append(word)
                except:
                    words = []
                return words

            dict_str = "{"
            # keys from formatstr
            keys = get_words(strip_leading_pipes=True, string=format_str)
            vals = get_words(strip_leading_pipes=False, string=val_str)
            line = 0
            if var_type == 'fixed':
                # fixed layout
                while line * len(keys) <= len(vals) - len(keys):
                    line_empty = True
                    entry = ""
                    for key in keys:
                        val = vals[line * len(keys) + keys.index(key)]
                        line_empty = line_empty and len(val) == 0
                        if not (key == ''):
                            entry += f'{quote(key)}:{quote(val)},'
                    if not (ignore_emptylines and line_empty):
                        dict_str += entry
                    line += 1
            elif var_type == 'toets' or var_type == 'werkvorm':
                val_txt = ''
                entry = ''
                key = ''
                key_index = 0
                line_empty = True
                for val in vals:
                    if (var_type == 'toets' and val in toetsvormen) or (var_type == 'werkvorm' and val in werkvormen):
                        # write previous line if present (i.e.key<>'')
                        if not (ignore_emptylines and line_empty) and key != '':
                            dict_str += f'{quote(key)}:{quote(val_txt)},'
                        key_index = 0
                        line_empty = True
                        val_txt = ''
                    if key_index < len(keys):
                        key = keys[key_index]
                        val_txt += val
                        line_empty = line_empty and len(val_txt) == 0
                        if not (ignore_emptylines and line_empty) and key != '':
                            dict_str += f'{quote(key)}:{quote(val_txt)},'
                        key_index += 1
                        val_txt = ''
                        key = ''
                    else:
                        # end of keys reached, string values together and add to last key
                        if val != '':
                            key = "miscellaneous"
                            val_txt += val + ";"
                if not (key == ''):
                    dict_str += f'{quote(key)}:{quote(val_txt)},'
            else:
                raise Exception("value type is neither fixed, toets or werkvorm!")
            dict_str += "}"
            return dict_str

        def create_dict_list(file_name):
            file = open(file_name, encoding="UTF-8")

            output = ""
            output_line = ""
            key = ""
            for line in file.readlines():
                if '{' in line:
                    output_line += "{"
                elif '}' in line:
                    # add key/value pair 'id':<use course> to be used as ID for future storage Firestore
                    id = get_substr(output_line, '"naam":"', ' - ')
                    output_line += f'"id":"{id}",'
                    output_line += "}\n"
                    # remove commas before and of dict as json will not accept these
                    output_line = output_line.replace(",}", "}")
                    output += output_line
                    output_line = ""

                elif '$$' in line:  # line contains key
                    key = get_substr(line, '$$$', '$$&')
                    key = key.replace('"', '\'')
                    output_line += f'"{key}":'
                else:
                    formatter = get_substr(line, '^^$', '^^&')
                    value = line.replace('^^$' + formatter + '^^&', "")
                    value = value.strip('\n')
                    if formatter != '':
                        var_type = 'fixed'
                        if 'toets' in formatter:
                            var_type = 'toets'
                        if 'werkvorm' in formatter:
                            var_type = "werkvorm"
                        value = to_dict_str(format_str=formatter, val_str=value, ignore_emptylines=True,
                                            var_type=var_type)
                    # value=value.replace('"','\'')
                    value = value.replace('|', '')
                    output_line += f'"{value}",'
            file.close()

            file = open(file_name, mode="w", encoding="UTF-8")
            file.write(output)
            file.close()

        def store_dict(dict_str, coll_path, id_key=None):
            def strip_quotes(s):
                qstart = s.find('"')
                qend = s.rfind('"')
                return s[qstart + 1:qend]

            def find_key_value(s):
                def find_word(s):
                    qstart = s.find('"')
                    qend = s[qstart + 1:].find('"') + qstart + 1
                    if qstart < 0 or qend < 0:
                        return '', -1
                    return s[qstart + 1:qend], qstart

                key, qstart = find_word(s)
                length = qstart + len(key) + 2
                s = s.replace('"' + key + '"', '', 1)
                val, qstart = find_word(s)
                length = length + qstart + len(val) + 2
                return key, val, length

            def write_dict():
                if id_key is not None:
                    doc_ref_id = doc_dict[id_key]
                else:
                    try:  # try to access collection if it already exists and count nr of docs it contains
                        coll_ref = self.client.collection(coll_path)
                        # doc id is coll name plus [nr docs in collection]
                        doc_ref_id = f'{coll_path[coll_path.rfind("/") + 1:]}_{len(list(coll_ref.stream()))}'
                    except:
                        doc_ref_id = f'{coll_path[coll_path.rfind("/") + 1:]}_0'
                doc_ref_path = f"{coll_path}/{doc_ref_id}"
                self.client.document(doc_ref_path).set(doc_dict)
                return doc_ref_id

            substrings = []
            keys = []
            # remove the curly braces from the string
            doc_dict = {}
            st = dict_str.find('{')
            end = dict_str.rfind('}')
            if st < 0 or end < 0:
                raise Exception("start and/or end braces missing")
            st += 1
            sub = dict_str[st:end]
            while len(sub) > 0 and '"' in sub:
                key, value, length = find_key_value(sub)
                if key in keys:
                    write_dict()
                    keys = []
                    doc_dict = {}
                keys.append(key)
                if '{' in value:
                    # store sub-dicts to be stored in FS after the document has been created, as 
                    # the sub-collection must be created within a document
                    right_brace_pos = sub.find('}')
                    quote_after_right_brace = sub[right_brace_pos:].find('"')
                    end_quote_in_sub = right_brace_pos + quote_after_right_brace
                    new_sub = sub[sub.find('{'):end_quote_in_sub]
                    substrings.append([new_sub, key])
                    # cut out subsection
                    sub = sub[end_quote_in_sub + 2:]
                else:
                    if length > 0:
                        doc_dict[key] = value
                        sub = sub[length + 1:]
            doc_ref_id = write_dict()
            # now that the doc exists, add any sub-collections recursively
            for item in substrings:
                store_dict(item[0], f'{coll_path}/{doc_ref_id}/{item[1]}')

            return doc_dict

        # initialize Firestorm database

        tmp = f'osiris_export_{datetime.now().strftime("%H_%M_%S")}.tmp'
        # read raw text file and flag headers, so we can encode the text for re-scripting in pseudo-json
        create_encoded_lines(source_file, tmp)
        # transform encoded text into pseudo-json
        create_dict_list(tmp)
        # overwrite any pre-existing version
        self.client.recursive_delete(self.client.collection(collection_name))
        file = open(tmp, encoding="UTF-8")
        data = file.readlines()
        for index, line in enumerate(data):
            store_dict(dict_str=line, coll_path=collection_name, id_key='id')
            print(
                f'\tCourse {index + 1} of {len(data)} successfully imported in Firestore collection "{collection_name}".',
                end="\r")
        file.close()
        remove(tmp)


'''
En daarna: 
-splitsen 10 EC vakken in twee docs
-checken op dubbele punten, & , (,)
-toevoegen extra velden:
    bbt_optional	
    learninglines	
    lecturer	
    mwt_optional	
    year
'''
