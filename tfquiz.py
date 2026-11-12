"""Animal True or False Shorts (2026-11-12; Guess The Animal Quiz kanalı 49 medyan → yeni format, kullanıcı onayı).
Her video 5 iddia ("An octopus has three hearts."), izleyici DOĞRU / YANLIŞ der, sonra büyük damga + kısa açıklama.
Bilgiler elle seçilmiş, yaygın kabul gören gerçekler (uydurma / tartışmalı yok); her videoda doğru ve yanlış karışık. İngilizce, ABD.
Görünüm diğer kanallardan farklı: orman yeşili zemin, krem kart, kırmızı/yeşil mühür damgası.
    python tfquiz.py --dry-run | --auto
"""
import os, random, sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw
import shortkit as K

HERE = Path(__file__).resolve().parent
LOG = HERE / 'records' / 'tfquiz_published.csv'
OUT = HERE / 'out' / 'tfquiz'
DRY = '--dry-run' in sys.argv
N_Q, THINK, SHOW = 5, 4.2, 3.6
INTRO, OUTRO = 1.6, 3.0
BG1, BG2, CARD, INKC = (22, 74, 52), (8, 32, 22), (250, 244, 228), (30, 36, 30)
GREEN, RED, GOLD = (46, 170, 92), (214, 64, 56), (255, 214, 70)

# (emoji, iddia, doğru mu, kısa açıklama)
FACTS = [
    ('🐙', 'An octopus has three hearts.', True, 'Two pump blood to the gills, one to the body.'),
    ('🐙', 'Octopus blood is blue.', True, 'It uses copper-based hemocyanin, not iron.'),
    ('🐙', 'An octopus has ten arms.', False, 'It has eight arms. Squid have ten limbs.'),
    ('🦒', 'A giraffe has the same number of neck bones as a human.', True, 'Both have seven. Giraffe bones are just huge.'),
    ('🦒', 'Giraffes sleep about ten hours a day.', False, 'In the wild they often sleep under two hours.'),
    ('🐨', 'Koalas can sleep up to 20 hours a day.', True, 'Their eucalyptus diet gives very little energy.'),
    ('🐨', 'Koalas are a type of bear.', False, 'They are marsupials, like kangaroos.'),
    ('🐨', 'Koala fingerprints look almost like human ones.', True, 'Even under a microscope they are hard to tell apart.'),
    ('🦩', 'Flamingos get their pink color from their food.', True, 'Pigments in shrimp and algae turn them pink.'),
    ('🦩', 'Flamingos are born pink.', False, 'Chicks are grey or white at first.'),
    ('🦈', 'Sharks existed before trees.', True, 'Sharks are over 400 million years old; trees came later.'),
    ('🦈', 'A shark can smell one drop of blood in the whole ocean.', False, 'Their smell is great, but not ocean-wide.'),
    ('🐘', 'Adult elephants cannot jump.', True, 'Their legs are built to carry weight, not leap.'),
    ('🐘', "An elephant's trunk has tens of thousands of muscles.", True, 'Scientists estimate around 40,000.'),
    ('🦦', 'Sea otters sometimes hold hands while sleeping.', True, 'It keeps them from drifting apart.'),
    ('🐝', 'Honeybees share directions with a dance.', True, 'The "waggle dance" points to flowers.'),
    ('🐝', 'Every bee dies after it stings.', False, 'Mostly honeybee workers stinging mammals do.'),
    ('🦉', 'Owls can turn their heads all the way around.', False, 'About 270 degrees, not a full circle.'),
    ('🦉', 'Owls cannot move their eyes in their sockets.', True, 'That is why they turn their heads so far.'),
    ('🐢', 'Some tortoises live for more than 150 years.', True, 'Giant tortoises are among the longest-lived animals.'),
    ('🐢', 'A turtle can crawl out of its shell.', False, 'The shell is part of its skeleton.'),
    ('🦘', 'A newborn kangaroo is about the size of a jelly bean.', True, 'It grows inside the pouch for months.'),
    ('🦘', 'Kangaroos cannot easily walk backwards.', True, 'Their big tail and feet make it hard.'),
    ('🐆', 'Cheetahs can roar like lions.', False, 'They purr, chirp and hiss instead.'),
    ('🐆', 'A cheetah can hold its top speed for several minutes.', False, 'Its sprints last only about 20 to 30 seconds.'),
    ('🐬', 'Dolphins sleep with half of their brain at a time.', True, 'The other half stays alert to breathe.'),
    ('🐬', 'Dolphins are fish.', False, 'They are mammals and breathe air.'),
    ('🐊', 'Crocodiles cannot stick out their tongues.', True, 'A membrane holds the tongue in place.'),
    ('🐊', 'Alligators live in only two countries: the US and China.', True, 'There are just two alligator species.'),
    ('🐻‍❄️', 'Polar bears have black skin.', True, 'It helps them soak up heat from the sun.'),
    ('🐻‍❄️', 'Polar bear fur is actually white.', False, 'Each hair is clear and only looks white.'),
    ('🦓', 'No two zebras have the same stripes.', True, 'Every stripe pattern is unique.'),
    ('🐌', 'Snails have thousands of tiny teeth.', True, 'They sit on a tongue-like ribbon called a radula.'),
    ('🦋', 'Butterflies taste with their feet.', True, 'Sensors on their feet taste the leaves.'),
    ('🐍', 'Snakes smell with their tongues.', True, 'The tongue carries scents to a special organ.'),
    ('🐍', 'Snakes are slimy.', False, 'Their scales are dry and smooth.'),
    ('🐍', 'All snakes lay eggs.', False, 'Many snakes give birth to live young.'),
    ('🐸', 'Some frogs can freeze solid and survive.', True, 'The wood frog thaws out in spring.'),
    ('🐸', 'Touching a toad gives you warts.', False, 'Warts come from a human virus, not toads.'),
    ('🐋', 'The blue whale is the biggest animal ever known.', True, 'Bigger than any known dinosaur.'),
    ('🐋', 'Whales are fish.', False, 'They are mammals that breathe air.'),
    ('🐦', 'Hummingbirds can fly backwards.', True, 'They are the only birds that can truly do it.'),
    ('🦇', 'Bats are blind.', False, 'Bats can see; many also use echolocation.'),
    ('🦇', 'Bats are the only mammals that can truly fly.', True, 'Flying squirrels only glide.'),
    ('🐜', 'Ants do not have lungs.', True, 'Air moves through tiny holes in their bodies.'),
    ('🦥', 'Sloths can hold their breath for up to 40 minutes.', True, 'They slow their heart rate way down.'),
    ('🐔', 'Birds are living dinosaurs.', True, 'They evolved from small feathered dinosaurs.'),
    ('🐔', 'Chickens cannot fly at all.', False, 'They can fly short distances.'),
    ('🐴', 'Horses cannot breathe through their mouths.', True, 'They breathe only through the nose.'),
    ('🐄', 'A cow has four stomach compartments.', True, 'It helps them digest grass.'),
    ('🐱', 'Cats cannot taste sweet things.', True, 'They lack the sweet taste receptor.'),
    ('🐱', 'Cats always land on their feet.', False, 'Often, but falls can still hurt them.'),
    ('🐶', "A dog's nose print is unique, like a fingerprint.", True, 'No two nose prints are the same.'),
    ('🐶', 'Dogs see only in black and white.', False, 'They see blues and yellows.'),
    ('🐶', 'One dog year always equals seven human years.', False, 'It depends on the dog\'s size and age.'),
    ('🐼', 'Giant pandas eat for 10 to 16 hours a day.', True, 'Bamboo has very few calories.'),
    ('🐼', 'Red pandas are baby giant pandas.', False, 'They are a completely different animal.'),
    ('🦈', 'Some sharks must keep swimming to breathe.', True, 'Water must flow over their gills.'),
    ('🐟', 'Seahorse fathers give birth.', True, 'The male carries the eggs in a pouch.'),
    ('🐟', 'Goldfish have a three-second memory.', False, 'They can remember things for months.'),
    ('🦜', 'Some parrots can live more than 60 years.', True, 'Big parrots can outlive their owners.'),
    ('🦒', 'Giraffes have dark blue-purple tongues.', True, 'The color may protect them from sunburn.'),
    ('🐫', 'Camels store water in their humps.', False, 'The humps store fat, not water.'),
    ('🐿️', 'Squirrels help plant trees by forgetting buried nuts.', True, 'Forgotten nuts can sprout into trees.'),
    ('🦅', "A bald eagle's nest can weigh more than a ton.", True, 'They add to the same nest every year.'),
    ('🦔', 'Porcupines can shoot their quills.', False, 'Quills come off only on contact.'),
    ('🐂', 'Bulls get angry at the color red.', False, 'They react to the moving cape, not its color.'),
    ('🐘', 'Elephants are scared of mice.', False, 'There is no good evidence for this myth.'),
    ('🐧', 'Penguins live at the North Pole.', False, 'Wild penguins live in the Southern Hemisphere.'),
    ('🐧', 'Penguins can fly.', False, 'They "fly" underwater but not in the air.'),
    ('🐰', "Carrots are a rabbit's main food.", False, 'Rabbits mainly eat hay and grass.'),
    ('🐦', 'Mother birds reject chicks touched by people.', False, 'Most birds have a weak sense of smell.'),
    ('🦎', 'Chameleons change color mainly to match the background.', False, 'Mostly for mood, temperature and signals.'),
    ('🦍', 'Gorillas are meat eaters.', False, 'They mostly eat plants.'),
    ('🐭', 'Mice like cheese more than any other food.', False, 'They prefer grains and sweet foods.'),
]
TAGS = ['animal facts', 'true or false', 'animal quiz', 'animals', 'fun facts', 'quiz', 'shorts']
_HOOKS = ['Animal True or False!', 'True or False: Animal Edition!', 'Animal Myths or Facts?', 'Fact or Myth? Animals!', 'Can You Spot the Animal Myth?',
          'Only Animal Experts Get 5/5!', 'Animal Facts Quiz!', 'Real or Fake Animal Fact?', 'Wild True or False!', 'Is This Animal Fact True?',
          'Animal Myth Buster Quiz!', 'True or False? Wild Animals!', 'Think You Know Animals?', 'Animal Brain Test!', 'Weird Animal Facts: True or False?',
          'Zoo Quiz: True or False!', 'Nature Quiz: Fact or Myth?', 'Animal Trivia: True or False!', 'Guess If It\'s True!', 'Fact Check: Animals!']
_EM = ['🐾', '🦉', '🐙', '🦒']
_TAILS = ['5 Questions {0}', 'Score Yourself {1}', 'Comment Your Score {2}', 'No Googling {3}', 'Play Along {0}', 'Challenge a Friend {1}', 'Quick Quiz {2}',
          'Keep Your Streak {3}', 'How Many Did You Get? {0}', 'Test Yourself {1}', 'Daily Quiz {2}', 'Beat the Timer {3}']
TITLES = [f'{h} {t.format(*_EM)} #{{n}}' for h in _HOOKS for t in _TAILS]


def make_plan(rnd, recent):
    pool = [f for f in FACTS if K.emoji_ok(f[0])]
    fresh = [f for f in pool if f[1] not in recent] or pool
    for _ in range(50):   # doğru ve yanlış karışık (en az 2'şer)
        pick = rnd.sample(fresh if len(fresh) >= N_Q else pool, N_Q)
        if 2 <= sum(1 for f in pick if f[2]) <= 3: return pick
    return pick


def stamp(img, ok, u):
    """Mühür: hafif eğik, büyüyerek oturur."""
    col = GREEN if ok else RED; word = 'TRUE' if ok else 'FALSE'
    s = Image.new('RGBA', (700, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle([10, 10, 690, 250], radius=40, outline=col + (255,), width=16, fill=(255, 255, 255, 215))
    K.text(d, (350, 132), ('✓ ' if False else '') + word, 150, fill=col, stroke=(255, 255, 255))
    k = 1.4 - 0.4 * K.ease(u); s = s.resize((int(700 * k), int(260 * k)), Image.LANCZOS).rotate(-8 if ok else 8, expand=True, resample=Image.BICUBIC)
    img.alpha_composite(s, (int(K.W / 2 - s.width / 2), int(500 - s.height / 2)))   # emojinin üstüne (iddia metni okunur kalsın)


def frame_fn(p):
    qs = p['qs']; seg = THINK + SHOW; total = INTRO + N_Q * seg + OUTRO

    def f(T):
        img = K.gradient(BG1, BG2, False).copy(); d = ImageDraw.Draw(img)
        if T < INTRO:
            u = K.ease(T / 0.5)
            K.text(d, (K.W / 2, 740), 'ANIMAL', int(150 * u) + 1, fill=GOLD)
            K.text(d, (K.W / 2, 900), 'TRUE OR FALSE?', int(110 * u) + 1)
            K.text(d, (K.W / 2, 1060), f"5 QUESTIONS · #{p['n']}", int(60 * u) + 1)
            return img
        if T >= INTRO + N_Q * seg:
            u = K.ease((T - INTRO - N_Q * seg) / 0.5)
            K.text(d, (K.W / 2, 720), 'HOW MANY', int(110 * u) + 1)
            K.text(d, (K.W / 2, 850), 'DID YOU GET?', int(110 * u) + 1, fill=GOLD)
            K.text(d, (K.W / 2, 1010), 'COMMENT YOUR SCORE', int(70 * u) + 1)
            K.text(d, (K.W / 2, 1160), f"NEXT: QUIZ #{p['n'] + 1}", int(60 * u) + 1)
            return img
        i = int((T - INTRO) // seg); lt = T - INTRO - i * seg; e, claim, ok, why = qs[i]; show = lt >= THINK
        K.text(d, (K.W / 2, 130), f'QUESTION {i + 1}/5', 66, fill=GOLD)
        d.rounded_rectangle([80, 230, K.W - 80, 1300], radius=50, fill=CARD + (255,))
        em = K.emoji_img(e, 380); img.alpha_composite(em, (int(K.W / 2 - em.width / 2), 300))
        K.text_block(d, K.W / 2, 860, claim.upper(), 72, K.W - 260, fill=INKC, max_lines=4, stroke=CARD)
        if show:
            stamp(img, ok, (lt - THINK) / 0.35); d = ImageDraw.Draw(img)
            K.text_block(d, K.W / 2, 1220, why, 50, K.W - 240, fill=INKC, max_lines=2, stroke=CARD)
        for j, (lab, col) in enumerate([('TRUE', GREEN), ('FALSE', RED)]):
            x0 = 110 + j * (K.W - 220) // 2 + (12 if j else 0); x1 = x0 + (K.W - 220) // 2 - 12
            dim = show and ((lab == 'TRUE') != ok)
            d.rounded_rectangle([x0, 1380, x1, 1560], radius=40, fill=(tuple(c // 3 for c in col) if dim else col) + (255,))
            K.text(d, ((x0 + x1) / 2, 1470), lab, 84)
        if not show:
            frac = max(0.0, 1 - lt / THINK)
            d.rounded_rectangle([90, 1680, K.W - 90, 1726], radius=23, fill=(255, 255, 255, 110))
            d.rounded_rectangle([90, 1680, 90 + max(46, (K.W - 180) * frac), 1726], radius=23, fill=GOLD)
        return img
    events = [(INTRO + i * seg, 'new') for i in range(N_Q)] + [(INTRO + i * seg + s, 'tick') for i in range(N_Q) for s in (1, 2, 3, 4)]
    events += [(INTRO + i * seg + THINK, 'ding') for i in range(N_Q)] + [(INTRO + N_Q * seg, 'end')]
    return f, total, events


def main():
    a = sys.argv[1:]
    if '--auto' in a and K.today_count(LOG) >= int(os.environ.get('PER_DAY') or 3):
        print('bugünkü sayı doldu'); return
    rows = K.rows(LOG); recent = {x for r in rows[-10:] for x in r['topic_id'].split(':', 1)[-1].split('|')}
    rnd = random.Random(); qs = make_plan(rnd, recent)
    n = len(rows) + 1; p = dict(qs=qs, n=n, seed=rnd.randrange(10 ** 6))
    seen = {K.tkey(r['title']) for r in rows}
    opts = [t.format(n=n) for t in TITLES]; rnd.shuffle(opts)
    title = next((o for o in opts if K.tkey(o) not in seen), opts[0])
    desc = ('Animal True or False! 5 animal facts and myths. Answer before the timer ends.\n\n'
            + '\n'.join(f"{k + 1}. {q[1]} → {'TRUE' if q[2] else 'FALSE'}: {q[3]}" for k, q in enumerate(qs))
            + '\n\nHow many did you get? Comment your score 👇 New quiz every day.\n\n'
            'Emoji: Noto Color Emoji by Google (SIL Open Font License).\n\n#shorts #animalfacts #trueorfalse #animals #quiz')
    f, total, events = frame_fn(p)
    st = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
    print(f'[tf] #{n} {title}', flush=True)
    mp4 = K.render(f, total, events, p['seed'], OUT / f'tf_{st}.mp4')
    if DRY: print('  [dry-run]', mp4); return
    pa = K.publish_at(['15:00', '18:00', '20:30'], K.today_count(LOG))
    vid = K.upload(mp4, title + ' #shorts', desc, TAGS, pa, category='24')
    # kayıt: iddia metinleri (tekrarı önlemek için) — '|' içermez
    K.record(LOG, 'tf:' + '|'.join(q[1] for q in qs), vid, title, pa)
    print(f'  ✓ https://youtu.be/{vid} ({pa})')


if __name__ == '__main__':
    main()
