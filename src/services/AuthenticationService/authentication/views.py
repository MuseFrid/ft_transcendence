from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.hashers import make_password, check_password
import requests, secrets, os
from .models import UserToken

# TODO : HTTPS, check django security settings

@csrf_exempt
# 42 auth
@require_GET
def oauth42(request):
	code = request.GET.get('code', None)
	if not code:
		return JsonResponse({'error': 'Code not provided'}, status=400)
	try:
		# Exchange the authorization code for an access token
		response = requests.post('https://api.intra.42.fr/oauth/token', data={
			'grant_type': 'authorization_code',
			'client_id': os.environ['42_CLIENT_UID'],
			'client_secret': os.environ['42_CLIENT_SECRET'],
			'code': code,
			'redirect_uri': os.environ['OAUTH_REDIRECT_URI'],  # Replace with your redirect URI
		})
		
		if response.status_code != 200:
			return JsonResponse({'error': 'Failed to get access token'}, status=response.status_code)

		data = response.json()
		access_token = data['access_token']
		# Get the user's profile
		response = requests.get('https://api.intra.42.fr/v2/me', headers={
			'Authorization': f'Bearer {access_token}',
		})
		
		if response.status_code != 200:
			return JsonResponse({'error': 'Failed to fetch user data'}, status=response.status_code)

		data = response.json()
		username = data['login']
		email = data['email']

		# Check if a user with this email already exists
		if not User.objects.filter(email=email).exists():
			if User.objects.filter(username=username).exists():
				username += secrets.token_hex(4)
				if User.objects.filter(username=username).exists(): # TODO : improve
					return JsonResponse({'error': 'Username already taken'}, status=400)
			# Create a new user
			User.objects.create_user(username=username, email=email)

		user = User.objects.get(email=email)
		login(request, user)
		token = secrets.token_hex(16)
		hashed_token = make_password(token)
		UserToken.objects.update_or_create(user=user, defaults={'token': hashed_token})

		return JsonResponse({'message': f'Logged in successfully as {username}'}, status=201)
	
	except:
		return JsonResponse({'error': 'An error occurred while processing your request'}, status=500)

@csrf_exempt # Disable CSRF protection for this view
@require_POST
def register(request): # TODO : login at same time ?
	try:
		username = request.POST.get('username')
		password = request.POST.get('password')
		email = request.POST.get('email')
		if not username or not password or not email:
			return JsonResponse({'error': 'Missing required fields'}, status=400)
		if User.objects.filter(username=username).exists():
			return JsonResponse({'error': 'Username already taken'}, status=400)
		if User.objects.filter(email=email).exists():
			return JsonResponse({'error': 'Email already taken'}, status=400)
		User.objects.create_user(username=username, password=password, email=email)
		return JsonResponse({'message': 'User registered successfully'})
	except:
		return JsonResponse({'error': 'Failed to register user'}, status=400)

@csrf_exempt # Disable CSRF protection for this view
@require_POST
# login  # TODO : check
def login_view(request):
	try:
		username = request.POST.get('username')
		password = request.POST.get('password')
		if not username or not password:
			return JsonResponse({'error': 'Missing required fields'}, status=400)
		user = authenticate(request, username=username, password=password) # slow
		if not user: # TODO : handle email
			username = User.objects.get(email=username).username
			print(username)
			user = authenticate(request, username=username, password=password)
		if user is not None:
			login(request, user)
			token = secrets.token_hex(16)
			hashed_token = make_password(token)
			UserToken.objects.update_or_create(user=user, defaults={'token': hashed_token})
			return JsonResponse({'token': token, 'UserId': user.id})
		else:
			return JsonResponse({'error': 'Invalid login credentials'}, status=400)
	except:
		return JsonResponse({'error': 'Failed to login'}, status=400)
	
@csrf_exempt # Disable CSRF protection for this view
@require_POST
def logout_view(request):
	try:
		if request.user.is_authenticated:
			UserToken.objects.filter(user=request.user).delete()
		logout(request)
		return JsonResponse({'message': 'Logged out successfully'})
	except:
		return JsonResponse({'error': 'Failed to logout'}, status=400)

def user_to_dict(user):
	return {
		'id': user.id,
		'username': user.username,
		'email': user.email
	}

def verify_token(request, token=None):
	user_id = request.GET.get('UserId')

	if not token:
		auth_header = request.META.get('HTTP_AUTHORIZATION', '')
		token = auth_header.split(' ')[1] if ' ' in auth_header else ''

	try:
		user_token = UserToken.objects.get(user_id=user_id)
		if check_password(token, user_token.token):
			return 200
		else:
			return 401
	except UserToken.DoesNotExist:
		return 404

@csrf_exempt # Disable CSRF protection for this view
@require_GET
def me(request):
	# session_key = request.session.session_key
	if request.user.is_authenticated:
		return JsonResponse(user_to_dict(request.user))
	
	status = verify_token(request)
	if (status == 200):
		user = User.objects.get(id=request.GET.get('UserId'))
		return JsonResponse(user_to_dict(user))
	elif (status == 401):
		return JsonResponse({'error': 'Invalid token'}, status=401)
	return JsonResponse({'error': 'User token not found'}, status=404)

@csrf_exempt # Disable CSRF protection for this view
# service comunication
def get_user_from_session(request): # TODO : remove and use /me ?
	session_key = request.GET.get('session_key')
	token = request.GET.get('token') # TODO : HTTP_AUTHORIZATION
	if not session_key:
		status = verify_token(request, token)
		if (status == 200):
			user = User.objects.get(id=request.GET.get('UserId'))
			return JsonResponse({'username': user.username, 'email': user.email})
		elif (status == 401):
			return JsonResponse({'error': 'Invalid token'}, status=401)
		return JsonResponse({'error': 'User token not found'}, status=404)
	else:
		sess = Session.objects.get(session_key=session_key)
		uid = sess.get_decoded().get('_auth_user_id')
		user = User.objects.get(id=uid)
	return JsonResponse({'username': user.username, 'email': user.email})


# dev
def views_game(request):
	with open(os.path.join(os.path.dirname(__file__), 'templates/home.html'), 'r') as file:
		data = file.read()
	return HttpResponse(data)

# dev
def get_css(request):
	with open(os.path.join(os.path.dirname(__file__), 'templates/main.css'), 'r') as file:
		data = file.read()
	return HttpResponse(data, content_type='text/css')

# dev
def get_game_page(request):
	with open(os.path.join(os.path.dirname(__file__), 'templates/game.html'), 'r') as file:
		data = file.read()
	return HttpResponse(data)

def get_js(request):
	with open(os.path.join(os.path.dirname(__file__), 'templates/pong.js'), 'r') as file:
		data = file.read()
	return HttpResponse(data, content_type='text/javascript')