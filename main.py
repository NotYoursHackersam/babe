import os
import discord
import asyncio
from discord import app_commands
from abilities import apply_sqlite_migrations

from models import Base, engine


def generate_oauth_link(client_id):
    base_url = "https://discord.com/api/oauth2/authorize"
    redirect_uri = "http://localhost"
    scope = "bot"
    permissions = "8"  # Administrator permission for simplicity, adjust as needed.
    return f"{base_url}?client_id={client_id}&permissions={permissions}&scope={scope}"

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents, activity=discord.CustomActivity("Watching Nexus Sanctuary"))
tree = app_commands.CommandTree(bot)

# Prefix for commands
PREFIX = "!"

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
        
    if message.content.startswith(PREFIX + "embed"):
        # Check for allowed role
        allowed_role_id = os.environ.get('ALLOWED_ROLE_ID')
        if not allowed_role_id:
            await message.channel.send("<a:cross:1340593448142635068> Bot configuration error: ALLOWED_ROLE_ID not set.")
            return
            
        try:
            allowed_role_id = int(allowed_role_id)
        except ValueError:
            await message.channel.send("<a:cross:1340593448142635068> Invalid ALLOWED_ROLE_ID configuration.")
            return
            
        if not any(role.id == allowed_role_id for role in message.author.roles):
            await message.channel.send("<a:cross:1340593448142635068> You do not have permission to use this command.")
            return
            
        # Parse the command content
        content = message.content[len(PREFIX + "embed"):].strip()
        if not content:
            await message.channel.send("<a:cross:1340593448142635068> Please provide content for the embed.")
            return
            
        # Check for custom color
        color_match = content.split(" ", 1)
        embed_color = 0x00ff00  # Default green color
        title = None
        footer = None
        
        # Check for color
        if len(color_match) > 1 and color_match[0].lower() == "color:":
            try:
                color_name = color_match[1].split(" ", 1)[0].lower()
                color_map = {
                    "red": 0xFF0000,
                    "green": 0x00FF00,
                    "blue": 0x0000FF,
                    "yellow": 0xFFFF00,
                    "purple": 0x800080,
                    "orange": 0xFFA500,
                    "pink": 0xFFC0CB,
                    "cyan": 0x00FFFF,
                    "magenta": 0xFF00FF
                }
                embed_color = color_map.get(color_name, 0x00ff00)
                content = " ".join(color_match[1].split(" ", 1)[1:]) if len(color_match[1].split(" ", 1)) > 1 else ""
            except Exception:
                embed_color = 0x00ff00
        
        # Check for title
        title_match = [part for part in content.split() if part.startswith("title:")]
        if title_match:
            title_part = title_match[0]
            title = content[content.index(title_part) + len(title_part):].split("/")[0].strip()
            content = content.replace(f"{title_part} {title}/", "").strip()
        
        # Check for footer
        footer_match = [part for part in content.split() if part.startswith("footer:")]
        if footer_match:
            footer_part = footer_match[0]
            footer = content[content.index(footer_part) + len(footer_part):].split("/")[0].strip()
            content = content.replace(f"{footer_part} {footer}/", "").strip()
        
        # Create and send embed
        embed = discord.Embed(description=content, color=embed_color)
        if title:
            embed.title = title
        if footer:
            embed.set_footer(text=footer)
        await message.channel.send(embed=embed)
        
        # Try to delete the original command message
        try:
            await message.delete()
        except discord.errors.Forbidden:
            await message.channel.send("<a:warn:1340593913517309982> Could not delete the original message. Ensure bot has message management permissions.")
    
    # New purge command
    if message.content.startswith(PREFIX + "purge"):
        # Check for allowed role
        allowed_role_id = os.environ.get('ALLOWED_ROLE_ID')
        if not allowed_role_id:
            await message.channel.send("<a:cross:1340593448142635068> Bot configuration error: ALLOWED_ROLE_ID not set.")
            return
            
        try:
            allowed_role_id = int(allowed_role_id)
        except ValueError:
            await message.channel.send("<a:cross:1340593448142635068> Invalid ALLOWED_ROLE_ID configuration.")
            return
            
        if not any(role.id == allowed_role_id for role in message.author.roles):
            await message.channel.send("<a:cross:1340593448142635068> You do not have permission to use this command.")
            return
        
        # Parse the number of messages to delete
        try:
            num_messages = int(message.content.split()[1])
        except (IndexError, ValueError):
            await message.channel.send("<a:cross:1340593448142635068> Please specify a valid number of messages to purge.")
            return
        
        # Delete messages
        try:
            # Delete the command message and the specified number of messages before it
            deleted_messages = await message.channel.purge(limit=num_messages + 1)
            
            # Send a temporary confirmation message
            confirm_msg = await message.channel.send(f"<a:tic:1340605623729000460> Deleted {len(deleted_messages) - 1} messages.")
            
            # Delete the confirmation message after 5 seconds
            await asyncio.sleep(5)
            await confirm_msg.delete()
        except discord.errors.Forbidden:
            await message.channel.send("<a:cross:1340593448142635068> I do not have permission to delete messages.")

@tree.command(name='say')
async def say_command(interaction: discord.Interaction, message: str):
    """Send a private message

    Parameters
    ----------
    message : str
        The message to send privately"""
    allowed_role_id = os.environ.get('ALLOWED_ROLE_ID')
    
    if not allowed_role_id:
        await interaction.response.send_message("<a:cross:1340593448142635068> Bot configuration error: ALLOWED_ROLE_ID not set.", ephemeral=True)
        return
    
    # Convert allowed_role_id to integer
    try:
        allowed_role_id = int(allowed_role_id)
    except ValueError:
        await interaction.response.send_message("<a:cross:1340593448142635068> Invalid ALLOWED_ROLE_ID configuration.", ephemeral=True)
        return
    
    # Check if user has the required role
    if not any(role.id == allowed_role_id for role in interaction.user.roles):
        await interaction.response.send_message("<a:cross:1340593448142635068> You do not have permission to use this command.", ephemeral=True)
        return
    
    # Send private message
    try:
        await interaction.user.send(message)
        await interaction.response.send_message("<a:tic:1340605623729000460> Message sent privately.", ephemeral=True)
    except discord.errors.Forbidden:
        await interaction.response.send_message("<a:cross:1340593448142635068> Could not send private message. Check your privacy settings.", ephemeral=True)

def main():
    # Track AFK users with a dictionary
    afk_users = {}

    # Handle AFK mentions and removal
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
            
        # Check if AFK user sends a message
        if message.author.id in afk_users:
            afk_status = afk_users[message.author.id]
            del afk_users[message.author.id]
            await message.channel.send(f"<a:tic:1340605623729000460> Welcome back {message.author.mention}! Your **AFK** status has been removed.")
            
        # Check if message mentions any AFK users    
        for mention in message.mentions:
            if mention.id in afk_users:
                await message.channel.send(f"<a:tic:1340605623729000460> {mention.name} is **AFK**: {afk_users[mention.id]}")
                
        # Handle commands
        if message.content.startswith(PREFIX + "afk"):
            # Check for allowed role
            allowed_role_id = os.environ.get('ALLOWED_ROLE_ID')
            if not allowed_role_id:
                await message.channel.send("<a:cross:1340593448142635068> Bot configuration error: ALLOWED_ROLE_ID not set.")
                return
                
            try:
                allowed_role_id = int(allowed_role_id)
            except ValueError:
                await message.channel.send("<a:cross:1340593448142635068> Invalid ALLOWED_ROLE_ID configuration.")
                return
                
            if not any(role.id == allowed_role_id for role in message.author.roles):
                await message.channel.send("<a:cross:1340593448142635068> You do not have permission to use this command.")
                return
            
            # Extract AFK message
            afk_message = message.content[len(PREFIX + "afk"):].strip()
            
            # Set AFK status
            afk_users[message.author.id] = afk_message if afk_message else "Away"
            
            # Confirm AFK status
            await message.channel.send(f"<a:tic:1340605623729000460> **AFK** set to: {afk_users[message.author.id]}")
            
    # Slash command for AFK
    @tree.command(name='afk')
    async def afk_command(interaction: discord.Interaction, message: str = None):
        """Set your AFK status
        
        Parameters
        ----------
        message : str
            Optional AFK message"""
        
        allowed_role_id = os.environ.get('ALLOWED_ROLE_ID')
        if not allowed_role_id:
            await interaction.response.send_message("<a:cross:1340593448142635068> Bot configuration error: ALLOWED_ROLE_ID not set.", ephemeral=True)
            return
            
        try:
            allowed_role_id = int(allowed_role_id)
        except ValueError:
            await interaction.response.send_message("<a:cross:1340593448142635068> Invalid ALLOWED_ROLE_ID configuration.", ephemeral=True)
            return
            
        if not any(role.id == allowed_role_id for role in interaction.user.roles):
            await interaction.response.send_message("<a:cross:1340593448142635068> You do not have permission to use this command.", ephemeral=True)
            return
            
        # Set AFK status
        afk_users[interaction.user.id] = message if message else "Away"
        
        # Confirm AFK status
        await interaction.response.send_message(f"<a:tic:1340605623729000460> **AFK** set to: {afk_users[interaction.user.id]}")
            

    client_id = os.environ.get('CLIENT_ID')
    bot_token = os.environ.get('BOT_TOKEN')
    allowed_role_id = os.environ.get('ALLOWED_ROLE_ID')
    
    if not client_id and not bot_token:
        print("🚨 Oops! Both CLIENT_ID 🆔 and BOT_TOKEN 🔑 environment variables are missing. 🚨")
    elif not client_id:
        print("🚨 Oops! The CLIENT_ID 🆔 environment variable is missing. 🚨")
    elif not bot_token:
        print("🚨 Oops! The BOT_TOKEN 🔑 environment variable is missing. 🚨")
    elif not allowed_role_id:
        print("🚨 Oops! The ALLOWED_ROLE_ID 🛡️ environment variable is missing. 🚨")
    
    if not client_id or not bot_token or not allowed_role_id:
        print("Let's fix that together! 😊 Here's how:\n" +
              "1. 🌐 Go to the Discord Developer Portal. 🌐\n" +
              "2. 🆕 Create a new application and navigate to the 'Bot' section. 🤖\n" +
              "3. ➕ Click 'Add Bot' and confirm by clicking 'Yes, do it!'. ✅\n" +
              "4. 📋 Under the 'TOKEN' section, click 'Copy' to get your BOT_TOKEN. 🔑\n" +
              "5. 📋 Navigate to the 'OAuth2' section, under 'CLIENT ID', click 'Copy' to get your CLIENT_ID. 🆔\n" +
              "6. 🔐 Set these values in the Env Secrets tab. 🔐\n" +
              "7. 🤖 If your bot will have any ability to read/reply to messages, then under the 'BOT' section, enable the slider titled 'Message Content Intent' ✅\n" +
              "8. 🛡️ Find the role ID for the allowed role in your Discord server settings. 🛡️\n" +
              "For bot permissions, it's recommended to start with basic permissions and adjust as needed for your app's functionality. Let's make your bot awesome! 🚀")
        return
    
    oauth_link = generate_oauth_link(client_id)
    print(f"🔗 Click this link to invite your Discord bot to your server 👉 {oauth_link}")
    bot.run(bot_token)

if __name__ == "__main__":
    main()
