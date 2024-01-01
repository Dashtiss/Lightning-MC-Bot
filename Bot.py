import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import difflib
from discord.ui import Button, View

CommitNumber = "1"

# Sets up all the variables
lastNumber = 0
HighestNumber = 0
HasHitHighest = False
lastUsers = ""
UsersButtonPushed = {}
# Load or create UsersButtonPushed dictionary from a JSON file
if os.path.exists("saves.json"):
    with open("saves.json", "r") as file:
        saves = json.load(file)
        lastNumber = saves["LastNumber"]
        HighestNumber = saves["HighestNumber"]
        lastUsers = saves["LastUser"]
        UsersButtonPushed = saves["UsersButtonPushed"]
# Set up Discord intents for specific events
intents = discord.Intents.default()
intents.message_content = True

# Load environment variables from .env file
load_dotenv()

# Enumerate channel types
Types = discord.ChannelType

# List to store words
words = []

# Dictionary to store Discord text channels by name
DiscordTextChannels = {
    'staff-chat': 1010722709354844230,
    'admin-stuff': 1138990105386819724,
    'bots': 1011794713361260544,
    "clickertest": 1190345552978776094
    # Add more channels as needed
}


def GetText() -> str:
    """
    Generate a string with user button press information.

    Returns:
    - str: User button press information.
    """
    text = ""
    for key, value in UsersButtonPushed.items():
        text += f"{key} has pressed the button {value} {'times' if value > 1 else 'time'}\n"
    return text


class CounterButton(Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label='Click me!')
        self.count = 0

    async def callback(self, interaction: discord.Interaction):
        global UsersButtonPushed
        user_who_pressed = interaction.user
        try:
            UsersButtonPushed[str(user_who_pressed.name)] += 1
        except KeyError:
            UsersButtonPushed[str(user_who_pressed.name)] = 1
        text = GetText()
        text += f"{user_who_pressed.mention} pressed the button last"
        await interaction.response.edit_message(
            content=text,
            view=self.view)


class CounterView(View):
    def __init__(self):
        super().__init__()
        self.add_item(CounterButton())


def CheckName(message: str):
    """
    Check if the message starts with specific prefixes indicating different roles.

    Args:
    - message (str): The message content.

    Returns:
    - bool: True if the message starts with specific prefixes, False otherwise.
    """
    prefixes = ["[Member]", "[Admin]", "[VIP]", "[MVP]", "[Owner]"]
    return any(message.startswith(prefix) for prefix in prefixes)


def is_similar_to_word(word, word_list, threshold=0.8):
    """
    Check if a word is similar to any word in a list using Ratcliff/Obershelp similarity.

    Parameters:
        word (str): The word to check for similarity.
        word_list (list): The list of words to compare against.
        threshold (float): The similarity threshold. Defaults to 0.8.

    Returns:
        bool: True if a similar word is found, False otherwise.
    """
    for existing_word in word_list:
        similarity = difflib.SequenceMatcher(None, word, existing_word).ratio()
        if similarity >= threshold:
            return True

    return False


# Initialize the custom client with intents
client = commands.Bot(intents=intents, command_prefix="!")


@client.event
async def on_ready():
    """
    Event handler when the bot is ready.

    Prints information about connected servers and channels.
    """
    print(f'{client.user} has connected to Discord!     {client.status}')
    game = discord.Game("Galaxysten is cool")
    await client.change_presence(status=discord.Status.idle, activity=game)
    await client.add_cog(HelpCog(client))
    botschannel = client.get_channel(DiscordTextChannels["bots"])
    embed = discord.Embed(
        title="Hit the Highest",
        description=f"Checks\nIs Testing: ✅\nIs Online: ✅",
        color=0x58fe75  # You can customize the color using hexadecimal
    )
    await botschannel.send(content=f"{client.user.name} is online")
    await botschannel.send(embed=embed)

    for guild in client.guilds:
        print("Server: ", end="")
        print(guild)
        print("Users: ", end="")
        print("User count: ", end="")
        print(int(guild.member_count))
        print("Is lightningMC: ", end="")
        print(guild.name == "LightningMC")

        channel = guild.get_channel(DiscordTextChannels["clickertest"])
        async for message in channel.history(limit=100):
            await message.delete()
        counter_view = CounterView()
        message = await channel.send(GetText(), view=counter_view)
        counter_view.message = message


@client.event
async def on_message(message):
    try:
        if str(message.content).startswith("!"):
            msg = str(message.content)
            if msg.startswith("!help"):
                pass
            elif msg.startswith("!check-api"):
                import requests
            elif msg.startswith("!clearbutton"):
                global UsersButtonPushed
                await message.channel.send("Clearing Button")
                UsersButtonPushed = {}

        if str(message.author) == "LightningMC-Survival#5428":
            if CheckName(str(message.content)):
                Player = message.content.split(":")[0].split(" ")[1]
                Player.replace("\\", "")
                for word in message.content.split():
                    if is_similar_to_word(word.lower(), words, threshold=0.88):
                        staff_chat_channel = message.guild.get_channel(
                            DiscordTextChannels.get("bots"))
                        if staff_chat_channel:
                            embed = discord.Embed(
                                title="Chat Message Warn",
                                description=f"Chat Message Warn:\nPlayer: {Player}\nMessage Content: {str(message.content).split(': ')[1]}",
                                color=0x78bef9  # You can customize the color using hexadecimal
                            )
                            await staff_chat_channel.send(
                                embed=embed)
                            print(
                                f"Chat Message Warn:\nPlayer: {Player}\nMessage Content: {message.content}")
                            await message.delete()
                            break
                        else:
                            print("Error: 'staff-chat' channel not found.")
    except Exception as E:
        staff_chat_channel = message.guild.get_channel(
            DiscordTextChannels.get("bots"))
        if staff_chat_channel:
            embed = discord.Embed(
                title="Error Has happened",
                description=f"Error: {E}\n\nArgs: {E.args}",
                color=0xff0000  # You can customize the color using hexadecimal
            )
            await staff_chat_channel.send(
                embed=embed)
            print(
                f"Error: {E}\n\nArgs: {E.args}")


@client.event
async def on_message(message):
    global lastNumber, lastUsers, HasHitHighest, HighestNumber
    if message.channel.name == "count":
        try:
            number = int(str(message.content))
        except ValueError:
            return
        if number - 1 == lastNumber and str(message.author.name) != lastUsers:
            await message.add_reaction('✅')

            lastNumber = number
            if lastNumber > HighestNumber:
                if not HasHitHighest:
                    embed = discord.Embed(
                        title="Hit the Highest",
                        description=f"Yall have hit the highest number on this server",
                        color=0x58fe75  # You can customize the color using hexadecimal
                    )
                    await message.channel.send(embed=embed)
                    HasHitHighest = True
                HighestNumber = number

            lastUsers = str(message.author.name)
        elif str(message.author.name) == lastUsers:

            await message.add_reaction('❌')
            embed = discord.Embed(
                title="Only one at a time.",
                description=f"Players can only go one time and have to wait for another person to go\nUser {message.author.mention} messed up,restarting",
                color=0xff0000  # You can customize the color using hexadecimal
            )
            await message.channel.send(embed=embed)
            lastNumber = 0
            lastUsers = ""
            HasHitHighest = False
        elif number - 1 > lastNumber or number - 1 < lastNumber:

            await message.add_reaction('❌')
            embed = discord.Embed(
                title="Number wasn't synchronized",
                description=f"The numbers didn't add up\nUser {message.author.mention} messed up, restarting",
                color=0xff0000  # You can customize the color using hexadecimal
            )
            await message.channel.send(embed=embed)
            lastNumber = 0
            lastUsers = ""
            HasHitHighest = False


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def test_command(self, ctx):
        """test command"""
        print("got message")
        # Create a message with bot information
        help_message = "Hello! I'm your cool bot. Here are some commands:\n\n" \
                       "!help - Get information about the bot\n" \
                       "!ping - Check the bot's latency\n" \
                       "!your_command - Your custom command\n"

        # Send the help message as a private message
        await ctx.author.send(help_message)

def Run():
    global words
    try:
        # Get the bot token from the environment variables
        bot_token = os.getenv('TOKEN')

        if not bot_token:
            print("Bot token not found. Please make sure to set it as an environment variable.")
        else:
            print('Loading Words')
            # Load words from a JSON file
            with open("words.json", "r") as file:
                words = json.load(file)
            print(f'Finished loading all {len(words)} words')
            # Run the bot with the token
            client.run(bot_token)
            with open("saves.json", "w") as file:
                code = {"LastNumber": lastNumber, "LastUser": lastUsers, "HighestNumber": HighestNumber,
                        "UsersButtonPushed": UsersButtonPushed}
                json.dump(code, file)
    except KeyboardInterrupt:
        with open("saves.json", "w") as file:
            code = {"LastNumber": lastNumber, "LastUser": lastUsers, "HighestNumber": HighestNumber,
                    "UsersButtonPushed": UsersButtonPushed}
            json.dump(code, file)


if __name__ == "__main__":
    Run()