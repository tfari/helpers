""" Tests for NotionHandler. Utilizes a notion page to test on, by default it cleans up after itself (you can set
CLEAN_AFTER_RUN to False if you prefer not to) but comments must be deleted by hand as it is impossible via the API."""

import os
import time
import json
import datetime
from unittest import TestCase
from helpers.notion_handler import NotionHandler

# Set these before testing, or use a _keys_for_test.json file: {"test_notion_handler": {"token": TOKEN,
# "version": VERSION, "init_test_page_id": INIT_TEST_PAGE_ID, "cover_image_test_url": COVER_IMAGE_TEST_URL,
# "icon_test_emoji": ICON_TEST_EMOJI}}

TOKEN = ''
VERSION = ''
INIT_TEST_PAGE_ID = ''
COVER_IMAGE_TEST_URL = ''
ICON_TEST_EMOJI = ''

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(f'{SCRIPT_PATH}/_keys_for_tests.json'):
    with open(f'{SCRIPT_PATH}/_keys_for_tests.json', 'r', encoding='utf-8') as r_file:
        jsoned = json.load(r_file)["test_notion_handler"]
        TOKEN = jsoned["token"]
        VERSION = jsoned["version"]
        INIT_TEST_PAGE_ID = jsoned["init_test_page_id"]
        COVER_IMAGE_TEST_URL = jsoned["cover_image_test_url"]
        ICON_TEST_EMOJI = jsoned["icon_test_emoji"]

# Useful constants
TEST_TIME = datetime.datetime.now()
WRONG_UID = f'{INIT_TEST_PAGE_ID[:-1]}{"f" if INIT_TEST_PAGE_ID[-1] != "f" else "a"}'
CLEAN_AFTER_RUN = True


class TestNotionHandler(TestCase):
    db_row_testing: dict
    _created_objs_list: list
    nh: NotionHandler

    @classmethod
    def setUpClass(cls) -> None:
        """ Instantiate NotionHandler """
        cls.nh = NotionHandler(TOKEN, VERSION)
        title_obj = [{'type': 'text', 'text': {'content': f'{TEST_TIME}row_testing_db', 'link': None}}]
        cls.db_row_testing = cls.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj)
        cls._created_objs_list = [cls.db_row_testing]

    @classmethod
    def tearDownClass(cls) -> None:
        """ Delete all created objects """
        object_to_trash_method = {
            'page': cls.nh.trash_page,
            'database': cls.nh.trash_db,
            'block': cls.nh.trash_block
        }
        if CLEAN_AFTER_RUN:
            for obj in cls._created_objs_list:
                # do not trash INIT_TEST_PAGE_ID
                if TestNotionHandler.normalizeUIDs(obj['id']) != TestNotionHandler.normalizeUIDs(INIT_TEST_PAGE_ID):
                    try:
                        object_to_trash_method[obj['object']](obj['id'])
                    except NotionHandler.ValidationError as ve:
                        print(ve, obj)

    @staticmethod
    def normalizeUIDs(block_id: str) -> str:
        """ For some reason Notion returns some ids with "-" separators, but intake them without as well """
        return block_id.replace('-', '')

    def test_valid_token_and_version(self):
        NotionHandler(TOKEN, VERSION)
        # Without version, uses _CURRENT_VERSION in NotionHandler
        NotionHandler(TOKEN)

    def test_invalid_token_raises_InvalidToken(self):
        self.assertRaises(NotionHandler.InvalidToken, NotionHandler, '666')

    def test_invalid_version_raises_InvalidVersion(self):
        self.assertRaises(NotionHandler.InvalidVersion, NotionHandler, TOKEN, '666')

    def test_get_page(self):
        page = self.nh.get_page(INIT_TEST_PAGE_ID)
        self.assertEqual("page", page['object'])
        self.assertEqual(self.normalizeUIDs(INIT_TEST_PAGE_ID), self.normalizeUIDs(page['id']))

    def test_get_page_raises_InvalidRequestURL(self):
        self.assertRaises(NotionHandler.InvalidRequestURL, self.nh.get_page, '')

    def test_get_page_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.get_page, '666')

    def test_get_page_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_page, WRONG_UID)

    def test_post_page(self):
        title = f'{TEST_TIME}_test_post_page'
        title_dict = {'title': [{'type': 'text', 'text': {'content': title}}]}

        # 1 - Untitled
        up = self.nh.post_page(INIT_TEST_PAGE_ID)
        self._created_objs_list.append(up)

        # 2 - Title only
        title_page = self.nh.post_page(INIT_TEST_PAGE_ID, title_dict)  # Title only
        self._created_objs_list.append(title_page)
        self.assertEqual("page", title_page['object'])
        self.assertEqual(title, title_page['properties']['title']['title'][0]['text']['content'])

        # 3 - Full page
        second_title = f'{TEST_TIME}_test_post_page_full'
        second_title_dict = {'title': [{'type': 'text', 'text': {'content': second_title}}]}
        children = [{'heading_2': {'rich_text': [{'text': {'content': f'test_post_page_children'}}]}}]
        icon = {'emoji': ICON_TEST_EMOJI}
        cover = {'external': {'url': COVER_IMAGE_TEST_URL}}
        full_page = self.nh.post_page(INIT_TEST_PAGE_ID, second_title_dict, children=children, icon=icon, cover=cover)
        self._created_objs_list.append(full_page)

        self.assertEqual(second_title, full_page['properties']['title']['title'][0]['text']['content'])
        self.assertEqual(COVER_IMAGE_TEST_URL, full_page['cover']['external']['url'])
        self.assertEqual(ICON_TEST_EMOJI, full_page['icon']['emoji'])
        self.assertTrue(self.nh.get_block(full_page['id'])['has_children'])  # tightly coupled

    def test_post_page_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.post_page, '', '')

    def test_post_page_raises_ParentNotFound(self):
        self.assertRaises(NotionHandler.ParentNotFound, self.nh.post_page, WRONG_UID, '')

    def test_update_page(self):
        self.nh.update_page(INIT_TEST_PAGE_ID)  # No changes

        updating_page = self.nh.post_page(INIT_TEST_PAGE_ID, {})
        self._created_objs_list.append(updating_page)
        
        # Full changes
        second_title = f'{TEST_TIME}_test_update_page_properties_TITLE_CHANGE'
        second_title_dict = {'title': [{'type': 'text', 'text': {'content': second_title}}]}
        icon = {'emoji': ICON_TEST_EMOJI}
        cover = {'external': {'url': COVER_IMAGE_TEST_URL}}
        edited_page = self.nh.update_page(updating_page['id'], properties=second_title_dict, icon=icon, cover=cover)
        self.assertEqual(second_title, edited_page['properties']['title']['title'][0]['text']['content'])
        self.assertEqual(COVER_IMAGE_TEST_URL, edited_page['cover']['external']['url'])
        self.assertEqual(ICON_TEST_EMOJI, edited_page['icon']['emoji'])

        # Not passing icon and cover does not null icon + cover
        third_title = f'{TEST_TIME}_test_update_page_properties_SECOND_EDIT'
        third_title_dict = {'title': [{'type': 'text', 'text': {'content': third_title}}]}
        edited_page = self.nh.update_page(updating_page['id'], properties=third_title_dict)
        self.assertEqual(third_title, edited_page['properties']['title']['title'][0]['text']['content'])
        self.assertEqual(COVER_IMAGE_TEST_URL, edited_page['cover']['external']['url'])
        self.assertEqual(ICON_TEST_EMOJI, edited_page['icon']['emoji'])

        # Null icon + cover
        edited_page = self.nh.update_page(updating_page['id'], icon=None, cover=None)
        self.assertIsNone(edited_page['cover'])
        self.assertIsNone(edited_page['icon'])

    def test_update_page_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.update_page, INIT_TEST_PAGE_ID,
                          properties={'title': 666})

    def test_update_page_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.update_page, WRONG_UID)

    def test_trash_recover_page(self):
        title_dict = {'title': [{'type': 'text', 'text': {'content': f'{TEST_TIME}test_trash_recover_page'}}]}
        trashing_page = self.nh.post_page(INIT_TEST_PAGE_ID, title_dict)
        self._created_objs_list.append(trashing_page)
        trash_response = self.nh.trash_page(trashing_page["id"])
        self.assertTrue(trash_response["archived"])
        self.nh.recover_page(trashing_page["id"])
        self.assertFalse(self.nh.get_page(trashing_page["id"])["archived"])

    def test_trash_page_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.trash_page, WRONG_UID)

    def test_recover_page_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.recover_page, WRONG_UID)

    def test_get_token_bot_user(self):
        self.assertEqual('bot', self.nh.get_token_bot_user()['type'])

    def test_get_user_list(self):
        users = self.nh.get_user_list()
        for u in users['results']:
            self.assertEqual('user', u['object'])

    def test_get_user(self):
        bot = self.nh.get_token_bot_user()
        user = self.nh.get_user(bot['id'])
        self.assertEqual(bot, user)

    def test_get_user_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_user, WRONG_UID)

    def test_post_and_get_comments(self):
        first_comment = [{'text': {'content': f'{TEST_TIME}_test_post_comment_page_id'}}]
        c = self.nh.post_comment(INIT_TEST_PAGE_ID, first_comment)
        discussion_id = c['discussion_id']
        second_comment = [{'text': {'content': f'{TEST_TIME}_test_post_comment_discussion_id'}}]
        c2 = self.nh.post_comment(discussion_id, second_comment, is_discussion_id=True)
        comments = self.nh.get_comments(INIT_TEST_PAGE_ID)

        has_first, has_second = False, False
        for comment in comments['results']:
            if comment == c:
                has_first = True
            elif comment == c2:
                has_second = True

        self.assertTrue(has_first)
        self.assertTrue(has_second)

    def test_get_comments_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_comments, WRONG_UID)

    def test_post_comments_raises_ParentNotFound(self):
        comment = [{'text': {'content': f'{TEST_TIME} test_post_comment_raises_ParentNotFound'}}]
        self.assertRaises(NotionHandler.ParentNotFound, self.nh.post_comment, WRONG_UID, comment)

    def test_search(self):
        # 1 - Test query by name
        root_page = self.nh.get_page(INIT_TEST_PAGE_ID)
        by_name_search = self.nh.search(query=root_page["properties"]["title"]["title"][0]["text"]["content"])
        self.assertEqual(root_page, by_name_search['results'][0])

        # 2 - Test query blanket
        blanket_search = self.nh.search()
        has_root = False
        for r in blanket_search['results']:
            if r == root_page:
                has_root = True
        self.assertTrue(has_root)

        # 3 - Check for DATABASE only
        db_only_search = self.nh.search(filter_type=NotionHandler.SearchFilterType.DATABASE)
        non_dbs_len = len([o for o in db_only_search['results'] if o['object'] != 'database'])
        self.assertEqual(0, non_dbs_len)

        # 4 - Check for PAGE only
        page_only_search = self.nh.search(filter_type=NotionHandler.SearchFilterType.PAGE)
        non_pages_len = len([o for o in page_only_search['results'] if o['object'] != 'page'])
        self.assertEqual(0, non_pages_len)

        # 5 - Check sort orders are reversed when using ascending
        time.sleep(10)  # This fails when run with all tests (second search has extra things) sleeping seems to solve it
        normal_order_search = [o['last_edited_time'] for o in self.nh.search()['results']]
        reverse_order_search = [o['last_edited_time'] for o in self.nh.search(sort_ascending=True)['results']]
        self.assertEqual(normal_order_search, reverse_order_search[::-1])

    def test_post_db(self):
        expected_prop = {'Name': {'id': 'title', 'name': 'Name', 'type': 'title', 'title': {}}}
        # title_prop = ['rich_text': {'text': {'content': {}}}]
        # 1 - No properties, no title, not is_inlined
        db = self.nh.post_db(INIT_TEST_PAGE_ID)
        self._created_objs_list.append(db)

        self.assertTrue(db['is_inline'])
        self.assertEqual(expected_prop, db['properties'])
        self.assertEqual([], db['title'])

        # 2 - Title, not is_inlined
        expected_title = f'{TEST_TIME}_test_post_db_w_title'
        title_obj = [{'type': 'text', 'text': {'content': expected_title, 'link': None}}]
        db2 = self.nh.post_db(INIT_TEST_PAGE_ID, is_inline=False, title_rich_texts=title_obj)
        self._created_objs_list.append(db2)

        self.assertFalse(db2['is_inline'])
        self.assertEqual(expected_title, db2['title'][0]['text']['content'])

        # 3 - W. Properties
        db3 = self.nh.post_db(INIT_TEST_PAGE_ID, properties={'Name': {'title': {}},
                                                             'Prop': {'number': {}}})
        self._created_objs_list.append(db3)
        self.assertTrue('Prop' in db3['properties'])

    def test_post_db_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.post_db, INIT_TEST_PAGE_ID, properties={'Name': {}})

    def test_post_db_raises_ParentNotFound(self):
        self.assertRaises(NotionHandler.ParentNotFound, self.nh.post_db, WRONG_UID)

    def test_get_db(self):
        title_obj = [{'type': 'text', 'text': {'content': f'{TEST_TIME}_test_get_db_pre_posting', 'link': None}}]
        db = self.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj)
        self._created_objs_list.append(db)
        self.assertEqual(db, self.nh.get_db(db['id']))

    def test_get_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_db, INIT_TEST_PAGE_ID)

    def test_query_db(self):
        # Set up
        title_obj = [{'type': 'text', 'text': {'content': f'{TEST_TIME}_query_db_tests', 'link': None}}]
        query_db = self.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj)
        self._created_objs_list.append(query_db)

        for i in range(0, 11):
            self.nh.post_row_db(query_db['id'],  {'Name': {'title': [{'text': {'content': f'Row {i}'}}]}})

        # 1 - Blanket query (all db)
        results = self.nh.query_db(query_db['id'])
        self.assertEqual(11, len(results['results']))

        # 2 - Filter query
        frules = {'property': 'Name', 'rich_text': {'contains': '1'}}
        results = self.nh.query_db(query_db['id'], filter_rules=frules)
        self.assertEqual(2, len(results['results']))

        # 3 - Sort query
        sort = [{'property': 'Name', 'direction': 'descending'}]
        results = self.nh.query_db(query_db['id'], sorts=sort)
        # Sorted alphabetically
        self.assertEqual(f'Row 9', results['results'][0]['properties']['Name']['title'][0]['text']['content'])

    def test_query_db_raise_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.query_db, WRONG_UID)

    def test_update_db_properties(self):
        title_obj = [{'type': 'text', 'text': {'content': f'{TEST_TIME}test_update_db_properties', 'link': None}}]
        db = self.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj, is_inline=False)
        self._created_objs_list.append(db)

        # 1 - No changes
        db2 = self.nh.update_db_properties(db['id'])
        self.assertEqual(db, db2)

        # 2 - Edit inline
        db3 = self.nh.update_db_properties(db['id'], is_inline=True)
        self.assertTrue(db3['is_inline'])

        # 3 - Edit title
        new_title = f'{TEST_TIME}test_update_db_properties_new_title'
        new_title_obj = [{'type': 'text', 'text': {'content': new_title, 'link': None}}]
        db4 = self.nh.update_db_properties(db['id'], title_rich_texts=new_title_obj)
        self.assertEqual(new_title, db4['title'][0]['text']['content'])

        # 4 - Add properties
        db5 = self.nh.update_db_properties(db['id'], properties={'NewProp': {'type': 'number', 'number': {}}})
        self.assertTrue('NewProp' in db5['properties'])
        self.assertEqual('number', db5['properties']['NewProp']['type'])

        # 5 - Edit properties
        db6 = self.nh.update_db_properties(db['id'], properties={'NewProp': {'type': 'checkbox', 'checkbox': {}}})
        self.assertEqual('checkbox', db6['properties']['NewProp']['type'])

        # 6 - Remove properties
        db7 = self.nh.update_db_properties(db['id'], properties={'NewProp': None})
        self.assertFalse('NewProp' in db7['properties'])

    def test_update_db_properties_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.update_db_properties, INIT_TEST_PAGE_ID)

    def test_update_db_properties_raises_ValidationError(self):
        title_name = f'{TEST_TIME}test_update_db_properties_raises_ValidationError'
        title_obj = [{'type': 'text', 'text': {'content': title_name, 'link': None}}]

        db = self.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj)
        self._created_objs_list.append(db)
        self.assertRaises(NotionHandler.ValidationError, self.nh.update_db_properties, db['id'],
                          properties={'Name': None})

    def test_trash_recover_db(self):
        title_obj = [{'type': 'text', 'text': {'content': f'{TEST_TIME}_test_recover_db', 'link': None}}]
        db = self.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj)
        self._created_objs_list.append(db)
        trash_response = self.nh.trash_db(db['id'])
        self.assertTrue(trash_response['archived'])
        self.nh.recover_db(trash_response['id'])
        self.assertFalse(self.nh.get_db(trash_response['id'])['archived'])

    def test_trash_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.trash_db, INIT_TEST_PAGE_ID)

    def test_recover_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.recover_db, INIT_TEST_PAGE_ID)

    def test_post_get_row_db(self):
        props = {'Name': {'title': [{'text': {'content': 'Add Row'}}]}}
        row = self.nh.post_row_db(self.db_row_testing['id'], props)
        created_row = self.nh.get_row_db(row['id'])
        self.assertEqual(row, created_row)
        self.assertTrue('Name' in created_row['properties'])

    def test_post_row_db_raises_ParentNotFound(self):
        self.assertRaises(NotionHandler.ParentNotFound, self.nh.post_row_db, WRONG_UID, {})

    def test_post_row_db_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.post_row_db, INIT_TEST_PAGE_ID, {'666': {}})

    def test_get_row_db_raises_InvalidRequestUrl(self):
        self.assertRaises(NotionHandler.InvalidRequestURL, self.nh.get_row_db, '')

    def test_get_row_db_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.get_row_db, '666')

    def test_get_row_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_row_db, WRONG_UID)

    def test_update_row_db(self):
        prev_props = {'Name': {'title': [{'text': {'content': f'test_update_row_db'}}]}}
        new_props = {'Name': {'title': [{'text': {'content': f'test_update_row_db_passed'}}]}}
        db = self.db_row_testing
        row = self.nh.post_row_db(db['id'], prev_props)
        self.nh.update_row_db(row['id'], new_props)
        self.assertEqual('test_update_row_db_passed',
                         self.nh.get_row_db(row['id'])['properties']['Name']['title'][0]['text']['content'])

    def test_update_row_db_raises_ValidationError(self):
        props = {'Name': {'title': [{'text': {'content': f'test_update_row_db_raises_ValidationError'}}]}}
        db = self.db_row_testing
        row = self.nh.post_row_db(db['id'], props)
        self.assertRaises(NotionHandler.ValidationError, self.nh.update_row_db, row['id'], {'Name': {}})

    def test_update_row_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.update_row_db, WRONG_UID, {})

    def test_trash_recover_row_db(self):
        props = {'Name': {'title': [{'text': {'content': f'test_trash_row_db'}}]}}
        row = self.nh.post_row_db(self.db_row_testing['id'], props)
        trash_response = self.nh.trash_row_db(row_id=row['id'])
        self.assertTrue(trash_response['archived'])
        self.nh.recover_row_db(row['id'])
        self.assertFalse(self.nh.get_row_db(row['id'])['archived'])

    def test_trash_row_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.trash_row_db, WRONG_UID)

    def test_recover_row_db_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.recover_row_db, WRONG_UID)

    def test_get_row_db_property_item(self):
        title_obj = [{'type': 'text', 'text': {'content': f'{TEST_TIME}_test_get_row_db_property_item', 'link': None}}]
        db = self.nh.post_db(INIT_TEST_PAGE_ID, title_rich_texts=title_obj,
                             properties={'Name': {'title': {}}, 'Number': {'number': {}}})
        self._created_objs_list.append(db)

        props = {'Name': {'title': [{'text': {'content': f'test_get_row_db_property_items'}}]}, 'Number': {'number': 0}}
        make_row = self.nh.post_row_db(db['id'], props)
        title_item = self.nh.get_row_db_property_item(make_row['id'], 'title')
        number_item = self.nh.get_row_db_property_item(make_row['id'], make_row['properties']['Number']['id'])
        self.assertTrue('results' in title_item)
        self.assertEqual(0, number_item['number'])

    def test_get_row_db_property_item_raises_ParentNotFound(self):
        self.assertRaises(NotionHandler.ParentNotFound, self.nh.get_row_db_property_item, WRONG_UID, '666')

    def test_get_row_db_property_item_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_row_db_property_item, INIT_TEST_PAGE_ID, '666')

    def test_get_block(self):
        self.assertEqual(INIT_TEST_PAGE_ID, self.nh.get_block(INIT_TEST_PAGE_ID)['id'].replace('-', ''))

    def test_get_block_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_block, WRONG_UID)

    def test_get_post_block_children(self):
        new_header = {'heading_2': {'rich_text': [{'text': {'content': f'{TEST_TIME}_test_get_post_block_children'}}]}}
        response = self.nh.post_block_children(INIT_TEST_PAGE_ID, [new_header])
        self._created_objs_list.append(response['results'][0])

        get_children = self.nh.get_block_children(INIT_TEST_PAGE_ID)

        has_created = False
        for o in get_children['results']:
            if o['id'] == response['results'][0]['id']:
                has_created = True
        self.assertTrue(has_created)

    def test_get_block_children_raises_ParentNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.get_block_children, WRONG_UID)

    def test_post_block_raises_ParentNotFound(self):
        self.assertRaises(NotionHandler.ParentNotFound, self.nh.post_block_children, WRONG_UID, [])

    def test_post_block_raises_ValidationError(self):
        wrong_children = [{'a': 1}]
        self.assertRaises(NotionHandler.ValidationError, self.nh.post_block_children, INIT_TEST_PAGE_ID, wrong_children)

    def test_update_block(self):
        new_header = {'heading_2': {'rich_text': [{'text': {'content': f'{TEST_TIME}_test_update_block'}}]}}
        updated_header = {'heading_2': {'rich_text': [{'text': {'content': f'{TEST_TIME}_test_update_block_passed'}}]}}
        posted_header = self.nh.post_block_children(INIT_TEST_PAGE_ID, [new_header])['results'][0]
        self._created_objs_list.append(posted_header)

        updated_block = self.nh.update_block(posted_header['id'], updated_header)
        self.assertEqual(f'{TEST_TIME}_test_update_block_passed', updated_block['heading_2']['rich_text'][0][
            'text']['content'])

    def test_update_block_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.update_block, WRONG_UID, {})

    def test_update_block_raises_ValidationError(self):
        self.assertRaises(NotionHandler.ValidationError, self.nh.update_block, INIT_TEST_PAGE_ID, {})

    def test_trash_recover_block(self):
        new_header = {'heading_2': {'rich_text': [{'text': {'content': f'{TEST_TIME}_test_recover_block'}}]}}
        block_response = self.nh.post_block_children(INIT_TEST_PAGE_ID, [new_header])
        trash_response = self.nh.trash_block(block_response['results'][0]['id'])
        self._created_objs_list.append(trash_response)

        self.assertTrue(trash_response['archived'])
        recover_response = self.nh.recover_block(trash_response['id'])
        self.assertFalse(recover_response['archived'])

    def test_trash_block_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.trash_block, WRONG_UID)

    def test_recover_block_raises_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.recover_block, WRONG_UID)

    def test_delete_block_endpoint(self):
        new_header = {'heading_2': {'rich_text': [{'text': {'content': f'{TEST_TIME}_test_delete_block_endpoint'}}]}}
        block_response = self.nh.post_block_children(INIT_TEST_PAGE_ID, [new_header])
        delete_response = self.nh.delete_block_endpoint(block_response['results'][0]['id'])
        self.assertTrue(delete_response['archived'])

    def test_delete_block_endpoint_ObjectNotFound(self):
        self.assertRaises(NotionHandler.ObjectNotFound, self.nh.delete_block_endpoint, WRONG_UID)
