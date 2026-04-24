import json, time, os

S = 'chSylv1'
M = 'chMe001'

def n(i, t, **k):    return dict(id=i, type=t, **k)
def dlg(i, c, text, pose='neutral', side='center'): return n(i, 'dialogue', char_id=c, text=text, pose=pose, side=side, tpl_id=None)
def nar(i, text):    return n(i, 'narration', text=text, tpl_id=None)
def bg(i, p):        return n(i, 'bg', bg=p)
def fx(i, k):        return n(i, 'effect', kind=k, dur=0.5)
def img(i, p):       return n(i, 'image', image=p)
def music(i, p):     return n(i, 'music', music=p)
def jump(i, sid):    return n(i, 'jump', scene_id=sid, transition='dissolve')
def opt(i, text, scene): return dict(id=i, text=text, scene=scene)
def choice(i, prompt, opts): return n(i, 'choice', prompt=prompt, opts=opts)
def setvar(i, var, val): return n(i, 'setvar', var_name=var, var_val=val)

scenes = [
    dict(id='scStart', label='Start', bg=None, music=None, events=[
        music('e00', 'audio/illurock.opus'),
        bg('e01', 'images/bg lecturehall.jpg'),
        fx('e02', 'fade'),
        nar('e03', "It's only when I hear the sounds of shuffling feet and supplies being put away that I realize that the lecture's over."),
        nar('e04', "Professor Eileen's lectures are usually interesting, but today I just couldn't concentrate on it."),
        nar('e05', "I've had a lot of other thoughts on my mind...thoughts that culminate in a question."),
        nar('e06', "It's a question that I've been meaning to ask a certain someone."),
        bg('e07', 'images/bg uni.jpg'),
        fx('e08', 'fade'),
        nar('e09', "When we come out of the university, I spot her right away."),
        img('e10', 'images/sylvie green normal.png'),
        fx('e11', 'dissolve'),
        nar('e12', "I've known Sylvie since we were kids. She's got a big heart and she's always been a good friend to me."),
        nar('e13', "But recently... I've felt that I want something more."),
        nar('e14', "More than just talking, more than just walking home together when our classes end."),
        choice('e15', "As soon as she catches my eye, I decide...", [
            opt('o01', "To ask her right away.", 'scRway'),
            opt('o02', "To ask her later.", 'scLater'),
        ]),
    ]),
    dict(id='scRway', label='Right Away', bg=None, music=None, events=[
        dlg('r01', S, "Hi there! How was class?", 'happy'),
        dlg('r02', M, "Good..."),
        nar('r03', "I can't bring myself to admit that it all went in one ear and out the other."),
        dlg('r04', M, "Are you going home now? Wanna walk back with me?"),
        dlg('r05', S, "Sure!", 'happy'),
        bg('r06', 'images/bg meadow.jpg'),
        fx('r07', 'fade'),
        nar('r08', "After a short while, we reach the meadows just outside the neighborhood where we both live."),
        nar('r09', "It's a scenic view I've grown used to. Autumn is especially beautiful here."),
        nar('r10', "When we were children, we played in these meadows a lot, so they're full of memories."),
        dlg('r11', M, "Hey... Umm..."),
        img('r12', 'images/sylvie green smile.png'),
        fx('r13', 'dissolve'),
        nar('r14', "She turns to me and smiles. She looks so welcoming that I feel my nervousness melt away."),
        nar('r15', "I'll ask her...!"),
        dlg('r16', M, "Ummm... Will you..."),
        dlg('r17', M, "Will you be my artist for a visual novel?"),
        img('r18', 'images/sylvie green surprised.png'),
        nar('r19', "Silence."),
        nar('r20', "She looks so shocked that I begin to fear the worst. But then..."),
        img('r21', 'images/sylvie green smile.png'),
        choice('r22', "Sure, but what's a \"visual novel\"?", [
            opt('o03', "It's a videogame.", 'scGame'),
            opt('o04', "It's an interactive book.", 'scBook'),
        ]),
    ]),
    dict(id='scGame', label='The Game', bg=None, music=None, events=[
        dlg('g01', M, "It's a kind of videogame you can play on your computer or a console."),
        dlg('g02', M, "Visual novels tell a story with pictures and music."),
        dlg('g03', M, "Sometimes, you also get to make choices that affect the outcome of the story."),
        dlg('g04', S, "So it's like those choose-your-adventure books?", 'happy'),
        dlg('g05', M, "Exactly! I've got lots of different ideas that I think would work."),
        dlg('g06', M, "And I thought maybe you could help me...since I know how you like to draw."),
        dlg('g07', M, "It'd be hard for me to make a visual novel alone."),
        img('g08', 'images/sylvie green normal.png'),
        dlg('g09', S, "Well, sure! I can try. I just hope I don't disappoint you.", 'neutral'),
        dlg('g10', M, "You know you could never disappoint me, Sylvie."),
        jump('g11', 'scMarry'),
    ]),
    dict(id='scBook', label='The Book', bg=None, music=None, events=[
        setvar('b00', 'book', 'True'),
        dlg('b01', M, "It's like an interactive book that you can read on a computer or a console."),
        img('b02', 'images/sylvie green surprised.png'),
        dlg('b03', S, "Interactive?", 'surprised'),
        dlg('b04', M, "You can make choices that lead to different events and endings in the story."),
        dlg('b05', S, "So where does the \"visual\" part come in?", 'surprised'),
        dlg('b06', M, "Visual novels have pictures and even music, sound effects, and sometimes voice acting to go along with the text."),
        img('b07', 'images/sylvie green smile.png'),
        dlg('b08', S, "I see! That certainly sounds like fun. I actually used to make webcomics way back when, so I've got lots of story ideas.", 'happy'),
        dlg('b09', M, "That's great! So...would you be interested in working with me as an artist?"),
        dlg('b10', S, "I'd love to!", 'happy'),
        jump('b11', 'scMarry'),
    ]),
    dict(id='scMarry', label='Marry Me', bg='images/bg club.jpg', music=None, events=[
        fx('m01', 'dissolve'),
        nar('m02', "And so, we become a visual novel creating duo."),
        fx('m03', 'dissolve'),
        nar('m04', "Over the years, we make lots of games and have a lot of fun making them."),
        nar('m05', "We take turns coming up with stories and characters and support each other to make some great games!"),
        nar('m06', "And one day..."),
        img('m07', 'images/sylvie blue normal.png'),
        fx('m08', 'dissolve'),
        dlg('m09', S, "Hey...", 'sad'),
        dlg('m10', M, "Yes?"),
        img('m11', 'images/sylvie blue giggle.png'),
        dlg('m12', S, "Will you marry me?", 'custom2'),
        dlg('m13', M, "What? Where did this come from?"),
        img('m14', 'images/sylvie blue surprised.png'),
        dlg('m15', S, "Come on, how long have we been dating?", 'angry'),
        dlg('m16', M, "A while..."),
        img('m17', 'images/sylvie blue normal.png'),
        dlg('m18', S, "These last few years we've been making visual novels together, spending time together, helping each other...", 'sad'),
        dlg('m19', S, "I've gotten to know you and care about you better than anyone else. And I think the same goes for you, right?", 'sad'),
        dlg('m20', M, "Sylvie..."),
        img('m21', 'images/sylvie blue giggle.png'),
        dlg('m22', S, "But I know you're the indecisive type. If I held back, who knows when you'd propose?", 'custom2'),
        img('m23', 'images/sylvie blue normal.png'),
        dlg('m24', S, "So will you marry me?", 'sad'),
        dlg('m25', M, "Of course I will! I've actually been meaning to propose, honest!"),
        dlg('m26', S, "I know, I know.", 'sad'),
        dlg('m27', M, "I guess... I was too worried about timing. I wanted to ask the right question at the right time."),
        img('m28', 'images/sylvie blue giggle.png'),
        dlg('m29', S, "You worry too much. If only this were a visual novel and I could pick an option to give you more courage!", 'custom2'),
        fx('m30', 'dissolve'),
        nar('m31', "We get married shortly after that."),
        nar('m32', "Our visual novel duo lives on even after we're married...and I try my best to be more decisive."),
        nar('m33', "Together, we live happily ever after even now."),
        nar('m34', "{b}Good Ending{/b}."),
    ]),
    dict(id='scLater', label='Later', bg=None, music=None, events=[
        nar('l01', "I can't get up the nerve to ask right now. With a gulp, I decide to ask her later."),
        fx('l02', 'dissolve'),
        nar('l03', "But I'm an indecisive person."),
        nar('l04', "I couldn't ask her that day and I end up never being able to ask her."),
        nar('l05', "I guess I'll never know the answer to my question now..."),
        nar('l06', "{b}Bad Ending{/b}."),
    ]),
]

proj = dict(
    id='tqremake',
    title='The Question Remake',
    author='McMax',
    created=time.time(),
    updated=time.time(),
    cover=None,
    resolution=[1280, 720],
    characters=[
        dict(id=S, name='Sylvie', display='Sylvie', color='#c8ffc8', sprites=dict(
            neutral='images/sylvie green normal.png',
            happy='images/sylvie green smile.png',
            sad='images/sylvie blue normal.png',
            angry='images/sylvie blue surprised.png',
            surprised='images/sylvie green surprised.png',
            custom1='images/sylvie green giggle.png',
            custom2='images/sylvie blue giggle.png',
        )),
        dict(id=M, name='Me', display='Me', color='#c8c8ff', sprites=dict(
            neutral='', happy='', sad='', angry='', surprised='', custom1='', custom2='',
        )),
    ],
    scenes=scenes,
    start='scStart',
    text_tpls=[dict(id='default', name='Default', font='DejaVuSans.ttf', size=22,
        color='#ffffff', bold=False, italic=False, outline=True, outline_color='#000000',
        outline_size=2, shadow=False, shadow_color='#000000aa', box_bg='#00000099',
        box_pad=20, typing_speed=0)],
    trans_tpls=[dict(id='default', name='Dissolve', type='dissolve', dur=0.5, color='#000000')],
    folders=[],
    layout=dict(
        scStart=[80, 60], scRway=[340, 60], scGame=[600, 60],
        scBook=[600, 240], scMarry=[860, 150], scLater=[340, 260],
    ),
)

out = os.path.join('game', 'vnv_projects', 'tqremake.json')
with open(out, 'w', encoding='utf-8') as f:
    json.dump(proj, f, indent=2, ensure_ascii=False)
print(f"Done. {sum(len(s['events']) for s in scenes)} events across {len(scenes)} scenes.")
