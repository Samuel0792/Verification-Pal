import discord
from discord import app_commands
from discord.ext import tasks
from flask import Flask, request, jsonify
import requests
import random
import json
from threading import Thread
from datetime import datetime, timedelta
import asyncio
from pyngrok import ngrok

TOKEN = "MTMwODU1MTkxMDQxMTg2MjA4Ng.GzvKbE.P_xAHnP_VSGKpi3NZUzBW873Su3qt-8tWt8L0w"

app = Flask(__name__)

intents = discord.Intents.default()
intents.guilds = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

UPLAND_VISITORS_API = "https://api.upland.me/teleports/visitors"
VERIFICATION_CODES = {}
TEST_VISITORS = {}

PROPERTY_NAME = "2474 Poett LN,  Santa Clara"

PROPERTIES = {
    "2474 Poett LN Santa Clara": "79291993431780",
    "1931 Cyril Ave Los Angeles": "77237304754523",
    "2150 Thelma Ave Los Angeles": "77239620010441",
    "13 AV DE LA METALLURGIE Saint Denis": "86478550195604",
    "4424 N Indiana Ave Kansas City": "80418131248833",
    "6400 Miller Detroit": "82419821088913",
    "2826 S Wabash Chicago": "82078840845593",
    "600 Dekalb Brooklyn": "81361984391288",
    "13111 Atlantic Ave Queens": "81365373392682",
    "Avenida Rodrigues Alves 8B Rio De Janeiro": "41778007204261",
    "443 Burnett Ave San Francisco": "79533971194646",
    "2075 De La Cruz Blvd Santa Clara": "79289443295838" ,
    "3420 Bronx Blvd Bronx": "81475348033274",
    "26 West Side Rd Bermuda": "76137090193204",
    "300 Kensal Road London": "88107751789432",
    "740 Six Flags Arlington": "76420540234143",
    "1000 NW 42nd AVE Miami": "72080291977915",
    "6919 Bay Drive Miami Beach": "72125422690791",
    "1286 Emerald Bay Rd Lake Tahoe": "80249653719765",
    "40 Arden St Manhattan": "81468670699694",
    "29 Pass Jouffroy Paris": "86455498305359",
    "2704 Coffee Pot Ct Las Vegas": "78560171499074",
    "5938 Music Street New Orleans": "74718928182236",
    "1-Chome-2-5 Shirokanedai Tokyo": "78216967695526",
    "6312 La Vista Dr Dallas": "76456913248235",
    "610 E Naples Dr Las Vegas": "78507709147261",
    "3940 Martin Luther King Jr Drive Cleveland": "81835185520465",
    "Avenida Santa Fe 1860 Buenos Aires": "34492114317968",
}

@app.route("/")
def home():
    return "Bot is running!"


@bot.event
async def on_ready():
    await tree.sync()
    print(f'Logged in as {bot.user} and slash commands synced.')

def get_visitors(property_id: str):
    """
    Fetch visitors from simulated data (for testing) or actual API.
    """
    if property_id in TEST_VISITORS:
        return [{"username": ign} for ign in TEST_VISITORS[property_id]]

    headers = {'User-Agent': 'DiscordBot Verification'}
    response = requests.get(f"{UPLAND_VISITORS_API}/{property_id}", headers=headers)
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print("Error parsing visitors JSON")
    return []


@tree.command(name="verify", description="List all properties available for verification.")
async def verify(interaction: discord.Interaction):
    """
    Lists all properties sorted alphabetically by the first letter of the property address, ignoring numbers.
    """
    
    sorted_properties = sorted(
        PROPERTIES.keys(),
        key=lambda x: next((char for char in x if char.isalpha()), "").lower()
    )
    properties_list = "\n".join([f"- **{address}**" for address in sorted_properties])

    await interaction.response.send_message(
        f"🌟 **Available Properties for Verification (Alphabetical):**\n"
        f"{properties_list}\n\n"
        "Use `/verifyign [ign] [property_address]` to verify if you've visited a property. 🏡"
    )

@tree.command(name="verifyign", description="Verify if your IGN has visited a specific property.")
async def verify_ign(interaction: discord.Interaction, ign: str, property_address: str = None):
    """
    Verifies if a user with the given IGN has visited a property.
    If no property is provided, displays an error message and instructions.
    """
    if property_address is None or property_address not in PROPERTIES:
        
        properties_list = "\n".join([f"- **{address}**" for address in PROPERTIES.keys()])
        await interaction.response.send_message(
            f"❌ **Invalid or Missing Property Address!**\n"
            f"Here’s the list of valid properties:\n\n{properties_list}\n\n"
            "Please use /verifyign [ign] [property_address] to verify your IGN. 🏡"
        )
        return

    
    property_id = PROPERTIES[property_address]

    
    visitors = get_visitors(property_id)
    matching_visitors = [v for v in visitors if v.get("username") == ign]

    if matching_visitors:
        
        VERIFICATION_CODES[interaction.user.id] = str(random.randint(100000, 999999))
        await interaction.user.send(
            f"🌟 **Well done, {interaction.user.name}!**\n"
            f"You’ve visited **{property_address}** 🏡 and qualified for access.\n"
            f"Your unique verification code is: **{VERIFICATION_CODES[interaction.user.id]}**\n"
            "Submit this code using /submitcode in the main channel to gain access to the exclusive area! 🎉"
        )
        await interaction.response.send_message(
            f"✅ {interaction.user.mention}, check your DMs for your verification code! 📩"
        )
    else:
        await interaction.response.send_message(
            f"🚫 **Oh no, {interaction.user.name}!**\n"
            f"You haven’t visited **{property_address}** yet! Make sure to stop by and try again. 🏡"
        )


@tree.command(name="submitcode", description="Submit your verification code to gain access.")
async def submit_code(interaction: discord.Interaction, code: str):
    """
    Allows users to submit their verification code to gain temporary access to a private channel.
    """
    user_id = interaction.user.id
    if user_id in VERIFICATION_CODES and VERIFICATION_CODES[user_id] == code:
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name="Verified")

        if role is None:
            try:
                role = await guild.create_role(name="Verified", reason="Role for verified users")
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ I don’t have permissions to create roles. Please check my `Manage Roles` access!"
                )
                return

        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"✅ **Access Granted!** 🎉\n"
                f"{interaction.user.mention}, you now have access to the exclusive area for the rest of the day! 🕒"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ I don’t have permissions to assign roles. Please check my role hierarchy and permissions!"
            )
            return

        channel = discord.utils.get(guild.channels, name="locked-channel")
        if channel:
            try:
                await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ I don’t have permissions to manage channel permissions. Please check my access!"
                )

        await remove_access_at_midnight(interaction, interaction.user, channel)
        del VERIFICATION_CODES[user_id]
    else:
        await interaction.response.send_message(
            "❌ **Invalid Code!**\n"
            "Double-check your code and try again, or request a new one with `/verifyign`. 📩"
        )

async def remove_access_at_midnight(interaction, user, channel):
    """
    Removes access to the locked channel at midnight of the current day.
    """
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    wait_time = (midnight - now).seconds

    await asyncio.sleep(wait_time)

    try:
        await user.remove_roles(discord.utils.get(interaction.guild.roles, name="Verified"))
        await channel.set_permissions(user, overwrite=None)
        await interaction.channel.send(
            f"⏳ **Time’s up, {user.name}!**\n"
            "Your access to the exclusive area has expired. 🚪\n"
            "Feel free to visit the property again and verify for access! 🏡"
        )
    except discord.Forbidden:
        await interaction.channel.send(
            "❌ I couldn’t update permissions. Please check my access!"
        )

def get_public_url(port=8080):
    try:
        # Fetch public IP address from ipify service
        response = requests.get("https://api.ipify.org?format=json")
        response.raise_for_status()
        public_ip = response.json().get("ip")

        if public_ip:
            public_url = f"http://{public_ip}:{port}"
            print(f"Public URL: {public_url}")
            return public_url
        else:
            print("Unable to fetch public IP address.")
            return None
    except requests.RequestException as e:
        print(f"Error fetching public IP address: {e}")
        return None

# Replace with your server's port number if it's different
get_public_url(port=8080)


def run_flask():
    app.run(host='0.0.0.0', port=8080)

def run_flask():
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    # Expose the Flask app to the public
    public_url = "http://127.0.0.1:8080"
    print("Public URL:", public_url)
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    bot.run(TOKEN)




