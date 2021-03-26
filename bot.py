import os
import discord
import logging
import aiofiles
from dotenv import load_dotenv
from discord.ext import commands
from quote import generate_quote
import uuid


# set up logging for the bot
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter((logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')))
logger.addHandler(handler)


# load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv('DISCORD_GUILD')

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='?', intents=intents)
bot.warnings = {}

for guild in bot.guilds:
        bot.warnings[guild.id] = {}

        with aiofiles.open(f"{guild.id}.txt", mode="a") as temp:
            pass

        with aiofiles.open(f"{guild.id}.txt", mode="r") as file:
            lines = file.readlines()

            for line in lines:
                data = line.split(" ")
                warning_id = (data[0])
                member_id = int(data[1])
                admin_id = int(data[2])
                reason = " ".join(data[3:]).strip("\n")

                try:
                    bot.warnings[guild.id][member_id][0] += 1
                    bot.warnings[guild.id][member_id][1].append((warning_id, admin_id, reason))

                except KeyError:
                    bot.warnings[guild.id][member_id] = [1, [(warning_id, admin_id, reason)]]

@bot.event
async def on_ready():

    print(bot.user.name + " is ready.")


@bot.event
async def on_guild_join(guild):
    bot.warnings[guild.id] = {}




# quote generator
@bot.command(aliases=['quote', 'randomquote', 'qu'], help='Responds with a random quote')
async def quote_gen(ctx):
    response = generate_quote()
    await ctx.send(response)


# moderation commands

# ban command
@bot.command(name='ban', help='Bans a member.')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason="No reason given"):
    try:
        if member == ctx.message.author:
            await ctx.send('Can not ban yourself.')
            return
        if member is None:
            await ctx.send('A member must be specified.')
            return
        else:
            message = f'You have been banned form {ctx.guild.name} for {reason}'
            em = discord.Embed(title=f"Banned {member}!", description=f"Reason: {reason} By: {ctx.author.mention}")
            await member.send(message)
            await ctx.channel.send(embed=em)
            await member.ban(reason=reason)
    except:
        await ctx.send(f'Error in banning {member} from the server.')


# unbans a user
@bot.command(name='unban', help='Unbans a member.')
@commands.has_permissions(ban_members=True)
async def unban(ctx, *, member):
    try:
        x = int(member)
        banned_users = await ctx.guild.bans()

        for ban_entry in banned_users:
            user = ban_entry.user
            if user.id == x:
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.mention}')
                return

    except ValueError:
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split("#")
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'Unbanned {user.mention}')
                return


# kick command
@bot.command(name='kick', help='Kicks a member.')
@commands.has_permissions(kick_members=True)
async def kick_member(ctx, member: discord.Member = None, *, reason="No reason given"):
    try:
        if member == ctx.message.author:
            await ctx.send('Can not kick yourself.')
            return
        if member is None:
            await ctx.send('A member must be specified.')
            return
        else:
            message = f'You have been kicked form {ctx.guild.name} for {reason}'
            em = discord.Embed(title=f"Kicked {member.mention}!",
                               description=f"Reason: {reason} By: {ctx.author.mention}")
            await member.send(message)
            await ctx.channel.send(embed=em)
            await member.kick(reason=reason)
    except:
        await ctx.send(f'Error in kicking {member} from the server.')


@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member = None, *, reason=None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    if reason is None:
        return await ctx.send("Please provide a reason for warning this user.")

    try:
        warn_id = str(uuid.uuid4())
        first_warning = False
        bot.warnings[ctx.guild.id][member.id][0] += 1
        bot.warnings[ctx.guild.id][member.id][1].append((warn_id, ctx.author.id, reason))

    except KeyError:
        warn_id = str(uuid.uuid4())
        first_warning = True
        bot.warnings[ctx.guild.id][member.id] = [1, [(warn_id, ctx.author.id, reason)]]

    count = bot.warnings[ctx.guild.id][member.id][0]

    async with aiofiles.open(f"{ctx.guild.id}.txt", mode="a") as file:
        await file.write(f"{warn_id} {member.id} {ctx.author.id} {reason}\n")
    await ctx.send(f"{member.mention} has {count} {'warning' if first_warning else 'warnings'}.")
    await ctx.send(bot.warnings)


@bot.command()
@commands.has_permissions(administrator=True)
async def warnings(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send("The provided member could not be found or you forgot to provide one.")

    embed = discord.Embed(title=f"Displaying Warnings for {member.name}", description="", colour=discord.Colour.red())
    try:

        for i in bot.warnings[ctx.guild.id][member.id][1]:
            warn_id = i[0]
            admin_id = i[1]
            reason = i[2:]
            admin = ctx.guild.get_member(admin_id)
            embed.description +=  f"ID: {warn_id} | {admin.mention}\n {reason}\n"

        await ctx.send(embed=embed)
        await ctx.send(bot.warnings)

    except KeyError:  # no warnings
        await ctx.send("This user has no warnings.")


# random functions
@bot.command(aliases=['av', 'avatar', 'AV', 'Av', 'AVATAR'], help='Shows your avatar.')
async def show_avatar(ctx, *, member: discord.Member = None):
    # if there was no user specified then return the avatar of the message author
    if member is None:
        name = ctx.author.name
        show_av = discord.Embed(

            title=name,
            color=discord.Color.dark_blue()
        )
        show_av.set_image(url=f'{ctx.author.avatar_url}')
        await ctx.send(embed=show_av)
    # if the member was specified then return the avatar of the
    else:
        name = member.name
        show_av = discord.Embed(

            title=name,
            color=discord.Color.dark_blue()
        )
        show_av.set_image(url=f'{member.avatar_url}')
        await ctx.send(embed=show_av)


@bot.command(name='ping', help='Shows the ping.')
async def show_ping(ctx):
    p = round(bot.latency, 4) * 1000
    await ctx.send(f'{p}ms')


# channel creation/deletion functions
@bot.command(aliases=['crch', 'create-channel', 'create-ch'],
             help='Allows you to create text channels\n takes channel name as the input.')
@commands.has_permissions(administrator=True)
async def create_text_channel(ctx, channel_name):
    # get the existing channels
    existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    # check if the name of the channel is passed as a arg
    if channel_name is None:
        await ctx.send('A channel name is required.')
    # if the channel does not exist already then create one
    if not existing_channel:
        await ctx.send(f'New channel created named:  {channel_name}')
        await ctx.guild.create_text_channel(channel_name)
    # if it already exists tell the member that it does
    else:
        await ctx.send(f'{channel_name} already exits.')


@bot.command(aliases=['dlch', 'delete-channel', 'delete-ch'],
             help='Allows you to delete text channels\n takes channel name as the input.')
@commands.has_permissions(administrator=True)
async def delete_channel(ctx, channel_name):
    # check is the channel that is entered exists
    existing_channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if channel_name is None:
        await ctx.send('A channel name is required.')
    # if it exists delete it
    if existing_channel is not None:
        await existing_channel.delete()
        await ctx.send(f'{channel_name} was deleted.')
    # if it does not exist inform the user
    else:
        await ctx.send(f'{channel_name} could not be found.')


# error handling
@create_text_channel.error
async def channel_create_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Sorry you do not have the required permissions to create channels.')


@delete_channel.error
async def delete_channel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('Sorry you do not have the required permissions to delete channels.')


@show_avatar.error
async def show_avatar_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('User can not be found.')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        text = 'The command that was entered was not found.'
        await ctx.send(text)
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You dont have all the requirements.")


bot.run(TOKEN)
