import requests as r
import json
import sys
import os
import numpy as np

class TranslatorApi:
	
	def __init__(self,email):	
		self.base_url = "https://api.mymemory.translated.net/get?q={}&langpair=en|hu&de={}"
		self.key_url = "https://api.mymemory.translated.net/keygen?user=kmarko&pass=C1pitan0"
		self.key = ""
		self.email = email
	
	def getKey(self):
		result = r.get(url=self.key_url)
		data = result.json()
		self.key = data["key"]
		
	def translate(self, string_to_translate):
		URL = self.base_url.format(string_to_translate,self.email)
		#URL = self.base_url.format(string_to_translate,self.key)
		result = r.get(url = URL) 
		data = result.json()
		return data["responseData"]["translatedText"]
	
class MockTranslatorApi(TranslatorApi):
	
	def __init__(self,email):	
		super().__init__(email)
		
	def translate(self, string_to_translate):
		return string_to_translate
		
		
class Fraction:

	def __init__(self, number, from_to, text):
		self.number = number
		self.from_to = from_to
		self.text = text
		self.lines = []
		
	def toString(self):
		return "{} {} {}".format(str(self.number), self.from_to, self.text)
		
	def toSub(self):
		return "{}\n{}\n{}\n".format(str(self.number), self.from_to, self.text)
		
	def setLines(self, lines):
		self.lines = lines

class Speech(Fraction):

	def __init__(self, number, from_to, text, fractions):
		super().__init__(number, from_to, text)
		self.fractions = fractions
	
class Parser:

	def __init__(self, file_name_from_translate):
		self.file_name_from_translate = file_name_from_translate
		#self.last_was_space = True
		self.pos = 0
	
	def read_lines(self):
		file_from_translate = open(self.file_name_from_translate, 'r') 
		lines = file_from_translate.readlines()
		lines_count = len(lines)
		return (lines,lines_count)

	def read_fractions(self):
		fractions = []
		lines,_ = self.read_lines()
		number = 0
		from_to = ""
		text = ""
		ls = []
		for line in lines:
			line = line.strip()
			if line == "":
				fraction = Fraction(number,from_to,text)
				fraction.setLines(ls)
				fractions.append(fraction)
				self.pos = 0
				number = 0
				from_to = ""
				ls = []
				text = ""
			elif self.pos == 0:
				number = int(line)
				self.pos = 1
			elif self.pos == 1:
				self.pos = 2
				from_to = line
			else:
				ls.append(line)
				text = text + " " + line
		return fractions
		
	def is_speech_end(self,fraction):
		t = fraction.text
		last_char = t[len(t)-1]
		end_chars = [".", "!", "?"]
		return last_char in end_chars
		
	def get_from_to(self, fractions):
		first = fractions[0]
		last = fractions[len(fractions)-1]
		first_time = first.from_to.split("-->")[0]
		last_time = last.from_to.split("-->")[1]
		return "{} --> {}".format(first_time, last_time)

	def to_speech(self, fractions):
		speech = []
		speech_fractions = []
		i = 1
		for fraction in fractions:
			if self.is_speech_end(fraction):
				if len(speech_fractions) == 0:
					speech.append(Fraction(i,fraction.from_to,fraction.text.strip()))
				else:
					t = ""
					for sf in speech_fractions:
						t = t + " " + sf.text
					speech.append(Fraction(i,self.get_from_to(speech_fractions),t.strip()))
					speech_fractions = []
				i = i + 1
			else:
				speech_fractions.append(fraction)
		return speech

class Parser_v2(Parser):
	def __init__(self, file_name_from_translate):
		super().__init__(file_name_from_translate)
		
	def to_speech(self, fractions):
		speech = []
		speech_fractions = []
		i = 1
		for fraction in fractions:
			if self.is_speech_end(fraction):
				if len(speech_fractions) == 0:
					speech.append(Speech(i,fraction.from_to,fraction.text.strip(),[fraction]))
				else:
					speech_fractions.append(fraction)
					t = ""
					for sf in speech_fractions:
						t = t + " " + sf.text
						
					speech.append(Speech(i,self.get_from_to(speech_fractions),t.strip(),speech_fractions))
					speech_fractions = []
				i = i + 1
			else:
				speech_fractions.append(fraction)
		return speech	
	
def translate_v1(from_file, email_addr):
	email = email_addr
	from_translate = from_file
	to_translate = from_file + "_hu"
	old_translate = from_file + "_en"
	new_translate = from_translate
	
	x = TranslatorApi(email)
	x.getKey()
	p = Parser(from_translate)
	fractios = p.read_fractions()
	speeches = p.to_speech(fractios)
	
	scount = len(speeches)
	fcount = 100
	modscount = int(scount/fcount)
	i = 1
	j = 0
	sub = ""
	
	file_to_translate = open(to_translate, 'w') 	
	
	for speech in speeches:	
		hun = x.translate(speech.text)
		speech.text = hun.replace("&quot;",'"')
		if i % modscount == 0:
			print(str(j) + "%",end='\r')
			j = j + 1
		try:
			speech.number = i
			sub = speech.toSub()
			file_to_translate.writelines(sub)
			i = i + 1
		except:
			try:
				print(speech.toSub())
			except:
				print("error")
	file_to_translate.close()	
	
	os.rename(from_translate,old_translate)
	os.rename(to_translate,new_translate)
	
def write_sub(i, speech, file_to_translate):
	try:
		speech.number = i
		sub = speech.toSub()
		file_to_translate.writelines(sub)
		i = i + 1
		return i
	except:
		try:
			print(speech.toSub())
			return i
		except:
			print("error")
			return i
	
	
			
def print_sub(i, speech):
	try:
		speech.number = i
		sub = speech.toSub()
		print(sub)
		i = i + 1
	except:
		try:
			print(speech.toSub())
		except:
			print("error")
	
	return i

def text_weight(text):
	return len(text)
	
def correc_rounding(word_weights,weight_percents):
	scale = [ww/weight_percents[i] for i, ww in enumerate(word_weights)]
	return np.argmin(np.array(scale))

def speech_fracturing(speech):

	original_fractions = speech.fractions
	fractions_count = len(original_fractions)
	
	weights = [text_weight(original_fraction.text) for original_fraction in original_fractions]
	total_weight = sum(weights)
	weight_percents = [weight/total_weight for weight in weights]
	
	words = speech.text.split(" ")
	words_count = len(words)
	word_weights = [int(words_count*weight_percent) for weight_percent in weight_percents]
	
	if sum(word_weights) != words_count:
		arg_i = correc_rounding(word_weights,weight_percents)
		word_weights[arg_i] = word_weights[arg_i] + 1
	
	i = 0
	j = word_weights[0]
	
	fractions = []
	for ind, original_fraction in enumerate(original_fractions):
		word_weight = word_weights[ind]
		text = " ".join(words[i:j])
		
		ls = original_fraction.lines
		ls_count = len(ls)
		
		ls_weights = [text_weight(l) for l in ls]
		total_ls_weights = sum(ls_weights)
		ls_weight_percents = [ls_weight/total_ls_weights for ls_weight in ls_weights]
		
		ls_words = text.split(" ")
		ls_words_count = len(ls_words)
		ls_word_weights = [int(ls_words_count*ls_weight_percent) for ls_weight_percent in ls_weight_percents]
		
		if sum(ls_word_weights) != ls_words_count:
			arg_li = correc_rounding(ls_word_weights,ls_weight_percents)
			ls_word_weights[arg_li] = ls_word_weights[arg_li] + 1
			
		li = 0
		lj = ls_word_weights[0]
		new_line_text = ""
		for jnd, l in enumerate(ls):
			ls_word_weight = ls_word_weights[jnd]
			new_line_text = new_line_text + " ".join(ls_words[li:lj]) + "\n"
			
			li = lj
			lj = lj + ls_word_weights[jnd]
			
		text = new_line_text
		
		i = j
		j = j + word_weights[ind]
		fractions.append(Fraction(0,original_fraction.from_to,text))
		
	return fractions
replacement_dict = [
	("&quot;",'"'),
		
	("À","Á"),
	("Â","Á"),
	("Ã","Á"),
	("Å","Á"),
	("Ä","Á"),
	
	("È","É"),
	("Ê","É"),
	("Ë","É"),
	
	("Ì","Í"),
	("Î","Í"),
	("Ï","Í"),
	
	("Ò","Ó"),
	
	("Ô","Ö"),
	("Õ","Ö"),
	
	("Ù","Ú"),
	("Û","Ú"),
	
	("à","á"),
	("â","á"),
	("ã","á"),
	("ä","á"),
	("å","á"),
	
	("è","é"),
	("ê","é"),
	("ë","é"),
	
	("ì","í"),
	("î","í"),
	("ï","í"),
			
	("ò","ó"),	
	
	("ô","ő"),	
	("õ","ó"),
	
	("ù","ú"),
	
	("û","ü"),
	("ũ","ű"),
	
	
]
def replace(text):
	global replacement_dict
	for (fr, to) in replacement_dict:
		text = text.replace(fr, to)
	return text
	
def translate_v2(from_file, email_addr):
	email = email_addr
	from_translate = from_file
	to_translate = from_file + "_hu"
	old_translate = from_file + "_en"
	new_translate = from_translate
	
	x = TranslatorApi(email)
	x.getKey()
	p = Parser_v2(from_translate)
	fractios = p.read_fractions()
	speeches = p.to_speech(fractios)
	
	scount = len(speeches)
	fcount = 100
	modscount = np.max([int(scount/fcount),1])
	i = 1
	j = 0
	sub = ""
	
	file_to_translate = open(to_translate, 'w') 	
	
	for speech in speeches:	
		hun = x.translate(speech.text)
		speech.text = replace(hun)
		if i % modscount == 0:
			print(str(j) + "%",end='\r')
			j = j + 1
			
		fractures = speech_fracturing(speech)
		for fracture in fractures:
			i = write_sub(i, fracture, file_to_translate)
	file_to_translate.close()	
	
#os.rename(from_translate,old_translate)
#os.rename(to_translate,new_translate)
	
#translate_v1(sys.argv[1], sys.argv[2])

translate_v2(sys.argv[1], sys.argv[2])
