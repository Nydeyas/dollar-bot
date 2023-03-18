import asyncio
from typing import List

import discord
from discord import Message
from discord.ext import commands, tasks
from discord.ext.commands import Context
import os
from difflib import SequenceMatcher
from Levenshtein import distance
from collect_data import collect_data

# Intents and token
intents = discord.Intents.default()
intents.message_content = True
TOKEN = os.environ['TOKEN']

# Change the no_category default string
help_command = commands.DefaultHelpCommand(
    no_category='Commands',
)

# Set bot activity status
activity = discord.Activity(type=discord.ActivityType.listening, name="$help")

# Bot
bot = discord.ext.commands.Bot(command_prefix=["$"], activity=activity, case_insensitive=True, intents=intents,
                               help_command=help_command)

# Public values
bot.g_channel = [1070659462194544711, 864900249306660865]
bot.g_state = 1
bot.g_bundle = {}
bot.g_categories = []
bot.g_shops = []
bot.g_data = []
rows_limit = 20  # max number of rows showed in the list of products
required_score = 58  # minimum score of similarity in the search(0-100)


@bot.event
async def on_ready() -> None:
    print(f'Logged as: {bot.user}')
    await update_data()
    print("g_data size: ", len(bot.g_data))


@tasks.loop(minutes=120)
async def update_data() -> None:
    print("Preparation for data collection...")
    shops, categories, data = await collect_data()

    print("Applying new data...")
    bot.g_state = 0  # bot controls blocked
    await asyncio.sleep(3)  # wait in case of handle state running
    bot.g_shops, bot.g_categories, bot.g_data = shops, categories, data
    bot.g_state = 1
    print(f"Using categories: {bot.g_categories}")
    print(f"Using shops: {bot.g_shops}")


@bot.command(aliases=['sprawdź', 'sprawdz'], brief='Sprawdza ceny produktów', description='Sprawdza ceny produktów')
async def ceny(ctx: Context) -> None:
    # Check if command was sended on a bot channel and status != 0
    if ctx.channel.id in bot.g_channel and bot.g_state:
        bot.g_state = 1
        await handle_state1(message=ctx.message)


@bot.event
async def on_message(message: Message) -> None:
    # Check if the message was sent on a bot channel and the message is not a command
    if message.channel.id in bot.g_channel and not message.content.startswith(tuple(bot.command_prefix)):
        if message.author == bot.user:
            return
        # Back to previous menu
        if message.content.lower() == 'w' and bot.g_state >= 3:
            bot.g_state -= 2
            message.content = ''  # without content, handle() takes previous data

        state_dict = {
            1: handle_state1,  # idle mode
            2: handle_state2,  # categories panel showed
            3: handle_state3,  # list of products or search result panel showed
            4: handle_state4,  # individual product panel showed
        }
        handler = state_dict.get(bot.g_state, None)
        if handler:
            await handler(message)

    await bot.process_commands(message)


async def handle_state1(message: Message) -> None:
    """Idle mode"""
    ctx = await bot.get_context(message)
    if str(ctx.command) == 'ceny' or not message.content:
        # Check if there are any shops and categories
        if bot.g_shops and bot.g_categories:
            # Make description
            description = "**Wybierz kategorię:**\n\n"
            counter = 1
            for c in bot.g_categories:
                description += f"{counter}. {c.capitalize()}\n"
                counter += 1
            # Clear bundles
            bot.g_bundle.clear()
            # Change state of the Bot
            bot.g_state = 2
        else:
            description = "Brak produktów w bazie."

        # Send embedded message
        embed = construct_embedded_message(description=description)
        await message.channel.send(embed=embed)


async def handle_state2(message: Message) -> None:
    """Categories panel shown"""
    # Check if category already exist (searching for product instead)
    if 'category_id' in bot.g_bundle.keys():
        # Search
        if message.content:
            # Search a product based on the phrase
            phrase_split = message.content.split(' ')
            i_id_to_matches: List[List[int, int]] = []
            for i_counter, i in enumerate(list(bot.g_data[0].categories[bot.g_bundle['category_id']].items)):
                matches = 0
                for word in phrase_split:
                    if word.lower() in i.name.lower():
                        matches += 1
                i_id_to_matches.append([i_counter, matches])
            # Sorting results
            i_id_to_matches.sort(key=lambda x: x[1], reverse=True)

            # Making list of items
            items = []
            for L in i_id_to_matches[:rows_limit]:
                item = bot.g_data[0].categories[bot.g_bundle['category_id']].items[L[0]]
                items.append(item)
            bot.g_bundle['items_search'] = items
        # Back
        else:
            items = bot.g_bundle.get('items_search')
            if not items:
                items = bot.g_data[0].categories[bot.g_bundle.get('category_id', 0)].items

    # Check for category
    else:
        # Check for the numeric choice
        if message.content.isnumeric():
            msg_int = int(message.content)
            if msg_int in range(1, len(bot.g_categories) + 1):
                category_id = msg_int - 1
            else:
                await message.channel.send("Wybrano nieprawidłową liczbę.")
                return
        # Check for the text choice
        else:
            msg = message.content.lower()
            for count, value in enumerate(bot.g_categories):
                if msg in value.lower():
                    category_id = count
                    break
            else:
                await message.channel.send("Nie rozpoznano kategorii.")
                return
        bot.g_bundle['category_id'] = category_id
        # Making list of items
        items = bot.g_data[0].categories[category_id].items

    # Make description
    field_name = ''
    field_price = ''
    for counter, i in enumerate(items[:rows_limit]):
        name = i.name
        if len(name) > 40:
            name = name[:38] + "..."
        field_name += f"{counter + 1}. {name}\n"
        field_price += f"{i.price}\n"
    description = "**Wprowadź nazwę produktu do wyszukania lub wybierz z listy znalezionych produktów:**\n\n"
    # Send embedded message
    embed = construct_embedded_message(field_name, field_price, description=description,
                                       footer='(w - wróć)')
    await message.channel.send(embed=embed)
    bot.g_state = 3


async def handle_state3(message: Message) -> None:
    """List of products or search result panel shown"""
    # Check for the number choice
    if message.content.isnumeric():
        msg_int = int(message.content)
        items = bot.g_data[0].categories[bot.g_bundle['category_id']].items
        if msg_int in range(1, min(rows_limit, len(items)) + 1):
            # Search for similar product in all shops
            if bot.g_bundle.get('items_search', None):
                picked_name = bot.g_bundle['items_search'][msg_int - 1].name
            else:
                picked_name = items[msg_int - 1].name
            s_id_to_i_id = {}
            for s_counter, s in enumerate(list(bot.g_data)):
                i_id_to_score = {}
                max_i_id = 0
                for i_counter, i in enumerate(s.categories[bot.g_bundle['category_id']].items):
                    smp = simple_match_percentage(picked_name.lower(), i.name.lower())
                    ldp = levenshtein_distance_percentage(picked_name.lower(), i.name.lower())
                    lcsp = longest_common_substring_percentage(picked_name.lower(), i.name.lower())
                    score = 25 * smp + 5 * ldp + 70 * lcsp
                    i_id_to_score[i_counter] = score
                    max_i_id = max(i_id_to_score, key=i_id_to_score.get)
                max_score = i_id_to_score.get(max_i_id, 0)
                # print(bot.g_data[s_counter].categories[bot.g_bundle['category_id']].items[max_i_id])
                # print(max_score)
                if max_score >= required_score:
                    s_id_to_i_id[s_counter] = max_i_id
            # Check if there are any results (should be at least 1 from the origin)
            if s_id_to_i_id:
                # Sort dict by price
                s_id_to_i_id_sorted = dict(sorted(
                    s_id_to_i_id.items(),
                    key=lambda x: bot.g_data[x[0]].categories[bot.g_bundle['category_id']].items[x[1]].price)
                )
                # Make description
                description = "**Znalezione produkty:**\n\n"
                counter = 1
                for s_id, i_id in s_id_to_i_id_sorted.items():
                    item = bot.g_data[s_id].categories[bot.g_bundle['category_id']].items[i_id]
                    shop = bot.g_data[s_id]
                    description += f"{counter}.{shop.name.capitalize()}\n" \
                                   f"{item.name}\n" \
                                   f"{item.price}\n" \
                                   f"{item.link}\n\n"
                    counter += 1
                # Send embedded message
                embed = construct_embedded_message(description=description, footer='(w - wróć)')
                await message.channel.send(embed=embed)

            # Change state of the Bot
            bot.g_state = 4
        else:
            await message.channel.send("Wybrano nieprawidłową liczbę.")
    # Check for the text choice
    else:
        await handle_state2(message)


async def handle_state4(message: Message) -> None:
    """Individual product panel shown"""
    # TODO
    pass


def construct_embedded_message(*fields: str, title: str = 'Ceny produktów', description: str = '', footer: str = '',
                               colour: int = 0x00c09a) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        colour=discord.Colour(colour),
        description=description,
    )
    for f in fields:
        embed.add_field(name="", value=f, inline=True)
    embed.set_footer(text=footer)
    return embed


def simple_match_percentage(s1: str, s2: str) -> float:
    """Computes the simple comparison of s1 and s2"""
    assert min(len(s1), len(s2)) > 0, "One of the given string is empty"
    s1_split = s1.split(" ")
    result = [1 for x in s1_split if x in s2]
    return len(result) / len(s1_split)


def longest_common_substring(s1: str, s2: str) -> str:
    """Computes the longest common substring of s1 and s2"""
    seq_matcher = SequenceMatcher(isjunk=None, a=s1, b=s2)
    match = seq_matcher.find_longest_match(0, len(s1), 0, len(s2))

    if match.size:
        return s1[match.a: match.a + match.size]
    else:
        return ""


def longest_common_substring_percentage(s1: str, s2: str) -> float:
    """Computes the longest common substring percentage of s1 and s2"""
    assert min(len(s1), len(s2)) > 0, "One of the given string is empty"
    return len(longest_common_substring(s1, s2)) / min(len(s1), len(s2))


def levenshtein_distance_percentage(s1: str, s2: str) -> float:
    """Computes the Levenshtein distance"""
    assert min(len(s1), len(s2)) > 0, "One of the given string is empty"
    return 1. - distance(s1, s2) / max(len(s1), len(s2))


bot.run(TOKEN)
