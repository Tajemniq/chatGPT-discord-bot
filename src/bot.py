import os
import asyncio
import discord
from src.log import logger
from random import randrange

from g4f.client import Client
from g4f.Provider import RetryProvider, OpenaiChat, FreeChatgpt, Gemini, Liaobots, Bing, Gemini

from src.aclient import discordClient
from discord import app_commands
from src import log, art, personas


def run_discord_bot():
    @discordClient.event
    async def on_ready():
        await discordClient.send_start_prompt()
        await discordClient.tree.sync()
        loop = asyncio.get_event_loop()
        loop.create_task(discordClient.process_messages())
        logger.info(f'{discordClient.user} już działa!')


    @discordClient.tree.command(name="chat", description="Porozmawiaj z ChatGPT")
    async def chat(interaction: discord.Interaction, *, message: str):
        if discordClient.is_replying_all == "True":
            await interaction.response.defer(ephemeral=False)
            await interaction.followup.send(
                "> **WARN: Jesteś już w trybie replyAll. Jeśli chcesz użyć polecenia Slash, przełącz się do trybu normalnego za pomocą polecenia `/replyall` **")
            logger.warning("\x1b[31mJesteś już w trybie replyAll, nie możesz użyć komendy slash!\x1b[0m")
            return
        if interaction.user == discordClient.user:
            return
        username = str(interaction.user)
        discordClient.current_channel = interaction.channel
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /chat [{message}] in ({discordClient.current_channel})")

        await discordClient.enqueue_message(interaction, message)


    @discordClient.tree.command(name="prywatny", description="Przełączanie trybu prywatnego")
    async def prywatny(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if not discordClient.isprywatny:
            discordClient.isprywatny = not discordClient.isprywatny
            logger.warning("\x1b[31mPrzejście do trybu prywatnego\x1b[0m")
            await interaction.followup.send(
                "> **INFO: Następnie odpowiedź zostanie wysłana w trybie prywatnym. Jeśli chcesz przełączyć się z powrotem do trybu publicznego, użyj `/publiczny`**")
        else:
            logger.info("Jesteś już w trybie prywatnym!")
            await interaction.followup.send(
                "> **WARN: Jesteś już w trybie prywatnym. Jeśli chcesz przełączyć się do trybu publicznego, użyj `/publiczny`**")


    @discordClient.tree.command(name="publiczny", description="Przełączanie dostępu publicznego")
    async def publiczny(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        if discordClient.isprywatny:
            discordClient.isprywatny = not discordClient.isprywatny
            await interaction.followup.send(
                "> **INFO: Następnie odpowiedź zostanie wysłana bezpośrednio na kanał. Jeśli chcesz przełączyć się z powrotem do trybu prywatnego, użyj `/prywatny`**")
            logger.warning("\x1b[31mSwitch to publiczny mode\x1b[0m")
        else:
            await interaction.followup.send(
                "> **WARN: Jesteś już w trybie publicznym. Jeśli chcesz przełączyć się do trybu prywatnego, użyj `/prywatny`**")
            logger.info("Jesteś już w trybie publicznym!")


    @discordClient.tree.command(name="replyall", description="Przełączanie dostępu replyAll")
    async def replyall(interaction: discord.Interaction):
        discordClient.replying_all_discord_channel_id = str(interaction.channel_id)
        await interaction.response.defer(ephemeral=False)
        if discordClient.is_replying_all == "True":
            discordClient.is_replying_all = "False"
            await interaction.followup.send(
                "> **INFO: Następnie bot odpowie na polecenie Slash. Jeśli chcesz przełączyć się z powrotem do trybu replyAll, użyj `/replyAll` again**")
            logger.warning("\x1b[31mPrzejście do trybu normalnego\x1b[0m")
        elif discordClient.is_replying_all == "False":
            discordClient.is_replying_all = "True"
            await interaction.followup.send(
                "> **INFO: Następnie bot wyłączy komendę Slash i będzie odpowiadał na wszystkie wiadomości tylko na tym kanale. Jeśli chcesz wrócić do normalnego trybu, użyj `/replyAll` **")
            logger.warning("\x1b[31mSwitch to replyAll mode\x1b[0m")


    @discordClient.tree.command(name="model-chatu", description="Przełączanie modelu czatu między 'gemeni' i 'gpt-4'")
    @app_commands.choices(model=[
        app_commands.Choice(name="gemeni", value="gemeni"),
        app_commands.Choice(name="gpt-4", value="gpt-4"),
    ])
    async def chat_model(interaction: discord.Interaction, model: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)
        try:
            if model.value == "gemeni":
                discordClient.reset_conversation_history()
                discordClient.chatBot = Client(provider=RetryProvider([Gemini, FreeChatgpt], shuffle=False))
                discordClient.chatModel = model.value
            elif model.value == "gpt-4":
                discordClient.reset_conversation_history()
                discordClient.chatBot = Client(provider=RetryProvider([Liaobots, OpenaiChat, Bing], shuffle=False))
                discordClient.chatModel = model.value

            await interaction.followup.send(f"> **INFO: Model czatu został przełączony na {model.name}.**")
            logger.info(f"Przełączono model czatu na {model.name}")

        except Exception as e:
            await interaction.followup.send(f'> **Błąd przełączania modelu: {e}**')
            logger.error(f"Błąd przełączania modelu: {e}")

    @discordClient.tree.command(name="reset", description="Całkowite zresetowanie historii konwersacji")
    async def reset(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        discordClient.conversation_history = []
        await interaction.followup.send("> **INFO: Zapomniałem o wszystkim.**")
        personas.current_persona = "standard"
        logger.warning(
            f"\x1b[31m{discordClient.chat_model} bot został pomyślnie zresetowany\x1b[0m")


    @discordClient.tree.command(name="help", description="Wyświetl komendy bota")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(""":star: **PODSTAWOWE POLECENIA** \n
        - `/chat [wiadomość]` Czat z ChatGPT(gpt-4)
        - `/wygeneruj [wartość][model]` Wygeneruj obraz z określonym modelem
        - `/switchpersona [persona]` Przełączanie między opcjonalnymi jailbreakami ChatGPT
                `dan`: DAN 13.5 (Najnowszy działający monit ChatGPT Jailbreak)
                `Smart mode`: AIM (Zawsze inteligentny i makiaweliczny)
                `Developer Mode`: programista specjalizujący się w obszarze sztucznej inteligencji
        - `/prywatny` ChatGPT przełącza się w tryb prywatny
        - `/publiczny` ChatGPT przełącza się w tryb publiczny
        - `/replyall` ChatGPT przełącza między trybem replyAll i trybem domyślnym
        - `/reset` Wyczyść historię konwersacji
        - `/model-chatu` Przełącz inny model czatu
                `gpt-4`: GPT-4 model
                `Gemini`: Google gemeni-pro model""")

        logger.info(
            "\x1b[31mKtoś potrzebuje pomocy!\x1b[0m")


    @discordClient.tree.command(name="wygeneruj", description="Generowanie obrazu przy użyciu modelu Dall-e-3")
    @app_commands.choices(model=[
        app_commands.Choice(name="gemeni", value="gemeni"),
        app_commands.Choice(name="openai", value="openai"),
        app_commands.Choice(name="bing", value="bing")
    ])
    async def wygeneruj(interaction: discord.Interaction, *, prompt: str, model: app_commands.Choice[str]):
        if interaction.user == discordClient.user:
            return

        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : /wygeneruj [{prompt}] w ({channel})")

        await interaction.response.defer(thinking=True, ephemeral=discordClient.isprywatny)
        try:
            image_url = await art.wygeneruj(model.value, prompt)

            await interaction.followup.send(image_url)

        except Exception as e:
            await interaction.followup.send(
                f'> Coś poszło nie tak, spróbuj później.\n\nKomunikat o błędzie:{e}')
            logger.info(f"\x1b[31m{username}\x1b[0m :{e}")

    @discordClient.tree.command(name="switchpersona", description="Przełączanie między opcjonalnymi jailbreakami chatGPT")
    @app_commands.choices(persona=[
        app_commands.Choice(name="Do Anything Now", value="dan"),
        app_commands.Choice(name="Smart mode(AIM)", value="aim"),
        app_commands.Choice(name="Developer Mode", value="Developer Mode"),
    ])
    async def switchpersona(interaction: discord.Interaction, persona: app_commands.Choice[str]):
        if interaction.user == discordClient.user:
            return

        await interaction.response.defer(thinking=True)
        username = str(interaction.user)
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '/switchpersona [{persona.value}]' ({channel})")

        persona = persona.value

        if persona == personas.current_persona:
            await interaction.followup.send(f"> **WARN: Już ustawione na `{persona}` **")
        elif persona in personas.PERSONAS:
            try:
                await discordClient.switch_persona(persona)
                personas.current_persona = persona
                await interaction.followup.send(
                f"> **INFO: Przełączono na `{persona}` **")
            except Exception as e:
                await interaction.followup.send(
                    "> ERROR: Coś poszło nie tak, spróbuj ponownie później! ")
                logger.exception(f"Błąd podczas przełączania persony: {e}")
        else:
            await interaction.followup.send(
                f"> **ERROR: Brak dostępnej persony: `{persona}` 😿**")
            logger.info(
                f'{username} zażądał niedostępnej osoby: `{persona}`')


    @discordClient.event
    async def on_message(message):
        if discordClient.is_replying_all == "True":
            if message.author == discordClient.user:
                return
            if discordClient.replying_all_discord_channel_id:
                if message.channel.id == int(discordClient.replying_all_discord_channel_id):
                    username = str(message.author)
                    user_message = str(message.content)
                    discordClient.current_channel = message.channel
                    logger.info(f"\x1b[31m{username}\x1b[0m : '{user_message}' ({discordClient.current_channel})")

                    await discordClient.enqueue_message(message, user_message)
            else:
                logger.exception("replying_all_discord_channel_id nie znaleziono, należy użyć polecenia `/replyall`.")

    TOKEN = os.getenv("DISCORD_BOT_TOKEN")

    discordClient.run(TOKEN)
