#!/usr/bin/env python3
"""Seed nosleep-style horror stories directly into stories_cache.json.

Used when Reddit scraping is blocked. The stories are original (not scraped)
so they avoid copyright issues. Each one is written in nosleep first-person
voice, ~900 chars body so it clears the default 55-sec narration floor and
renders as a ~80-90 sec short. All entries get subreddit='nosleep' so the
horror code paths in auto.py trigger:
  - voice forced to en-US-RogerNeural (deep male)
  - sounds/horror.mp3 mixed under the voice
  - horror color grade applied

Run once, commit stories_cache.json, push.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "stories_cache.json")


def _entry(id_suffix, title, body):
    text = f"{title}. {body}"
    return {
        "id": f"seed-h-{id_suffix}",
        "subreddit": "nosleep",
        "title": title,
        "body": body,
        "text": text,
    }


STORIES = [
    _entry("001",
        "My neighbor's daughter waves at me every morning. No one lives there.",
        "I moved into this duplex three months ago. The first week I saw a little girl in the upstairs window of the unit next door, just standing there watching me leave for work. She waved. I waved back, felt good about myself, kept walking. She was there the next day too. And the next. Yesterday I asked the landlord about my neighbors. The unit's been empty since 2019. There's no power running to it. He showed me the lease records, walked me through, dust on everything, no furniture, no anything, sheet over the kitchen counter. I told him about the girl. He stopped halfway up the stairs and turned around and said we should go. We were standing in the hallway when I heard tapping on the window. I went to look. It was the girl. She was outside this time. Three stories up. Just floating there, her palms flat against the glass. She mouthed the word hi. This morning she was at my window. She wasn't outside this time."),
    _entry("002",
        "I got an email back from my brother. He died in 2018.",
        "Same address. Same signature. Same dumb auto-reply he set up in college that he never turned off, the one we all used to laugh about. The body of the email said hey saw your message been thinking about you a lot lately. I never sent him a message. His account was deactivated by my parents the week of the funeral, I watched my dad do it. I called Gmail support and they said the account doesn't exist and hasn't for years. I forwarded the email to my own address to prove it was real. When it arrived, the sender was me. The body of the forwarded email was different than the original. It said he's not the one you should be worried about. I sat at my desk for a long time. Then I tried to reply and ask what that meant. The send button was greyed out, said recipient blocked. I checked the blocked list. There was one address on it, blocked yesterday. It was mine."),
    _entry("003",
        "There are footprints in the snow leading up to my back door. They start in the middle of my yard.",
        "It snowed about four inches overnight. I let the dog out at 6 AM and she wouldn't go past the porch, kept whining and looking up at me. I went out to see what was wrong and there were boot prints, men's size 11 maybe, leading from a single spot ten feet into the yard, straight to my back door. No prints leading TO that spot. They just start. Like someone dropped down out of the sky and walked over. The door was locked. The screen door was open. I went inside to call the police. While I was on hold I noticed the boot prints had continued. They lead down my hallway, faint wet outlines on the hardwood. They stop at my daughter's room. Her door was closed. The dispatcher kept asking if I was still there. I couldn't make my voice work. I could hear my daughter breathing through the door, slow and even, asleep. I could hear someone else breathing too."),
    _entry("004",
        "The babysitter we hired keeps texting us updates. We never hired one.",
        "We were out at dinner for our anniversary. At 8:47 my phone buzzed: Kids are in bed, all good, love you guys. Wrong number, I figured. Then at 9:15: Sarah had a bad dream but I sang to her and she's fine now. My daughter's name is Sarah. I called my wife into the bathroom and showed her. She went pale. Our kids were at her mother's house for the night. We drove home at maybe 90 the whole way. The front door was locked. The house was quiet. We checked Sarah's room first. Her bed was warm. Indented like someone had been lying in it. There was a hair on the pillow that wasn't hers. My wife called her mom in tears. The kids were fine, asleep at grandma's, had been all evening. My phone buzzed again as we stood there. New message. It said you're home early. The next one said I'll get out of your way then. I heard the back door close."),
    _entry("005",
        "I checked the timestamp on a photo I took this morning. It was taken tomorrow.",
        "I take a photo of my coffee every morning, dumb habit, post it on my story. This morning's photo. December 12th, 7:14 AM. I opened the file properties out of curiosity because the photo looked off, slightly darker than usual, the angle wrong. Date taken: December 13th, 7:14 AM. Tomorrow. I checked my phone clock, today's date. I checked the system clock on my laptop, today's date. I took another photo of the wall. That one was tomorrow too. Every photo I take now is dated one day in the future. I just took one of my bedroom. There's a man standing in the corner. He's not in the room. He's not in the room when I look. He's only in the photos. He's closer in each new one. In the most recent shot he's standing right behind me. I'm taking the photo at arm's length, facing my phone. I can see myself in it. I'm not smiling. I am right now."),
    _entry("006",
        "I locked myself out of my apartment. The neighbor's key fit my door.",
        "Came home late, no keys, I knocked on my neighbor Dave's door because he has a spare for me. Dave wasn't home. The door across the hall opened though, woman I'd never seen before, asked if everything was okay. I explained. She said oh I have a spare for this unit, hold on. Came back with a brass key. I told her this is the wrong unit. She smiled and said try it. I did. It worked. I stepped inside. All my stuff was there, same furniture, same dishes in the sink, same photo of my mom on the fridge. She was still standing in my doorway. She said welcome home. I asked her to leave. She said this isn't your home yet. Then she closed the door from the outside. I tried to open it. The handle wouldn't turn. I'm still in here. I've been in here for two days. The food in the fridge doesn't go bad. My phone has service but no one I call recognizes my voice."),
    _entry("007",
        "I got a friend request from myself. Same name, same photo, three years of posts I never made.",
        "The profile picture is one I never uploaded. It's me, but I'm standing in a field I don't recognize, wearing a shirt I don't own. The posts go back to 2022. Photos of me at restaurants I've never been to. Status updates in my voice, talking about my real friends by name. One post from last month says had a great talk with my brother today, hope he's doing well. I don't have a brother. I declined the request. Five minutes later it sent again. I blocked it. New request came through from a different profile. Same photo. Same posts. I messaged my best friend and asked if anyone had been impersonating me. She wrote back what are you talking about, we just got dinner last night, you were acting weird the whole time and now you don't remember? I haven't seen her in two months. I scrolled back through my own real account. There's a check-in at the restaurant from last night. I wasn't there."),
    _entry("008",
        "The voice on my baby monitor isn't my baby. It's me.",
        "I heard her crying around 3 AM, normal night. Got up, went to the nursery, soothed her back to sleep. Came back to bed. The monitor started crackling. I turned the volume up. It was my own voice coming through, the things I'd just said to her, the lullaby I'd just sung, in my exact voice, but slightly delayed. Like a recording playing back. I went back to her room to check. She was asleep. The monitor in her room was unplugged. It had been unplugged the whole time. I never plugged it in. I haven't used the monitor since she turned two. She's four now. I went back to the receiver in our bedroom and listened. The voice was still talking. It was still in my voice. But it wasn't saying anything I'd said. It was telling her a story I had never heard. The story was about a daddy who couldn't find his daughter. I went to her room one more time. The bed was empty. The window was open. There was a recording device on the sill, still running. The voice memo title was tomorrow's date."),
    _entry("009",
        "The wrong number told me to lock my doors. Then he described my house.",
        "Phone rang at 11:48 PM. Older guy, gravelly voice. He said hi son, you need to lock your doors right now. I said you have the wrong number. He said no I don't, you're in the brick house on Cedar, second from the corner, the one with the basketball hoop in the driveway. He described my mailbox. He described the dent in my garage door from last winter that I never got fixed. He said the front door is unlocked right now. I checked. He was right. I locked it. He was still on the line. He said the back door too. I locked that. He said good. Now go upstairs. I asked who he was. He didn't answer for a long time. Then he said I'm you, calling from forty minutes from now. Please go upstairs. Then he said don't go in the basement. I asked why. He said because you're already down there."),
    _entry("010",
        "We found a hiking trail that isn't on any map. We took it anyway.",
        "Three of us, day hike in the Cascades, well-marked trails, did everything right, downloaded the map, told someone where we were going. About two miles in we found a side path branching off to the left, no sign, but clearly maintained. We figured the rangers added it recently. We took it. It went on for about an hour. Trees got taller, weirdly tall, and the light got grey even though it was barely noon. We came to a clearing. There was a campfire burning. Three sleeping bags. Three packs. Our packs. We were still wearing our packs. We turned around and ran. Got back to the main trail in twenty minutes flat. Drove home in silence. None of us has talked about it. But last week I checked my pack. There's a campfire smell in it that won't go away. And my hiking boots, the ones I had on that day, have mud on them that hasn't dried. It's been five months."),
    _entry("011",
        "My smart speaker keeps reading me messages from my old phone. The phone broke in 2019.",
        "Yesterday it said new message from Mom received Tuesday 4:14 PM. The message was about Thanksgiving plans from 2018. Today it said you have seventeen unread messages. It started reading them. They were all from people I used to know, dates from years ago, things I remember happening. One of them was from my ex, asking what time to pick me up for the concert. We broke up before that concert. I never went. The speaker just read the message in her exact voice, not the robot voice it usually uses. The next message was from me, to me, sent next Wednesday. It said please don't go. I asked the speaker to stop. It didn't. It kept reading messages, faster now, voices overlapping. Voices of people I haven't talked to in years. Voices of people who are dead. Then one voice cut through all of them, slow and calm, my voice, saying come to the kitchen. I unplugged the speaker. It kept talking."),
    _entry("012",
        "I keep finding new rooms in my apartment. I've lived here for six years.",
        "Last Tuesday it was a small linen closet next to the bathroom. I don't remember a linen closet. Wednesday a half-bath off the kitchen I'd never seen, light still on like someone had just used it. Thursday a sliding door in my bedroom that opens to a sunroom. The sunroom has a view of a beach. My apartment is on the third floor of a building in Cleveland. I went out into the sunroom and the door closed behind me. I couldn't get it open. I could hear the ocean. I was out there for what felt like hours. When the door finally opened again, my bedroom was different. My bed was made. I never make my bed. Today there's a new door in my hallway. It's locked. I can hear someone inside knocking to come out. The voice through the door sounds like mine. It keeps telling me which key opens it. The key is on my keychain. I've had it for years. I don't know what it's for. I haven't tried it yet."),
]


def main():
    if not os.path.exists(CACHE):
        existing = []
        print(f"Cache not found at {CACHE}; creating new one.")
    else:
        with open(CACHE) as f:
            existing = json.load(f)
        print(f"Loaded {len(existing)} existing stories.")

    by_id = {s["id"]: s for s in existing}
    added = 0
    for s in STORIES:
        if s["id"] in by_id:
            continue
        by_id[s["id"]] = s
        added += 1
    out = list(by_id.values())
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Added {added} horror stories. Cache now has {len(out)} total.")

    avg = sum(len(s["body"]) for s in STORIES) // len(STORIES)
    print(f"Avg body length: {avg} chars (~{avg//16} sec narration)")
    print(f"\nNext: git add stories_cache.json && git commit -m 'seed horror stories' && git push")


if __name__ == "__main__":
    main()
