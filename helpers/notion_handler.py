"""
API wrapper for handling private Notion integrations.

Reference: https://developers.notion.com/reference
Current version: 2022-06-28

Requirements:
    - requests
"""
import time
import json
from enum import Enum
from typing import Optional

import requests


class EmptyArgument:
    """ Use to differentiate between non-passed arguments and actual None as argument """


class HTTPMethod(Enum):
    """ Request Method constants """
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class NotionHandler:
    """ API Handler """
    CURRENT_VERSION = '2022-06-28'
    _VALIDATION_URL = 'https://api.notion.com/v1/users/me'  # Use this as validation ping
    _BASE_URL = 'https://api.notion.com/v1'

    # PAGES
    _GET_PAGE = _BASE_URL + '/pages/{}'
    _POST_PAGE = _BASE_URL + '/pages'
    _UPDATE_PAGE = _BASE_URL + '/pages/{}'
    _DELETE_PAGE = _BASE_URL + '/pages/{}'

    # USERS
    _BOT_USER = _BASE_URL + '/users/me'
    _LIST_USERS = _BASE_URL + '/users'
    _GET_USER = _BASE_URL + '/users/{}'

    # COMMENTS
    _GET_COMMENTS = _BASE_URL + '/comments?block_id={}'
    _POST_COMMENT = _BASE_URL + '/comments'

    # SEARCH
    _SEARCH = _BASE_URL + '/search'

    # DATABASES
    _GET_DATABASE = _BASE_URL + '/databases/{}'
    _POST_DATABASE = _BASE_URL + '/databases'
    _UPDATE_DATABASE = _BASE_URL + '/databases/{}'
    _DELETE_DATABASE = _BASE_URL + '/databases/{}'
    _QUERY_DATABASE = _BASE_URL + '/databases/{}/query'

    _GET_ROW_PROPERTY_ITEM = _BASE_URL + '/pages/{}/properties/{}'

    # BLOCKS
    _GET_BLOCK = _BASE_URL + '/blocks/{}'
    _GET_BLOCK_CHILDREN = _BASE_URL + '/blocks/{}/children'
    _POST_BLOCK_CHILDREN = _BASE_URL + '/blocks/{}/children'
    _UPDATE_BLOCK = _BASE_URL + '/blocks/{}'
    _DELETE_BLOCK = _BASE_URL + '/blocks/{}'

    def __init__(self, token: str, version: str = '', rate_sleep: int = 1, max_retry_rounds: int = 10):
        """
        :param token: Integration Token
        :param version: API Version to use, CURRENT_VERSION will be used if not passed
        :param rate_sleep: Seconds to use when rate limited
        :param max_retry_rounds: Max times to retry an api call when rate limited

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.InvalidToken:
        :raises NotionHandler.InvalidVersion:
        """
        self.token = token
        self.version = version if version != '' else NotionHandler.CURRENT_VERSION
        self._rate_sleep = rate_sleep
        self._max_retry_rounds = max_retry_rounds

        self._headers = {'Authorization': f'Bearer {self.token}', 'Notion-Version': self.version,
                         'Content-Type': 'application/json'}

        self.__validate()

    def __api_request(self, url: str, method: HTTPMethod, *, data: Optional[dict] = None, retry_round: int = 0) -> dict:
        """ Wrap Notion API requests. Handle rate-limiting and catch JSON, HTTP and API errors.

        :param url: str, url to perform the HTTP request to
        :param method: GET/POST/PATCH
        :param data: data for POST requests
        :param retry_round: internal int for retrying calls on rate limiting
        :return: dict, JSON response of valid API call

        :raise NotionHandler.UnexpectedError: If there is any unexpected error
        :raise NotionHandler.RequestError: If there is a requests raise
        :raise NotionHandler.JSONDecodeError: If there is an issue decoding the response's json
        :raise NotionHandler.MaxRetriesReached: If it retries a call more than max_retry_rounds times

        :raise NotionHandler.APIError: Lets self.__handle_errors escalate its exceptions
        """
        str_data = json.dumps(data) if data else None
        try:
            response = requests.request(method=str(method.value), url=url, headers=self._headers, data=str_data)
            if response.status_code == 429:  # Rate limited
                if retry_round > self._max_retry_rounds:
                    raise NotionHandler.MaxRetriesReached(f'Exceeded {self._max_retry_rounds} retries on url: {url}')
                else:
                    time.sleep(self._rate_sleep)
                    return self.__api_request(url, method, data=data, retry_round=retry_round + 1)
            elif response.status_code == 200:
                return response.json()
            else:
                self.__handle_api_errors(response.json())  # This will raise APIErrors

        except requests.RequestException as e:
            raise NotionHandler.RequestError(f'on url: {url}, err: {e.__class__.__name__}: {e}')
        except json.decoder.JSONDecodeError as e:
            raise NotionHandler.JSONDecodeError(f'on url: {url}: {e}')
        except Exception as e:
            if isinstance(e, NotionHandler.APIError):
                raise e
            raise NotionHandler.UnexpectedError(f'on url: {url}, err: {e.__class__.__name__}: {e}')

    def api_request(self, url: str, method: HTTPMethod, *, data: Optional[dict] = None) -> dict:
        """ Wrap Notion API requests. Handle rate-limiting and catch JSON, HTTP and API errors.

        :param url: str, url to perform the HTTP request to
        :param method: GET/POST/PATCH
        :param data: data for POST requests
        :return: dict, JSON response of valid API call

        :raise NotionHandler.GeneralRequestError: Lets self.__api_request escalate its exceptions
        :raise NotionHandler.APIError: Lets self.__handle_errors escalate its exceptions
        """
        response = self.__api_request(url, method, data=data)
        if response.get('has_more'):
            next_cursor = response['next_cursor']
            while next_cursor is not None:
                if data is not None:
                    data['start_cursor'] = next_cursor
                    new_url = url
                else:
                    new_url = url + f'?start_cursor={next_cursor}'

                new_response = self.__api_request(new_url, method, data=data)
                response['results'] += new_response['results']
                next_cursor = new_response['next_cursor'] if new_response['has_more'] else None

        return response

    @staticmethod
    def __handle_api_errors(response_json: dict) -> None:
        """ Translates error responses into appropriate APIError exceptions
        ref: https://developers.notion.com/reference/errors
        """
        error_to_exception = {
            401: NotionHandler.InvalidToken,
            403: NotionHandler.InsufficientPermissions,
            404: NotionHandler.ObjectNotFound,
            409: NotionHandler.ConflictError,
            500: NotionHandler.InternalServerError,
            503: NotionHandler.ServiceUnavailable
        }
        error_400_code_to_exception = {
            'invalid_json': NotionHandler.InvalidJSON,
            'invalid_request_url': NotionHandler.InvalidRequestURL,
            'invalid_request': NotionHandler.InvalidRequest,
            'validation_error': NotionHandler.ValidationError,
            'missing_version': NotionHandler.InvalidVersion
        }
        if error_to_exception.get(response_json['status']):
            raise error_to_exception.get(response_json['status'])(f'Code: "{response_json["code"]}". '
                                                                  f'Message: "{response_json["message"]}"')

        if error_400_code_to_exception.get(response_json['code']):
            raise error_400_code_to_exception.get(response_json['code'])(f'Code: "{response_json["code"]}". Message:'
                                                                         f' "{response_json["message"]}"')

        raise NotionHandler.APIError(response_json)

    def __validate(self):
        """ Validate Token and Version

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.InvalidToken:
        :raises NotionHandler.InvalidVersion:
        """
        self.api_request(NotionHandler._VALIDATION_URL, HTTPMethod.GET)

    # Pages

    def get_page(self, page_id: str) -> dict:
        """ Retrieves page properties by ID.

        ref: https://developers.notion.com/reference/retrieve-a-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.InvalidRequestURL:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.api_request(NotionHandler._GET_PAGE.format(page_id), HTTPMethod.GET)

    def post_page(self, parent_id: str, properties: dict = None, *, children: list = None,
                  icon: dict = None, cover: dict = None, _is_parent_database: bool = False) -> dict:
        """ Post a page

        ref: https://developers.notion.com/reference/post-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ParentNotFound:
        """
        page_post_data = {
            'parent': {'type': 'page_id', 'page_id': parent_id},
            'properties': properties if properties else {},
            'children': children if children else [],
            'icon': icon,
            'cover': cover
        }
        if _is_parent_database:
            page_post_data['parent'] = {'type': 'database_id', 'database_id': parent_id}

        try:
            return self.api_request(NotionHandler._POST_PAGE, HTTPMethod.POST, data=page_post_data)
        except NotionHandler.ObjectNotFound as e:
            raise NotionHandler.ParentNotFound(e)

    def update_page(self, page_id: str, *, properties: dict = None,
                    icon: Optional[dict] = EmptyArgument, cover: Optional[dict] = EmptyArgument) -> dict:
        """ Update a page

        ref: https://developers.notion.com/reference/patch-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ObjectNotFound:
        """
        page_update_data = {
            'properties': properties if properties else {},
        }
        if icon is not EmptyArgument:
            page_update_data['icon'] = icon
        if cover is not EmptyArgument:
            page_update_data['cover'] = cover
        return self.api_request(NotionHandler._UPDATE_PAGE.format(page_id), HTTPMethod.PATCH, data=page_update_data)

    def trash_page(self, page_id: str) -> dict:
        """ Send a page to the trash bin

        ref: https://developers.notion.com/reference/patch-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        page_trash_data = {
            'archived': True
        }
        return self.api_request(NotionHandler._DELETE_PAGE.format(page_id), HTTPMethod.PATCH, data=page_trash_data)

    def recover_page(self, page_id: str) -> dict:
        """ Recover a page that was sent to the trash bin

        ref: https://developers.notion.com/reference/patch-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        page_trash_data = {
            'archived': False
        }
        return self.api_request(NotionHandler._DELETE_PAGE.format(page_id), HTTPMethod.PATCH, data=page_trash_data)

    # Users

    def get_token_bot_user(self) -> dict:
        """ Get the bot User associated with the token used to interface with the API

        ref: https://developers.notion.com/reference/get-self

        :raises NotionHandler.GeneralRequestError:
        """
        return self.api_request(NotionHandler._BOT_USER, HTTPMethod.GET)

    def get_user_list(self) -> dict:
        """ Get the User list

        ref: https://developers.notion.com/reference/get-users

        :raises NotionHandler.GeneralRequestError:
        """
        return self.api_request(NotionHandler._LIST_USERS, HTTPMethod.GET)

    def get_user(self, user_id: str) -> dict:
        """ Get a specific User

        ref: https://developers.notion.com/reference/get-user

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.api_request(NotionHandler._GET_USER.format(user_id), HTTPMethod.GET)

    # Comments

    def get_comments(self, block_or_page_id: str) -> dict:
        """ Get un-resolved Comments from a page or block

        ref: https://developers.notion.com/reference/retrieve-a-comment

        :raises NotionHandler.CallError: General request errors
        """
        return self.api_request(NotionHandler._GET_COMMENTS.format(block_or_page_id), HTTPMethod.GET)

    def post_comment(self, parent_id: str, rich_text_object: list, *, is_discussion_id: bool = False) -> dict:
        """ Post a comment in a page or existing discussion thread.

        ref: https://developers.notion.com/reference/post-search

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ParentNotFound:
        """
        comment_post_data = {
            'parent': {'page_id': parent_id},
            'rich_text': rich_text_object
        }
        if is_discussion_id:
            del comment_post_data['parent']
            comment_post_data['discussion_id'] = parent_id

        try:
            return self.api_request(NotionHandler._POST_COMMENT, HTTPMethod.POST, data=comment_post_data)
        except NotionHandler.ObjectNotFound as e:
            raise NotionHandler.ParentNotFound(e)

    # Search

    class SearchFilterType(str, Enum):
        """ Filter types for searches """
        PAGE = 'page'
        DATABASE = 'database'

    def search(self, *, query: str = None, filter_type: SearchFilterType = None, sort_ascending: bool = False) -> dict:
        """ Search all original pages, databases, and child pages/databases shared with the integration. (Does not
        return linked databases)

        Currently only a single sort is allowed, and it sorts by last_edited_time.

        If query is not passed it performs a blanket search, ordered by descending last_edited_time.

        Beware of timing issues when using search, if not enough time has passed it might not return.

        ref: https://developers.notion.com/reference/post-search

        :raises NotionHandler.GeneralRequestError:
        """
        search_post_data = {
            'query': query if query else '',
            'sort': {'timestamp': 'last_edited_time', 'direction': 'descending' if not sort_ascending else 'ascending'}
        }
        if filter_type:
            search_post_data['filter'] = {'property': 'object', 'value': filter_type}

        return self.api_request(NotionHandler._SEARCH, HTTPMethod.POST, data=search_post_data)

    # Databases

    def get_db(self, database_id: str) -> dict:
        """ Get a database

        ref: https://developers.notion.com/reference/retrieve-a-database

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.api_request(NotionHandler._GET_DATABASE.format(database_id), HTTPMethod.GET)

    def post_db(self, parent_page_id: str, properties: dict = None, *,
                title_rich_texts: list = None, is_inline: bool = True) -> dict:
        """ Create a database, inlined by default.

        If no properties are provided, the db will be created with an empty Name property.

        ref: https://developers.notion.com/reference/create-a-database

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ParentNotFound:
        :raises NotionHandler.ValidationError:
        """
        post_db_data = {
            'parent': {'type': 'page_id', 'page_id': parent_page_id},
            'properties': properties if properties else {'Name': {'title': {}}},
            'is_inline': is_inline
        }

        if title_rich_texts:
            post_db_data['title'] = title_rich_texts

        try:
            return self.api_request(NotionHandler._POST_DATABASE, HTTPMethod.POST, data=post_db_data)
        except NotionHandler.ObjectNotFound as e:
            raise NotionHandler.ParentNotFound(e)

    def update_db_properties(self, database_id: str, title_rich_texts: list = None, properties: dict = None,
                             is_inline: bool = None) -> dict:
        """ Update a database's properties

        ref: https://developers.notion.com/reference/update-a-database

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        :raises NotionHandler.ValidationError:
        """
        update_db_data = {}
        if title_rich_texts:
            update_db_data['title'] = title_rich_texts
        if properties:
            update_db_data['properties'] = properties
        if is_inline:
            update_db_data['is_inline'] = is_inline

        return self.api_request(NotionHandler._UPDATE_DATABASE.format(database_id), HTTPMethod.PATCH,
                                data=update_db_data)

    def trash_db(self, database_id: str):
        """ Send a database to the trash bin

        ref: https://developers.notion.com/reference/update-a-database

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        db_trash_data = {
            'archived': True
        }
        return self.api_request(NotionHandler._DELETE_DATABASE.format(database_id), HTTPMethod.PATCH,
                                data=db_trash_data)

    def recover_db(self, database_id: str):
        """ Recover a database that was sent to the trash bin

        ref: https://developers.notion.com/reference/update-a-database

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        db_trash_data = {
            'archived': False
        }
        return self.api_request(NotionHandler._DELETE_DATABASE.format(database_id), HTTPMethod.PATCH,
                                data=db_trash_data)

    def query_db(self, database_id: str, filter_rules: dict = None, sorts: list[dict] = None) -> dict:
        """ Get a list of rows contained in the database, filtered and ordered according to filter_rules adn sorts.

        ref: https://developers.notion.com/reference/post-database-query

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        query_data = {}
        if filter_rules:
            query_data['filter'] = filter_rules
        if sorts:
            query_data['sorts'] = sorts

        return self.__api_request(NotionHandler._QUERY_DATABASE.format(database_id), HTTPMethod.POST, data=query_data)

    # Database rows

    def post_row_db(self, database_id: str, properties: dict = None) -> dict:
        """ Post a row to a db

        ref: https://developers.notion.com/reference/post-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ParentNotFound:
        """
        return self.post_page(database_id, properties=properties, _is_parent_database=True)

    def get_row_db(self, row_id: str) -> dict:
        """" Get a row from a db

        ref: https://developers.notion.com/reference/retrieve-a-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.InvalidRequestURL:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.get_page(row_id)

    def update_row_db(self, row_id: str, properties: dict) -> dict:
        """ Updates a row's properties

        ref: https://developers.notion.com/reference/patch-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ValidationError:
        :raises NotionHandler.ObjectNotFound:
        """
        row_update_data = {
            'properties': properties
        }
        return self.api_request(NotionHandler._UPDATE_PAGE.format(row_id), HTTPMethod.PATCH, data=row_update_data)

    def trash_row_db(self, row_id: str) -> dict:
        """ Send a row to the trash bin

        ref: https://developers.notion.com/reference/patch-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        row_trash_data = {'archived': True}
        return self.api_request(NotionHandler._DELETE_PAGE.format(row_id), HTTPMethod.PATCH, data=row_trash_data)

    def recover_row_db(self, row_id: str) -> dict:
        """ Recover a row from the trash bin

        ref: https://developers.notion.com/reference/patch-page

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        row_trash_data = {
            'archived': False
        }
        return self.api_request(NotionHandler._DELETE_PAGE.format(row_id), HTTPMethod.PATCH, data=row_trash_data)

    def get_row_db_property_item(self, row_id: str, property_id: str) -> dict:
        """ Retrieves a property item from a row

        ref: https://developers.notion.com/reference/retrieve-a-page-property

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ParentNotFound
        :raises NotionHandler.ObjectNotFound:
        """
        try:
            return self.api_request(NotionHandler._GET_ROW_PROPERTY_ITEM.format(row_id, property_id), HTTPMethod.GET)
        except NotionHandler.ObjectNotFound as e:
            raise NotionHandler.ParentNotFound(e)
        except NotionHandler.ValidationError as e:
            raise NotionHandler.ObjectNotFound(e)

    # Blocks

    def get_block(self, block_id: str) -> dict:
        """ Get a block object

        ref: https://developers.notion.com/reference/retrieve-a-block

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.api_request(NotionHandler._GET_BLOCK.format(block_id), HTTPMethod.GET)

    def get_block_children(self, parent_block_id: str) -> dict:
        """ Get block's children blocks

        ref: https://developers.notion.com/reference/get-block-children

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.api_request(NotionHandler._GET_BLOCK_CHILDREN.format(parent_block_id), HTTPMethod.GET)

    def post_block_children(self, parent_block_id: str, children: list) -> dict:
        """ Posts new children blocks to the parent block

        ref: https://developers.notion.com/reference/patch-block-children

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ParentNotFound:
        :raises NotionHandler.ValidationError:
        """
        block_data = {'children': children}
        try:
            return self.api_request(NotionHandler._POST_BLOCK_CHILDREN.format(parent_block_id),
                                    HTTPMethod.PATCH, data=block_data)
        except NotionHandler.ObjectNotFound as e:
            raise NotionHandler.ParentNotFound(e)

    def update_block(self, block_id: str, block_object: dict) -> dict:
        """ Updates block content

        ref: https://developers.notion.com/reference/update-a-block

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        :raises NotionHandler.ValidationError
        """
        return self.api_request(NotionHandler._UPDATE_BLOCK.format(block_id), HTTPMethod.PATCH, data=block_object)

    def trash_block(self, block_id: str) -> dict:
        """ Send a block to the trash bin

        ref: https://developers.notion.com/reference/update-a-block

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        trash_data = {'archived': True}
        return self.api_request(NotionHandler._DELETE_BLOCK.format(block_id), HTTPMethod.PATCH, data=trash_data)

    def recover_block(self, block_id: str) -> dict:
        """ Recover a block from the trash bin

        ref: https://developers.notion.com/reference/update-a-block

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        trash_data = {'archived': False}
        return self.api_request(NotionHandler._DELETE_BLOCK.format(block_id), HTTPMethod.PATCH, data=trash_data)

    def delete_block_endpoint(self, block_id: str) -> dict:
        """ Send a block to the trash point from the Delete block endpoint

        ref: https://developers.notion.com/reference/delete-a-block

        :raises NotionHandler.GeneralRequestError:
        :raises NotionHandler.ObjectNotFound:
        """
        return self.api_request(NotionHandler._DELETE_BLOCK.format(block_id), HTTPMethod.DELETE)

    # Exceptions

    class NotionHandlerError(Exception):
        """ Base exception """

    class GeneralRequestError(NotionHandlerError):
        """ Error for APICalls """

    class UnexpectedError(GeneralRequestError):
        """ Unexpected errors """

    class RequestError(GeneralRequestError):
        """ Requests raised an error """

    class JSONDecodeError(GeneralRequestError):
        """ JSON decoding raised an error """

    class MaxRetriesReached(GeneralRequestError):
        """ Max retries reached on an API request """

    class APIError(NotionHandlerError):
        """ Base error for API errors """

    # API Errors

    class InvalidJSON(APIError):
        """ Data was invalid JSON """

    class InvalidRequestURL(APIError):
        """ The request URL is not valid """

    class InvalidRequest(APIError):
        """ The request is not supported """

    class ValidationError(APIError):
        """ The request body does not match the schema for the expected parameters. """

    class InvalidVersion(APIError):
        """ Version was invalid """

    class InvalidToken(APIError):
        """ Token was invalid """

    class InsufficientPermissions(APIError):
        """ Integration does not have sufficient permissions for operation """

    class ObjectNotFound(APIError):
        """ 404 return """

    class ParentNotFound(APIError):
        """ Parent object not found """

    class ConflictError(APIError):
        """ Transaction could not be completed """

    class InternalServerError(APIError):
        """ Unexpected error occurred """

    class ServiceUnavailable(APIError):
        """ Notion is unavailable, or database is an unqueryable state """
