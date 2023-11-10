import datetime
from utils.music.models import LavalinkPlayer
import disnake
from utils.music.converters import fix_characters, time_format, get_button_style
import itertools
from utils.others import ProgressBar, PlayerControls


class DefaultProgressbarStaticSkin:

    __slots__ = ("name", "preview")

    def __init__(self):
        self.name = "default_progressbar_static"
        self.preview = "https://cdn.discordapp.com/attachments/554468640942981147/1047187414176759860/progressbar_static_skin.png"

    def setup_features(self, player: LavalinkPlayer):
        player.mini_queue_feature = False
        player.controller_mode = True
        player.auto_update = 15
        player.hint_rate = player.bot.config["HINT_RATE"]
        player.static = True

    def load(self, player: LavalinkPlayer) -> dict:

        data = {
            "content": None,
            "embeds": []
        }

        embed = disnake.Embed(color=player.bot.get_color(player.guild.me))
        embed_queue = None

        if not player.paused:
            embed.set_author(
                name="Tocando Agora:",
                icon_url="https://cdn.discordapp.com/attachments/480195401543188483/895862881105616947/music_equalizer.gif"
            )
        else:
            embed.set_author(
                name="Em Pausa:",
                icon_url="https://cdn.discordapp.com/attachments/480195401543188483/896013933197013002/pause.png"
            )

        if player.current_hint:
            embed.set_footer(text=f"💡 Dica: {player.current_hint}")
        elif player.node.identifier != "LOCAL":
            embed.set_footer(
                text=str(player),
                icon_url="https://cdn.discordapp.com/attachments/480195401543188483/907119505971486810/speaker-loud-speaker.gif"
            )

        if player.current.is_stream:
            duration = "```ansi\n🔴 [31;1m Livestream[0m```"
        else:

            progress = ProgressBar(
                player.position,
                player.current.duration,
                bar_count=17
            )

            duration = f"```ansi\n[34;1m[{time_format(player.position)}] {('='*progress.start)}[0m🔴️[36;1m{'-'*progress.end} " \
                       f"[{time_format(player.current.duration)}][0m```\n"

        vc_txt = ""
        queue_img = ""

        try:
            vc_txt = f"\n> *️⃣ **⠂Canal de voz:** {player.guild.me.voice.channel.mention}"
        except AttributeError:
            pass

        txt = f"[`{player.current.single_title}`]({player.current.uri})\n\n" \
              f"> 💠 **⠂Por:** {player.current.authors_md}\n" \
              f"> ✋ **⠂Pedido por:** <@{player.current.requester}>\n" \
              f"> 🔊 **⠂Volume:** `{player.volume}%`"

        if player.current.track_loops:
            txt += f"\n> 🔂 **⠂Repetições restante:** `{player.current.track_loops}`"

        if player.loop:
            if player.loop == 'current':
                e = '🔂'
                m = 'Música atual'
            else:
                e = '🔁'
                m = 'Fila'
            txt += f"\n> {e} **⠂Modo de repetição:** `{m}`"

        if player.nightcore:
            txt += f"\n> 🇳 **⠂Efeito nightcore:** `ativado`"

        if player.current.album_name:
            txt += f"\n> 💽 **⠂Álbum:** [`{fix_characters(player.current.album_name, limit=20)}`]({player.current.album_url})"

        if player.current.playlist_name:
            txt += f"\n> 📑 **⠂Playlist:** [`{fix_characters(player.current.playlist_name, limit=20)}`]({player.current.playlist_url})"

        if player.keep_connected:
            txt += "\n> ♾️ **⠂Modo 24/7:** `Ativado`"

        elif player.restrict_mode:
            txt += f"\n> 🔒 **⠂Modo restrito:** `Ativado`"

        if player.ping:
            txt += f"\n> 📶 **⠂Latência:** `{player.ping}ms`"

        txt += f"{vc_txt}\n"

        if player.command_log:
            txt += f"> {player.command_log_emoji} **⠂Última Interação:** {player.command_log}\n"

        txt += duration

        if qlenght:=len(player.queue):

            queue_txt = "\n".join(
                f"`{(n + 1):02}) [{time_format(t.duration) if not t.is_stream else '🔴 Livestream'}]` [`{fix_characters(t.title, 33)}`]({t.uri})"
                for n, t in (enumerate(itertools.islice(player.queue, 20)))
            )

            embed_queue = disnake.Embed(title=f"Músicas na fila: {qlenght}", color=player.bot.get_color(player.guild.me),
                                        description=f"\n{queue_txt}")

            if not player.loop and not player.keep_connected and not player.paused and not player.current.is_stream:

                queue_duration = 0

                for t in player.queue:
                    if not t.is_stream:
                        queue_duration += t.duration

                embed_queue.description += f"\n`[⌛ As músicas acabam` <t:{int((disnake.utils.utcnow() + datetime.timedelta(milliseconds=(queue_duration + (player.current.duration if not player.current.is_stream else 0)) - player.position)).timestamp())}:R> `⌛]`"

            embed_queue.set_image(url=queue_img)

        embed.description = txt
        embed.set_image(url=player.current.thumb)

        data["embeds"] = [embed_queue, embed] if embed_queue else [embed]

        data["components"] = [
            disnake.ui.Button(emoji="⏯️", custom_id=PlayerControls.pause_resume, style=get_button_style(player.paused)),
            disnake.ui.Button(emoji="⏮️", custom_id=PlayerControls.back),
            disnake.ui.Button(emoji="⏹️", custom_id=PlayerControls.stop),
            disnake.ui.Button(emoji="⏭️", custom_id=PlayerControls.skip),
            disnake.ui.Button(emoji="📑", custom_id=PlayerControls.queue),
            disnake.ui.Select(
                placeholder="Mais opções:",
                custom_id="musicplayer_dropdown_inter",
                min_values=0, max_values=1,
                options=[
                    disnake.SelectOption(
                        label="Adicionar música", emoji="<:add_music:588172015760965654>",
                        value=PlayerControls.add_song,
                        description="Adicionar uma música/playlist na fila."
                    ),
                    disnake.SelectOption(
                        label="Adicionar favorito", emoji="⭐",
                        value=PlayerControls.enqueue_fav,
                        description="Adicionar um de seus favoritos na fila."
                    ),
                    disnake.SelectOption(
                        label="Tocar do inicio", emoji="⏪",
                        value=PlayerControls.seek_to_start,
                        description="Voltar o tempo da música atual para o inicio."
                    ),
                    disnake.SelectOption(
                        label="Volume", emoji="🔊",
                        value=PlayerControls.volume,
                        description="Ajustar volume."
                    ),
                    disnake.SelectOption(
                        label="Misturar", emoji="🔀",
                        value=PlayerControls.shuffle,
                        description="Misturar as músicas da fila."
                    ),
                    disnake.SelectOption(
                        label="Readicionar", emoji="🎶",
                        value=PlayerControls.readd,
                        description="Readicionar as músicas tocadas de volta na fila."
                    ),
                    disnake.SelectOption(
                        label="Repetição", emoji="🔁",
                        value=PlayerControls.loop_mode,
                        description="Ativar/Desativar repetição da música/fila."
                    ),
                    disnake.SelectOption(
                        label="Nightcore", emoji="🇳",
                        value=PlayerControls.nightcore,
                        description="Ativar/Desativar o efeito nightcore."
                    ),
                    disnake.SelectOption(
                        label="Ativar/Desativar modo restrito", emoji="🔐",
                        value=PlayerControls.restrict_mode,
                        description="Apenas DJ's/Staff's podem usar comandos restritos."
                    ),
                ]
            ),
        ]

        return data

def load():
    return DefaultProgressbarStaticSkin()
