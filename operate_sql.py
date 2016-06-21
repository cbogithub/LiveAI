#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from setup import core_sql, talk_sql, twlog_sql, wordnet_sql
from sql_models import *
import natural_language_processing
import dialog_generator
import _
from _ import p, d, MyObject, MyException
import threading
from contextlib import contextmanager
# @_.timeit

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@webdata_sql.atomic()
def get_ss(url):
	datas = SS.select().where(SS.url ==  url).order_by(SS.time.desc()).limit(100)
	return datas

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@webdata_sql.atomic()
def get_ss_dialog_within(person = '', kw = 'カバン', n = 100000):
	dialogs = SSdialog.select().where(SSdialog.text.contains(kw)).limit(n)
	def _func(obj):
		try:
			rel_obj = SSdialog_relation.select().where(SSdialog_relation.id2== obj.id).get()
		except DoesNotExist:
			return None
		try:
			if not person:
				response_obj = SSdialog.select().where(SSdialog.id == rel_obj.id3).get()
			else:
				response_obj = SSdialog.select().where(SSdialog.id == rel_obj.id3, SSdialog.person.contains(person)).get()
		except DoesNotExist:
			return None
		return obj.text, response_obj.text
	return _.compact([_func(dialog_obj) for dialog_obj in dialogs])
def save_ss_dialog(url, retry_cnt = 0):
	reg = natural_language_processing.RegexTools()
	@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
	@webdata_sql.atomic()
	def _save_ssdialog():
		datas = SS.select().where(SS.url ==  url).order_by(SS.time.desc()).limit(100)
		text = ''.join([data.text for data in datas])
		dialog_ls = reg.extract_discorse(text)
		id_ls = []
		for dialog in dialog_ls:
			dialog['url'] = url
			ss_dialog = SSdialog.create(**dialog)
			id_ls.append(ss_dialog.id)
		trigrams = _.convert_gram(id_ls, n_gram = 3)
		[SSdialog_relation.create(id1 = trigram[0], id2 = trigram[1], id3 = trigram[2]) for trigram in trigrams]
		return True
	return _save_ssdialog()

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def save_stats(stats_dict = {'whose': 'sys', 'status': '', 'number': 114514}):
	t = Stats.create(**stats_dict)
	return t

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def get_stats(whose = 'sys', status = '', n = 100):
	stats_data = Stats.select().where(Stats.whose ==  whose, Stats.status == status).order_by(Stats.time.desc()).limit(n)
	data_ls = [(data.number, data.time) for data in stats_data]
	return data_ls

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def upsert_core_info(whose_info = '', info_label = '', kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True):
	core_info, is_created = CoreInfo.get_or_create(whose_info = whose_info, info_label = info_label, defaults = kwargs)
	if is_update:
		update = CoreInfo.update(**kwargs).where(CoreInfo.whose_info ==whose_info, CoreInfo.info_label == info_label)
		update.execute()
	return core_info

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def save_task(taskdict = {'who':'_mmKm', 'what': 'call', 'to_whom': '_apkX', 'when':datetime.utcnow()}):
	t = Task.create(**taskdict)
	return t
	# p(''.join(['TASK_SAVED]',taskdict['who'], '_', taskdict['what']]))

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def search_tasks(when = datetime.now(), who = '_mmKm', n = 10):
	active = Task.select().where(~Task.status == 'end')
	if not who:
		tasks = active.where(Task.when < when).order_by(Task.id.desc()).limit(n)
	else:
		tasks = active.where(Task.when < when, Task.who == who).order_by(Task.id.desc()).limit(n)
	tasklist = [task._data for task in tasks]
	return tasklist

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def update_task(taskid = None, who_ls = [], kinds = [], taskdict = {'who':'', 'what': 'call', 'to_whom': '_apkX', 'when':datetime.utcnow()}):
	if who_ls:
		if not kinds:
			task = Task.update(**taskdict).where(Task.id == taskid)
		elif not taskid:
			task = Task.update(**taskdict).where(Task.what << kinds, Task.who << who_ls)
		else:
			task = Task.update(**taskdict).where(Task.id == taskid, Task.what << kinds, Task.who << who_ls)
	else:
		if not kinds:
			task = Task.update(**taskdict).where(Task.id == taskid)
		elif not taskid:
			task = Task.update(**taskdict).where(Task.what << kinds)
		else:
			task = Task.update(**taskdict).where(Task.id == taskid, Task.what << kinds)
	task.execute()

#####twlog_sql#######
@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@twlog_sql.atomic()
def save_tweet_status(status_dic = {
				'status_id' : '',
				'screen_name' : '',
				'name' : '',
				'text' : '',
				'user_id' : '',
				'in_reply_to_status_id_str' : '',
				'bot_id' : '',
				'createdAt' : datetime.utcnow(),
				'updatedAt' : datetime.utcnow()
			}):
	tweetstatus = Tweets.create(**status_dic)
	return tweetstatus._data
@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@twlog_sql.atomic()
def get_tweet_dialog(status_id = 1):
	return Tweets.select().where(Tweets.status_id == status_id).get()._data
@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@twlog_sql.atomic()
def get_twlog(status_id = 1, retry_cnt = 0):
	return Tweets.select().where(Tweets.status_id == status_id).get()._data

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@twlog_sql.atomic()
def save_tweet_dialog(twdialog_dic = {
				'SID' : '',
				'KWs' : '',
				'nameA' : '',
				'textA' : '',
				'nameB' : '',
				'textB' : '',
				'posi' : 1,
				'nega' : 0,
				'bot_id' : 'bot',
				'createdAt' : datetime.utcnow(),
				'updatedAt' : datetime.utcnow()
			}, retry_cnt = 0):
		twdialog = TwDialog.create(**twdialog_dic)
		return twdialog

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@twlog_sql.atomic()
def get_twlog_list(n = 1000, UserList = [], BlackList = [], contains = ''):
	if not UserList:
		tweets = Tweets.select().where(Tweets.text.contains(contains), ~Tweets.text.contains('RT'), ~Tweets.screen_name << BlackList, ~Tweets.text.contains('【')).order_by(Tweets.createdAt.desc()).limit(n)
	else:
	 	tweets = Tweets.select().where(Tweets.screen_name << UserList , ~Tweets.screen_name << BlackList, ~Tweets.text.contains('RT'), ~Tweets.text.contains('【')).order_by(Tweets.createdAt.desc()).limit(n)
	tweetslist = [_.clean_text(tweet.text) for tweet in tweets]
	return tweetslist

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def get_phrase(s_type = '', status = '', n = 10, character = 'sys'):
	if character == 'sys':
		Ps = Phrases.select().where(Phrases.status == status).limit(n)
	elif not status:
		Ps = Phrases.select().where(Phrases.s_type == s_type, Phrases.character == character).limit(n)
	elif not s_type:
		Ps = Phrases.select().where(Phrases.status == status, Phrases.character == character).limit(n)
	else:
		Ps = Phrases.select().where(Phrases.s_type == s_type, Phrases.status == status, Phrases.character == character).limit(n)
	if len(Ps) == 0:
		Ps = Phrases.select().where(Phrases.status == status).limit(n)
		return ''.join([np.random.choice([p.phrase for p in Ps]), '\n(代:[', status, ']of\'', character, '\')'])
	else:
		return np.random.choice([p.phrase for p in Ps])

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def save_phrase(phrase, author = '_mmkm', status = 'mid', s_type = 'UserLearn', character = 'sys'):
	P = Phrases.create(phrase = phrase)
	return P

# [TODO]
@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def update_phrase(phrase, ok_add = 0, ng_add = 1):
	P = Phrases.select().where(Phrases.phrase == phrase).get()
	P.ok_cnt = P.ok_cnt + ok_add
	P.ng_cnt = P.ng_cnt + ng_add
	P.save()
	return True

@contextmanager
def userinfo_with(screen_name):
	try:
		userstatus = get_userinfo(screen_name)
		yield userstatus
	finally:
		 save_userinfo(userstatus)
def read_userinfo(screen_name):
	return get_userinfo(screen_name = screen_name)
@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def get_userinfo(screen_name):
	if screen_name == 'h_y_ok':
		screen_name = '例外h_y_ok'
	userinfo, is_created = Users.get_or_create(screen_name = screen_name, defaults = {'name' : screen_name,
		'nickname' : screen_name,
		'cnt' : 0,
		'total_cnt' : 0,
		'reply_cnt' : 0,
		'exp' : 0,
		'mode' : 'dialog',
		'context' : '',
		'time' : datetime.utcnow()
		})
	userinfo_dic = userinfo._data
	userinfo_dic['is_created'] = is_created
	return userinfo_dic

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@core_sql.atomic()
def save_userinfo(userstatus):
	userinfo = Users(**userstatus)
	userinfo.save()
	return userstatus

@_.retry(OperationalError, tries=10, delay=0.3, max_delay=None, backoff=1, jitter=0)
@wordnet_sql.atomic()
def get_wordnet_result(lemma, retry_cnt = 0):
	n = 10
	langs_ls = ['jpn', 'eng']
	langs_ls = ['jpn']
	wn_relation = {}
	def convert_synset_into_words(target_synset):
		try:
			same_sense_set = Sense.select().where(Sense.synset == target_synset).limit(n)
			same_sense_wordid_ls = [same_sense_word.wordid for same_sense_word in same_sense_set]
			same_sense_words = Word.select().where(Word.wordid << same_sense_wordid_ls, Word.lang << langs_ls).limit(n)
			same_sense_lemma_ls = [same_sense_word.lemma for same_sense_word in same_sense_words]
			return same_sense_lemma_ls
		except:
			return []	
	W = Word.select().where(Word.lemma == lemma).get()
	selected_wordid = W.wordid
	wn_sense = Sense.select().where(Sense.wordid == selected_wordid).get()
	selected_synset = wn_sense.synset
	coordinated_lemma_ls = convert_synset_into_words(target_synset = selected_synset)
	synlinks = Synlink.select().where(Synlink.synset1 == selected_synset).limit(n)
	wn_relation = {link: words_ls for link, words_ls in [(synlink.link, convert_synset_into_words(target_synset = synlink.synset2))  for synlink in synlinks] if words_ls}
	wn_relation['coordinate'] = coordinated_lemma_ls
	return wn_relation
class BotProfile(MyObject):
	def __init__(self, bot_id = 'a'):
		self.bot_id = bot_id
		self.read()
	def save(self):
		upsert_core_info(whose_info = self.bot_id, info_label = 'name', kwargs = {'Char1': self.name, 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)
		upsert_core_info(whose_info = self.bot_id, info_label = 'description', kwargs = {'Char1': self.description, 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)
		upsert_core_info(whose_info = self.bot_id, info_label = 'location', kwargs = {'Char1': self.location, 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)
		upsert_core_info(whose_info = self.bot_id, info_label = 'url', kwargs = {'Char1': self.url, 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)
		upsert_core_info(whose_info = self.bot_id, info_label = 'abs_icon_filename', kwargs = {'Char1': self.abs_icon_filename, 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)
		upsert_core_info(whose_info = self.bot_id, info_label = 'abs_banner_filename', kwargs = {'Char1': self.abs_banner_filename, 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)
	def read(self):
		self.name = upsert_core_info(whose_info = self.bot_id, info_label = 'name', kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = False)._data['Char1']
		self.description = upsert_core_info(whose_info = self.bot_id, info_label = 'description', kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = False)._data['Char1']
		self.location = upsert_core_info(whose_info = self.bot_id, info_label = 'location', kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = False)._data['Char1']
		self.url = upsert_core_info(whose_info = self.bot_id, info_label = 'url', kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = False)._data['Char1']
		self.abs_icon_filename = upsert_core_info(whose_info = self.bot_id, info_label = 'abs_icon_filename',kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = False)._data['Char1']
		self.abs_banner_filename = upsert_core_info(whose_info = self.bot_id, info_label = 'abs_banner_filename', kwargs = {'Char1': '', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = False)._data['Char1']
if __name__ == '__main__':
	# a = read_userinfo('h_y_okaaaaaaaaaaaa')/Users/masaMikam/Desktop/Data/user/LiveAI_Umi/_mmKm_20160605015744_banner.jpg
	# save_phrase('test')
	# a = upsert_core_info(whose_info = 'LiveAI_Umi', info_label = 'abs_banner_filename', kwargs = {'Char1': '/Users/masaMikam/Desktop/Data/user/LiveAI_Umi/_mmKm_20160605015744_banner.jpg', 'Char2': '', 'Char3': '', 'Int1':0, 'Int2':0}, is_update = True)._data['Char1']
	a = get_phrase(status = 'kusoripu', character = 'sys')
	p(a)
	# a = search_tasks(when = datetime.now(), who = '_mmKm', n = 10)
	# with userinfo_with(screen_name = '_mmKmmm') as userinfo:


	# save_userinfo(a)
	# update_phrase('', ok_add = 0, ng_add = 1)


