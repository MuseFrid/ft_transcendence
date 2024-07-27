from .models import Game, PongPlayer, GameType, PlayerGameTypeStats, GameHistory
from django.contrib.auth.models import User
from django.db.models import F
from asgiref.sync import sync_to_async
import asyncio

party_list = {}

maps = [
	[ # 0
	],
	[ # 1
		{
			'type': 'triangle',
			'vertices': [
				{'x': 600, 'y': 150},
				{'x': 600 + 20, 'y': 0},
				{'x': 600 - 20, 'y': 0}
			]
		},
		{
			'type': 'triangle',
			'vertices': [
				{'x': 200, 'y': 50},
				{'x': 200 + 20, 'y': 0},
				{'x': 200 - 20, 'y': 0}
			]
		},
		{
			'type': 'triangle',
			'vertices': [
				{'x': 200, 'y': 450},
				{'x': 200 + 20, 'y': 600},
				{'x': 200 - 20, 'y': 600}
			]
		},
		{
			'type': 'triangle',
			'vertices': [
				{'x': 600, 'y': 550},
				{'x': 600 + 20, 'y': 600},
				{'x': 600 - 20, 'y': 600}
			]
		}
	],
	[ # 2
		{
			'type': 'rectangle',
			'vertices': [
				{'x': 0, 'y': 0},
				{'x': 50, 'y': 0},
				{'x': 50, 'y': 100},
				{'x': 0, 'y': 100}
			]
		},
		{
			'type': 'rectangle',
			'vertices': [
				{'x': 0, 'y': 500},
				{'x': 50, 'y': 500},
				{'x': 50, 'y': 600},
				{'x': 0, 'y': 600}
			]
		},
		{
			'type': 'rectangle',
			'vertices': [
				{'x': 750, 'y': 0},
				{'x': 800, 'y': 0},
				{'x': 800, 'y': 100},
				{'x': 750, 'y': 100}
			]
		},
		{
			'type': 'rectangle',
			'vertices': [
				{'x': 750, 'y': 500},
				{'x': 800, 'y': 500},
				{'x': 800, 'y': 600},
				{'x': 750, 'y': 600}
			]
		},
	],
	[ # 3
	]
]

import random
def make_map3():
	map3 = []
	for i in range(100, 400, 50):
		for j in range(100, 550, 50):
			if i%20 == 0 and not j%20 == 0 :
				continue
			if not i%20 == 0 and j%20 == 0 :
				continue
			if random.randint(1, 10)%2 == 0:
				continue
			map3.append({
				'type': 'rectangle',
				'vertices': [
					{'x': i - 25/2, 'y': j - 25/2},
					{'x': i + 25 - 25/2, 'y': j - 25/2},
					{'x': i + 25 - 25/2, 'y': j + 25 - 25/2},
					{'x': i - 25/2, 'y': j + 25 - 25/2},
				]
			})
			map3.append({
				'type': 'rectangle',
				'vertices': [
					{'x': 800 - i - 25/2, 'y': j - 25/2},
					{'x': 800 - i + 25 - 25/2, 'y': j - 25/2},
					{'x': 800 - i + 25 - 25/2, 'y': j + 25 - 25/2},
					{'x': 800 - i - 25/2, 'y': j + 25 - 25/2},
				]
			})
	maps[3] = map3 

class Party:
	def __init__(self, prop, id):
		self.game_id = id
		self.width = prop.width
		self.height = prop.height
		self.ball = prop.ball
		self.positions = prop.playerPositions
		self.player_number = prop.playerNumber
		players = prop.players.all()
		self.players = [self.get_player_info(player) for player in players]
		self.state = 'waiting'
		self.score = prop.maxScore
		self.player_speed = prop.paddleSpeed
		self.paddlePadding = 40
		self.paddleWidth = 10
		self.paddleHeight = 100
		self.ballR = 5
		if prop.mapId == 3:
			make_map3()
		self.map = maps[prop.mapId]

		self.players = sorted(self.players, key=lambda x: x['n'])

	def get_player_info(self, player):
		return {
			'name': player.player.username,
			'id': player.id,
			'score': player.score,
			'token': player.token,
			'n': player.n,
			'hit': 0
		}

	def add_ai_player(self):
		self.players.append({
			'name': 'AI',
			'id': 0,
			'score': 0,
			'n': 2,
			'token': 'AI',
			'hit': 0
		})
		threading.Thread(target=ai_play, args=(self,)).start()
	
	def save(self):
		try:
			game = Game.objects.get(id=self.game_id)  # Get the game
			for player in self.players:
				if player['name'] == 'AI': # TODO : other
					continue
				# save player score
				p = PongPlayer.objects.get(id=player['id'])
				p.score = player['score']
				p.save()

				# save player stats
				p = User.objects.get(username=player['name'])
				game_type = GameType.objects.get(name="pong")

				stats, created = PlayerGameTypeStats.objects.get_or_create(player=p, game_type=game_type)
				stats.games_played = F('games_played') + 1
				if player['score'] >= self.score: 
					stats.games_won = F('games_won') + 1
				else:
					stats.games_lost = F('games_lost') + 1
				stats.total_score = F('total_score') + player['score']
				stats.save()

				# save history
				pong = game.gameProperty
				GameHistory.objects.get_or_create(player=p, game=pong, score=player['score'])
				# delete game
			game.delete()
		except Exception as e:
			game.delete()

party_list = {}

def setup(game_id, player):
	game = Game.objects.filter(id=game_id).first()
	party = party_list.get(game_id)
	if party:
		setting = {
			'obstacles': party.map,
		}
	if party and party.state == 'playing':
		return setting
	if game:
		prop = game.gameProperty
		if not prop.ball:
			prop.ball = {'x': prop.width/2, 'y': prop.height/2, 'dx': prop.ballSpeed, 'dy': prop.ballSpeed}
		party = Party(prop, game_id)
		if party.player_number == 1:
			party.add_ai_player()
		if party.player_number == prop.players.count():
			party.state = 'playing'
		party_list[game_id] = party
		
		return {'obstacles': party.map}
	return None

def get_pong_state(game_id):
	game = party_list.get(game_id)
	if game is None:
		return {'error': f'Game ID {game_id} not found in party list.'}
	# if game.state == 'waiting':
	# 	return {'error': 'Game not started yet.'}
	scores = [player['score'] for player in game.players]
	username = [player['name'] for player in game.players]
	game_state = {
		'x': game.ball['x'],
		'y': game.ball['y'],
		'positions': game.positions,
		'scores': scores,
		'usernames': username,
		'state': game.state
	}
	if (game.state == 'finished'):
		game_state['winner'] = game.players[0] if game.players[0]['score'] >= game.score else game.players[1]
		del party_list[game_id]  # remove party from party_list
	return game_state

def get_n(id, token):
	game = party_list.get(id)
	if game is None:
		# print(f"Game ID {id} not found in party list.")
		return
	for player in game.players:
		if player['token'] == token:
			return player['n']
	return None

def move_pong(game_id, n, direction):
	game = party_list.get(game_id)
	if game is None:
		return
	if game.state != 'playing':
		return
	if game.positions[n - 1] > 50 and direction == 'up':
		game.positions[n - 1] -= game.player_speed
	elif game.positions[n - 1] < game.height - 50 and direction == 'down':
		game.positions[n - 1] += game.player_speed

import time
def ai_play(game):
	last_update_time = 0
	while True:
		if game.ball['dx'] > 0 or game.ball['x'] > game.width/2:
			# pass
			current_time = time.time()
			if current_time - last_update_time >= 1:
				# Update future ball position
				future_y = game.ball['y']
				future_x = game.ball['x']
				future_dy = game.ball['dy']
				future_dx = game.ball['dx']
				for _ in range(100):  # Predict x frames ahead
					future_y += future_dy
					future_x += future_dx
					# Check for future collision with top and bottom
					if future_y <= 0 + game.ballR or future_y >= game.height - game.ballR:
						future_dy *= -1  # Reverse future y direction
						future_y += future_dy*1.5
				
					new_ball = {'x': future_x, 'y': future_y}
					for shape in game.map:
						if in_polygon_with_radius(new_ball, shape['vertices'], game.ballR):
							nex_x = future_x + (future_dx * -1)
							new_point = {'x': nex_x, 'y': future_y}
							if in_polygon_with_radius(new_point, shape['vertices'], game.ballR):
								future_dy *= -1
								future_y += future_dy
							else:
								future_dx *= -1
								future_x += future_dx
						if future_x >= game.width:
							break

					# Check for future collision goal
					if future_x >= game.width - game.paddlePadding:
						break

				# Update the last update time
				last_update_time = current_time

			# Move paddle towards future ball position
			for _ in range(20):
				if future_y < game.positions[1] - 10:
					move_pong(game.game_id, 2, 'up')
					time.sleep(0.05)
					if future_y >= game.positions[1]:
						break
				elif future_y > game.positions[1] + 10:
					move_pong(game.game_id, 2, 'down')
					time.sleep(0.05)
					if future_y <= game.positions[1]:
						break
		else:
			time.sleep(0.5)
		time.sleep(0.1)

def check_collision(game, vertices):
	if in_polygon_with_radius(game.ball, vertices, game.ballR):
		nex_x = game.ball['x'] + (game.ball['dx'] * -1)
		new_point = {'x': nex_x, 'y': game.ball['y']}
		if in_polygon_with_radius(new_point, vertices, game.ballR):
			game.ball['dy'] *= -1
			game.ball['y'] += game.ball['dy']
		else:
			game.ball['dx'] *= -1
			game.ball['x'] += game.ball['dx']

import threading
async def update_pong(game_id):
	if game_id not in party_list:
		# print(f"Game ID {game_id} not found in party list.")
		return
	game = party_list[game_id]
	if game.state != 'playing':
		# print(f"Game ID {game_id} not playing.")
		return
	
	# move ball
	game.ball['x'] += game.ball['dx']
	game.ball['y'] += game.ball['dy']
	# check out collision y
	if game.ball['y'] <= 0 + game.ballR or game.ball['y'] >= game.height - game.ballR:
		game.ball['dy'] *= -1
		game.ball['y'] += game.ball['dy']*1.5

	# check out collision x
	if game.ball['x'] <= game.paddlePadding/4 + game.ballR:
		game.players[1]["score"] += 1
		game.ball['x'] = game.width/2
	if game.ball['x'] >= game.width - game.paddlePadding/4 - game.ballR:
		game.players[0]["score"] += 1
		game.ball['x'] = game.width/2

	# check game over
	if game.players[0]["score"] >= game.score or game.players[1]["score"] >= game.score:
		game.state = 'finished'
		await sync_to_async(game.save)()
		# del party_list[game_id]  # remove party from party_list
		return game.state

	# check collision player 1
	paddleVertices = [
		{'x': game.paddlePadding, 'y': game.positions[0] - game.paddleHeight/2},
		{'x': game.paddlePadding + game.paddleWidth, 'y': game.positions[0] - game.paddleHeight/2},
		{'x': game.paddlePadding + game.paddleWidth, 'y': game.positions[0] + game.paddleHeight/2},
		{'x': game.paddlePadding, 'y': game.positions[0] + game.paddleHeight/2}
	]
	check_collision(game, paddleVertices)
		

	# check collision player 2
	paddleVertices = [
		{'x': game.width - game.paddlePadding, 'y': game.positions[1] - game.paddleHeight/2},
		{'x': game.width - game.paddlePadding - game.paddleWidth, 'y': game.positions[1] - game.paddleHeight/2},
		{'x': game.width - game.paddlePadding - game.paddleWidth, 'y': game.positions[1] + game.paddleHeight/2},
		{'x': game.width - game.paddlePadding, 'y': game.positions[1] + game.paddleHeight/2}
	]
	check_collision(game, paddleVertices)
	
	for shape in game.map:
		check_collision(game, shape['vertices'])

import math
def in_polygon_with_radius(point, vertices, radius=0):
    x, y = point['x'], point['y']

    # Check the point itself first
    if in_polygon(point, vertices):
        return True

    # Check around the point in a circle defined by the radius
    for angle in range(0, 360, 20):  # Check every 20 degrees
        rad = math.radians(angle)
        x_offset = radius * math.cos(rad)
        y_offset = radius * math.sin(rad)

        test_point = {'x': x + x_offset, 'y': y + y_offset}
        if in_polygon(test_point, vertices):
            return True

    return False

def in_polygon(point, vertices):
	x, y = point['x'], point['y']
	num_vertices = len(vertices)

	inside = False
	j = num_vertices - 1
	for i in range(num_vertices):
		if (vertices[i]['y'] > y) != (vertices[j]['y'] > y) and \
				x < (vertices[j]['x'] - vertices[i]['x']) * (y - vertices[i]['y']) / (vertices[j]['y'] - vertices[i]['y']) + vertices[i]['x']:
			inside = not inside
		j = i
	return inside