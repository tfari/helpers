""" Handler for Notion API interaction """
import json.decoder
import time
import requests

GET, POST, PATCH = 'GET', 'POST', 'PATCH'  # Handy constants


class NotionHandler:
    """
    Handler for Notion API interaction
    """
    _VALIDATION_URL = 'https://api.notion.com/v1/databases'
    _DB_PARENT_FIND_URL = 'https://api.notion.com/v1/search'
    _PAGE_QUERY_URL = 'https://api.notion.com/v1/blocks/%s/children'

    _HEADERS = {'Authorization': '',
                'Notion-Version': '',
                'Content-Type': 'application/json'}

    _DB_RETRIEVE_URL = 'https://api.notion.com/v1/databases/%s'
    _DB_QUERY_URL = 'https://api.notion.com/v1/databases/%s/query'
    _DB_QUERY_DATA = """{}"""
    _DB_QUERY_DATA_WITH_CURSOR = """{
        "start_cursor": "%s"}"""

    _DB_UPDATE_PAGE_URL = 'https://api.notion.com/v1/pages/%s'
    _DB_APPEND_BLOCK_CHILDREN = 'https://api.notion.com/v1/blocks/%s/children'
    _DB_CREATE_DATABASE = 'https://api.notion.com/v1/databases'
    _DB_ADD_TO_DATABASE = 'https://api.notion.com/v1/pages'
    _DB_QUERY_PAGE = 'https://api.notion.com/v1/blocks/%s/children'

    def __init__(self, notion_token: str, notion_version: str, sleep_time_on_rate_limit: int):
        """
        :param notion_token: str, valid Notion token
        :param notion_version: str, Notion API Version information
        :param sleep_time_on_rate_limit: int, time to wait when rate limited
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise InvalidToken: if the Notion token is invalid
        :raise APIError: on any other API error
        """
        self.notion_token = notion_token
        self.notion_version = notion_version
        self.sleep_time_on_rate_limit = sleep_time_on_rate_limit

        self._HEADERS['Authorization'] = 'Bearer %s' % notion_token
        self._HEADERS['Notion-Version'] = notion_version

        self._validate_notion_token()

    def _wrap_notion_api_request(self, url, method=GET, data=None) -> dict:
        """
        Wrap a Notion request in order to handle rate-limiting and to catch JSON, HTTP and
        API errors.

        :param url: str, url to perform the HTTP request to
        :param method: GET/POST/PATCH
        :param data: data for POST requests
        :return: dict, JSON response of valid API call

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise InvalidToken: if the Notion token is invalid
        :raise InvalidDatabaseUuid: if the Notion database is not a valid uuid
        :raise DatabaseIDNotFound: if the Notion database was not found
        :raise APIError: on any other API error
        """
        r = requests.request(method, url, headers=self._HEADERS, data=data)
        if r.status_code != 200:
            if r.status_code == 429:   # Too many requests
                time.sleep(self.sleep_time_on_rate_limit)
                return self._wrap_notion_api_request(url, method, data)
            else:
                try:
                    self._handle_api_errors(r)
                except json.decoder.JSONDecodeError:
                    raise self.HTTPError(f'HTTP Error: {url}, : {r}')
        else:
            try:
                return r.json()
            except json.decoder.JSONDecodeError:
                raise self.JSONErrorOn200Return(f'JSONErrorOn200Return: {url}, : {r}')

    def _handle_api_errors(self, r: requests.Response) -> None:
        """
        Attempt to call r.json() and then raise according to the status_code and error contents.

        :param r: requests.Response object
        :raise InvalidToken: if the Notion token is invalid
        :raise InvalidDatabaseUuid: if the Notion database is not a valid uuid
        :raise DatabaseIDNotFound: if the Notion database was not found
        :raise APIError: on any other API error
        """
        response_json = r.json()
        if r.status_code == 401:
            raise self.InvalidToken(f'Invalid Notion token: "{self.notion_token}"')
        elif r.status_code == 400 and response_json['code'] == 'validation_error':
            if response_json['message'].find('valid uuid') != -1:
                print(response_json)
                raise self.InvalidDatabaseUuid()
            else:
                raise self.APIError(response_json)
        elif r.status_code == 404 and response_json['code'] == 'object_not_found':
            raise self.DatabaseIDNotFound()
        else:
            raise self.APIError(r.status_code, response_json)

    def _validate_notion_token(self) -> None:
        """
        Validate Notion token
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise InvalidToken: if the Notion token is invalid
        :raise APIError: on any other API error
        """
        self._wrap_notion_api_request(self._VALIDATION_URL)

    def _query_all_pages(self, results: list = None, start_cursor: str = None) -> list:
        """
        Query all Notion pages. If the API returns a multi-page result, call itself recursively with
        the next start_cursor and accumulate  results before returning.

        :param results: list, previously gathered results if multi-page return. Used by function.
        :param start_cursor: str, cursor for multi-page query. Used by function.
        :return: list, Notion pages

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        """
        # Initialize variables
        results = [] if not results else results
        data = self._DB_QUERY_DATA if not start_cursor else \
            self._DB_QUERY_DATA_WITH_CURSOR % start_cursor

        r = self._wrap_notion_api_request(self._DB_PARENT_FIND_URL, method=POST, data=data)
        results.extend(r['results'])

        if 'has_more' in r.keys() and r['has_more'] is True:
            return self._query_all_pages(results, r['next_cursor'])
        return results

    def update_page_properties(self, page_id: str, properties: dict) -> dict:
        """
        Update Notion page's properties

        :param page_id: valid page ID
        :param properties: valid page updating properties JSON, as defined by the API

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        :return: API response
        """
        data = json.dumps(properties)
        result = self._wrap_notion_api_request(self._DB_UPDATE_PAGE_URL % page_id, method=PATCH, data=data)
        return result

    def write_on_page(self, page_id: str, contents: dict) -> dict:
        """
        Append block children to a Notion page

        :param page_id: valid page ID
        :param contents: valid contents JSON for appending block children, as defined by the API

        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        :return: API response
        """
        data = json.dumps(contents)
        result = self._wrap_notion_api_request(self._DB_APPEND_BLOCK_CHILDREN % page_id, method=PATCH, data=data)
        return result

    def query_db(self, db_id: str, results: list = None, start_cursor: str = None) -> list:
        """
        Query a Notion database with id db_id and return the results. If the API returns a
        multi-page result, call itself recursively with the next start_cursor and accumulate
        results before returning.

        :param db_id: str, valid Notion database id
        :param results: list, previously gathered results if multi-page return. Used by function.
        :param start_cursor: str, cursor for multi-page query. Used by function.
        :return: list, Notion database rows
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise InvalidDatabaseUuid: if the Notion database is not a valid uuid
        :raise DatabaseIDNotFound: if the Notion database was not found
        :raise APIError: on any other API error
        """
        # Initialize variables
        results = [] if not results else results
        data = self._DB_QUERY_DATA if not start_cursor else \
            self._DB_QUERY_DATA_WITH_CURSOR % start_cursor

        r = self._wrap_notion_api_request(self._DB_QUERY_URL % db_id, method=POST, data=data)
        results.extend(r['results'])

        if 'has_more' in r.keys() and r['has_more'] is True:
            return self.query_db(db_id, results, r['next_cursor'])
        return results

    def create_database(self, database_schema: dict) -> dict:
        """
        Create a database
        :param database_schema: valid JSON database schema, as defined by the API
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        :return: API response
        """
        database_schema = json.dumps(database_schema)
        result = self._wrap_notion_api_request(self._DB_CREATE_DATABASE, method=POST, data=database_schema)
        return result

    def update_to_database(self, data: dict) -> dict:
        """
        Update a database
        :param data: valid database update JSON, as defined by the API
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        :raise InvalidDatabaseUuid: if the Notion database is not a valid uuid
        :raise DatabaseIDNotFound: if the Notion database was not found
        :return: API response
        """
        data = json.dumps(data)
        result = self._wrap_notion_api_request(self._DB_ADD_TO_DATABASE, method=POST, data=data)
        return result

    def query_page(self, page_id: str) -> dict:
        """
        Query a Notion page
        :param page_id: valid Notion page id
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise APIError: on any other API error
        :return: API response
        """
        result = self._wrap_notion_api_request(self._DB_QUERY_PAGE % page_id)
        return result

    def get_db(self, db_id: str, db_structure: list) -> dict:
        """
        Get a Notion database with id db_id and validate it.
        :return: dict, Notion database information
        :raise JSONErrorOn200Return: if the answer from the request was 200 but was not a JSON
        :raise HTTP Error: if the answer from the request was an error and not a JSON
        :raise InvalidDatabaseUuid: if the Notion database is not a valid uuid
        :raise DatabaseIDNotFound: if the Notion database was not found
        :raise InvalidDBStructure: if the Notion database does not follow structure of _DB_STRUCTURE
        :raise APIError: on any other API error
        """
        try:
            db = self._wrap_notion_api_request(self._DB_RETRIEVE_URL % db_id)
            self.validate_db_structure(db, db_structure)
            return db
        except self.InvalidDatabaseUuid:
            raise self.InvalidDatabaseUuid(f'Invalid database uuid: "{db_id}"')
        except self.DatabaseIDNotFound:
            raise self.DatabaseIDNotFound(f'Database ID not found: "{db_id}". (Is it shared?)')

    def validate_db_structure(self, db: dict, db_structure: list) -> None:
        """
        Validate a Notion database by the rules in _DB_STRUCTURE
        :param db: dict, database as returned by a Notion DB_RETRIEVE API call
        :param db_structure: A list containing tuples of (NAME, TYPE), in order to validate a db has the structure the
        client requires in order to operate.
        :raise InvalidDBStructure: if the Notion database does not follow structure of _DB_STRUCTURE
        """
        for structure_rules in db_structure:
            column_key, expected_column_type = structure_rules[0], structure_rules[1]
            try:
                real_column_type = db['properties'][column_key]['type']
                if real_column_type != expected_column_type:
                    raise self.InvalidDBStructure(f'InvalidDBStructure: Column "{column_key}" '
                                                  f'should be of type: "{expected_column_type}" '
                                                  f'but was: "{real_column_type}" in the Notion\'s '
                                                  f'database.')
            except KeyError:
                raise self.InvalidDBStructure(f'InvalidDBStructure: Column "{column_key}" does '
                                              f'not exist in the Notion\'s database.')

    class JSONErrorOn200Return(Exception):
        """ .json() failed on a 200 return error """

    class InvalidDBStructure(Exception):
        """ The Notion database does not the specified structure """

    class HTTPError(Exception):
        """ Answer from an HTTP request was an error and not a valid JSON API return"""

    class APIError(Exception):
        """ Unexpected Notion API Error """

    class InvalidToken(APIError):
        """ Invalid Notion Token """

    class InvalidDatabaseUuid(APIError):
        """ Invalid Database Uuid """

    class DatabaseIDNotFound(APIError):
        """ Database ID was not found by Notion's integration """

    class CouldNotFindParent(APIError):
        """ Could not find parent Page of a database """

# Wrappers


class RichText:
    """ Wrapper for conveniently working with RichText Notion objects """
    def __init__(self, txt: str, href: str = None, bold: bool = False, color: str = None):
        self.txt = txt
        self.href = href
        self.bold = bold
        self.color = color

    def parse(self) -> dict:
        """ Transform object into convenient JSON dict representation """
        final_object = {'type': 'text', 'text': {'content': self.txt}}
        if self.href:
            final_object['text']['link'] = {'type': 'url', 'url': self.href}
        if self.bold:
            if not final_object.get('annotations'):
                final_object['annotations'] = {}
            final_object['annotations']['bold'] = True
        if self.color:
            if not final_object.get('annotations'):
                final_object['annotations'] = {}
            final_object['annotations']['color'] = self.color

        return final_object


class ObjectBlock:
    """ Base class for all Object block wrappers """


class ContentsTable(ObjectBlock):
    """ Wrapper for Contents Table block objects """
    def __str__(self):
        return {'object': 'block', 'type': 'table_of_contents', 'table_of_contents': {}}


class Heading(ObjectBlock):
    """ Wrapper for Heading1, Heading2 and Heading3 block objects """
    def __init__(self, lvl: int, txt: str):
        self.lvl = lvl
        self.txt = txt

    def __str__(self) -> dict:
        """ Transform object into convenient JSON dict representation """
        return {'object': 'block', 'type': f'heading_{str(self.lvl)}', f'heading_{str(self.lvl)}':
                {'text': [{'type': 'text', 'text': {'content': self.txt}}]}}


class Paragraph(ObjectBlock):
    """ Wrapper for Paragraph block objects """
    def __init__(self, rich_txt_list: list[RichText]):
        self.rich_txt_list = rich_txt_list

    def __str__(self) -> dict:
        """ Transform object into convenient JSON dict representation """
        return {'object': 'block', 'type': 'paragraph', 'paragraph':
                {'text': [rt.parse() for rt in self.rich_txt_list]}}


class CodeBlock(ObjectBlock):
    """ Wrapper for CodeBlock block objects """
    def __init__(self, txt: str, language: str = None):
        self.txt = txt
        self.language = language

    def __str__(self) -> dict:
        """ Transform object into convenient JSON dict representation """
        return {'object': 'block', 'type': 'code', 'code':
                {'text': [{'type': 'text', 'text': {'content': self.txt}}],
                 'language': 'plain text'}}


class Toggle(ObjectBlock):
    """ Wrapper for Toggle block objects """
    def __init__(self, rich_txt_list: list[RichText], children: list[ObjectBlock]):
        self.rich_txt_list = rich_txt_list
        self.children = children

    def __str__(self) -> dict:
        """ Transform object into convenient JSON dict representation """
        children_parsed = [c.__str__() for c in self.children]
        return {
            'object': 'block',
            "type": "toggle",
            "toggle": {
                "text": [rt.parse() for rt in self.rich_txt_list],
                "children": children_parsed
            }
        }
