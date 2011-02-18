from Tkinter import *
import concepttools,sys

__version__ = "2.0"
__author__ = "hugo@media.mit.edu"
__url__ = 'www.conceptnet.org'
config_filename = 'ConceptNet.ini'
welcome_text = """
    ***************************************************
    Welcome to the ConceptNet v2 mini-browser!
    (for more info, please visit www.conceptnet.org)
    ***************************************************
    The purpose of this browser is to allow you to
    explore the ConceptNet API interactively!
    Instructions for browsing:
    - First, click on one of the light-green or yellow
    buttons to select a mode of browsing
    - In the red box, enter some input text
        - Light-green buttons signify "node-level" modes,
        so you may only input concepts like "apple" or
        "eat food". You'll notice that the query
        automatically executes when you press the space
        bar or the return key. In this mode, concepts
        must be given in normalized form (verbs in
        infinitive form, no plurals, no "the" or "a")
        - Yellow buttons signify "document-level" modes, so
        you can paste any amount of text into the red
        box (e.g. a sentence to a document) and the text
        doesn't have to be normalized. In this mode, you
        must press the return key to execute your query.
    - Results are displayed in the deep-green box and
    you may have to scroll to see all of the results
    - Most modes are self-explanatory, but for
    additional information, please consult the api's
    html documentation and www.conceptnet.org
    That's all! So enjoy!
"""

c = concepttools.ConceptTools()
root = Tk()
mode_var = StringVar()

root.title("conceptnet 2.0 mini-browser"),root.option_add('*Font',('Courier', 14, 'bold'))

frame1,win2,frame3 = Frame(root),Frame(root,height="1",bg="#CCFF99"),Frame(root)

frame1.pack(fill=BOTH,expand=NO),win2.pack(fill=BOTH,expand=NO),frame3.pack(fill=BOTH,expand=YES)

win,win3,win_scroll,win3_scroll = Text(frame1,bg="#FF3300",fg="white",height="3",wrap=WORD),Text(frame3,wrap=WORD,height="30",width="20",bg="#669933",fg="white"),Scrollbar(frame1),Scrollbar(frame3)

win_scroll.pack(side=RIGHT,fill=Y),win3_scroll.pack(side=RIGHT,fill=Y),win.pack(fill=BOTH,expand=NO),win2.pack(fill=BOTH,expand=NO),win3.pack(fill=BOTH,expand=1)

win.config(yscrollcommand=win_scroll.set),win3.config(yscrollcommand=win3_scroll.set),win_scroll.config(command=win.yview),win3_scroll.config(command=win3.yview)

Radiobutton(win2,text="BROWSE",variable=mode_var,value='browse',fg="#FF3399",bg='#CCFF99',indicatoron=0).pack(side=LEFT),Radiobutton(win2,text="CONTEXT",variable=mode_var,value='context',indicatoron=0,fg="#FF3399",bg='#CCFF99').pack(side=LEFT),Radiobutton(win2,text="PROJECTION",variable=mode_var,value='projection',indicatoron=0,fg="#FF3399",bg='#CCFF99').pack(side=LEFT),Radiobutton(win2,text="ANALOGY",variable=mode_var,value='analogy',indicatoron=0,fg="#FF3399",bg='#CCFF99').pack(side=LEFT),Radiobutton(win2,text="GUESS CONCEPT",variable=mode_var,value='guessconcept',indicatoron=0,fg="#FF3399",bg='#FFFF66').pack(side=LEFT),Radiobutton(win2,text="GUESS TOPIC",variable=mode_var,value='guesstopic',indicatoron=0,fg="#FF3399",bg='#FFFF66').pack(side=LEFT),Radiobutton(win2,text="GUESS MOOD",variable=mode_var,value='guessmood',indicatoron=0,fg="#FF3399",bg='#FFFF66').pack(side=LEFT),Radiobutton(win2,text="SUMMARIZE",variable=mode_var,value='summarize',indicatoron=0,fg="#FF3399",bg='#FFFF66').pack(side=LEFT)

win3.insert(0.0,welcome_text)

def execution1(x):
	#if mode_var.get() not in ['guessmood','guesstopic','guessconcept','summarize']:
	#	return execution2(x)
	#else:
		return False

def execution2(x):
	win3.delete(0.0,END)
	if win.get(0.0,END).strip()=='':
		win3.insert(0.0,welcome_text)
		return
	
	mode = mode_var.get() 
	input = win.get(0.0,END).encode('ascii','ignore').strip()
	concepts = [tok.strip() for tok in input.split(',')]
	if mode == 'context':
		result = '\n'.join(['%s (%d%%)' % (concept, weight*100) for concept, weight in c.spreading_activation(concepts)] ) +'\n\n'
	
	elif mode == 'projection':
		result = '\n\n'.join([ v[0].upper() + '\n' + '\n'.join( [ z[0] + ' (' + str(int(z[1]*100)) + '%)' for z in v[1] ] [:10]) for v in c.get_all_projections(concepts)] ) +'\n\n'

	elif mode == 'analogy':
		result = '\n\n'.join( ['[~' + match[0] + '] (' + str(match[2]) + ')\n  ' + '\n  '.join( ['==' + struct[0] + '==> ' + struct[1] + ' (' +str(struct[2]) + ') ' for struct in match[1]] ) for match in c.get_analogous_concepts(input)])

	elif mode == 'guessconcept':
		result = '\n\n'.join( [ '[is it: ' + match[0] + '?] (' + str(match[2]) + ')\n  ' + '\n  '.join([ '==' + struct[0] + '==> ' + struct[1] + ' (' + str(struct[2]) + ') ' for struct in match[1]] ) for match in c.nltools.guess_concept(input)])

	elif mode == 'guesstopic':
		result = '\n'.join( [ z[0] + ' (' + str(int(z[1]*100)) + '%)' for z in c.nltools.guess_topic(input)[1]]) + '\n\n'

	elif mode == 'guessmood':
		result = '\n'.join([ z[0] + ' (' + str(int(z[1]*100)) + '%)' for z in c.nltools.guess_mood(input) ] ) + '\n\n'

	elif mode == 'summarize':
		result = c.nltools.summarize_document(input) + '\n\n'

	elif mode == 'foo':
		result = ''
		
	else:
		result = c.display_node(input) + '\n\n'

	win3.insert(0.0,result)
	return True

win.bind('<space>',execution1),win.bind('<Return>',execution2)
root.mainloop()
