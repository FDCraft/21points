import collections
import random
from typing import List, Dict

from mcdreforged.api.all import *


class Room(Serializable):
    open: bool = False
    isRunning: bool = False
    name: str = ""
    players: List[str] = []
    stopPlayers: List[str] = []
    playerCard: Dict[str, int] = dict()


Prefix = '!!21points'
room: Room

def help(src: PlayerCommandSource):
    reply = lambda msg: src.get_server().tell(src.player, msg)
    
    reply("§7=======§r 21点游戏 §7=======§r")
    reply("§7!!21points help§r: 显示本帮助信息")
    reply("§7!!21points join§r: 创建或加入一场游戏")
    reply("§7!!21points leave§r: 离开游戏")
    reply("§7!!21points start§r: 开始游戏")
    reply("§7!!21points get§r: 拿牌")
    reply("§7!!21points stop§r: 停牌")
    reply("§7!!21points giveup§r: 弃牌")
    reply("§7=======§r 规则 §7=======§r")
    reply("【游戏开始后，每位玩家都会从 2-20 拿到随机的初始点数。可以通过 !!21points get 继续拿牌，获得随机的1-10的点数。】")
    reply("【当觉得自己的牌已经足够合适时，通过 !!21points stop 停牌。也可以通过 !!21points giveup 来弃牌。】")
    reply("【当总点数已经超过 21 的时候，玩家爆牌。弃牌与爆牌的玩家将直接受到 Abs(21 - point) 的伤害。】")
    reply("【当剩下的玩家都停牌时，会开始结算。最接近 21 点的玩家获胜，其余玩家均受到 Abs(21 - point) 的伤害。】")
    return None


def join(src: PlayerCommandSource):
    if not room.isRunning:
        if not room.open:
            room.open = True
            room.name = src.player
            room.players.append(src.player)
            src.get_server().say(f"§e{src.player} §b开启了一场21点游戏，在聊天栏输入 §d!!21points join §b以加入游戏！")
            src.get_server().say("§b在聊天栏输入 §d!!21points leave §b以离开游戏。")
            src.get_server().tell(src.player, "§b在聊天栏输入 §d!!21points start §b以开始游戏。")
        else: 
            if src.player not in room.players:
                room.players.append(src.player)
                src.get_server().say(f"§e{src.player} §b加入了一场21点游戏，当前已有 §e{len(room.players)} §b位玩家！")
                src.get_server().tell(src.player, "§b在聊天栏输入 §d!!21points leave §b以离开游戏。")
            else:
                src.get_server().tell(src.player, "§d您已加入本场游戏！") 
    else:
        src.get_server().tell(src.player, "§d21点游戏正在进行中，请等待本场游戏结束！")
    
    return None


def leave(src: PlayerCommandSource):
    global room
    if src.player in room.players:
        if not room.isRunning:
            if src.player == room.name:
                room = Room()
                src.get_server().say(f"§b庄主离开了游戏，本场游戏取消！")
            else: 
                room.players.remove(src.player)
                src.get_server().say(f"§e{src.player} §b离开了21点游戏！当前还有 §e{len(room.players)} §b位玩家！")
        else:
            src.get_server().tell(src.player, "§d21点游戏正在进行中，不能离开！")
    else:
        src.get_server().tell(src.player, "§d您尚未加入游戏！")
    
    return None


def start(src: PlayerCommandSource):
    if (room.open):
        if (not room.isRunning):
            if (src.player == room.name):
                src.get_server().say(f"§e{src.player} §b发起的一场21点游戏准备开始！当前已有 §e{len(room.players)} §b位玩家！")
                room.isRunning = True
                for player in room.players:
                    room.playerCard[player] = random.randint(2, 20)
                    src.get_server().tell(player, f"§e{player} §b，你的初始牌和是 §b{room.playerCard[player]} 。")
            else:
                src.get_server().tell(src.player, "§d您不是本场游戏的庄主！")
        else:
            src.get_server().tell(src.player, "§d21点游戏正在进行中，请等待本场游戏结束！")
    else: 
        src.get_server().tell(src.player, "§b还不存在需要启动的游戏！在聊天栏输入 §d!!21points join §b以开始一场游戏！")
    
    return None


def get(src: PlayerCommandSource):
    if room.isRunning:
        if (src.player in room.players and src.player not in room.stopPlayers):
            card = random.randint(1, 10)
            room.playerCard[src.player] = room.playerCard[src.player] + card
            src.get_server().say(f"§e{src.player} §b抽到了 §e{card} §b！现在他的牌和是 §e{room.playerCard[src.player]} 。")
            if (room.playerCard[src.player] > 21):
                damage = abs(room.playerCard[src.player] - 21) * 2
                src.get_server().say(f"§e{src.player} §b爆牌！将会受到 §e{damage} §b的伤害！")
                src.get_server().execute(f'damage {src.player} {damage} minecraft:generic_kill')
                room.playerCard.pop(src.player)
                room.players.remove(src.player)
                check(src)
        else:
            src.get_server().tell(src.player, f"§e{src.player} §b,你没有加入游戏或你已经停牌/爆牌/弃牌了！")
    else: 
        src.get_server().tell(src.player, "§b未存在启动的游戏！")
    
    return None


def stop(src: PlayerCommandSource):
    if room.isRunning:
        if (src.player in room.players and src.player not in room.stopPlayers):
            src.get_server().say(f"§e{src.player} §b以点数 §e{room.playerCard[src.player]} §b停牌！")
            room.stopPlayers.append(src.player)
            check(src)
        else:
            src.get_server().tell(src.player, f"§e{src.player} §b,你没有加入游戏或你已经停牌/爆牌/弃牌了！")
    else: 
        src.get_server().tell(src.player, "§b未存在启动的游戏！")
    
    return None


def fail(src: PlayerCommandSource):
    if room.isRunning:
        if (src.player in room.players and src.player not in room.stopPlayers):
            damage = abs(room.playerCard[src.player] - 21) * 2
            src.get_server().say(f"§e{src.player} §b以点数 §e{room.playerCard[src.player]} §b弃牌！将会受到 §e{damage} §b的伤害！")
            src.get_server().execute(f'damage {src.player} {damage} minecraft:generic_kill')
            room.playerCard.pop(src.player)
            room.players.remove(src.player)
            check(src)
        else:
            src.get_server().tell(src.player, f"§e{src.player} §b,你没有加入游戏或你已经停牌/爆牌/弃牌了！")
    else: 
        src.get_server().tell(src.player, "§b未存在启动的游戏！")
    
    return None


def check(src: PlayerCommandSource):
    global room

    if (len(room.players) == len(room.stopPlayers)):
        src.get_server().say("§b全部玩家停牌！正在结算...")
        MaxPlayer = ""
        MaxSize = 0

        for key, value in room.playerCard.items():
            if value > MaxSize:
                MaxPlayer = key
                MaxSize = value
            
        src.get_server().say(f"§e{MaxPlayer} §b是最后的赢家！他的点数: §e{MaxSize} §b！")

        for key, value in room.playerCard.items():
                if key != MaxPlayer:
                    damage = abs(value - 21) * 2
                    src.get_server().execute(f'damage {key} {damage} minecraft:generic_kill')

        room = Room()

    return None


def leave_server(server: ServerInterface, player):
    global room
    if player in room.players:
        if not room.isRunning:
            if player == room.name:
                room = Room()
                server.say(f"§b庄主离开了游戏，本场游戏取消！")
            else: 
                room.players.remove(player)
                server.say(f"§e{player} §b离开了21点游戏！当前还有 §e{len(room.players)} §b位玩家！")
        else:
            room = Room()
            server.say("§d哎呀，有人逃跑啦！本场游戏取消！")

    
    return None


def on_player_left(server: ServerInterface, player):
	leave_server(server, player)

def on_load(server: PluginServerInterface, old):
    global room
    room = Room()
    server.register_help_message(Prefix, '21点小游戏')
    server.register_command(Literal(Prefix).requires(lambda src: src.is_player).
                        runs(help).
                        then(Literal('help').runs(help)).                            
                        then(Literal('join').runs(join)).
                        then(Literal('leave').runs(leave)).
                        then(Literal('start').runs(start)).
                        then(Literal('get').runs(get)).
                        then(Literal('stop').runs(stop)).
                        then(Literal('giveup').runs(fail)))
