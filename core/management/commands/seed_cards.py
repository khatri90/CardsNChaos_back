"""
Management command to seed database with card packs.
Imports all cards from the original cards.js data.
"""

from django.core.management.base import BaseCommand
from core.models import Pack, Card


# Card data from cards.js
CARD_PACKS = {
    "standard": {
        "name": "Standard Chaos",
        "description": "The classic experience.",
        "black": [
            "Why am I sticky?",
            "What's that smell?",
            "I got 99 problems but _ isn't one.",
            "Make a haiku.",
            "Warn your children about _.",
            "What ended my previous relationship?",
            "What's the next big superhero/sidekick duo?",
            "During sex, I like to think about _.",
            "What are my parents hiding from me?",
            "The class field trip was completely ruined by _.",
            "What's my secret power?",
            "I drink to forget _.",
            "What's the crustiest thing I own?",
            "Daddy, why is mommy crying?",
            "How did I lose my virginity?",
            "I never truly understood _ until I encountered _.",
            "Rumor has it that Vladimir Putin's favorite dish is _.",
            "What's the most common search term on my browser history?",
            "The new safety video warns against _ while operating heavy machinery.",
            "Look, I didn't want to show you this, but here's a picture of _.",
            "In M. Night Shyamalan's new movie, Bruce Willis discovers that he had really been _ all along.",
            "When I am a billionaire, I shall erect a 50-foot statue to commemorate _.",
            "What's the gift that keeps on giving?",
            "Life for American Indians was forever changed when the White Man introduced them to _.",
            "Coming to Broadway this season, _: The Musical.",
            "It's a pity that kids these days are all getting involved with _.",
            "Here is the church. Here is the steeple. Open the doors and see _.",
            "The blind date was going horribly until we discovered our shared interest in _.",
            "What's the new fad diet?",
            "The Smithsonian Museum of Natural History has just acquired an exhibit on _.",
            "When I'm in prison, I'll have _ smuggled in.",
            "But before I kill you, Mr. Bond, I must show you _.",
            "I do not know with what weapons World War III will be fought, but World War IV will be fought with _.",
            "I don't know what's more shocking: the fact that I'm gay, or the fact that I'm _.",
            "What helps Obama unwind?",
            "Hey Reddit! I'm _. Ask me anything.",
            "The healing process began when I joined a support group for victims of _.",
            "While the United States raced the Soviet Union to the moon, the Mexican government funneled millions of pesos into research on _.",
            "Next on ESPN2: The World Series of _.",
            "Siri, show me pictures of _.",
            "The best part of waking up is _ in your cup."
        ],
        "white": [
            "A lifetime of sadness.",
            "An erection that lasts longer than four hours.",
            "My soul.",
            "A salty surprise.",
            "A cooler full of organs.",
            "The Blood of Christ.",
            "A micropenis.",
            "Being a dick to children.",
            "Genuine human connection.",
            "Dying.",
            "Flightless birds.",
            "The Amish.",
            "My ex-wife.",
            "Alcoholism.",
            "Farting and walking away.",
            "Bees?",
            "Selecting a new king.",
            "Police brutality.",
            "White privilege.",
            "A balanced breakfast.",
            "Doing crimes.",
            "Some guy.",
            "My inner demons.",
            "Puppies!",
            "Grandma's ashes.",
            "Silence.",
            "A mime having a stroke.",
            "Used panties.",
            "Becoming a blueberry.",
            "Three dicks at the same time.",
            "A defective condom.",
            "A disappointing birthday party.",
            "A falcon with a cap on its head.",
            "A guinea pig who's seen some sh*t.",
            "A homoerotic subplot.",
            "A man on the brink of orgasm.",
            "A mating display.",
            "A middle-aged man on roller skates.",
            "A mimosa consumed on a Tuesday morning.",
            "A monkey smoking a cigar.",
            "A mopey zoo lion.",
            "A nu-male with a patchy beard.",
            "A pile of squirming bodies.",
            "A pyramid of severed heads.",
            "A really cool hat.",
            "A stray pubic hair.",
            "A supermassive black hole.",
            "A three-way with my wife and Shaquille O'Neal.",
            "A time travel paradox.",
            "A tiny horse.",
            "A web of lies.",
            "A windmill full of corpses.",
            "A woman scorning.",
            "A zero-risk way to make $2,000 from home.",
            "Active listening.",
            "Adderall.",
            "African children.",
            "Agriculture.",
            "AIDS.",
            "Albert Einstein.",
            "Alcohol poisoning.",
            "All my friends dying.",
            "All of this blood.",
            "An all-you-can-eat shrimp dinner.",
            "An army of skeletons.",
            "An asymmetric boob job.",
            "An icepick lobotomy.",
            "An ugly face.",
            "An unstoppable wave of fire ants.",
            "Anal fissures.",
            "Ancient aliens.",
            "Another goddamn vampire movie.",
            "Another shot of morphine.",
            "Apologizing."
        ]
    },
    "nsfw": {
        "name": "After Dark",
        "description": "Not for the faint of heart.",
        "black": [
            "I'm sorry, Professor, but I couldn't complete my homework because of _.",
            "What's the most emo?",
            "Rub a dub dub, three men in a _.",
            "What is Batman's guilty pleasure?",
            "TSA guidelines now prohibit _ on airplanes.",
            "When I was a child, I was traumatized by _.",
            "In a world ravaged by _, our only hope is _.",
            "My plan for world domination involves _.",
            "What's the most offensive thing you can say at a funeral?",
            "Only two things in life are certain: death and _.",
            "Science will never explain the origin of _.",
            "The secret to a lasting marriage is communication, communication, and _.",
            "What did I bring back from Mexico?",
            "To prepare for his upcoming role, the actor immersed himself in the world of _.",
            "The 69th Annual Hunger Games picked a new twist: _.",
            "Why does my pee burn?",
            "I learned the hard way that you can't cheer up a grieving friend with _.",
            "Introducing X-treme Baseball! It's like baseball, but with _!",
            "What is the ultimate aphrodisiac?",
            "After the earthquake, Sean Penn brought _ to the people of Haiti.",
            "In the new Disney Channel Original Movie, Hannah Montana struggles with _ for the first time.",
            "Instead of coal, Santa now gives the bad children _.",
            "What's the worst thing that could happen on your honeymoon?",
            "A romantic, candlelit dinner would be incomplete without _."
        ],
        "white": [
            "A big black dick.",
            "Getting naked and watching Nickelodeon.",
            "Touching a dong.",
            "Pixelated bukkake.",
            "Anal beads.",
            "Two midgets shitting into a bucket.",
            "A fetus.",
            "A gassy antelope.",
            "A glass of jarate.",
            "A hot mess.",
            "A Japanese tourist.",
            "A joyless empty void.",
            "A leprechaun.",
            "A little boy who won't shut the f*ck up.",
            "A man who isn't Bob Dole.",
            "A mexican.",
            "A moment of silence.",
            "A pangender octopus roaming the cosmos in search of love.",
            "A sausage festival.",
            "A sea of troubles.",
            "A sickly child-king.",
            "A snapping turtle biting the tip of your penis.",
            "A spastic nerd.",
            "A stray bullet.",
            "A team of lawyers.",
            "A tribe of warrior women.",
            "A video of Oprah sobbing into a lean cuisine.",
            "A wet dream.",
            "A whole thing of butter.",
            "Abortions.",
            "Academy Award winner Meryl Streep.",
            "Accepting the way things are.",
            "Accidentally slipping yourself a roofie.",
            "Actually getting shot, for real.",
            "Adolf Hitler.",
            "Adult Friendfinder.",
            "Advice from a wise, old black man.",
            "African children.",
            "AIDS.",
            "Alcoholism.",
            "All-you-can-eat shrimp for $4.99.",
            "Alter boys.",
            "American Gladiators.",
            "Amputees.",
            "An AR-15 assault rifle.",
            "An honest cop with nothing left to lose.",
            "An M. Night Shyamalan plot twist.",
            "An Oedipus complex.",
            "An unhinged guest.",
            "Anal.",
            "Another goddamn vampire movie.",
            "Another shot of morphine.",
            "Apologizing.",
            "Appreciative snapping.",
            "Arnold Schwarzenegger.",
            "Asians who aren't good at math.",
            "Assless chaps.",
            "Attitude.",
            "Auschwitz.",
            "Auto-erotic asphyxiation.",
            "Axes.",
            "Balls.",
            "Barack Obama.",
            "Basic human decency.",
            "Batman.",
            "Battleships.",
            "Being a dick to children.",
            "Being a motherfucking sorcerer.",
            "Being a woman.",
            "Being fabulous.",
            "Being marginalized.",
            "Being on fire.",
            "Being rich.",
            "Bill Nye the Science Guy.",
            "Bingeing and purging.",
            "Bio-engineered assault turtles with acid breath.",
            "Bisexuality.",
            "Bitches.",
            "Black people.",
            "Bling.",
            "Blood farts.",
            "Blowing up Parliament."
        ]
    },
    "geek": {
        "name": "Geek & Gamers",
        "description": "Gamers rise up.",
        "black": [
            "It's dangerous to go alone! Take _.",
            "Use the Force, Luke. Use _.",
            "You have died of _.",
            "The cake is a _.",
            "In the next patch, Blizzard is nerfing _.",
            "My D&D character died because of _.",
            "_ is the only way to defeat the final boss.",
            "I'd like to trade my Charizard for _.",
            "What's the password to the secret level?",
            "404 Error: _ not found."
        ],
        "white": [
            "Ganon's crotch rot.",
            "Installing Windows Updates.",
            "404 Error: File Not Found.",
            "Lag.",
            "Blue Screen of Death.",
            "A level 1 Rattata.",
            "Buying a GF for 10gp.",
            "Leeroy Jenkins.",
            "The Konami Code.",
            "Teabagging your corpse.",
            "Rage quitting.",
            "Steam Summer Sale.",
            "Half-Life 3."
        ]
    },
    "desi": {
        "name": "Desi Parents",
        "description": "Emotional damage guaranteed.",
        "black": [
            "Log kya kahenge agar _?",
            "Ammi ki chappal vs _.",
            "Rishta rejected because of _.",
            "Chai mein _ gir gaya.",
            "Beta, when are you giving us _?",
            "The real reason for the power cut is _.",
            "My astrologer said I should avoid _.",
            "Bollywood's next big hit: Dilwale _ Le Jayenge."
        ],
        "white": [
            "Engineering degree.",
            "Phupho ki saazish.",
            "Biryani with aloo.",
            "Kaala jadoo.",
            "Fair & Lovely.",
            "Sharma ji ka beta.",
            "Aarranged marriage.",
            "Dowry (allegedly).",
            "Spicy Golgappe.",
            "Watching cricket instead of working.",
            "Sending 'Good Morning' WhatsApp forwards."
        ]
    },
    "czech": {
        "name": "Czech Republic",
        "description": "Ponozky v sandalech & pivo.",
        "black": [
            "Prezident Zeman opet vravora, protoze _.",
            "Co skryva Andrej Babis ve sve slozce?",
            "Prazska MHD je zpozdena kvuli _.",
            "Muj tajny recept na svickovou obsahuje _.",
            "V Brne konecne postavili _.",
            "Karel Gott by nikdy nezpival o _.",
            "Co najdes v kazde ceske hospode?",
            "Nejhorsi darek k Vanocum je _.",
            "V nove epizode Ulice uvidime _.",
            "Co zpusobilo pad koruny?",
            "Muj soused je podezrely, protoze ma na zahrade _.",
            "Na Palave letos urodilo neobvykle mnozstvi _.",
            "Ceska posta ztratila muj balicek s _.",
            "Co dela Okamura ve volnem case?",
            "Kluci z Prahy natocili video o _.",
            "Jedine, co Cesi miluji vic nez pivo, je _.",
            "Konecne! Vlada schvalila dotace na _.",
            "Co jsem si privezl z dovolene v Chorvatsku?",
            "Babicka mi upletla svetr s motivem _.",
            "Kdo za to muze? Kalousek a _."
        ],
        "white": [
            "Ponozky v sandalech.",
            "Utopenec.",
            "Becherovka na snidani.",
            "Fronta na banany.",
            "Rizek velky jako sloni ucho.",
            "Zdenek Troska.",
            "Pivo levnejsi nez voda.",
            "Vajecny konak.",
            "Slevy v Kauflandu.",
            "Hokejova prohra.",
            "Jaromir Jagr.",
            "Krtecek v kalhotkach.",
            "Vanocni kapr ve vane.",
            "Tuzemak.",
            "Smazeny syr s hranolky.",
            "Pastika na chlebu.",
            "Skoda Fabia 1.2 HTP.",
            "D1 v rekonstrukci.",
            "Tunel Blanka.",
            "Knedliky.",
            "Chlebicky.",
            "Okurková sezona.",
            "Burcak.",
            "Vestkyne Jolanda.",
            "Babisovy uzeniny.",
            "Prazsky orloj (v rekonstrukci).",
            "Cesky lev.",
            "Tatranka v batohu.",
            "Slevomat.",
            "Exekuce.",
            "Milos Zeman na clunu."
        ]
    },
    "chaos": {
        "name": "Chaos (Family Friendly)",
        "description": "Simple jokes for everyone.",
        "black": [
            "Why did the chicken cross the road? To get to _.",
            "Knock knock. Who's there? _.",
            "My favorite food is _.",
            "I love to play with _.",
            "The best superpower would be _.",
            "My dog ate my _.",
            "I want to be a _ when I grow up.",
            "What smells funny?",
            "Never trust a person who likes _.",
            "The secret ingredient in mom's soup is _.",
            "I'm afraid of _.",
            "What moves really fast?",
            "If I had a million dollars, I would buy _.",
            "The moon is actually made of _.",
            "My teacher is secretly _.",
            "In the future, cars will run on _.",
            "What's under my bed?",
            "The funniest word in the world is _.",
            "I can't believe I ate _!",
            "Stop! Hammer time. Can't touch _."
        ],
        "white": [
            "A banana.",
            "Pizza.",
            "Homework.",
            "A cat.",
            "A dog.",
            "Ice cream.",
            "Spaghetti.",
            "A dinosaur.",
            "A robot.",
            "My bed.",
            "Video games.",
            "Slime.",
            "A unicorn.",
            "Broccoli.",
            "A fart.",
            "Grandma.",
            "A giant spider.",
            "Bubblegum.",
            "A spaceship.",
            "A potato.",
            "Socks.",
            "The toilet.",
            "Chocolate.",
            "A monkey.",
            "School.",
            "Vacation.",
            "A clown.",
            "A wizard.",
            "Magic.",
            "Ninja skills."
        ]
    }
}


class Command(BaseCommand):
    help = 'Seed database with initial card packs'

    def handle(self, *args, **options):
        total_count = 0

        for pack_id, pack_data in CARD_PACKS.items():
            # Create or update pack
            pack, created = Pack.objects.update_or_create(
                id=pack_id,
                defaults={
                    'name': pack_data['name'],
                    'description': pack_data.get('description', ''),
                    'enabled': True
                }
            )

            action = "Created" if created else "Updated"
            self.stdout.write(f'{action} pack: {pack.name}')

            # Get existing cards to avoid duplicates
            existing_texts = set(
                Card.objects.filter(pack=pack)
                .values_list('text', flat=True)
            )

            # Add black cards
            for text in pack_data.get('black', []):
                if text not in existing_texts:
                    Card.objects.create(
                        text=text,
                        card_type='black',
                        pack=pack
                    )
                    total_count += 1

            # Add white cards
            for text in pack_data.get('white', []):
                if text not in existing_texts:
                    Card.objects.create(
                        text=text,
                        card_type='white',
                        pack=pack
                    )
                    total_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Seeding complete. Added {total_count} new cards.')
        )

        # Print summary
        for pack in Pack.objects.all():
            black_count = pack.cards.filter(card_type='black').count()
            white_count = pack.cards.filter(card_type='white').count()
            self.stdout.write(f'  {pack.name}: {black_count} black, {white_count} white')


