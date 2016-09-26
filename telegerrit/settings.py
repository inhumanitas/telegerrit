import os

base_dir = os.path.dirname(__file__)

token_file = os.path.join(base_dir, '.token')

bot_father_token = open(token_file).readlines()[0].strip()

db_path = os.path.join(base_dir, 'sqlite.db')

ssh_config = 'review'

gerrit_url_template = 'http://gerrit.tionix.loc/#/c/{change_id}/'
